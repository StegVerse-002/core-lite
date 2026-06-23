# StegGuardian Receipt Emission Validation

This pass adds receipt emission validation for the StegGuardian adapter path.

## Command

```text
python tools/validate_stegguardian_receipt_emission.py
```

## Inputs

- `examples/stegguardian_adapter_expected_output.json`
- `examples/stegguardian_receipt_emission_expected.json`

## Validation Scope

The validator checks that receipt material:

- contains required receipt fields;
- matches the adapter output decision;
- matches adapter output receipt material;
- preserves `disclosure_minimized = true`;
- includes non-empty decision reasons.

## Next Target

Generate receipt material directly from general-store evaluation instead of comparing static examples.
