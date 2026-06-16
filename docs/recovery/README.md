# StegVerse-002 Recovery Module Index

Status: active index  
Entity: StegVerse-002  
Repository: core-lite  
Scope: recovery evidence, finalization review, finalize-one proposal, and future execution-lane separation

## Current activated module

The currently activated recovery/finalization module is:

```text
SV002-M11_TO_M13_NON_MUTATING_RECOVERY_FINALIZATION_MODULE
```

Activation decision:

```text
ACTIVATED_NON_MUTATING
```

Current authority boundary:

```text
execution_authority: none
cleanup_authority: none
bulk_authority: none
replacement_authority: none
original_removal_authority: none
mutation_performed: false
```

## Primary human-readable documents

Read these in order:

1. [`RECOVERY_BUNDLE_TRANSITION_REQUIREMENT.md`](RECOVERY_BUNDLE_TRANSITION_REQUIREMENT.md)  
   Defines why recovery bundles must carry explicit transition blocks and why recovery evidence is not install authority.

2. [`SV002_M11_STAGE_CLOSE_SUMMARY.md`](SV002_M11_STAGE_CLOSE_SUMMARY.md)  
   Summarizes the M11 governed repo recovery proof: stale bundle failed closed, corrected evidence bundle admitted.

3. [`SV002_M12_FINALIZATION_AUTHORITY_DESIGN.md`](SV002_M12_FINALIZATION_AUTHORITY_DESIGN.md)  
   Defines the M12 review-only finalization authority design and separates planning from execution.

4. [`SV002_M12_STAGE_CLOSE_SUMMARY.md`](SV002_M12_STAGE_CLOSE_SUMMARY.md)  
   Summarizes M12 destination planning and finalization checking as non-executing review evidence.

5. [`SV002_M13_FINALIZE_ONE_CANDIDATE_REQUIREMENTS.md`](SV002_M13_FINALIZE_ONE_CANDIDATE_REQUIREMENTS.md)  
   Defines the requirements for the M13 finalize-one candidate proposal lane.

6. [`SV002_M13_STAGE_CLOSE_SUMMARY.md`](SV002_M13_STAGE_CLOSE_SUMMARY.md)  
   Summarizes the M13 finalize-one candidate proposal result and guardrails.

7. [`SV002_M11_TO_M13_RECOVERY_FINALIZATION_PROOF_MAP.md`](SV002_M11_TO_M13_RECOVERY_FINALIZATION_PROOF_MAP.md)  
   Consolidates the M11-M13 proof chain for humans and downstream agents.

8. [`SV002_M11_TO_M13_ACTIVATION_SUMMARY.md`](SV002_M11_TO_M13_ACTIVATION_SUMMARY.md)  
   Activates the M11-M13 chain as a completed non-mutating recovery/finalization proof module.

## Machine-readable task catalog supplement

The activated module has a dedicated machine-readable supplement:

```text
tools/tasks/task_catalog.recovery_m11_m13.json
```

It catalogs:

```text
sv002.repo.recovery.corrected_bundle_validation
sv002.repo.recovery.one_bundle_proof
sv002.repo.recovery.cge_regression_guard
sv002.repo.recovery.destination_plan
sv002.repo.recovery.finalize_check
sv002.repo.recovery.finalize_one_candidate
sv002.repo.recovery.authority_boundary_regression
sv002.repo.recovery.m11_to_m13_activation
```

## Primary report and receipt artifacts

### M11

```text
reports/current/repo_recovery_corrected_bundle_validation.json
receipts/current/transition_table_receipt.jsonl
receipts/current/cge_recovery_proof_regression_receipt.jsonl
```

### M12

```text
reports/current/repo_recovery_destination_plan.json
reports/current/repo_recovery_finalize_check.json
receipts/current/repo_recovery_destination_plan_receipt.jsonl
receipts/current/repo_recovery_finalize_check_receipt.jsonl
```

### M13

```text
reports/current/repo_recovery_finalize_one_candidate.json
receipts/current/repo_recovery_finalize_one_candidate_receipt.jsonl
```

### Boundary regression

```text
reports/current/recovery_authority_boundary_regression.json
receipts/current/recovery_authority_boundary_regression_receipt.jsonl
```

## Workflow map

```text
.github/workflows/repo-recovery-rebuild-corrected.yml
.github/workflows/repo-recovery-ingest-one-proof.yml
.github/workflows/cge-recovery-proof-regression.yml
.github/workflows/repo-recovery-destination-plan.yml
.github/workflows/repo-recovery-finalize-check.yml
.github/workflows/repo-recovery-finalize-one-candidate.yml
.github/workflows/recovery-authority-boundary-regression.yml
```

## Current status by stage

```text
SV002-M11: complete — recovery evidence admission and CGE regression guard
SV002-M12: complete — finalization design and review-only planning
SV002-M13: complete — finalize-one proposal and authority-boundary regression
```

## Interpretation rules

1. Recovery evidence admission is not finalization authority.
2. Destination planning is not execution authority.
3. Review eligibility is not execution permission.
4. Finalize-one proposal is not repository mutation.
5. Capturing pre-mutation hashes is not consent to mutate.
6. Cleanup authority cannot be inferred.
7. Original-removal authority cannot be inferred.
8. Bulk sequencing cannot begin until single-bundle execution is separately proven.
9. Future mutation requires a separate transition-table and CGE authority lane.
10. Activation of this module means only non-mutating proof infrastructure is activated.

## Next module

The recommended next module is:

```text
SV002-M14_FINALIZE_ONE_EXECUTION_AUTHORITY_DESIGN
```

That future module must start as design-only and must not inherit execution authority from M11-M13.

Minimum first document:

```text
docs/recovery/SV002_M14_FINALIZE_ONE_EXECUTION_AUTHORITY_DESIGN.md
```

Minimum required boundaries:

```text
operator mutation intent receipt
transition-table finalization action distinct from evidence admission
CGE finalization authority check distinct from recovery evidence admission
exact diff or replacement plan
pre/post hash verification
rollback/dispute posture
post-finalization verification receipt
regression guard blocking unauthorized mutation
```

## Close statement

This index makes the activated recovery/finalization module discoverable by humans, automation, and downstream agents. It does not grant execution authority.
