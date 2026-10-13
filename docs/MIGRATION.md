# Audit and migration notes

The source was `douwwii/NAS` at `1ad208c` (11 reachable commits). Original clones and a Git bundle are retained outside this repository under the portfolio's `.migration/` directory.

The original root combined source, lab inputs, bytecode and generated outputs. Bytecode, 24 generated configurations and visualization JSON were removed from current Git tracking; they remain in the original clone and historical commits. Generators and runtime modules now form `network_automation`, intent is in `configs`, and the topology is in `labs`. Root executable entry points retain their names.

Corrections: declare the Python 3.13+ Telnet dependency, resolve project runtime cleanup relative to the selected lab, limit single-router full reset to its target, and reconcile shutdown customer interfaces. The generation algorithm is unchanged. Ruff standardizes formatting and imports.

The historical-object audit examined 104 distinct reachable blobs using token, private-key and assigned-secret patterns. No matching secret was found; this limited scan is not a proof that no secret exists. Private IP ranges and AS values belong to the supplied academic lab. IOS binaries were absent from tracked files and are now explicitly ignored.

The original history is retained without force pushes. The owner requested public publication under `douwwii/network-configuration-automation`; the local origin is updated when that rename is applied. No original history or contributor attribution is removed.

Final review makes deployment modes mutually exclusive and stops subsequent stages after failed router jobs. Offline regression tests cover those failure paths.
