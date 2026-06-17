# M15 SDK / CLI Surface

## Purpose

M15 exposes a small governed SDK and CLI surface for `StegVerse-002/core-lite`.

The SDK and CLI do not provide raw mutation authority. They call existing governed boundaries:

```text
TransitionTableResolver
BundleIngestor
IncomingMailbox
CandidateReviewer
CandidateApplier
```

## SDK

```python
from core_lite.sdk import CoreLiteClient

client = CoreLiteClient(".")
client.ingest_bundle("candidate.zip")
client.process_incoming("incoming")
client.review_candidate("candidate_ref.json")
client.apply_candidate("candidate_ref.json", "reports/current/candidate_bundle_review_report.json")
```

## CLI

```bash
python scripts/core_lite_cli.py resolve-transition bundle_manifest.json
python scripts/core_lite_cli.py ingest-bundle candidate.zip
python scripts/core_lite_cli.py process-incoming --incoming-dir incoming
python scripts/core_lite_cli.py review-candidate candidate_ref.json
python scripts/core_lite_cli.py apply-candidate candidate_ref.json reports/current/candidate_bundle_review_report.json
```

## Validation

```bash
python -m pytest -q tests/test_sdk_cli_surface.py
python scripts/run_m15_sdk_cli_tests.py
```

Expected outputs:

```text
reports/current/m15_sdk_cli_validation_report.json
receipts/current/m15_sdk_cli_validation_receipt.jsonl
outputs/m15_sdk_cli_validation.md
dist/run_artifacts/m15-sdk-cli-validation.zip
```

## Boundary

M15 is a developer surface, not an authority expansion.

The SDK and CLI must remain wrappers around governed boundaries and must not become a direct repo mutation API.
