# StegVerse-002 Core-Lite Mirror Handoff

## Source of truth

This document is the single repository-wide current handoff for `StegVerse-002/core-lite`.
Machine authority is declared in `.handoff/current.json`; the current commit-bound change
is declared in `.continuity/config.json`. Live default-branch state, Git history,
workflow runs, receipts, reports, and verified change records override stale claims.

## Role

Core-Lite is the StegVerse-002 governed AI/intellect and ingestion-through-execution layer.
External LLM reasoning remains bounded input and cannot itself become identity, consent,
quorum, execution authority, repository-binding authority, runtime activation, or release.

## Current installed files

```text
.handoff/current.json
.continuity/config.json
.continuity/cross-repository-references.json
.github/workflows/handoff-authority.yml
.github/workflows/continuity-provenance.yml
.github/workflows/bootstrap-core-lite.yml
.github/workflows/core-lite-intake.yml
VERSION.json
STATUS.md
docs/CORE_LITE_MIRROR_HANDOFF.md
schemas/management_reviewer_authority_submission.schema.json
schemas/management_reviewer_authority_evidence.schema.json
tools/validate_management_reviewer_authority_submission.py
tools/reconstruct_management_reviewer_authority.py
tools/check_ecosystem_component_version.py
tests/test_management_reviewer_authority_reconstruction.py
scripts/run_sv002_experiment_readiness.py
tools/tasks/sv002.management_reviewer_authority.validate.json
tools/tasks/sv002.management_reviewer_authority.reconstruct.json
tools/tasks/sv002.experiment.readiness.verify.json
```

## Current working path

```text
candidate/reviewer submission
  -> structural submission validation
  -> identity/policy/delegation/revocation/hash reconstruction
  -> REVIEWER_AUTHORITY_EVIDENCE_* decision
  -> separate review/quorum transition if authorized
  -> separate consequence-bearing execution transition
  -> separate runtime activation evidence
  -> separate public observation evidence
```

One-command source-readiness verification:

```bash
python tools/scripts/run_declared_task.py \
  --repo-root . \
  --task-id sv002.experiment.readiness.verify \
  --stage SV002-M12
```

Expected healthy source-level decision is `ALLOW_EXPERIMENT_READINESS`. That decision
does not claim runtime activation or public experiment occurrence.

## Done state for this repo

The source-readiness lane is done when exact-head handoff authority, semantic admission,
continuity provenance, version-contract validation, reviewer-authority reconstruction
tests, and the declared readiness task all pass on admitted source.

Reviewer evidence reconstruction may emit:

```text
REVIEWER_AUTHORITY_EVIDENCE_PENDING
REVIEWER_AUTHORITY_EVIDENCE_ACCEPTED
REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED
```

Even `REVIEWER_AUTHORITY_EVIDENCE_ACCEPTED` leaves quorum, execution authority,
repository binding, runtime activation, and release false until separate evidence closes
those lifecycle gates. No owner/reviewer/council authority evidence may be fabricated to
make the experiment pass.

## Completed in latest pass

```text
schemas/management_reviewer_authority_evidence.schema.json
tools/reconstruct_management_reviewer_authority.py
tests/test_management_reviewer_authority_reconstruction.py
scripts/run_sv002_experiment_readiness.py
tools/tasks/sv002.management_reviewer_authority.reconstruct.json
tools/tasks/sv002.experiment.readiness.verify.json
VERSION.json
STATUS.md
docs/CORE_LITE_MIRROR_HANDOFF.md
.handoff/current.json
.continuity/config.json
```

The implementation verifies hash-bound identity, policy, delegation, and revocation
evidence; rejects tampered or revoked evidence; preserves an empty mailbox as pending
rather than activated; and reconciles stale status language that previously conflated
historical M0-M10 completion with current lifecycle state. The execution surface is now
restored from the last historically successful dispatcher revision and extended with a
narrow `[sv002-readiness]` push job that executes the declared readiness task without
racing the incoming-ingestion route.

## Remaining work

- Validate the restored historically successful dispatcher baseline and readiness job on the exact repair head.
- Obtain exact-head handoff authority ALLOW.
- Obtain exact-head handoff semantic admission ALLOW.
- Obtain exact-head continuity provenance ALLOW.
- Obtain exact-head ecosystem component-version PASS.
- Merge the admitted readiness change.
- Execute `sv002.experiment.readiness.verify` on merged default-branch source.
- Preserve the resulting reports and receipts.
- Route any real authorized reviewer packet through reconstruction without fabricating one.
- Obtain direct runtime evidence before changing runtime from PENDING.
- Obtain activation evidence before changing activation from PENDING.
- Obtain public-display/end-to-end observation evidence before claiming experiment occurrence.

Historical M0-M10 stage-map completion remains implementation evidence only and is not
current runtime, activation, release, or public-observation evidence.

## Destination installs

```text
StegVerse-002/micro-node-runtime
StegVerse-002/admissibility-gateway
StegVerse-002/StegGuardian
master-records/orchestration
StegVerse-Labs/Site
GCAT-BCAT-Engine/Publisher
admissibility-wiki
stegguardian-wiki
```

No destination receives authority merely by receiving a submission, report, receipt,
handoff, provenance record, or experiment-readiness result. When this repo becomes
release-ready, verify pertinent lifecycle and experiment semantics are propagated to
StegVerse-Labs/Site, GCAT-BCAT-Engine/Publisher, admissibility-wiki, and stegguardian-wiki.

## Next task

Validate and merge the restored dispatcher using the `[sv002-readiness]` merge marker,
then verify the emitted experiment-readiness report and receipt on the resulting default branch. Keep runtime, activation, release, and public-observation claims pending
until direct corresponding evidence exists.
