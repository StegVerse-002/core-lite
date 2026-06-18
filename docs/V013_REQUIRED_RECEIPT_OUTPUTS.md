# v0.1.3 Required Receipt Outputs

This file defines the receipt evidence required to finish the current v0.1.3 activation task.

## Required outputs

```text
receipts/current/v013_activation_receipt_install_receipt.jsonl
reports/current/v013_activation_receipt_install_report.json
receipts/current/transition_bundle_ingest_receipt.jsonl
receipts/current/heartbeat_evaluation_receipt.jsonl
receipts/current/scheduler_liveness_receipt.jsonl
receipts/current/repo_structure_verification_receipt.jsonl
reports/current/repo_structure_verification.json
```

## Completion rule

The task is not complete until these outputs are visible on `main` and the proof checker reports a complete proof state.

## Authority boundary

```text
candidate_evidence_only: true
canonical_authority: false
broad_authority: false
may_bind_repo_state: false
```

This file does not claim activation. It only defines the expected committed evidence.

## Trigger Bump

```text
bump_reason: installer workflow now watches this checklist
bump_target: core-lite-v013-receipt-installer.yml
bump_effect: create fresh repo-native event for required-output comparison
```
