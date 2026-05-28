# Task: Repair StegVerse-002 Declared Task Route and Workflow Diagnostics

## Operator Intent

Repair `StegVerse-002/core-lite` so connected LLM agents inside the repo can complete the workflow repair without requiring repeated manual intervention from the human operator.

The immediate failure pattern is:

- The output-authority bundle has been ingested and persisted.
- `scripts/package_stegverse_governed_output.py` exists on `main`.
- `tools/tasks/task_catalog.json` contains `stegverse.output.package`.
- Running the workflow with `task_id=stegverse.output.package` can show workflow success, but the expected output files are not reliably proven or persisted on `main`.

The workflow must be repaired so a declared task route actually executes the requested task, captures results, writes a clear GitHub Actions summary, checks expected output files, commits generated outputs, and fails closed when the task does not produce expected artifacts.

## Absolute Governance Directive

No broad authority is admissible.

The connected LLMs may propose and implement this bounded workflow repair only. They must not grant themselves ongoing authority, secret access, deployment authority, production mutation authority, release authority, or approval authority.

The repair must preserve StegVerse's principle:

> LLMs produce candidate evidence. StegVerse produces governed output.

## Current Known Facts

The repository is:

```text
StegVerse-002/core-lite
```

The relevant existing files are:

```text
.github/workflows/core-lite-intake.yml
tools/scripts/task_dispatcher.py
tools/tasks/task_catalog.json
scripts/package_stegverse_governed_output.py
docs/STEGVERSE_OUTPUT_AUTHORITY.md
```

The task catalog already includes:

```text
task_id: stegverse.output.package
command: python scripts/package_stegverse_governed_output.py --repo-root .
```

Expected output files from that task are:

```text
outputs/stegverse_output.md
outputs/stegverse_output.json
reports/current/stegverse_output_report.json
receipts/current/stegverse_output_receipt.jsonl
dist/run_artifacts/stegverse-governed-output.zip
```

## Required Repair

Modify only the minimum necessary files.

Primary target:

```text
.github/workflows/core-lite-intake.yml
```

Secondary documentation target, only if useful:

```text
docs/WORKFLOW_SUMMARY_DIAGNOSTICS.md
```

Do not modify unrelated files.

## Required Workflow Behavior

The workflow must route as follows:

```text
IF workflow_dispatch AND input_type/input_path are provided:
    run declared-input-route
    process the input through core_lite.multimodal.pipeline
    commit installed bundle files/reports/receipts/tracking/dist
    write GitHub Actions summary showing route, input, report, decision, installed_count, rejected_count, key file checks

ELSE IF workflow_dispatch AND task_id is provided AND agent_provider == none:
    run declared-task-route
    execute tools.scripts.task_dispatcher
    capture stdout/stderr/exit code
    check expected output files for known tasks
    commit outputs/reports/receipts/tracking/dist
    write GitHub Actions summary showing task_id, exit code, output checks, commit status
    fail closed if task exits nonzero or expected artifacts are missing for a task that declares expected artifacts

ELSE IF agent_provider is openai/claude/both:
    run governed LLM collaboration route

ELSE:
    run default intake/status route or write an explicit no-op summary
```

## Declared Task Route Requirements

Add or repair a `declared-task-route` job in `.github/workflows/core-lite-intake.yml`.

It must run when:

```yaml
github.event_name == 'workflow_dispatch'
inputs.task_id != ''
inputs.input_type == ''
inputs.input_path == ''
inputs.agent_provider == 'none'
```

It must:

1. Check out repo.
2. Set up Python.
3. Determine stage:

```bash
STAGE="${{ inputs.stage_override }}"
if [ -z "${STAGE}" ]; then STAGE="SV002-M10"; fi
```

4. Run:

```bash
python -m tools.scripts.task_dispatcher \
  --task-id "${{ inputs.task_id }}" \
  --task-catalog tools/tasks/task_catalog.json \
  --entity "${STEGVERSE_ENTITY}" \
  --stage "${STAGE}"
```

