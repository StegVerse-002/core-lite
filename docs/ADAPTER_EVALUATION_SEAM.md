# Adapter Evaluation Seam

This document defines the seam between adapter fixture checks and core-lite evaluation.

## Purpose

Core-lite receives an adapter input and returns a decision plus receipt material.

## Input Fields

- `cell_id`
- `subject_class`
- `interaction_type`
- `provider_class`
- `capability_state_ref`
- `provider_declaration_ref`
- `policy_ref`
- `evidence_refs`
- `context_refs`

## Required Resolution

Core-lite should resolve capability state, provider declaration state, policy, evidence, context, and continuity before returning a decision.

## Decision Values

- `ALLOW`
- `DENY`
- `CONDITIONAL`
- `FAIL_CLOSED`

## Current Stage

Current support checks fixture shape and expected output.

Next stage: add a mock resolver.

Final stage: replace mock resolution with live core-lite state resolution.
