# StegVerse-002 Core-Lite Mirror Handoff

## Source of truth

This document is the single repository-wide current handoff for `StegVerse-002/core-lite`.
Machine authority is declared in `.handoff/current.json`, and the current commit-bound
change is declared in `.continuity/config.json`.

Live default-branch state, Git history, workflow runs, receipts, committed reports, and
verified change records override historical conversation claims and stale status text.

## Role

Core-Lite is the StegVerse-002 ingestion-through-execution layer and governed AI/intellect
block. External LLM reasoning remains bounded input. It is never identity, consent,
quorum, execution authority, or repository-binding authority.

## Current version and lifecycle state

```text
component_id: STEGVERSE-002-CORE-LITE
component_version: 0.1.28
version_stage: DEVELOPMENT
release: NOT_CLAIMED
runtime: PENDING
activation: PENDING
authority_effect: NONE
source_readiness: IMPLEMENTED_PENDING_EXECUTED_PROOF
```

Historical M0-M10 completion remains implementation evidence only. It is not current
runtime, activation, release, or public-observation evidence.

## Experiment-readiness objective

The immediate goal is to prepare StegVerse-002 for the public experiment without
manufacturing authority or converting source success into an activation claim.

The source lane now includes:

```text
tools/reconstruct_management_reviewer_authority.py
schemas/management_reviewer_authority_evidence.schema.json
tests/test_management_reviewer_authority_reconstruction.py
tools/tasks/sv002.management_reviewer_authority.reconstruct.json
scripts/run_sv002_experiment_readiness.py
tools/tasks/sv002.experiment.readiness.verify.json
```

The reconstruction verifier independently resolves and verifies:

```text
reviewer identity evidence
policy evidence
delegation evidence
revocation evidence
evidence SHA-256 bindings
candidate scope
review-only action scope
```

Terminal reconstruction decisions are:

```text
REVIEWER_AUTHORITY_EVIDENCE_PENDING
REVIEWER_AUTHORITY_EVIDENCE_ACCEPTED
REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED
```

An accepted reconstruction still has:

```text
quorum_formed: false
execution_authority_granted: false
repository_binding_granted: false
runtime_activation_granted: false
```

No private, human, owner, council, or service authority evidence may be fabricated merely
to make the experiment pass.

## One-command source readiness

Declared task:

```bash
python tools/scripts/run_declared_task.py \
  --repo-root . \
  --task-id sv002.experiment.readiness.verify \
  --stage SV002-M12
```

The readiness task runs:

1. reviewer-authority reconstruction unit tests;
2. repository reviewer-authority reconstruction;
3. ecosystem component-version validation;
4. receipted readiness reporting.

Expected terminal decision when source is healthy:

```text
ALLOW_EXPERIMENT_READINESS
```

That decision means the source-level experiment lane is ready. It does not mean a
runtime is activated or publicly observed.

## Current authority path

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

Continuity provenance is an admission prerequisite. It does not grant review, quorum,
execution, repository-binding, release, or activation authority.

## Current management candidates

```text
SV002-MGMT-001: reduce Data-Continuation/core-lite workflows toward the two-workflow standard.
SV002-MGMT-002: reconcile or complete the high-risk missing scanner capability path.
SV002-MGMT-003: preserve the published 001-to-002 immutable-reference handoff mechanism.
```

Submission target remains `Data-Continuation/core-lite`, review-only, limited to those
candidate IDs.

## Experiment safety invariants

```text
capability != admissibility
source-ready != runtime
workflow-pass != activation
review-evidence != quorum
LLM-output != authority
receipt != consent
reconstruction != occurrence
merge != release
public page != observed end-to-end experiment
```

All unknown, missing, revoked, tampered, out-of-scope, or unreconstructable reviewer
authority evidence fails closed.

## Installed governance surfaces retained

```text
.handoff/current.json
.continuity/config.json
.continuity/cross-repository-references.json
.github/workflows/handoff-authority.yml
.github/workflows/continuity-provenance.yml
.github/workflows/bootstrap-core-lite.yml
.github/workflows/core-lite-intake.yml
VERSION.json
docs/CORE_LITE_MIRROR_HANDOFF.md
docs/STEGGUARDIAN_AUTOMATION_HANDOFF.md
schemas/management_reviewer_authority_submission.schema.json
tools/validate_management_reviewer_authority_submission.py
tools/tasks/sv002.management_reviewer_authority.validate.json
```

The existing stable dispatcher remains the execution surface. Ordinary capability
expansion should remain declared-task-driven rather than multiplying workflows.

## Remaining work after source merge

Machine-executable, evidence-bearing sequence:

1. obtain exact-head handoff semantic and continuity-provenance admission;
2. merge this admitted readiness change;
3. execute `sv002.experiment.readiness.verify` on merged source;
4. preserve the resulting report and receipt;
5. route any authorized reviewer packet through reconstruction without fabricating one;
6. obtain runtime evidence before setting `runtime.state` away from `PENDING`;
7. obtain runtime activation evidence before setting `activation.state` away from `PENDING`;
8. obtain public-display/end-to-end observation evidence before claiming experiment occurrence.

If the execution environment needed for steps 3-8 is unavailable to the current actor,
the repository must remain explicit about that boundary rather than inferring success.

## Destination installs / integrations

Current and future bounded evidence or execution integration may flow to:

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
handoff, provenance record, or experiment-readiness result.

## Release gate

Do not tag or release StegVerse-002 merely because source readiness is green. Release
requires the applicable version contract, validation evidence, continuity admission,
runtime/publication requirements, and release record to agree.

When release-ready, verify that pertinent lifecycle and experiment semantics are updated
or propagated to:

```text
StegVerse-Labs/Site
GCAT-BCAT-Engine/Publisher
admissibility-wiki
stegguardian-wiki
```

## Next task

Complete the current continuity change record, obtain exact-head machine validation,
merge if admitted, then execute the declared experiment-readiness task on the merged
default branch. Keep runtime and activation pending until direct evidence exists.
