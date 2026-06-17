# M16 Activation Evidence Export

## Purpose

M16 creates a single activation evidence surface for `StegVerse-002/core-lite`.

It does not grant authority and does not mutate source code. It checks that required repo paths exist, expected M11-M15 validation reports exist, and then exports a report, receipt, markdown summary, and artifact bundle.

## Command

```bash
python scripts/run_activation_evidence_export.py
```

## Expected Outputs

```text
reports/current/core_lite_activation_evidence_report.json
receipts/current/core_lite_activation_evidence_receipt.jsonl
outputs/core_lite_activation_evidence.md
dist/run_artifacts/core-lite-activation-evidence.zip
```

## Required Evidence Classes

```text
M11 bundle ingestion smoke report
M12 incoming mailbox validation report
M13 candidate review/apply validation report
M14 formalism linkage report
M15 SDK/CLI validation report
```

## Activation Boundary

Activation-ready status requires:

```text
required source paths present
expected validation reports present
expected validation reports allow/pass
activation evidence receipt written
```

A `REVIEW` decision means installation may exist but validation evidence is incomplete.

## Invariants

```text
candidate output is evidence, not authority
incoming/ is mailbox, not durable state
SDK/CLI is a wrapper, not raw mutation authority
formalism authority remains Data-Continuation/formalism-tests
```
