# Curiosity, Motive, and Affective Governance Handoff

## Authority and scope

This is a scoped handoff for the curiosity/motive governance adoption lane in
`StegVerse-002/core-lite`. It is subordinate to
`docs/CORE_LITE_MIRROR_HANDOFF.md` and cannot grant review, quorum, execution,
runtime, or repository-binding authority.

The canonical formulation remains installed in `StegVerse-Labs/StegCore` at
commit `42231a3862c2fe9b5898e6f75d72cff0b44e7396`. The Master Records anchor and
destination receipt remain the custody references declared in
`contracts/curiosity-motive-governance-adoption.json`.

## Completed stages

### SV002-CMG-01 — source anchor binding

Installed and provenance-validated:

- exact StegCore source commit;
- canonical module and test Git-blob hashes;
- Master Records anchor and returned destination receipt;
- four-finding separation requirements;
- explicit non-activation boundary.

### SV002-CMG-02 — local replay-witness adapter

Installed:

- `tools/curiosity_motive_governance_adapter.py`;
- `contracts/curiosity-motive-governance-adapter-contract.json`;
- deterministic canonical hashing for witnesses, events, findings, and records;
- event-chain reconstruction and earliest conversion-point identification;
- separate event, motivational, normative, and observer findings;
- fail-closed invalid-witness and unresolved-authority behavior;
- explicit refusal to infer phenomenal status or convert motive into authority.

The adapter consumes a pre-hashed witness. It does not silently repair,
materialize, or overwrite occurrence evidence. Reconstruction remains an
evidentiary operation and does not establish that an event occurred outside the
recorded witness.

## Current boundary

```text
local_adapter_installed: true
deterministic_fixtures_installed: false
test_harness_installed: false
declared_task_installed: false
hosted_validation_installed: false
runtime_activation: false
execution_authority_granted: false
repository_binding_authority_granted: false
continuity_occurrence_receipt_minted: false
```

A motivational finding may be supported while execution is denied. A denial
does not erase the motive finding. An observer description does not define the
actor's motive. None of those findings grants authority.

## Next task

Implement Stage `SV002-CMG-03` as a separate continuity transition:

1. add deterministic valid, tampered, unauthorized, and underdetermined witness
   fixtures;
2. add a stdlib test harness that verifies stable replay roots, conversion
   points, claim separation, and fail-closed tamper handling;
3. preserve the existing activation boundary.

Do not register a declared task, hosted workflow, or runtime activation receipt
until the fixture and test stage passes independently.
