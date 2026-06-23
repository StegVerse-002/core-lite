# General Store Seed Status

This pass added seed general stores for the StegGuardian adapter path.

## Added Stores

- `stores/capability-state/seed_records.json`
- `stores/provider/seed_records.json`
- `stores/rules/seed_records.json`
- `stores/evidence/seed_records.json`
- `stores/env/seed_records.json`

## Purpose

These files split the prior StegGuardian seed state record set into general core-lite store-shaped records.

## Next Target

Update adapter validation to resolve across these stores instead of the single seed state file.

## Boundary

These are seed records. They are not yet production persistence or full ecosystem reconstruction.