5. If `inputs.dry_run == 'true'`, pass `--dry-run`.
6. Write stdout to:

```text
reports/current/task_dispatcher_result.json
```

7. Write stderr to:

```text
reports/current/task_dispatcher_stderr.txt
```

8. Write exit code to:

```text
reports/current/task_dispatcher_exit_code.txt
```

9. Append a GitHub Actions summary containing:

```text
route
task_id
stage
dry_run
exit_code
stdout/stderr report paths
expected output checks
commit status
```

10. Commit generated task outputs:

```text
outputs/
reports/current/
receipts/current/
tracking/
dist/
agent_history/
```

11. Upload one evidence artifact named:

```text
declared-task-route-evidence
```

containing:

```text
outputs/
reports/current/
receipts/current/
tracking/
dist/
```

## Expected Output Checks for stegverse.output.package

For `task_id == stegverse.output.package`, check these files after task execution:

```text
outputs/stegverse_output.md
outputs/stegverse_output.json
reports/current/stegverse_output_report.json
receipts/current/stegverse_output_receipt.jsonl
dist/run_artifacts/stegverse-governed-output.zip
```

If any are missing after a non-dry-run successful task execution, the workflow must fail closed with a clear summary.

Failure should say:

```text
Declared task executed but expected StegVerse output artifacts are missing.
```

## Declared Input Route Requirements

Preserve the existing declared-input-route, but ensure it:

1. Runs when `input_type` and `input_path` are provided with `agent_provider=none`.
2. Fails clearly if either field is missing.
3. Lists `incoming/` files if `input_path` does not exist.
4. Runs:

```bash
python -m core_lite.multimodal.pipeline \
  --repo-root . \
  --input-type "${{ inputs.input_type }}" \
  --input-path "${{ inputs.input_path }}" \
  --entity "${STEGVERSE_ENTITY}" \
  --stage "${STAGE}"
```

5. Commits installed paths, including at minimum:

```text
.github/workflows/
core_lite/
scripts/
schemas/
examples/
docs/
tests/
tools/
config/
machine/
outputs/
reports/current/
receipts/current/
tracking/
dist/
agent_history/
vault_template/
```

6. Writes summary diagnostics from `reports/current/bundle_ingest_report.json`.

## Summary Requirement

Every workflow_dispatch run must write a quick-glance summary to `$GITHUB_STEP_SUMMARY`.

The summary must make the following immediately visible:

```text
route selected
task_id
input_type
input_path
stage
dry_run
agent_provider
exit code
decision/status
installed_count, if bundle
expected output checks, if task
commit status
```

## Safety Constraints

Do not:

- Add new secrets.
- Expose secrets.
- Deploy anything.
- Create a release tag.
- Grant broad authority.
- Modify production deployment behavior.
- Add unbounded file write paths.
- Make LLM outputs authoritative.
- Bypass CGE/TVC concepts.
- Remove existing governance receipts.
- Delete existing reports unless replacing current run output files under `reports/current/`.

## Done Condition

This task is done only when all of the following are true:

1. `.github/workflows/core-lite-intake.yml` has a working `declared-task-route`.
2. `.github/workflows/core-lite-intake.yml` has a working `declared-input-route`.
3. Workflow summaries clearly show route diagnosis.
4. Running `task_id=stegverse.output.package` with `agent_provider=none` creates and commits:

```text
outputs/stegverse_output.md
outputs/stegverse_output.json
reports/current/stegverse_output_report.json
receipts/current/stegverse_output_receipt.jsonl
dist/run_artifacts/stegverse-governed-output.zip
```

5. No release tag is created.

## Requested Output from Connected LLMs

Return a concise implementation summary and commit the repaired workflow to `main`.

If the connected LLMs cannot commit directly, they must produce a single complete replacement for:

```text
.github/workflows/core-lite-intake.yml
```

and explain the exact manual placement path.
