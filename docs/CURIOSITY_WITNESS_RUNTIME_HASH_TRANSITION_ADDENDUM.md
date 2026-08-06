# Curiosity Witness Runtime Custody Hash Transition Addendum

This addendum is subordinate to `docs/CURIOSITY_WITNESS_RUNTIME_INTAKE_MIRROR_HANDOFF.md`. It does not replace or compete with that canonical handoff and does not modify the runtime surfaces owned by pull request 6.

## Transition identity

```text
transition_id: SV002-CUSTODY-HASH-TRANSITION-REFERENCE-001
canonical_registry: master-records/core-lite/records/custody_chain_hash_transition_registry_001.json
local_reference: records/custody-hash-transition-reference-001.json
integration_lane: StegVerse-002/core-lite#7
runtime_owner: StegVerse-002/core-lite#6
canonical_dependency: master-records/core-lite#27
```

## Historical and current identities

The hashes in the completed runtime-intake and downstream chain remain valid historical evidence for the exact record versions then in force. They are not overwritten.

```text
Master Records custody record
historical_hash: f7db74f1a2caafab593f2beacc203901ac5a72d5d0fd44b7e0f9b209170a528f
current_migrated_hash: 216e2c43a572e11109165b5237ef82162b10dc6262b36156e3783dd6879d3103

Master Records acknowledgement
historical_hash: 0a98789be976aad5c18936fe823f9732d683f4e149051e34976eb4743678eb24
current_migrated_hash: b5b26eb34c731c7d195d4a5279cf4239086398bd9032ef9029807834abd11276

GCAT acknowledgement import
historical_hash: 1d65230536d7cc7db60cc544c84d42d9d25fc3c9382b66d703476ac34b88813e
current_migrated_hash: ed597ecde9b7736a610f273774820d662c5bec066bdad5e3980f33bc7ed87996
```

## Resolution rule

Consumers resolve each hash with its qualified repository, path, record version, and transition identity. Historical hashes cannot stand in for the current migrated records. The transition is append-only and preserves the prior completed runtime-intake evidence.

## Authority and collision boundary

This addendum grants no runtime activation, execution authority, repository binding, quorum, policy or publication authority, occurrence claim, or phenomenal-status claim. Pull request 6 remains the runtime-intake custody owner; pull request 7 remains the evidence-semantics integration lane.

## Completion and release

```text
implementation_state: COMPLETE_ON_BRANCH
validation_state: BLOCKED_PENDING_EXACT_HEAD_HOSTED_RUN
release_condition: PR-head workflow success, inspected jobs/logs/artifact, merge, and exact-main success
```
