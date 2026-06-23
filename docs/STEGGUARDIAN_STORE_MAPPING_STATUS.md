# StegGuardian Store Mapping Status

This pass added the bridge from seed state records to general core-lite stores.

## Added

- `contracts/stegguardian-store-mapping.json`
- `docs/STEGGUARDIAN_STORE_MIGRATION_PLAN.md`

## Current State

Adapter validation currently resolves against:

```text
state/stegguardian/seed_state_records.json
```

## Next Target

Implement the resolver path through general core-lite stores:

- capability state store;
- provider declaration store;
- policy store;
- evidence store;
- context store.

## Boundary

StegGuardian-specific policy logic should not be hard-coded into the general stores.
