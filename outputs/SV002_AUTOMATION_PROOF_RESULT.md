# SV002 Automation Proof Result

## Result

```text
FAIL_CLOSED
```

## Final decision

```text
FAIL_CLOSED_NO_PASSING_CANDIDATE
```

## One-paragraph explanation

The existing adapter path ran provider outputs through the candidate sandbox executor. OpenAI status: 0 valid / 1 total candidate packet(s). Claude status: 0 valid / 1 total candidate packet(s). Candidate packet status: 0 valid / 2 total. Sandbox status: failed/denied. M11 binding gate status: not reached. Selected candidate: none.

## Next action

```text
Read this file only, then adjust task.md or candidate constraints; no artifact scavenging required.
```

## Compact status table

| Field | Value |
|---|---|
| route | existing core-lite-intake adapter path |
| OpenAI | 0 valid / 1 total candidate packet(s) |
| Claude | 0 valid / 1 total candidate packet(s) |
| candidate packets | 0 valid / 2 total |
| sandbox | failed/denied |
| M11 binding gate | not reached |
| selected candidate | none |
| applied files | none |
| detailed report | `reports/current/adapter_candidate_sandbox_report.json` |
| receipt | `receipts/current/adapter_candidate_sandbox_receipt.jsonl` |

## Candidate details

- `sv002-m11-incoming-disposition-gate-repair` from `openai` → `DENY_CANDIDATE`
  - declared provider: `openai-or-claude`
  - error: `transition_class_denied:workflow-repair`
  - error: `target_prefix_denied:.github/workflows/core-lite-intake.yml`
- `sv002-m11-incoming-disposition-gate-repair` from `claude` → `DENY_CANDIDATE`
  - error: `transition_class_denied:workflow-repair`
  - error: `target_prefix_denied:.github/workflows/core-lite-intake.yml`
