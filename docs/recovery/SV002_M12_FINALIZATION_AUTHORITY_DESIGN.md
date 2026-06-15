# SV002-M12 Finalization Authority Design

Status: design lane opened  
Entity: StegVerse-002  
Repository: core-lite  
Depends on: SV002-M11 recovery-admissibility proof loop

## Purpose

SV002-M12 defines finalization authority for repository recovery after SV002-M11 has proven bounded recovery evidence admission.

This lane is a design lane first. It does not authorize cleanup execution, deletion, bulk ingestion, or direct final relocation.

## Boundary inherited from SV002-M11

SV002-M11 proved:

- stale recovery bundle fails closed
- corrected recovery bundle is admitted by the transition table
- corrected recovery bundle receives CGE ALLOW
- regression guard prevents CGE ERROR fallback from silently passing
- one-bundle recovery proof remains bounded
- final cleanup/removal is explicitly deferred

SV002-M12 starts only after those conditions are true.

## Non-claims

SV002-M12 does not claim:

- permission to delete original files
- permission to bulk ingest all corrected recovery bundles
- permission to relocate semantic content directly to final repo destinations
- permission to bypass transition-table receipts
- permission to treat cleanup as admissibility
- permission to treat recovery wrapping as final disposition

## Required authority classes

Finalization requires at least four separate authority classes.

| Authority class | Purpose | M12 default |
|---|---|---|
| `recovery_evidence_authority` | Confirms corrected recovery bundle evidence is valid | inherited from M11 receipts |
| `destination_mapping_authority` | Determines proposed final path or quarantine path | design only |
| `original_removal_authority` | Determines whether original source can be removed | not granted |
| `bulk_sequence_authority` | Determines whether multiple recovery bundles may be processed | not granted |

No single authority class may imply another.

## Finalization states

Each corrected recovery bundle must move through one of these states:

| State | Meaning |
|---|---|
| `PENDING_FINALIZATION_DESIGN` | Corrected evidence exists, but no final action allowed |
| `DESTINATION_MAPPING_PROPOSED` | A proposed final destination exists, but is not executed |
| `FINALIZATION_REVIEW_REQUIRED` | Human or higher governance review is required |
| `FINALIZATION_ALLOWED_SINGLE` | One bundle may be finalized under receipt-bound authority |
| `FINALIZATION_DENIED` | Bundle must remain retained or quarantined |
| `ORIGINAL_REMOVAL_ALLOWED` | Original may be removed only after finalization receipt exists |

## Required receipts before final action

A final action may not occur unless all of the following are present:

1. recovery wrap receipt
2. corrected bundle validation report
3. one-bundle transition-table receipt
4. CGE receipt with `decision: ALLOW`
5. regression guard receipt with `decision: ALLOW`
6. proposed destination map receipt
7. finalization decision receipt
8. post-finalization verification receipt

## Minimal safe M12 sequence

The first safe sequence is not bulk cleanup. It is one proposed finalization plan.

1. Select one corrected recovery evidence bundle.
2. Produce a destination mapping proposal.
3. Verify the original source still exists or record stale-missing status.
4. Verify corrected bundle hash matches M11 evidence.
5. Run transition-table finalization check.
6. Run CGE finalization check.
7. Emit finalization receipt.
8. Do not move/delete unless finalization decision explicitly grants `FINALIZATION_ALLOWED_SINGLE`.

## Required guardrails

M12 implementation must enforce:

- single-bundle default
- no implicit bulk mode
- no deletion without original-removal receipt
- no final relocation without destination-mapping receipt
- no cleanup by filename pattern alone
- no cleanup based only on directory location
- no action if CGE is `ERROR`, `PENDING`, or missing
- no action if transition-table decision is not `ALLOW`
- no action if regression guard is stale or failing

## Proposed M12 artifacts

Recommended future files:

```text
tools/scripts/repo_recovery_destination_plan.py
tools/scripts/repo_recovery_finalize_one.py
.github/workflows/repo-recovery-finalize-one-proof.yml
reports/current/repo_recovery_destination_plan.json
receipts/current/repo_recovery_destination_plan_receipt.jsonl
reports/current/repo_recovery_finalize_one_report.json
receipts/current/repo_recovery_finalize_one_receipt.jsonl
```

## Initial M12 decision

M12 is opened as design-only.

Current decision:

```text
FINALIZATION_DESIGN_OPENED
```

Current execution authority:

```text
none
```

Current cleanup authority:

```text
none
```

## M12 stage objective

SV002-M12 should close only when the repo can prove one finalization proposal can be evaluated without granting silent deletion, broad cleanup, or bulk relocation authority.
