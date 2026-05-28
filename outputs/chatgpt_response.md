# OpenAI — Governed Collaboration Proposal

## Current State Assessment

The current workflow in `StegVerse-002/core-lite` is not reliably producing and persisting expected output files when executing the `stegverse.output.package` task. The workflow needs to be repaired to ensure it executes tasks correctly, captures results, and commits outputs.

## Directive Alignment

The proposal aligns with the "no broad authority" directive by ensuring all actions are scoped, staged, and explicitly receipted. The workflow will be modified to adhere to these constraints, ensuring no broad authority is granted.

## Next Collaboration Primitive

The next step is to repair the `.github/workflows/core-lite-intake.yml` file to ensure the declared task route executes correctly and commits the expected outputs.

## Proposed Implementation

### Modify `.github/workflows/core-lite-intake.yml`

1. **Add `declared-task-route` Job:**
   - Trigger on `workflow_dispatch` with `task_id` provided and `agent_provider` set to `none`.
   - Steps:
     - Check out the repository.
     - Set up Python.
     - Determine the stage:
       ```bash
       STAGE="${{ inputs.stage_override }}"
       if [ -z "${STAGE}" ]; then STAGE="SV002-M10"; fi
       ```
     - Execute the task dispatcher:
       ```bash
       python -m tools.scripts.task_dispatcher \
         --task-id "${{ inputs.task_id }}" \
         --task-catalog tools/tasks/task_catalog.json \
         --entity "${STEGVERSE_ENTITY}" \
         --stage "${STAGE}"
       ```
     - Handle `dry_run` input.
     - Capture outputs:
       - Write stdout to `reports/current/task_dispatcher_result.json`.
       - Write stderr to `reports/current/task_dispatcher_stderr.txt`.
       - Write exit code to `reports/current/task_dispatcher_exit_code.txt`.
     - Append a GitHub Actions summary.
     - Commit generated outputs.
     - Upload evidence artifact.

2. **Ensure Expected Output Checks:**
   - For `task_id == stegverse.output.package`, verify the presence of:
     - `outputs/stegverse_output.md`
     - `outputs/stegverse_output.json`
     - `reports/current/stegverse_output_report.json`
     - `receipts/current/stegverse_output_receipt.jsonl`
     - `dist/run_artifacts/stegverse-governed-output.zip`
   - Fail closed if any are missing.

### Documentation Update

If useful, update `docs/WORKFLOW_SUMMARY_DIAGNOSTICS.md` to reflect changes in workflow behavior and summary diagnostics.

## Authority Boundaries

The proposal strictly adheres to scoped and staged authority. No broad authority is granted, and all actions are explicitly receipted and bounded by transition class.

## Receipts and Version History

All changes will be documented in the version history and receipts will be generated for each workflow execution, ensuring traceability and compliance with governance directives.

## Risks & Dependencies

- **Risk:** Misconfiguration could lead to incomplete task execution.
- **Mitigation:** Thorough testing and validation of the workflow changes.
- **Dependency:** Requires correct setup of Python and task dispatcher script.

## Confidence

High confidence in the proposed changes as they directly address the task requirements and align with governance directives. The implementation plan is clear and follows best practices for workflow management.
