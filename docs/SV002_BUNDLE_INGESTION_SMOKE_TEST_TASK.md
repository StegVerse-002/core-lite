# SV002 Bundle Ingestion Smoke Test Task

## Purpose

This adds a declared task to diagnose bundle ingestion without using the crowded `incoming/` mailbox.

## Run Through Existing Workflow

Use `.github/workflows/core-lite-intake.yml` manually with:

```text
task_id: sv002.bundle.ingestion.smoke_test
skip_tasks: false
stage_override: SV002-M11
repair_target: [blank]
input_type: [blank]
input_path: [blank]
kv_packet: [blank]
dry_run: false
agent_provider: none
```

## What It Does

The runner creates a controlled zip fixture at:

```text
tests/fixtures/bundles/minimal_ingestible_bundle.zip
```

The fixture contains a valid `bundle_manifest.json` with:

```text
schema: stegverse.bundle_manifest.v1
```

and one harmless target file:

```text
outputs/bundle_ingestion_smoke_probe.txt
```

Then it calls `core_lite.bundles.ingest.BundleIngestor` directly.

## Expected Outputs

```text
reports/current/bundle_ingestion_smoke_test_report.json
receipts/current/bundle_ingestion_smoke_test_receipt.jsonl
outputs/bundle_ingestion_smoke_test.md
dist/run_artifacts/bundle-ingestion-smoke-test.zip
```

## Interpretation

If this task passes, BundleIngestor can install a known-good bundle and the remaining failure is likely in workflow/incoming routing or malformed incoming bundles.

If this task fails, the report identifies the failure class.
