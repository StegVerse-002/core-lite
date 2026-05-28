# SV002 M11 Incoming Disposition Gate

## Correction

The incoming cleanup step must not mean blind deletion.

Each incoming payload must receive a disposition record before it is removed from `incoming/`.

## Current intended lifecycle

```text
incoming/foo.zip pushed
→ foo.zip is selected because it changed in the push
→ sha256 is computed
→ payload is copied to tracking/incoming_mailbox/<sha>/
→ pipeline evaluates staged payload
→ disposition record is written
→ if accepted/installed: incoming payload is removed
→ if rejected/failed: payload is copied to quarantine/incoming/<sha>/, then incoming payload is removed
→ durable evidence is committed
→ incoming/ returns to README.md only
```

## Four simultaneous bundles

If four payloads enter `incoming/` in the same push, the workflow processes all four in sorted path order.

Each receives its own hash-derived event directory and disposition record.

The final steady state remains:

```text
incoming/README.md
```

## Durable evidence

```text
reports/current/incoming_changed_files.txt
reports/current/incoming_disposition_summary.jsonl
receipts/current/incoming_disposition_receipt.jsonl
tracking/incoming_mailbox/<sha>/
quarantine/incoming/<sha>/  # only for failed/rejected payloads
dist/
```
