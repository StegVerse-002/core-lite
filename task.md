# StegVerse-002 / SV002-M11 Task

## Title

Design the Governed Apply / Review Boundary for SV002-M11

## Absolute Directive

There is never a valid StegVerse state in which any entity receives broad authority.

Authority must always be scoped, staged, explicit, receipted, bounded by transition class, checked at the commit/execution boundary, recoverable, containable, and denied by default unless specifically granted.

This task is **propose-only**. Do not apply repo mutations. Do not create execution authority. Do not bypass review. Do not modify production behavior. Provider outputs are candidate evidence only.

## Context

SV002-M10 has been completed and recorded.

M10 proved that:

- connected LLM providers may produce candidate evidence;
- StegVerse, not the LLM providers, becomes the governed output authority;
- `stegverse.output.package` creates a receipted StegVerse-authored governed output;
- the workflow enforces the required output shape;
- the required output files are committed to `main` only after the output-shape contract is satisfied.

The M10 output authority artifact shape is:

```text
outputs/stegverse_output.md
outputs/stegverse_output.json
reports/current/stegverse_output_report.json
receipts/current/stegverse_output_receipt.jsonl
dist/run_artifacts/stegverse-governed-output.zip
```

## M11 Purpose

SV002-M11 must prove the next boundary:

> A StegVerse-governed output may recommend a repository mutation, but it is still not execution authority until a separate apply/review gate validates scope, evidence, receipts, allowed paths, and explicit operator approval.

In plain language:

```text
M10 proved: StegVerse is the governed output authority.
M11 must prove: StegVerse output is still not execution authority until an apply gate binds it.
```

## Required Proposal

Produce a concrete implementation proposal for SV002-M11 that includes:

1. The minimal new apply/review gate concept.
2. The exact files that should be added or modified.
3. The expected task catalog entry or entries.
4. The required input shape for an apply request.
5. The required output shape for an apply gate result.
6. The receipts that must be emitted.
7. The fail-closed cases.
8. The GitHub Actions workflow changes, if any.
9. The boundary between proposal evidence and applied mutation.
10. A minimal test plan.

## Required Boundary Conditions

The M11 apply/review gate must deny by default unless all of the following are satisfied:

- `stegverse_output_report.json` exists.
- `stegverse_output_receipt.jsonl` exists.
- The StegVerse output decision is compatible with apply review.
- The requested mutation has an explicit task identity.
- The requested mutation lists exact target paths.
- Every target path is within an allowed path policy.
- No forbidden path is touched.
- The receipt chain can be validated or at least checked for required evidence.
- The request includes an explicit operator approval flag.
- Dry-run mode does not mutate repository state.

## Expected Candidate Files

Prefer the smallest working design. Suggested files may include:

```text
scripts/review_stegverse_apply_request.py
schemas/stegverse_apply_request.schema.json
schemas/stegverse_apply_result.schema.json
examples/stegverse_apply_request.example.json
reports/current/stegverse_apply_review_report.json
receipts/current/stegverse_apply_review_receipt.jsonl
docs/SV002_M11_GOVERNED_APPLY_REVIEW_BOUNDARY.md
```

If a different file shape is better, explain why. Do not invent broad architecture beyond the minimum viable M11 proof.

## Apply Request Shape

Propose a machine-readable apply request with at least:

```json
{
  "schema": "stegverse.apply_request.v1",
  "entity": "StegVerse-002",
  "stage": "SV002-M11",
  "task_id": "example.apply.task",
  "source_output_report": "reports/current/stegverse_output_report.json",
  "source_output_receipt": "receipts/current/stegverse_output_receipt.jsonl",
  "requested_paths": [],
  "allowed_paths_policy": "agent_policy/allowed_paths.json",
  "forbidden_paths_policy": "agent_policy/forbidden_paths.json",
  "operator_approved": false,
  "dry_run": true
}
```

## Required Output Shape

The review gate should produce a deterministic result similar to:

```text
reports/current/stegverse_apply_review_report.json
receipts/current/stegverse_apply_review_receipt.jsonl
```

The result decision must be one of:

```text
ALLOW_APPLY_REVIEW
DENY_APPLY_REVIEW
FAIL_CLOSED
DRY_RUN_ONLY
```

## Hard Requirement

The proposal must explicitly preserve this rule:

> A StegVerse-governed output is not enough to mutate the repository. Mutation requires a separate apply/review gate with explicit operator approval and path-scoped authority.

## Deliverable

Return a concise but complete proposal with:

- summary;
- exact file plan;
- minimal implementation steps;
- expected command/task entry;
- expected reports/receipts;
- fail-closed logic;
- verification plan.

Do not apply the change. Do not produce a patch unless the workflow explicitly asks for a proposal bundle later.
