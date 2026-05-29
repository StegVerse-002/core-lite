# SV002 Transition Table Gate Declared Task Runner

## Purpose

This bundle adds a declared task to `StegVerse-002/core-lite` so the existing `core-lite-intake.yml` workflow can run the manually installed Transition Table gate tests without needing a new workflow file.

## Target Repository

```text
StegVerse-002/core-lite
```

## Files

```text
tools/tasks/task_catalog.json
scripts/run_transition_table_gate_tests.py
```

## Run Through GitHub Actions

Use the existing workflow:

```text
.github/workflows/core-lite-intake.yml
```

Run manually with these fields:

```text
task_id: sv002.transition_table_gate.tests
skip_tasks: false
stage_override: SV002-M11
repair_target: [blank]
input_type: [blank]
input_path: [blank]
kv_packet: [blank]
dry_run: false
agent_provider: none
```

## Expected Outputs

```text
reports/current/transition_table_gate_test_report.json
receipts/current/transition_table_gate_test_receipt.jsonl
outputs/transition_table_gate_tests.md
dist/run_artifacts/transition-table-gate-tests.zip
```

## Notes

This task does not install files and does not ingest bundles.

It only runs:

```text
python -m pytest tests/test_transition_table_resolver.py tests/test_bundle_ingest_cge_transition_gate.py
```

The bundle-ingestion path remains a separate repair target.
