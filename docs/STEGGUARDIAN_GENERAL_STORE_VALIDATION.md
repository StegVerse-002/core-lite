# StegGuardian General Store Validation

The StegGuardian adapter validation path now resolves references across split general store seed files.

## Command

```text
python tools/validate_stegguardian_mock_resolution.py
```

## Store Sources

- `stores/capability-state/seed_records.json`
- `stores/provider/seed_records.json`
- `stores/rules/seed_records.json`
- `stores/evidence/seed_records.json`
- `stores/env/seed_records.json`

## Prior Source

The validator previously used:

```text
state/stegguardian/seed_state_records.json
```

That file remains useful as a compatibility fixture, but the validation path now uses general store-shaped records.

## Next Target

Bind receipt emission to the general-store evaluation result.
