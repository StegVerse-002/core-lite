# Bundle Ingestion Smoke Test

Decision: `ALLOW`
Success: `true`
Failure class: `none`
Fixture: `tests/fixtures/bundles/minimal_ingestible_bundle.zip`
Report: `reports/current/bundle_ingestion_smoke_test_report.json`
Receipt: `receipts/current/bundle_ingestion_smoke_test_receipt.jsonl`

## Ingest Report Summary

```json
{
  "decision": "ALLOW",
  "errors": [],
  "installed": [
    {
      "bytes": 136,
      "dry_run": false,
      "path": "outputs/bundle_ingestion_smoke_probe.txt",
      "sha256": "fba324d891cdce827b9fe3542160da38a84380a9079d42fea14ff78ea7917e48"
    }
  ],
  "rejected": [],
  "status": "success"
}
```

## Exception Tail

```text

```

## Probe

```json
{
  "exists": true,
  "path": "outputs/bundle_ingestion_smoke_probe.txt",
  "sha256": "sha256:fba324d891cdce827b9fe3542160da38a84380a9079d42fea14ff78ea7917e48",
  "text_preview": "SV002 bundle ingestion smoke-test probe\ngenerated_at=2026-05-29T16:28:41.534950+00:00\npurpose=verify BundleIngestor direct fixture path\n"
}
```

