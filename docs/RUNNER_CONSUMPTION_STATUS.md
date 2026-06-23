# Runner Consumption Status

This pass added the runner-facing contract for consuming no-manual sequence receipts.

## Added

- `contracts/runner-consumption-contract.json`
- `schemas/runner-consumption-result.schema.json`

## Source Receipt

```text
receipts/stegguardian-no-manual-sequence.json
```

## Result Receipt Target

```text
receipts/runner-consumption-result.json
```

## Purpose

A StegVerse automation runner can now consume the no-manual sequence receipt, execute supported processors and validators, and write a result receipt.

## Next Build Target

Implement the runner or connect this contract to the ecosystem automation layer.
