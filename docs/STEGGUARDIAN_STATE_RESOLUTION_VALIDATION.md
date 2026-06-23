# StegGuardian State Resolution Validation

The StegGuardian adapter validation path now reads seed state records instead of the mock resolution table.

## Command

```text
python tools/validate_stegguardian_mock_resolution.py
```

## Current State Source

```text
state/stegguardian/seed_state_records.json
```

## Superseded Fixture Source

```text
examples/stegguardian_mock_resolution_table.json
```

The mock table remains as historical fixture support, but the validator now uses seed state records.

## Current Behavior

- active records with resolved standing allow evaluation to continue;
- unresolved records return `FAIL_CLOSED`;
- missing records return `FAIL_CLOSED`.

## Next Target

Replace seed state records with the general core-lite state, policy, evidence, context, and continuity stores.
