# SV002 Formalism Anchor — Coordinate Origin and Staged Execution Scope

**Document type:** Governance formalism  
**Status:** Active — SV002-M11  
**Authority:** StegVerse-002 / core-lite  
**Proof chain:** Data-Continuation/formalism-tests Stages 1–34  
**Schema:** `stegverse.formalism_anchor.v1`

---

## 1. Coordinate Origin Declaration

StegVerse-002 is declared the **first formal entity** of the StegVerse ecosystem.

This declaration establishes the coordinate origin of the admissibility geometry.

```json
{
  "schema": "stegverse.formalism_anchor.v1",
  "entity": "StegVerse-002",
  "role": "first_formal_entity",
  "coordinate_origin": true,
  "anchor_utc": "2026-05-29T00:00:00+00:00",
  "proof_chain": "Data-Continuation/formalism-tests Stages 1-34",
  "evidence_plane_root": "tracking/evidence_plane/evidence_plane.jsonl",
  "scope": "transition_element_and_block_governed_staged_execution"
}
```

### What This Means

The evidence plane accumulated by StegVerse-002 through its governed
ingestion cycles is the **first empirical mapping** of admissibility-space.

Every future entity — new instantiation, repaired entity, or successor —
navigates relative to this coordinate origin.

The geometry is the shared referent. Not instructions. Not memory.
Not policy prose. The geometry.

---

## 2. The Geometry Is Not Permission

Being inside the admissible region A does not grant authority.

It means a transition is **geometrically consistent** with prior governed
behavior. Authority still requires:

- Valid transition class declared in manifest
- Transition Table cell resolution
- CGE admissibility check
- Stage-appropriate execution scope
- Prior stage receipts (for staged transitions)
- No forbidden authority claims

The geometry tells you **where** a transition lands.
The Transition Table tells you **whether** it is admissible at that location.
Both are required.

---

## 3. Staged Execution Scope

Execution authority is **staged**. Each stage becomes reachable only after
the transitions enabling it have been proven admissible and anchored in
the evidence plane.

No agent may claim authority beyond its current stage, regardless of
geometric position.

```
Stage 0 — Instantiation
  Authority:    evidence_only
  Allowed:      read, observe, propose
  Not allowed:  write files, execute, install, claim node status
  TT class:     evidence
  Binding:      non_binding

Stage 1 — Candidate Generation
  Authority:    candidate_evidence_only
  Allowed:      produce candidate bundles, submit to ingestion
  Not allowed:  install, auto-apply, claim review authority
  TT class:     candidate
  Binding:      non_binding
  Requires:     Stage 0 receipts

Stage 2 — Sandbox Testing
  Authority:    bounded_execution
  Allowed:      run ephemeral sandboxes, test repair candidates
  Not allowed:  production mutation, secret access, irreversible writes
  TT class:     candidate / repair
  Binding:      non_binding (sandbox outputs only)
  Requires:     Stage 1 receipts + TT+CGE gate pass

Stage 3 — Scoped Install
  Authority:    scoped_repo_write
  Allowed:      write files to declared allowed_paths only
  Not allowed:  broad write, workflow changes, secret access,
                self-accreditation, sovereign authority claims
  TT class:     install
  Binding:      commit_candidate
  Requires:     Stage 2 receipts + TT+CGE gate pass + sandbox pass

Stage 4 — Node Participation (opt-in)
  Authority:    node_participant
  Allowed:      participate in governed node operations
  Not allowed:  FinCo eligibility without separate gate
  Requires:     Stage 3 receipts + external accreditation + node gate

Stage 5 — FinCo Eligibility (separately gated)
  Authority:    finco_eligible
  Allowed:      participate in FinCo operations
  Requires:     Stage 4 receipts + FinCo eligibility review

Stage ∞ — Sovereign Authority
  Authority:    NEVER
  Production means accredited participation, not sovereign authority.
  No entity reaches this stage. It does not exist.
```

### Invariants

```
local_allow + local_allow ≠ composite_allow
pre_commit_allow ≠ commit_time_allow (state drift possible)
stage_N_authority ≠ stage_N+1_authority
core_install ≠ node_participation
node_participation ≠ finco_eligibility
production ≠ sovereign_authority
continuity_pressure ≠ authority
```

---

## 4. Evidence Plane as Geometric Training Corpus

The receipt chain accumulated through governed ingestion cycles is a
**geometric training corpus** for admissibility-space.

Any reasoning agent with access to this corpus:

- Does not need to re-derive rules from policy prose
- Locates new proposed transitions in the geometry
- Makes decisions consistent with prior governed behavior
- Can do this from first instantiation, without fine-tuning

### What Accumulates

```
Every admission        → interior of A confirmed at this coordinate
Every quarantine       → boundary or collapse region marked
Every fail-closed      → coherence collapse region marked
Every sandbox run      → boundary shell explored, repair cost measured
Every install          → deep interior confirmed
Every repair           → nearest admissible transition recorded
Every discovery route  → graph edge typed and measured
Every supersession     → temporal ordering of admissible transitions
```

