# SV002 Bundle Ingestion Smoke Test — sys.path Repair

## What was found

The repository scan showed that `scripts/run_bundle_ingestion_smoke_test.py` imports `core_lite.bundles.ingest` from a script under `scripts/`.

When GitHub Actions runs:

```text
python scripts/run_bundle_ingestion_smoke_test.py
```

Python may place `scripts/` at the front of `sys.path` instead of the repository root.

That can make:

```text
from core_lite.bundles.ingest import BundleIngestor
```

fail before `BundleIngestor` returns a report.

## What this repair does

This replacement inserts the repository root into `sys.path` before importing `core_lite`:

```python
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
```

It also prints `exception_tail` if anything still fails.

## Run

Use `core-lite-intake.yml`:

```text
task_id: sv002.bundle.ingestion.smoke_test
skip_tasks: false
stage_override: SV002-M11
input_type: [blank]
input_path: [blank]
dry_run: false
agent_provider: none
```
