# Verification record

Verification performed on Fedora on 2026-10-13:

- Python 3.14.8: 19 offline tests passed.
- Python 3.12.15: 19 offline tests passed.
- Ruff 0.17.0: lint and formatting checks passed.
- `python config_auto.py` generated 24 phase/full configuration files plus visualization JSON.
- All 24 generated files were byte-identical to the original tracked outputs at `1ad208c`.
- The default GNS3 topology was parsed and console discovery was tested without opening any console connection.

Telnet imports produce a deprecation warning: Python 3.12 uses its deprecated standard-library implementation, while Python 3.14 uses the declared third-party copy. This does not prevent offline generation but remains a maintenance limitation.

Live GNS3 deployment, Cisco IOS command acceptance, route convergence and end-to-end traffic were not checked: GNS3 and the required IOS runtime were unavailable. No configuration was sent to any router during verification.

Final publication review added regression checks for failed reset/phase jobs, mutually exclusive deployment modes and invalid reconciliation targets before console access. All tests passed with Python 3.12 and 3.14.
