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

The existing adapter path ran provider outputs through the candidate sandbox executor. OpenAI status: artifact present, no candidate packet. Claude status: artifact present, no candidate packet. Candidate packet status: 2 valid / 2 total. Sandbox status: failed/denied. M11 binding gate status: not reached. Selected candidate: none.

## Next action

```text
Read this file only, then adjust task.md or candidate constraints; no artifact scavenging required.
```

## Compact status table

| Field | Value |
|---|---|
| route | existing core-lite-intake adapter path |
| OpenAI | artifact present, no candidate packet |
| Claude | artifact present, no candidate packet |
| candidate packets | 2 valid / 2 total |
| sandbox | failed/denied |
| M11 binding gate | not reached |
| selected candidate | none |
| applied files | none |
| detailed report | `reports/current/adapter_candidate_sandbox_report.json` |
| receipt | `receipts/current/adapter_candidate_sandbox_receipt.jsonl` |

## Candidate details

- `sv002-m105-sandbox-proof` from `openai-or-claude` → `DENY_CANDIDATE`
  - error: `pytest_failed`
- `sv002-m105-sandbox-proof` from `openai-or-claude` → `DENY_CANDIDATE`
  - error: `pytest_failed`