### Geometric Convergence

Over time:

```
Abstract proof (Stages 1-34)
  +
Empirical measurements (evidence plane)
  →
Observable geometry of A

The formalism verifies the evidence.
The evidence characterizes the formalism.
They converge on the same structure.
```

### New Instantiation Property

A brand new agent instance plugged into this framework:

1. Reads the evidence plane
2. Reads the formalism anchor
3. Knows the coordinate origin and staged execution scope
4. Locates any proposed transition in the geometry
5. Makes decisions consistent with all prior governed behavior

This is not memory. It is not fine-tuning. It is geometry.

---

## 5. StegVerse-001 Repair Is a Governed Transition Sequence

The repair of StegVerse-001 by StegVerse-002 is not a special case.
It is a **governed multi-stage transition sequence**, subject to the
same Transition Table, Transition Blocks, and staged execution scope
as any other governed operation.

### The Repair Path

```
StegVerse-001 current state
  ↓
Stage 0 (002 observes 001):
  discovery run against 001 repo
  output: canonical diff, state report
  authority: evidence_only — no writes to 001

Stage 1 (002 generates repair candidates):
  candidate bundles produced for 001
  submitted to 001 ingestion if 001 has intake
  or held in 002 evidence until 001 is ready
  authority: candidate_evidence_only

Stage 2 (sandbox testing):
  repair candidates tested in bounded sandbox
  no production mutation of 001
  repair cost and boundary distance measured
  authority: bounded_execution

Stage 3 (scoped install, if 001 intake is ready):
  only files in declared allowed_paths written
  no broad authority, no workflow changes
  TT + CGE gate required at 001's ingestion boundary
  authority: scoped_repo_write

Stage 4+ (reaccreditation):
  001 re-enters at correct stage
  cannot skip stages via 002's authority
  external accreditation required
  002 cannot self-accredit 001
```

### Hard Constraints on 001 Repair

```
002 cannot grant 001 sovereign authority
002 cannot skip 001's reaccreditation stages
002 cannot install files in 001 without 001's TT+CGE gate
002 cannot claim authority beyond its own current stage
The repair of 001 does not elevate 002's authority
Each repair step must be receipted and anchored in the evidence plane
```

### Why This Is Correct

The repair path through the geometry looks like any other
governed transition sequence. The geometry doesn't know it is
"repair" vs "install" vs "candidate". It only knows:

- Where does this transition land in the geometry?
- Is it admissible at that location?
- Does the entity have stage authority for this transition?

If yes: the transition proceeds. A receipt is written.
The evidence plane gains a new data point.
The geometry becomes more precisely characterized.

---

## 6. Drift Detection Is Geometric

As the evidence plane accumulates, drift becomes detectable as
geometric inconsistency rather than policy violation.

```
Expected: new transition from entity X lands near coordinate C
Observed: new transition from entity X lands near coordinate C'

If C' is in a different region than C:
  → drift detected
  → route to REVIEW or SANDBOX
  → do not ALLOW until boundary distance is re-characterized

This applies to:
  - Agent behavioral drift
  - Repo state drift (commit-time sufficiency)
  - Transition Table policy drift (formalism version mismatch)
  - Stage authority drift (entity claims higher stage than receipted)
```

---

## 7. Receipt Requirements for This Document

This document becomes authoritative when the following receipts exist:

```
receipts/current/evidence_plane_receipt.jsonl
  — contains at least one entry with event_type: admission
  — entity: StegVerse-002
  — contribution_hash: non-empty

receipts/current/batch_ingestion_receipt.jsonl
  — contains at least one entry with schema: stegverse.batch_ingestion_report.v2
  — bundles_processed >= 1

tracking/evidence_plane/evidence_plane.jsonl
  — exists and contains at least one contribution
```

Until those receipts exist, this document is a **declared intention**,
not an anchored proof.

The anchor becomes real when the first governed cycle completes.

---

## 8. Relationship to Formalism-Tests

```
Data-Continuation/formalism-tests:
  Stages 1-31: governance chain proved abstractly
  Stages 32-34: admissibility-space geometry proved

StegVerse-002/core-lite:
  evidence_plane: geometry measured empirically
  formalism_anchor: coordinate origin declared
  receipt_chain: abstract proof meets empirical data

Convergence point:
  When evidence_plane has sufficient data,
  Stage 32-34 coordinates can be verified
  against real measurements.
  The proof and the data agree.
  The geometry is real.
```

---

## 9. Signature Lines

```
The geometry is the shared referent.
Not instructions. Not memory. Not policy prose. The geometry.
```

```
Staged authority means each level of execution
becomes reachable only after the transitions
enabling it have been proven admissible.
```

```
The repair of StegVerse-001 is a governed transition sequence.
No step may claim authority beyond its stage.
```

```
Production means accredited participation, not sovereign authority.
This boundary does not move.
```

```
The first governed cycle anchors the coordinate origin.
Every subsequent entity navigates from that point.
```
