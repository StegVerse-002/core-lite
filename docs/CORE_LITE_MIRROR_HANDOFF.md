# StegVerse-002 Core-Lite Mirror Handoff

Generated: 2026-06-17
Repo: StegVerse-002/core-lite
Current goal: v0.1.3-gllm activation through governed transition-bundle proof, heartbeat evidence, and repo-structure verification.

## Purpose

This file is the current handoff and task source of truth for non-Site/non-Publisher work in this repo.

It mirrors the role of `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` for the core-lite repo: a new session should check this file before continuing core-lite activation, proof, heartbeat, structure-verification, or destination-admissibility work.

## Current Scope

The active build scope is StegVerse-002/core-lite v0.1.3-gllm.

The goal is to prove that proposed LLM collaboration evidence can be packaged as candidate evidence, transported through ingestion, recorded with receipts, observed by heartbeat checks, and compared against required repo structure without creating broad or canonical authority.

## Current Activation Target

Activation requires:

```text
PROOF_COMPLETE
```

Required activation artifacts:

```text
dist/bundles/proposed_transition_bundle.json
dist/bundles/proposed_transition_bundle.zip
dist/bundles/proposed_transition_bundle.sha256
receipts/current/proposed_transition_bundle_receipt.jsonl
receipts/current/transition_bundle_ingest_receipt.jsonl
```

## Current Known State

Known present before this handoff:

```text
dist/bundles/proposed_transition_bundle.json
dist/bundles/proposed_transition_bundle.zip
dist/bundles/proposed_transition_bundle.sha256
receipts/current/proposed_transition_bundle_receipt.jsonl
```

Known missing or not yet observed before this handoff:

```text
receipts/current/transition_bundle_ingest_receipt.jsonl
receipts/current/heartbeat_evaluation_receipt.jsonl
receipts/current/scheduler_liveness_receipt.jsonl
reports/current/repo_structure_verification.json
receipts/current/repo_structure_verification_receipt.jsonl
```

## Current Build Files

Core scripts:

```text
scripts/package_transition_bundle.py
scripts/ingest_transition_bundle.py
scripts/check_transition_bundle_proof.py
scripts/evaluate_heartbeat_mode.py
scripts/check_scheduler_liveness.py
scripts/verify_repo_structure.py
```

Core workflows:

```text
.github/workflows/core-lite-intake.yml
.github/workflows/core-lite-autonomous-tick.yml
.github/workflows/core-lite-heartbeat-watchdog.yml
```

Core config:

```text
config/heartbeat_policy.json
config/repo_structure_targets.json
```

## Authority Boundary

All v0.1.3-gllm work remains candidate-only:

```text
candidate_evidence_only: true
canonical_authority: false
broad_authority: false
may_bind_repo_state: false
```

Candidate admission is not installation. The next boundary after v0.1.3 activation is destination admissibility / install-decision boundary.

## Next Build Steps

1. Verify whether `receipts/current/transition_bundle_ingest_receipt.jsonl` has appeared.
2. Verify whether heartbeat and scheduler receipts have appeared.
3. Verify whether `reports/current/repo_structure_verification.json` has appeared.
4. If no repo-native heartbeat evidence is present, inspect whether scheduled workflows are disabled, delayed, or not committing.
5. Once `PROOF_COMPLETE` is reached, begin v0.1.4 destination admissibility boundary.

## Status Reporting Rule

Future responses for this repo should end with these lines:

```text
StegVerse-002 - %complete
core-lite - %complete
core-lite - %complete TO GOAL ACTIVATION;
Fully developed files vs scaffolding/stubs - %complete
Δ [core-lite: ACTUAL vs BUILT] - EXPLANATION.
Thread archive readiness: STATUS.
```

The delta line should compare the stated repo completion against `reports/current/repo_structure_verification.json` when available. If that report is unavailable, the delta line must say verification is pending rather than guessing.

## Archive Readiness

This thread is not archive-ready until either:

1. v0.1.3 reaches `PROOF_COMPLETE`, or
2. this handoff is sufficient for a new session to continue without relying on prior chat context.

This handoff makes the current state portable, but activation remains incomplete until the ingestion receipt and repo-native heartbeat/structure verification are visible.
