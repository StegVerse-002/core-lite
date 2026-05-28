# OpenAI — Governed Collaboration Proposal

## Current State Assessment

The current workflow in `.github/workflows/core-lite-intake.yml` does not ensure that the expected file shape exists on `main` after a task execution. This can lead to a false positive success in GitHub Actions runs.

## Directive Alignment

The proposal aligns with the no-broad-authority directive by ensuring scoped and explicit authority in task execution and output validation. It adheres to the governance model by requiring evidence of output before marking a task as successful.

## Next Collaboration Primitive

The next step involves modifying the workflow to enforce output validation and ensure that all expected files are present before a task is considered successful.

## Proposed Implementation

1. **Modify `.github/workflows/core-lite-intake.yml`:**

   Add a job to validate the output files after task execution. The job should:

   - Execute the task using the provided command.
   - Capture stdout, stderr, and exit code.
   - Validate the presence of the following files:
     - `outputs/stegverse_output.md`
     - `outputs/stegverse_output.json`
     - `reports/current/stegverse_output_report.json`
     - `receipts/current/stegverse_output_receipt.jsonl`
     - `dist/run_artifacts/stegverse-governed-output.zip`
   - Fail the workflow if any file is missing.
   - Commit and push the files to `main` if all are present.

2. **GitHub Actions Step Summary:**

   - Display the selected route, task_id, command executed, exit code, presence of each expected file, and commit status.

## Authority Boundaries

The proposal respects authority boundaries by modifying only the workflow logic and not altering any scripts or creating new tasks. It ensures that the workflow remains local to repository artifacts and does not involve external deployments.

## Receipts and Version History

The workflow will generate receipts and reports for each run, ensuring traceability and adherence to governance rules. These artifacts will be committed to the repository for audit purposes.

## Risks & Dependencies

- **Risk:** The workflow might fail if the task execution does not produce the expected files.
- **Dependency:** The task execution relies on the correct functioning of `tools.scripts.task_dispatcher`.

## Confidence

The proposed changes are straightforward and align with the existing governance model. The implementation should effectively enforce the required output validation, ensuring that only successful task executions are marked as such.
