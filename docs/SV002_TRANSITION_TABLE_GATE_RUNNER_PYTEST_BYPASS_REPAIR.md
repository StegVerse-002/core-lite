# SV002 Transition Table Gate Runner Repair

## Purpose

This is a drop-in replacement for:

```text
scripts/run_transition_table_gate_tests.py
```

## Why

The two installed test files are executable script-style tests. They define `run_tests()` and execute when run directly:

```text
python tests/test_transition_table_resolver.py
python tests/test_bundle_ingest_cge_transition_gate.py
```

They are not normal pytest-collected test modules. Running them with:

```text
python -m pytest tests/test_transition_table_resolver.py tests/test_bundle_ingest_cge_transition_gate.py
```

can fail even when the scripts themselves would run correctly.

## Workflow

Run `core-lite-intake.yml` again with:

```text
task_id: sv002.transition_table_gate.tests
skip_tasks: false
stage_override: SV002-M11
input_type: [blank]
input_path: [blank]
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
