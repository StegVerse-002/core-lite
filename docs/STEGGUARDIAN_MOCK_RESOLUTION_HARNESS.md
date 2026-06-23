# StegGuardian Mock Resolution Harness

This document defines the temporary mock-resolution harness for StegGuardian adapter validation.

## Purpose

The harness lets core-lite evaluate adapter inputs against a local resolution table before live state lookup is connected.

## Resolution Table

```text
examples/stegguardian_mock_resolution_table.json
```

## Resolution States

- `resolved`
- `unresolved`

## Harness Rule

For adapter fixture validation:

- if all required references resolve, return the expected non-fail-closed decision for the fixture;
- if any required reference is unresolved, return `FAIL_CLOSED`.

## Non-Goal

This is not production standing evaluation.

It is a bridge from fixture-output comparison toward live core-lite state lookup.

## Replacement Target

Replace the mock resolution table with core-lite state, policy, evidence, context, and continuity records.
