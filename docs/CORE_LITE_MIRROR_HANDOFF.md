# Core-Lite Mirror Handoff

## Purpose

This handoff lets the next build session continue `StegVerse-002/core-lite` activation without needing prior chat context.

It mirrors the purpose of `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` for a non-Site/non-Publisher repository.

## Current Goal

```text
Goal: Core-Lite activation hardening
Repository: StegVerse-002/core-lite
Current activation surface: M11-M16
Activation state: installed_pending_validation_chain
```

## Current Source of Truth

```text
Repository state is source of truth for installed files.
Validation reports and receipts are source of truth for activation claims.
Chat history is not source of truth after this handoff exists.
```

## Built Files / Surfaces

```text
M11 bundle ingestion smoke test
M12 guarded incoming mailbox
M13 candidate review/apply separation
M14 formalism linkage check
M15 governed SDK/CLI wrapper
M16 activation evidence export
Repo structure delta verifier
Task addition registration utility
```

## Required Continuation Order

```text
1. Run M12 incoming mailbox validation.
2. Run M13 candidate review/apply validation.
3. Run M14 formalism linkage validation.
4. Run M15 SDK/CLI validation.
5. Register M12-M16 task additions into tools/tasks/task_catalog.json.
6. Run M16 activation evidence export.
7. Run repo structure delta verifier with the current displayed repo-completion percent.
8. If activation evidence reports ALLOW and repo structure delta is acceptable, mark core-lite activation complete.
9. Determine next integration goal candidate and reset progress values for that new goal.
```

## Commands

```bash
python scripts/run_m12_incoming_mailbox_tests.py
python scripts/run_m13_candidate_review_apply_tests.py
python scripts/run_m14_formalism_linkage_check.py
python scripts/run_m15_sdk_cli_tests.py
python tools/scripts/register_task_additions.py --dry-run
python tools/scripts/register_task_additions.py
python scripts/run_activation_evidence_export.py
python scripts/verify_repo_structure_delta.py --reported-repo-complete 84
```

## Evidence To Capture

```text
reports/current/m12_incoming_mailbox_validation_report.json
reports/current/m13_candidate_review_apply_validation_report.json
reports/current/m14_formalism_linkage_report.json
reports/current/m15_sdk_cli_validation_report.json
reports/current/core_lite_activation_evidence_report.json
reports/current/repo_structure_delta_report.json
receipts/current/*.jsonl
dist/run_artifacts/*.zip
```

## Boundary Rules

```text
candidate output is evidence, not authority
incoming/ is mailbox, not durable proof state
SDK/CLI is governed wrapper, not raw mutation authority
formalism authority remains Data-Continuation/formalism-tests
workflow changes require explicit review
root README overwrite remains denied unless explicitly authorized
```

## Archive Readiness

This handoff contains the repo state, continuation order, commands, evidence requirements, and boundary rules needed to continue. The prior chat thread is no longer required for forward progress once this file is present in the repository.
