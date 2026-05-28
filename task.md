# StegVerse-002 / core-lite Task

## Title

Repair declared-task execution so output-package success requires the expected file shape on `main`.

## Operator Context

The repo has already accepted and persisted the StegVerse output-authority bundle.

The following are present on `main`:

- `scripts/package_stegverse_governed_output.py`
- `tools/tasks/task_catalog.json`
- task catalog entry: `stegverse.output.package`

The script itself declares and writes the expected output shape:

- `outputs/stegverse_output.md`
- `outputs/stegverse_output.json`
- `reports/current/stegverse_output_report.json`
- `receipts/current/stegverse_output_receipt.jsonl`
- `dist/run_artifacts/stegverse-governed-output.zip`

However, a GitHub Actions run can currently appear successful without proving that this file shape exists on `main`.

This means the failure boundary is not the output-authority script and not the task catalog. The failure boundary is the workflow/task execution and persistence path.

## Objective

Modify `.github/workflows/core-lite-intake.yml` so a `workflow_dispatch` run with:

```text
task_id: stegverse.output.package
input_type: [blank]
input_path: [blank]
dry_run: false
agent_provider: none
```

does all of the following:

1. Routes into a real declared-task execution job.
2. Executes:

```bash
python -m tools.scripts.task_dispatcher \
  --task-id "stegverse.output.package" \
  --task-catalog tools/tasks/task_catalog.json \
  --entity "StegVerse-002" \
  --stage "SV002-M10"
```

3. Captures stdout, stderr, and exit code into `reports/current/`.
4. Checks that the expected output shape exists after task execution.
5. Fails the workflow if any expected file is missing.
6. Commits and pushes the expected outputs/reports/receipts/dist artifacts back to `main`.
7. Writes a clear GitHub Actions step summary showing:
   - selected route
   - task_id
   - command executed
   - exit code
   - each expected output file present/missing
   - commit status: `pushed`, `no_changes`, or `failed`

## Required Expected Output Contract

After `stegverse.output.package` runs, the workflow must require these files:

```text
outputs/stegverse_output.md
outputs/stegverse_output.json
reports/current/stegverse_output_report.json
receipts/current/stegverse_output_receipt.jsonl
dist/run_artifacts/stegverse-governed-output.zip
```

If any are missing, the workflow must fail.

Do not allow a green workflow result unless all five files exist.

## Scope

Only modify the minimum required workflow logic.

Preferred target file:

```text
.github/workflows/core-lite-intake.yml
```

Do not change the output-authority script unless inspection proves it is the direct cause.

Do not rename the existing task.

Do not create a second task for the same purpose.

Do not create a new workflow if the existing workflow can be repaired.

## Safety / Governance Rules

- LLM providers may propose code, but they do not become output authority.
- The workflow repair must preserve the rule that provider outputs are candidate evidence only.
- The task run must remain local to repository artifacts.
- No external deploy, publication, or consequence-bearing action is allowed.
- Do not add broad write patterns that commit `incoming/` bundles unless explicitly required.
- Prefer committing only:
  - `outputs/`
  - `reports/current/`
  - `receipts/current/`
  - `dist/`
  - `tracking/`
  - `agent_history/` if generated

## Done Definition

This task is done only when:

1. `.github/workflows/core-lite-intake.yml` has a declared-task route for `agent_provider=none` and nonblank `task_id`.
2. The declared-task route executes `tools.scripts.task_dispatcher`.
3. The route validates the exact output file shape for `stegverse.output.package`.
4. Missing expected files cause workflow failure.
5. Successful output package runs commit/push the generated files to `main`.
6. The GitHub Actions summary gives quick-glance diagnosis without opening logs.

## Verification Run

After repair, run:

```text
task_id: stegverse.output.package
skip_tasks: false
stage_override: SV002-M10
repair_target: [blank]
input_type: [blank]
input_path: [blank]
kv_packet: [blank]
dry_run: false
agent_provider: none
```

Expected result on `main`:

```text
outputs/stegverse_output.md
outputs/stegverse_output.json
reports/current/stegverse_output_report.json
receipts/current/stegverse_output_receipt.jsonl
dist/run_artifacts/stegverse-governed-output.zip
```

If the workflow completes green without those files on `main`, the repair is incomplete.
