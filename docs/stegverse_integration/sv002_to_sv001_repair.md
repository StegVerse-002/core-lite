# StegVerse-002 → StegVerse-001 Repair Path

## Overview

StegVerse-002 can repair `Data-Continuation/core-lite` at the stuck `SV001-M3` gate
using the repair tool in `tools/repair/sv001_repair.py`.

## How it works

StegVerse-002 operates as a bounded repair runner — not an autonomous agent.
It asks what the failure is (like a human operator would), classifies the blocker,
prepares a candidate fix, and tells the operator what to apply.

This mirrors the same pattern as StegVerse-001's own build: one bounded runner,
known blocker classes, STOP when intake succeeds.

## Operator steps

1. Get the failure text from the `Data-Continuation/core-lite` Actions tab
2. Paste it into `tracking/sv001_repair_input.txt`
3. Run via dispatcher:

   **GitHub Actions → core-lite-intake → Run workflow**
   ```
   task_id: sv001.repair.intake.enablement
   repair_target: Data-Continuation/core-lite
   ```

   Or from CLI:
   ```bash
   python -m tools.repair.sv001_repair \
     --target-repo Data-Continuation/core-lite \
     --failure-file tracking/sv001_repair_input.txt
   ```

4. Find the candidate in `dist/current/sv001_repair/`
5. Apply the candidate to the relevant file in `Data-Continuation/core-lite`
6. Rerun the `core-lite-intake` workflow in that repo
7. Repeat until intake succeeds
8. STOP — SV001-M3 complete

## STOP condition

```
Core-Lite Intake in Data-Continuation/core-lite succeeds with:
  task_id: blank
  skip_tasks: true
```

## Known blocker classes

| Class | File |
|-------|------|
| missing_cge_export | core_lite/cge.py |
| package_invocation_error | .github/workflows/core-lite-intake.yml |
| missing_internal_export | core_lite/ingest.py |
| receipt_signature_mismatch | core_lite/receipts.py |
| unknown_runtime_blocker | → REVIEW_REQUIRED |
