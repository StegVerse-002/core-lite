# SV002-M13 Finalize-One Candidate Requirements

Status: requirements lane opened  
Entity: StegVerse-002  
Repository: core-lite  
Depends on: SV002-M11 and SV002-M12

## Purpose

SV002-M13 is reserved for a future finalize-one candidate lane.

This document defines the conditions that must exist before any single recovery bundle may be finalized into repository state.

This document does not grant finalization authority. It does not create cleanup authority, deletion authority, relocation authority, bulk authority, or production mutation authority.

## Why this lane is separate from M12

SV002-M12 proved that a corrected recovery evidence bundle can be:

- destination-planned as `PLAN_ONLY`
- finalization-checked as `REVIEW_ONLY`
- classified as `FINALIZATION_ALLOWED_SINGLE_PROPOSAL_ONLY`

That status means review eligibility only. It is not execution permission.

SV002-M13 must be separate because executing even one finalization can mutate repository state.

## Required predecessor evidence

A finalize-one candidate may not run unless all of the following are present:

1. M11 corrected recovery bundle validation receipt.
2. M11 transition-table ALLOW receipt.
3. M11 CGE ALLOW receipt.
4. M11 CGE regression guard ALLOW receipt.
5. M12 destination plan receipt with `decision: PLAN_ONLY`.
6. M12 finalization check receipt with `decision: REVIEW_ONLY`.
7. M12 finalization status `FINALIZATION_ALLOWED_SINGLE_PROPOSAL_ONLY`.
8. Human/operator intent declaration for the exact bundle hash and proposed destination.

## Required exact binding values for first candidate

The first finalize-one candidate is limited to the already-proven recovery bundle:

```text
tracking/recovery_corrected/sv002_recovery_30d45378723de692_CHANGELOG.md.zip
```

Expected bundle hash:

```text
sha256:17f224bca33c1a1cff197b1f06f76058f9d61fb0e399c3b034070137bec52b3e
```

Expected proposed destination:

```text
CHANGELOG.md
```

Expected original source:

```text
CHANGELOG.md
```

## Candidate phases

### Phase 1 — intent receipt

Record an explicit operator intent receipt.

The receipt must state:

- bundle hash
- proposed destination path
- original source path
- expected action class
- whether replacement is requested
- whether original removal is requested
- whether rollback is required

Default values:

```text
replacement_requested: false
original_removal_requested: false
rollback_required: true
bulk_requested: false
```

### Phase 2 — preflight check

Preflight must verify:

- destination path is relative
- destination path contains no parent traversal
- bundle hash matches expected hash
- destination plan hash matches M12 receipt
- finalization check hash matches M12 receipt
- current destination hash is captured before any mutation
- payload hash is captured before any mutation
- proposed action is single-bundle only
- no cleanup authority is inferred

### Phase 3 — finalize-one proposal

The candidate may emit a proposal receipt.

The proposal receipt may state one of:

```text
FINALIZE_ONE_PROPOSED
FINALIZE_ONE_REVIEW_REQUIRED
FINALIZE_ONE_DENIED
FAIL_CLOSED
```

It may not execute mutation by default.

### Phase 4 — execution lane, separately admitted

Actual execution must be a separate lane and must require an explicit transition-table and CGE finalization authorization.

Execution cannot occur from Phase 1, Phase 2, or Phase 3 alone.

## Hard prohibitions

M13 candidate tooling must not:

- bulk ingest bundles
- delete original files
- delete old recovery bundles
- overwrite destination files without explicit replacement authority
- infer cleanup authority from a matching destination
- infer deletion authority from an admitted bundle
- treat review eligibility as execution permission
- mutate repository state when CGE is missing, ERROR, REVIEW, DENY, or FAIL_CLOSED
- mutate repository state when transition-table decision is not ALLOW

## Required future files

A safe M13 implementation should add these files only after this requirements document is accepted:

```text
tools/scripts/repo_recovery_finalize_one_candidate.py
.github/workflows/repo-recovery-finalize-one-candidate.yml
reports/current/repo_recovery_finalize_one_candidate.json
receipts/current/repo_recovery_finalize_one_candidate_receipt.jsonl
```

The candidate script should remain non-executing until a later explicit execution lane is designed.

## Stage posture

Current M13 posture:

```text
requirements_defined_only
```

Current execution authority:

```text
none
```

Current cleanup authority:

```text
none
```

Current original removal authority:

```text
none
```

Current bulk authority:

```text
none
```

## Close condition for this requirements step

This requirements step is complete when the repository contains a clear, reviewable statement that finalize-one execution requires a separate explicit authority lane and cannot be inferred from M11 or M12 evidence.
