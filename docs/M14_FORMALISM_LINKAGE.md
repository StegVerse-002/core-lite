# M14 Formalism Linkage

## Purpose

M14 validates that `StegVerse-002/core-lite` remains linked to the Stage 32-34 formalism proof path in:

```text
Data-Continuation/formalism-tests
```

The Site remains mirror-only. The formalism proof authority remains external to this repo.

## Required Formalism References

```text
Stage32-AdmissibilitySpaceCoordinates
Stage33-TransitionGraphGeometry
Stage34-RepairNearestAdmissible
```

## Required Decision Regions

```text
ALLOW
DENY
SANDBOX
REVIEW
FAIL_CLOSED
QUARANTINE
```

## Required Boundary Metrics

```text
d_A
d_bnd_A or d_boundary_A
delta_R
delta_P
delta_U
delta_O
delta_C
```

## Validation Command

```bash
python scripts/run_m14_formalism_linkage_check.py
```

Expected outputs:

```text
reports/current/m14_formalism_linkage_report.json
receipts/current/m14_formalism_linkage_receipt.jsonl
outputs/m14_formalism_linkage.md
dist/run_artifacts/m14-formalism-linkage.zip
```

## Boundary

This stage does not install code and does not grant authority. It verifies that policy-level linkage to the formalism proof path remains intact and receipt-bound.
