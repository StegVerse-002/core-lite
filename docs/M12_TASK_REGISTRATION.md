# M12 Task Registration

## Purpose

M12 now has task addition files for guarded incoming mailbox processing and standalone validation.

Instead of editing the large one-line `tools/tasks/task_catalog.json` by hand, use:

```bash
python tools/scripts/register_task_additions.py
```

## Addition Files

```text
tools/tasks/sv002_incoming_mailbox_process_task.json
tools/tasks/sv002_m12_incoming_mailbox_validation_task.json
```

The registration utility also scans future addition files matching:

```text
tools/tasks/*_task.json
tasks/task_catalog.*_addition.json
```

## Outputs

```text
reports/current/task_addition_registration_report.json
receipts/current/task_addition_registration_receipt.jsonl
```

## Safe Dry Run

```bash
python tools/scripts/register_task_additions.py --dry-run
```

## Commit Rule

Only commit the updated `tools/tasks/task_catalog.json` after the registration report shows:

```text
decision: ALLOW
errors: []
```

## Boundary

This utility does not execute tasks. It only registers declared task metadata into the stable task catalog.
