# StegGuardian Unified Validation

This document replaces manual validation sequencing for the StegGuardian adapter path.

## Single Command

```text
python tools/validate_stegguardian_adapter_all.py
```

## Included Checks

The unified validator runs:

- adapter fixture validation;
- general-store resolution validation;
- receipt emission validation;
- store-backed receipt generation validation.

## Done State

A user or automation no longer needs to manually run the StegGuardian adapter checks one by one.

## Next Target

Connect this single command to repository automation and remove any remaining manual handoff steps from the validation path.
