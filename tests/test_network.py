import sys
from pathlib import Path

import pytest

from network_automation import config_auto
from network_automation.config_common import allocate_subnets, get_loopbacks, load_intent
from network_automation.desired_state import build_phase4a_desired_state
from network_automation.reconcile_phase4a import parse_running_config, render_reconcile_commands
from network_automation.telnet_push import DEFAULT_PROJECT, clean_config_lines, router_console


def test_full_configs_cover_all_routers_and_protocols():
    intent = load_intent()
    configs = config_auto.build_full_configs(intent)
    assert set(configs) == set(intent["routeurs"])
    assert "router ospf 1" in configs["P1"]
    assert " mpls ip" in configs["P1"]
    assert " address-family vpnv4" in configs["PE1"]
    assert "  neighbor 10.255.255.4 send-community both" in configs["PE1"]
    assert "ip vrf CUST2" in configs["PE1"]
    assert " neighbor 172.16.0.9 remote-as 65000" in configs["CE3"]
    assert all(lines[-2:] == ["end", "write memory"] for lines in configs.values())


def test_core_allocations_are_stable_and_bounded():
    assert [str(net) for net in allocate_subnets("10.0.0.0/24", 30, 3)] == [
        "10.0.0.0/30",
        "10.0.0.4/30",
        "10.0.0.8/30",
    ]
    with pytest.raises(ValueError, match="too small"):
        allocate_subnets("10.0.0.0/30", 30, 2)
    assert get_loopbacks(load_intent())["PE2"]["ip"] == "10.255.255.4"


@pytest.mark.parametrize("router", ["PE1", "PE2", "CE1", "CE2", "CE3", "CE4"])
def test_reconciliation_is_empty_for_generated_desired_state(router):
    intent = load_intent()
    current = parse_running_config("\n".join(config_auto.build_full_configs(intent)[router]))
    assert render_reconcile_commands(router, build_phase4a_desired_state(intent)[router], current) == []


def test_reconciliation_enables_a_shutdown_customer_interface():
    intent = load_intent()
    current = parse_running_config("\n".join(config_auto.build_full_configs(intent)["CE1"]))
    current["interfaces"]["GigabitEthernet1/0"]["shutdown"] = True
    commands = render_reconcile_commands("CE1", build_phase4a_desired_state(intent)["CE1"], current)
    assert "interface GigabitEthernet1/0" in commands
    assert " no shutdown" in commands
    assert not any("erase" in command or "reload" in command for command in commands)


def test_reconciliation_changes_ce_as_without_reload():
    intent = load_intent()
    current = parse_running_config("\n".join(config_auto.build_full_configs(intent)["CE1"]))
    current["bgp"]["as"] = 65500
    commands = render_reconcile_commands("CE1", build_phase4a_desired_state(intent)["CE1"], current)
    assert "no router bgp 65500" in commands
    assert "router bgp 65101" in commands


def test_project_console_discovery_and_command_wrappers():
    assert DEFAULT_PROJECT is not None
    assert router_console(DEFAULT_PROJECT, "PE1") == 5012
    with pytest.raises(ValueError, match="not found"):
        router_console(DEFAULT_PROJECT, "MISSING")
    assert clean_config_lines(
        "configure terminal\n!\ninterface Loopback0\n ip address 10.0.0.1 255.255.255.255\nend\nwrite memory"
    ) == ["interface Loopback0", " ip address 10.0.0.1 255.255.255.255"]


def test_single_router_push_never_resets_other_routers(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        sys, "argv", ["config_auto.py", "--push-full", "CE1", "--project", str(tmp_path / "lab.gns3")]
    )
    monkeypatch.setattr(config_auto, "generate_all_configs", lambda: {"full": {"CE1": [], "PE1": []}})
    monkeypatch.setattr(config_auto, "router_console", lambda *_: 5000)
    monkeypatch.setattr(
        config_auto, "reset_router_before_push", lambda router, *_: calls.append(("reset", router))
    )
    monkeypatch.setattr(config_auto, "push_router_config", lambda router, *_: calls.append(("push", router)))
    monkeypatch.setattr(
        config_auto, "clean_dynamips_configs", lambda *_: pytest.fail("global cleanup requested")
    )
    monkeypatch.setattr(
        config_auto, "reset_pushable_routers", lambda *_: pytest.fail("global reset requested")
    )
    config_auto.main()
    assert calls == [("reset", "CE1"), ("push", "CE1")]


def test_generation_from_another_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert len(config_auto.build_full_configs(load_intent())) == 8
    assert Path(DEFAULT_PROJECT).is_file()


def test_failed_phase_stops_later_deployment_stages(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(config_auto, "pushable_routers", lambda *_: (["PE1", "P1"], []))

    def push(router, phase, *_):
        calls.append((router, phase))
        if router == "P1":
            raise OSError("simulated console failure")

    monkeypatch.setattr(config_auto, "push_router_config", push)
    with pytest.raises(RuntimeError, match="phase0_setup failed on: P1"):
        config_auto.push_in_order(
            {"phase0_setup": {}, "phase1_mpls": {}},
            ["phase0_setup", "phase1_mpls"],
            tmp_path / "lab.gns3",
            "127.0.0.1",
            "",
            1,
        )
    assert calls == [("PE1", "phase0_setup"), ("P1", "phase0_setup")]


def test_failed_reset_aborts_deployment(monkeypatch, tmp_path):
    monkeypatch.setattr(config_auto, "pushable_routers", lambda *_: (["PE1"], []))

    def fail_reset(*_):
        raise OSError("reset failed")

    monkeypatch.setattr(config_auto, "reset_router_before_push", fail_reset)
    with pytest.raises(RuntimeError, match="Router reset failed on: PE1"):
        config_auto.reset_pushable_routers({"full": {}}, tmp_path / "lab.gns3", "127.0.0.1", "", 1)


@pytest.mark.parametrize(
    "flags",
    [
        ["--push-phases", "--push-full", "CE1"],
        ["--push-full", "CE1", "--reconcile-phase4a", "ALL"],
    ],
)
def test_conflicting_deployment_modes_are_rejected_before_generation(monkeypatch, flags):
    monkeypatch.setattr(sys, "argv", ["config_auto.py", *flags])
    monkeypatch.setattr(config_auto, "generate_all_configs", lambda: pytest.fail("generation started"))
    with pytest.raises(SystemExit) as error:
        config_auto.main()
    assert error.value.code == 2


@pytest.mark.parametrize("target", ["MISSING", "P1"])
def test_invalid_reconciliation_target_is_rejected_before_console_access(monkeypatch, tmp_path, target):
    monkeypatch.setattr(config_auto, "collect_running_configs", lambda *_: pytest.fail("console accessed"))
    with pytest.raises(ValueError, match="only known PE and CE"):
        config_auto.reconcile_phase4a(tmp_path / "lab.gns3", "127.0.0.1", "", 1, target)
