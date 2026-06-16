# v0.1.3-gllm Activation Target

This document is a proof-control source marker for StegVerse-002/core-lite.

Its purpose is to keep the activation condition explicit and machine-checkable while the autonomous tick completes the v0.1.3-gllm transition-bundle proof.

## Required terminal state

The repository reaches v0.1.3-gllm activation when `scripts/check_transition_bundle_proof.py` returns:

```text
PROOF_COMPLETE
```

## Required artifacts

```text
dist/bundles/proposed_transition_bundle.json
dist/bundles/proposed_transition_bundle.zip
dist/bundles/proposed_transition_bundle.sha256
receipts/current/proposed_transition_bundle_receipt.jsonl
receipts/current/transition_bundle_ingest_receipt.jsonl
```

## Required authority posture

```text
candidate_evidence_only: true
canonical_authority: false
broad_authority: false
may_bind_repo_state: false
```

## Required transition rule

```text
transport_mechanism: ingestion
requires_ingestion: true
```

## Required next boundary

Candidate admission is not installation. After v0.1.3-gllm reaches `PROOF_COMPLETE`, the next build target is destination admissibility / install-decision boundary.

No broad authority is created by this activation target.
