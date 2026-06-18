# v0.1.3 Receipt Install Trigger

This file exists to trigger the repo-native v0.1.3 receipt installer workflow without relying on a scheduled beat.

The target workflow is:

```text
.github/workflows/core-lite-v013-receipt-installer.yml
```

The target script is:

```text
scripts/install_v013_activation_receipts.py
```

Expected evidence after the workflow runs:

```text
receipts/current/v013_activation_receipt_install_receipt.jsonl
reports/current/v013_activation_receipt_install_report.json
receipts/current/transition_bundle_ingest_receipt.jsonl
receipts/current/heartbeat_evaluation_receipt.jsonl
receipts/current/scheduler_liveness_receipt.jsonl
receipts/current/repo_structure_verification_receipt.jsonl
```

Authority posture remains:

```text
candidate_evidence_only: true
canonical_authority: false
broad_authority: false
may_bind_repo_state: false
```

This marker does not grant authority and does not claim activation. It only creates a repo-native change intended to activate receipt installation.

## Trigger Bump

```text
bump_reason: installer workflow trigger path added after original marker creation
bump_target: core-lite-v013-receipt-installer.yml
bump_effect: repo-native installer workflow should evaluate this marker path on push
```
