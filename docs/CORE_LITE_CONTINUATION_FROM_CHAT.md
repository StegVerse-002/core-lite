# Core-Lite Continuation Plan From Build Chat

## Purpose

This document captures the course correction from the StegVerse-002/core-lite build chat.

The main conclusion is that there is no hard technical reason to stop building `StegVerse-002/core-lite`. The repository exists, is accessible, and is already documented as the clean production-candidate Core-Lite target.

The prior `core-lite-v1.0.0` seed bundles should be treated as extracted stabilization patterns, not as a mandatory replacement for this repository unless the maintainer intentionally creates a separate clean-room repo.

## Current Repository Standing

`StegVerse-002/core-lite` remains the primary active repo.

The continuation should respect the repo's established design:

```text
stable dispatcher workflow
single task catalog
receipt-bound evidence
STOP-conditioned stages
manual-upload-ready / GitHub Actions-compatible operation
```

## Why the v1 Seed Path Was Proposed

The v1 seed path was proposed because the build chat encountered repeated friction around:

```text
incoming/ clutter
legacy bundles
manual repair artifacts
workflow route ambiguity
bundle-ingestion smoke-test failures
patch-loop fatigue
```

That was an engineering reset suggestion, not a finding that `StegVerse-002/core-lite` should be abandoned.

## Decision

Continue building `StegVerse-002/core-lite` directly.

Use the generated v1 seed work as a source of clean patterns, but fold only the useful pieces back into the existing repo through the stable dispatcher/task-catalog model.

## Do Not Do

```text
Do not add random historical incoming bundles.
Do not create ordinary capability expansion as new workflows unless necessary.
Do not bypass BundleIngestor for incoming bundle processing.
Do not treat model output as execution authority.
Do not advance stage claims without evidence.
```

## Continue Build Sequence

### M11 — Bundle Ingestion Stabilization

Goal:

```text
Known-good bundle installs.
Bad bundle quarantines.
Bundle ingestion emits report and receipt.
Failure surface is explicit.
```

Targets:

```text
core_lite/bundles/ingest.py
scripts/run_bundle_ingestion_smoke_test.py
tools/tasks/task_catalog.json
reports/current/bundle_ingestion_smoke_test_report.json
receipts/current/receipt.jsonl
```

### M12 — Guarded Incoming Mailbox

Goal:

```text
incoming/ is an ephemeral mailbox, not durable state.
ALLOW bundle -> processed.
Denied/quarantined bundle -> rejected or quarantine.
```

Targets:

```text
core_lite/incoming/
scripts/run_incoming_mailbox.py
tools/tasks/task_catalog.json
reports/current/incoming_mailbox_report.json
```

### M13 — Candidate Review / Apply Split

Goal:

```text
candidate review != candidate apply
review is evidence-only
apply requires matching prior review receipt
```

Targets:

```text
core_lite/candidates/
scripts/run_candidate_review_apply_smoke_test.py
tools/tasks/task_catalog.json
reports/current/candidate_review_report.json
reports/current/candidate_apply_report.json
```

### M14 — Stage 32–34 Formalism Linkage

Goal:

```text
Core-Lite policy references Stage 32, Stage 33, and Stage 34 formalism outputs from Data-Continuation/formalism-tests.
Site remains mirror-only.
```

Targets:

```text
core_lite/transition_table/policy.json
core_lite/transition_table/formalism.py
scripts/run_formalism_linkage_check.py
```

### M15 — SDK/CLI Surface

Goal:

```text
Expose stable developer-facing governed operations only.
No raw mutation API.
```

Targets:

```text
core_lite/sdk/
scripts/core_lite_cli.py
docs/SDK_CLI_SURFACE.md
```

## Activation Rule

A stage is active only when all are true:

```text
pytest passes
workflow passes
declared task passes
receipt exists
report exists
failure mode is tested
```

## Next Immediate Work

The next direct build step should be M11: stabilize bundle ingestion inside the existing repo while preserving the stable dispatcher pattern.
