# SV002-M10.5 — Builder-Decoupled, Triad-Enforced Construction

**Stage:** SV002-M10.5
**Entity:** StegVerse-002
**Capability:** candidate_bundle_review
**Status:** Installed

---

## Purpose

M10.5 removes the assistant, human operator, and manual upload mechanics from the
position of implicit build authority.

Any entity may propose a candidate transition.
The ecosystem validates it against schemas, manifests, receipts, allowed paths, and Triad constraints.
The ecosystem denies malformed or inadmissible transitions.
The ecosystem reports exact repair requirements.
Only admissible transitions may proceed to the next governed boundary.

---

## Triad Enforcement

**GCAT / BCAT** — legitimacy, governance, constraint, authority, and transition balance
**ECAT / ICAT** — entity coherence, inverse constraint, identity-bound admissibility, participant-state validity
**% Existence** — whether the resulting state remains coherent, livable, recoverable, and admissible

No participant is trusted by identity. All transitions are evaluated by admissibility.

---

## Candidate Review Decision Set

| Decision                  | Meaning                                      |
|---------------------------|----------------------------------------------|
| `ALLOW_CANDIDATE_REVIEW`  | Candidate passed all review checks           |
| `DENY_CANDIDATE`          | Candidate failed one or more checks          |
| `FAIL_CLOSED`             | Review could not complete — deny by default  |

---

## Required Checks

- candidate_bundle_ref schema valid
- source type allowed
- source reachable or locally present
- hash matches expected hash
- bundle opens cleanly
- manifest exists and schema valid
- manifest does not request broad authority
- root README overwrite not requested unless explicitly allowed
- workflow changes denied unless specific capability granted
- paths are within allowed_paths
- file hashes match manifest declarations
- declared transition class is allowed
- stage is allowed
- authority_ref present
- policy_ref present
- GCAT/BCAT admissibility check (stubbed — must be resolved for binding transitions)
- ECAT/ICAT entity coherence check (stubbed — must be resolved for binding transitions)
- % Existence / recoverability check (review-only until apply stage)
- receipt emitted
- report emitted

---

## Separation of Concerns

- Review and apply are separate stages
- Proposal authority ≠ transition authority
- Human approval ≠ Triad admissibility
- AI output ≠ system voice
- Workflow success ≠ governed transition completion

---

## Task IDs

Review: `stegverse.candidate.intake.review`
Apply (future): `stegverse.candidate.intake.apply`

---

## Done Definition

M10.5 is complete when:

1. A candidate bundle/reference can be supplied without manual per-file upload
2. The system can fetch or locate the candidate
3. The system validates hash, manifest, paths, and declared authority
4. The system emits a candidate review report
5. The system emits a candidate review receipt
6. The system denies malformed candidates automatically
7. No participant (ChatGPT, Claude, OpenAI, Rigel, GitHub) is treated as inherently trusted
8. The Triad is represented as the admissibility enforcement layer
9. Review and apply remain separate
10. No broad authority is granted
