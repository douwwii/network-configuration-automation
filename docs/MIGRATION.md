# Audit and migration notes

The source was `douwwii/NAS` at `1ad208c` (11 reachable commits). Original clones and a Git bundle are retained outside this repository under the portfolio's `.migration/` directory.

The original root combined source, lab inputs, bytecode and generated outputs. Bytecode, 24 generated configurations and visualization JSON were removed from current Git tracking; they remain in the original clone and historical commits. Generators and runtime modules now form `network_automation`, intent is in `configs`, and the topology is in `labs`. Root executable entry points retain their names.

Corrections: declare the Python 3.13+ Telnet dependency, resolve project runtime cleanup relative to the selected lab, limit single-router full reset to its target, and reconcile shutdown customer interfaces. The generation algorithm is unchanged. Ruff standardizes formatting and imports.

The historical-object audit examined 104 distinct reachable blobs using token, private-key and assigned-secret patterns. No matching secret was found; this limited scan is not a proof that no secret exists. Private IP ranges and AS values belong to the supplied academic lab. IOS binaries were absent from tracked files and are now explicitly ignored.

Renaming the GitHub repository and pushing the prepared branch require the owner's explicit approval. The local origin fetch URL initially retains `douwwii/NAS`; its push URL is disabled until approval. No remote was renamed, archived, deleted or pushed by this migration.
