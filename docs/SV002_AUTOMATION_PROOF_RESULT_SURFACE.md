# SV002 Automation Proof Result Surface

This bundle does **not** add a workflow.

It only replaces:

```text
scripts/adapter_candidate_sandbox.py
```

The replacement writes one human-readable result file:

```text
outputs/SV002_AUTOMATION_PROOF_RESULT.md
```

## Purpose

No more artifact scavenger hunt.

Each adapter run should now leave one file that says:

```text
PASS / DEFER / FAIL_CLOSED
```

and includes:

```text
route selected
provider status
candidate packet status
sandbox status
M11 gate status
next action
```

## Done condition

After the next adapter run, the only file you should need to open is:

```text
outputs/SV002_AUTOMATION_PROOF_RESULT.md
```
