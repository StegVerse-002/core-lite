# StegVerse-002 Core-Lite Ingestion Engine

Generated: `2026-05-26T01:24:32Z`

## Purpose

This bundle adds the functional bundle ingestion engine for `StegVerse-002/core-lite`.

It does **not** add a new workflow.

It does **not** include a root `README.md`.

It does **not** include a root `bundle_manifest.json`.

It plugs into the existing `core-lite-intake.yml` workflow path that already supports:

```text
input_type=bundle
input_path=<path>
```

The existing workflow calls:

```bash
python -m core_lite.multimodal.pipeline \
  --input-type bundle \
  --input-path "<path>" \
  --entity StegVerse-002 \
  --stage "<active_stage>"
```

This bundle replaces `core_lite/multimodal/pipeline.py` so that `input_type=bundle` routes into the new ingestion engine.

## Install / Upload

Upload every file in this bundle to its exact path.

No root files are included.

## Bundle Intake Flow

```text
incoming/<bundle>.zip
or
incoming/<expanded_bundle>/
→ core_lite.multimodal.pipeline input_type=bundle
→ core_lite.bundles.ingest.BundleIngestor
→ manifest validation
→ path policy check
→ hash verification
→ install allowed files
→ quarantine rejected files/bundles
→ receipt emission
→ ingestion event
→ report
```

## Existing Workflow Run

After upload, use the existing workflow only:

```text
Actions → core-lite-intake → Run workflow
```

Inputs:

```text
input_type: bundle
input_path: incoming/<your_bundle>.zip
dry_run: false
```

For a dry run:

```text
input_type: bundle
input_path: incoming/<your_bundle>.zip
dry_run: true
```

## Manifest Contract

Incoming bundles should contain a manifest at one of:

```text
bundle_manifest.json
manifest.json
```

The manifest must include:

```json
{
  "schema": "stegverse.bundle_manifest.v1",
  "bundle_name": "example",
  "files": [
    {
      "path": "docs/example/README.md",
      "sha256": "<sha256 hex>",
      "bytes": 123
    }
  ]
}
```

## Guardrails

The ingestion engine denies:

```text
README.md at repo root unless manifest explicitly sets allow_root_readme=true
bundle_manifest.json at repo root
.github/workflows/* unless manifest explicitly sets allow_workflows=true
incoming/* as a target path
absolute paths
paths containing ..
empty paths
```

Invalid files are not installed.

Invalid bundles are quarantined under:

```text
quarantine/bundles/
```

Receipts/events/reports are written under:

```text
receipts/current/
tracking/ingestion_events/
reports/current/
```
