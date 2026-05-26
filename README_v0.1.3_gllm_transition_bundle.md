# StegVerse-002 / core-lite — v0.1.3-gllm Transition Bundle Packaging

## Purpose

This package upgrades the governed LLM collaboration gate from:

```text
provider outputs → thread → reports → receipts
```

to:

```text
provider outputs → thread → reports → receipts → proposed-transition bundle → ingestion receipt
```

## What This Fixes

This bundle corrects the known issues in Claude’s first draft:

```text
manifest hash mismatch fixed
raw provider outputs included
version advanced to 0.1.3-gllm
intake no longer grants canonical authority
original repo paths preserved inside bundle
schema shape enforced through dependency-free validation
workflow packages bundle after coordination
```

## Upload Targets

```text
task.md
scripts/package_transition_bundle.py
scripts/ingest_transition_bundle.py
schemas/transition_bundle.v1.schema.json
docs/methodology/LLM_OUTPUT_TO_INGESTION_CHAIN.md
docs/methodology/TASK_AS_INTERFACE_METHODOLOGY.md
docs/methodology/FOUNDER_FAMILY_PRESERVATION_BOUNDARY.md
.github/workflows/core-lite-intake.yml
iosnoperiod.md
iosnoperiod/github/workflows/core-lite-intake-yml
```

## Display Path Note

The workflow file is displayed in some docs as:

```text
github/workflows/core-lite-intake.yml
```

Actual repo path has a leading dot:

```text
.github/workflows/core-lite-intake.yml
```

The zip preserves the leading dot. The `iosnoperiod/` mirror is included for iOS-safe handling.

## Done Condition

After workflow run:

```text
dist/bundles/proposed_transition_bundle.json
dist/bundles/proposed_transition_bundle.zip
dist/bundles/proposed_transition_bundle.sha256
receipts/current/proposed_transition_bundle_receipt.jsonl
```

Then local ingestion test:

```bash
python scripts/ingest_transition_bundle.py dist/bundles/proposed_transition_bundle.zip
```

Expected decision:

```text
ADMITTED_AS_CANDIDATE_EVIDENCE
```

## Authority Boundary

This package does not grant broad authority.

This package does not grant canonical authority.

This package does not move data across repo/org boundaries directly.

It only creates the proposed-transition bundle and verifies that ingestion can admit it as candidate evidence.
