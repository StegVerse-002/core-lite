# Manual Upload Map — Ingestion Engine

## Upload These Folders

```text
core_lite/
docs/
incoming/
machine/
schemas/
tests/
tools/
tracking/
```

## Do Not Upload

```text
README.md
bundle_manifest.json
.github/
reports/
receipts/
quarantine/
```

Those are either intentionally absent from this bundle or runtime outputs.

## Existing File Replaced

This bundle intentionally replaces:

```text
core_lite/multimodal/pipeline.py
```

Reason:

The existing workflow already calls `core_lite.multimodal.pipeline` for `input_type=bundle`. This replacement routes bundle input into the new ingestion engine.

## Existing Workflow Used

No new workflow is added.

Use the existing workflow:

```text
core-lite-intake.yml
```

with:

```text
input_type=bundle
input_path=incoming/<bundle>.zip
```
