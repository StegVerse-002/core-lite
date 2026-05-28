# SV002 Automation Proof Result

## Result

```text
DEFER
```

## Final decision

```text
CANDIDATE_SANDBOXED_GATE_DEFERRED
```

## One-paragraph explanation

The existing adapter path ran provider outputs through the candidate sandbox executor. OpenAI status: 1 valid / 1 total candidate packet(s). Claude status: 1 valid / 1 total candidate packet(s). Candidate packet status: 2 valid / 2 total. Sandbox status: pass. M11 binding gate status: DEFER. Selected candidate: sv002-m105-sandbox-proof.

## Next action

```text
No rerun needed. Resolve/implement the M11 Triad binding gate if real auto-apply is now desired.
```

## Compact status table

| Field | Value |
|---|---|
| route | existing core-lite-intake adapter path |
| OpenAI | 1 valid / 1 total candidate packet(s) |
| Claude | 1 valid / 1 total candidate packet(s) |
| candidate packets | 2 valid / 2 total |
| sandbox | pass |
| M11 binding gate | DEFER |
| selected candidate | sv002-m105-sandbox-proof |
| applied files | none |
| detailed report | `reports/current/adapter_candidate_sandbox_report.json` |
| receipt | `receipts/current/adapter_candidate_sandbox_receipt.jsonl` |

## Candidate details

- `sv002-m105-sandbox-proof` from `openai` → `SANDBOX_PASS_GATE_DEFER`
  - declared provider: `openai-or-claude`
  - pytest: `skipped; documentation/non-executable candidate`
- `sv002-m105-sandbox-proof` from `claude` → `SANDBOX_PASS_GATE_DEFER`
  - declared provider: `openai-or-claude`
  - pytest: `skipped; documentation/non-executable candidate`
