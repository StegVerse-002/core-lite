# SV002 M11 Ephemeral Incoming Mailbox

## Correction

`incoming/` is not a storage directory.

It is an ephemeral mailbox.

Only this file should remain:

```text
incoming/README.md
```

Any payload pushed into `incoming/` exists only long enough for ingestion to process or reject it. The workflow removes payloads after processing or failed processing, then commits the cleanup with receipts/reports/tracking evidence.

## Correct behavior

```text
push incoming/foo.zip
→ process only incoming/foo.zip
→ write reports/receipts/tracking/dist evidence
→ remove incoming/foo.zip
→ commit outputs and cleanup
→ incoming/ contains README.md only
```

## Existing files

Existing payloads in `incoming/` are not valid steady-state artifacts. The workflow cleanup step removes all incoming payloads except `incoming/README.md`.

## Durable evidence locations

```text
reports/current/
receipts/current/
tracking/
dist/
```
