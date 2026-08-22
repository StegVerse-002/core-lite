# StegVerse-002 Core-Lite Mirror Handoff

## Source of truth

This document is the single repository-wide current handoff for
`StegVerse-002/core-lite`. Machine authority is declared in
`.handoff/current.json`, and the current commit-bound change is declared in
`.continuity/config.json`.

The scoped StegGuardian automation lane remains at
`docs/STEGGUARDIAN_AUTOMATION_HANDOFF.md` and cannot supersede this record.

Live default-branch state, Git history, workflow runs, receipts, committed
reports, and verified change records override historical conversation claims.

## Role

Core-Lite is the StegVerse-002 ingestion-through-execution layer. Its current
goal is to receive and structurally validate candidate-specific reviewer
authority evidence without converting structural acceptance into review,
quorum, execution, or repository-binding authority.

## Current installed files

```text
.handoff/current.json
.continuity/config.json
.continuity/change-records/SV-CONT-CORE-LITE-20260804-001.json
.continuity/cross-repository-references.json
.github/workflows/handoff-authority.yml
.github/workflows/continuity-provenance.yml
.github/workflows/bootstrap-core-lite.yml
.github/workflows/core-lite-intake.yml
VERSION.json
docs/CORE_LITE_MIRROR_HANDOFF.md
docs/STEGGUARDIAN_AUTOMATION_HANDOFF.md
schemas/management_reviewer_authority_submission.schema.json
incoming/management_reviewer_authority/README.md
tools/check_ecosystem_component_version.py
tools/validate_management_reviewer_authority_submission.py
tools/tasks/sv002.management_reviewer_authority.validate.json
reports/current/management_reviewer_authority_submission_report.json
receipts/current/management_reviewer_authority_submission_receipt.jsonl
```

## Ecosystem component version contract

Normalized component identity is now installed under the shared StegVerse
component-version contract without changing repository authority:

```text
component_id: STEGVERSE-002-CORE-LITE
component_version: 0.1.27
version_stage: DEVELOPMENT
release: NOT_CLAIMED
runtime: PENDING
activation: PENDING
authority_effect: NONE
```

Evidence and enforcement:

```text
VERSION.json                                      commit 95697020e9637837223dd7e45426ba535ee1017f
tools/check_ecosystem_component_version.py        commit 2fa3901e3c02939464d1639056d5b2aa7b18a938
.github/workflows/bootstrap-core-lite.yml          commit d44ab534ba3a01f6e6e06ded781c0758341b5596
```

The existing `bootstrap-core-lite` workflow now contains a separate
non-mutating `version-contract` job for changes to the declaration, validator,
this handoff, or the workflow. The bootstrap identity action remains
manual-only. Workflow installation is not workflow execution evidence; hosted
PASS must be observed separately before this repository is counted as having
executed version-contract proof.

The version declaration records the repository-native v0.1.27 handoff lineage.
It does not create a release tag, runtime proof, review authority, quorum,
execution authority, repository-binding authority, or activation.

## Current working path

```text
repository change
  -> governing handoff authority ALLOW
  -> commit-bound change record
  -> changed-path and content-hash verification
  -> required cross-repository reference verification
  -> continuity provenance ALLOW
  -> candidate-specific reviewer authority submission
  -> structural completeness validation
  -> candidate and review-only scope validation
  -> validity and revocation posture validation
  -> evidence-hash format validation
  -> REVIEWER_AUTHORITY_SUBMISSION_PENDING or structural result
  -> future evidence reconstruction verifier
  -> separate management-action review transition
  -> separate execution transition
```

Retained workflow execution surfaces:

```text
.github/workflows/bootstrap-core-lite.yml
.github/workflows/core-lite-intake.yml
```

Declared task:

```bash
python tools/scripts/run_declared_task.py \
  --repo-root . \
  --task-id sv002.management_reviewer_authority.validate \
  --stage SV002-M12
```

## Done state for this repo

Completed chain:

```text
v0.1.20 DECLARED_TASK_WORKFLOW_WIRED
v0.1.21 MANAGEMENT_ACTION_CANDIDATE_SYNTHESIS_PENDING_001_ACCEPTANCE
v0.1.22 MANAGEMENT_PACKAGE_RETRIEVAL_TASK_READY
v0.1.23 MANAGEMENT_PACKAGE_CANDIDATE_EVIDENCE_ACCEPTED
v0.1.24 MANAGEMENT_ACTION_CANDIDATES_READY_FOR_REVIEW
v0.1.25 MANAGEMENT_ACTION_REVIEW_FAIL_CLOSED_PENDING_AUTHORIZED_QUORUM
v0.1.26 REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED
v0.1.27 REVIEWER_AUTHORITY_SUBMISSION_PENDING
```

The repository is handoff-capable through v0.1.27. The current authority lane is
done only when accepted submissions can be independently reconstructed against
identity, policy, delegation, revocation, and evidence-hash sources.

Continuity provenance is an admission prerequisite. It does not grant review,
quorum, execution, or repository-binding authority.

## Completed in latest pass

```text
v0.1.27 reviewer/quorum authority submission surface installed
single governing handoff declared in .handoff/current.json
StegGuardian automation handoff explicitly scoped
pinned reusable handoff-authority workflow installed and validated
commit-bound continuity config installed
pinned continuity-provenance caller installed
cross-repository validator reference pinned to commit and Git blob
adoption change record installed
normalized VERSION.json installed for repository-owned 0.1.27 DEVELOPMENT identity
owner-local fail-closed version validator installed
existing bootstrap workflow extended with non-mutating version-contract validation job
```

Current structural result remains:

```text
REVIEWER_AUTHORITY_SUBMISSION_PENDING
submission_count: 0
accepted_count: 0
rejected_count: 0
review_rerun_allowed: false
```

## Remaining work

Create a reconstruction verifier that resolves and verifies:

```text
reviewer identity evidence
policy references
delegation references
revocation status
evidence hashes
```

It must produce one of:

```text
REVIEWER_AUTHORITY_EVIDENCE_ACCEPTED
REVIEWER_AUTHORITY_EVIDENCE_DENIED
REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED
```

Current management candidates remain:

```text
SV002-MGMT-001: reduce Data-Continuation/core-lite workflows toward the two-workflow standard.
SV002-MGMT-002: reconcile or complete the high-risk missing scanner capability path.
SV002-MGMT-003: preserve the published 001-to-002 immutable-reference handoff mechanism.
```

Submission target remains `Data-Continuation/core-lite`, review-only, and
limited to those candidate IDs.

Boundary:

```text
structural_acceptance_grants_review_authority: false
structural_acceptance_forms_quorum: false
structural_acceptance_grants_execution_authority: false
may_bind_repo_state: false
execution_requires_separate_transition: true
```

## Destination installs

Current and future evidence may flow to:

```text
StegVerse-002/micro-node-runtime
StegVerse-002/admissibility-gateway
StegVerse-002/StegGuardian
master-records/orchestration
```

No destination receives authority merely by receiving a submission, report,
receipt, handoff, or provenance record.

## Next task

Run the pinned continuity-provenance gate. After it returns `ALLOW`, implement
the reviewer-authority evidence reconstruction verifier through a new change
record. Do not rerun management-action review automatically from structural
acceptance.

For the ecosystem-versioning lane, separately observe the installed
`version-contract` job on the exact default-branch source before claiming
executed validator evidence.
