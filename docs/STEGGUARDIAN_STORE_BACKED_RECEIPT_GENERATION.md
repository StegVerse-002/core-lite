# StegGuardian Store-Backed Receipt Generation

This pass adds receipt generation from the general-store validation path.

## Command

```text
python tools/generate_stegguardian_receipt_from_stores.py
```

## Source Input

```text
examples/stegguardian_adapter_input.json
```

## Store Sources

- `stores/capability-state/seed_records.json`
- `stores/provider/seed_records.json`
- `stores/rules/seed_records.json`
- `stores/evidence/seed_records.json`
- `stores/env/seed_records.json`

## Expected Receipt

```text
examples/stegguardian_receipt_emission_expected.json
```

## Current Status

The adapter path can now:

1. resolve references through split general stores;
2. determine the seed allow path;
3. generate receipt material;
4. compare generated receipt material against the expected receipt fixture.

## Remaining Gap

The next step is to consolidate adapter evaluation and receipt generation into a single validation command.
