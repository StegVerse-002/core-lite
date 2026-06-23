# StegGuardian Store Migration Plan

This plan moves StegGuardian adapter validation from seed state records into general core-lite stores.

## Current Source

```text
state/stegguardian/seed_state_records.json
```

## Mapping Contract

```text
contracts/stegguardian-store-mapping.json
```

## Migration Steps

1. Keep adapter input shape unchanged.
2. Route each reference type through the store mapping contract.
3. Resolve capability state from the capability state store.
4. Resolve provider declaration from the provider declaration store.
5. Resolve policy from the policy store.
6. Resolve evidence from the evidence store.
7. Resolve context from the context store.
8. Preserve the same decision values.
9. Emit receipt material through the existing adapter output shape.

## Done Criteria

The seed state file can be retired from the active validation path when the same adapter inputs produce the same expected decisions through general core-lite stores.

## Boundary

Do not hard-code StegGuardian-specific policy logic into core-lite stores.

Stores resolve standing inputs. The evaluator composes the decision at execution time.
