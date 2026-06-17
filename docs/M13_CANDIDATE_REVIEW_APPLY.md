# M13 Candidate Review / Apply Boundary

## Purpose

M13 implements the boundary already declared in the task catalog:

```text
candidate review != candidate apply
```

Review is evidence-only. Apply is consequence-bearing and requires a matching approved review report before it can invoke `BundleIngestor`.

## Review Command

```bash
python scripts/candidate_bundle_review.py --candidate-ref candidate_ref.json
```

Review emits:

```text
reports/current/candidate_bundle_review_report.json
receipts/current/candidate_bundle_review_receipt.jsonl
```

## Apply Command

```bash
python scripts/candidate_bundle_apply.py \
  --candidate-ref candidate_ref.json \
  --review-report reports/current/candidate_bundle_review_report.json
```

Apply requires:

```text
candidate_id matches review report
review decision is ALLOW_CANDIDATE_REVIEW
bundle_path exists in candidate ref
BundleIngestor returns ALLOW
```

Apply emits:

```text
reports/current/candidate_bundle_apply_report.json
receipts/current/candidate_bundle_apply_receipt.jsonl
```

## Standalone Validation

```bash
python scripts/run_m13_candidate_review_apply_tests.py
```

Expected outputs:

```text
reports/current/m13_candidate_review_apply_validation_report.json
receipts/current/m13_candidate_review_apply_validation_receipt.jsonl
outputs/m13_candidate_review_apply_validation.md
dist/run_artifacts/m13-candidate-review-apply-validation.zip
```

## Governance Boundary

Candidate review may inspect and admit a candidate for review posture only.

Candidate apply is the first consequence-bearing boundary and must be receipt-bound.
