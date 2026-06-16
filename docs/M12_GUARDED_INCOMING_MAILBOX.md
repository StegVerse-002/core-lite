# M12 Guarded Incoming Mailbox

## Purpose

M12 adds a guarded incoming mailbox to `StegVerse-002/core-lite` without returning to the earlier unbounded `incoming/` clutter problem.

`incoming/` is treated as a mailbox, not durable proof state.

## Processing Rules

```text
incoming/*.zip -> BundleIngestor
ALLOW / ALLOW_DRY_RUN -> incoming/processed/
anything else -> incoming/rejected/
unsupported files -> incoming/rejected/
directories -> reported, not recursively processed
```

## Outputs

```text
reports/current/incoming_mailbox_report.json
receipts/current/incoming_mailbox_receipt.jsonl
outputs/incoming_mailbox.md
dist/run_artifacts/incoming-mailbox.zip
```

## Runner

```bash
python scripts/run_incoming_mailbox.py
```

## Governance Boundary

The mailbox does not install directly. It delegates all bundle consequences to `BundleIngestor`.

This preserves the M11 proof boundary:

```text
submission -> BundleIngestor -> report/receipt -> processed or rejected source movement
```

## Next Catalog Step

Add task id:

```text
sv002.incoming.mailbox.process
```

through the stable dispatcher task catalog after tests pass.
