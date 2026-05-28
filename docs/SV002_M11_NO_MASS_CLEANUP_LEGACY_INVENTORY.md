# SV002 M11 No-Mass-Cleanup Legacy Inventory

## Correction

The incoming disposition gate must never mass-remove old payloads just because a new push occurred.

## Rule

Only payloads changed in the triggering push may be evaluated and removed, and only after a disposition record exists.

Legacy payloads already sitting in `incoming/` are inventoried but intentionally left in place until they receive their own explicit reconciliation/disposition action.

## Why

`incoming/` had already become polluted before the final mailbox invariant existed. Removing those old files automatically would be a mass cleanup, not governed disposition.

## Behavior

```text
push incoming/new.zip
→ evaluate new.zip
→ write disposition for new.zip
→ remove new.zip only
→ inventory old incoming files
→ do not delete old incoming files
```

## Durable evidence

```text
reports/current/incoming_changed_files.txt
reports/current/incoming_legacy_inventory.txt
reports/current/incoming_disposition_summary.jsonl
receipts/current/incoming_disposition_receipt.jsonl
tracking/incoming_mailbox/<sha>/
quarantine/incoming/<sha>/  # failed/rejected changed payloads only
```
