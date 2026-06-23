# StegGuardian Adapter Fixture Validation

This document defines the first executable fixture validation for StegGuardian adapter intake inside SV-002 core-lite.

## Command

Run from repository root:

```text
python tools/validate_stegguardian_adapter_fixtures.py
```

## Fixture Cases

The validator checks two seed adapter cases:

1. `examples/stegguardian_adapter_input.json` -> `ALLOW`
2. `examples/stegguardian_adapter_unresolved_input.json` -> `FAIL_CLOSED`

## What This Validates

- required adapter input fields exist;
- required output fields exist;
- expected decisions match;
- receipt material decision matches the output decision;
- disclosure minimization is explicitly set.

## What This Does Not Validate

This does not yet perform production standing evaluation.

It is a harness that verifies the adapter examples are shaped correctly before the core-lite standing evaluator consumes them.

## Next Step

Replace fixture-output comparison with live standing evaluation while preserving the same input and output contract.
