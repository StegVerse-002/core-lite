# SV002 Declared Task Route Output Shape Repair

Adds a real `declared-task-route` job that executes `tools.scripts.task_dispatcher`, enforces the expected output shape for `stegverse.output.package`, fails closed if any required file is missing, and commits outputs after successful verification.

Install `.github/workflows/core-lite-intake.yml`.

Run after install:

```text
task_id: stegverse.output.package
skip_tasks: false
stage_override: SV002-M10
input_type: [blank]
input_path: [blank]
dry_run: false
agent_provider: none
```
