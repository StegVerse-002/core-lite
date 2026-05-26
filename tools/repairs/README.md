# StegVerse-001 Repair Tool

## Purpose

Repairs `Data-Continuation/core-lite` at the stuck `SV001-M3` gate.

StegVerse-002 asks what the failure is (just as a human operator would),
classifies the blocker, prepares a candidate fix, and tells the operator
exactly what to apply.

It does NOT directly mutate the target repo.

## Usage

### From CLI

```bash
# With failure text pasted inline
python -m tools.repair.sv001_repair \
  --target-repo Data-Continuation/core-lite \
  --failure-text "cannot import name generate_cge_fingerprint from core_lite.cge"

# With failure text from file
python -m tools.repair.sv001_repair \
  --target-repo Data-Continuation/core-lite \
  --failure-file /tmp/intake_failure.txt
```

### From the dispatcher (GitHub Actions)

```
task_id: sv001.repair.intake.enablement
repair_target: Data-Continuation/core-lite
```

Paste the failure text into `tracking/sv001_repair_input.txt` before running.

## Known blocker classes

| Class | Description | Target file |
|-------|-------------|-------------|
| `missing_cge_export` | `generate_cge_fingerprint` not exported | `core_lite/cge.py` |
| `package_invocation_error` | Workflow uses `python script.py` not `python -m` | workflow yml |
| `missing_internal_export` | `ingest_incoming`, `load_core_policy` missing | `core_lite/ingest.py` |
| `receipt_signature_mismatch` | `ReceiptRecorder.record()` missing `actor` kwarg | `core_lite/receipts.py` |
| `unknown_runtime_blocker` | Unknown — returns REVIEW_REQUIRED | — |

## STOP condition

```
Core-Lite Intake succeeds with:
  task_id: blank
  skip_tasks: true
```

Once that succeeds, the repair is complete. Do not run further repair tasks.

## Operator workflow

1. Get the failure text from the GitHub Actions run
2. Run the repair tool with `--failure-text` or `--failure-file`
3. Find the candidate in `dist/current/sv001_repair/`
4. Apply the candidate to the relevant file in `Data-Continuation/core-lite`
5. Rerun the Core-Lite Intake workflow in that repo
6. Repeat until intake succeeds
7. STOP
