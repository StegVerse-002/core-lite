# StegGuardian Adapter Intake

This document defines the receiving-side intake boundary for StegGuardian adapter material inside SV-002 core-lite.

## Source Repository

`StegVerse-002/StegGuardian`

## Source Artifacts

- `contracts/core-lite-adapter-contract.json`
- `contracts/boundary-receipt-emission-contract.json`
- `examples/core_lite_adapter_input.json`
- `examples/core_lite_adapter_output.json`
- `docs/CORE_LITE_INTEGRATION_TEST_PLAN.md`

## Core-Lite Responsibility

Core-lite should receive StegGuardian adapter input as a governed standing evaluation request.

Core-lite should not import StegGuardian as a second engine.

## Intake Fields

The expected adapter input includes:

- `cell_id`
- `subject_class`
- `interaction_type`
- `provider_class`
- `capability_state_ref`
- `provider_declaration_ref`
- `policy_ref`
- `evidence_refs`
- `context_refs`

## Evaluation Responsibility

Core-lite should:

1. verify the adapter input shape;
2. resolve capability state;
3. resolve provider declaration state;
4. resolve policy reference;
5. resolve evidence references;
6. resolve execution context references;
7. evaluate standing at execution time;
8. return `ALLOW`, `DENY`, `CONDITIONAL`, or `FAIL_CLOSED`;
9. emit receipt material compatible with StegGuardian receipt requirements.

## Fail-Closed Rule

If any required reference cannot be resolved, reconstructed, or re-bound at execution time, core-lite should return `FAIL_CLOSED`.
