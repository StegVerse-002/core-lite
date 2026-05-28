# SV002-M11 — Governed Apply/Review Boundary

**Stage:** SV002-M11
**Entity:** StegVerse-002
**Capability:** governed_apply_review_boundary
**Status:** Installed

---

## Purpose

M11 installs the apply/review gate: a boundary that separates the act of
*proposing* an apply from the act of *executing* it.

No apply may proceed unless it passes the governed review boundary first.

---

## Boundary Contract

An apply request must:

1. Declare a `request_id`, `entity`, `stage`, `capability`, and `requester`
2. Be validated against `apply_request.schema.json`
3. Pass the CGE admissibility gate (ALLOW / DENY / DEFER)
4. Produce a structured `apply_review.schema.json` decision record
5. Emit a receipt before any mutation occurs
6. Only proceed to apply if decision is `ALLOW`

---

## Decision Set

| Decision | Meaning |
|----------|---------|
| `ALLOW`  | Apply request passed all boundary checks |
| `DENY`   | Apply request failed one or more checks |
| `DEFER`  | Apply request requires further review before proceeding |

---

## Separation of Concerns

- Review decision ≠ apply execution
- Requester identity ≠ admissibility
- Capability declaration ≠ capability grant
- Human approval ≠ Triad admissibility
- AI output ≠ apply authority

---

## Triad Enforcement

**GCAT/BCAT** — Is the requested apply legitimate under governance and
constraint? Does the transition balance check pass?

**ECAT/ICAT** — Is the requesting entity coherent and admissible? Does the
inverse constraint check pass?

**% Existence** — Does the resulting state remain coherent, livable,
recoverable, and admissible for all affected entities?

All three axes are checked. A DENY on any axis produces a DENY decision.
An unresolved axis defers to DEFER unless the request is trivially safe.

---

## Task IDs

Apply gate: `stegverse.apply.gate`

---

## Done Definition

M11 is complete when:

1. An apply request can be submitted as a structured JSON document
2. The gate validates the request schema
3. The gate runs CGE admissibility checks
4. The gate emits a structured review decision record
5. The gate emits a receipt before any mutation
6. DENY and DEFER halt execution with explanation
7. Only ALLOW proceeds
8. No requester identity grants automatic ALLOW
9. Triad axes are explicitly evaluated
10. Review and apply remain separated
