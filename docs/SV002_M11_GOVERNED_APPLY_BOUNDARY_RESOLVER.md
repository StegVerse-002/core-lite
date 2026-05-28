# SV002-M11 Governed Apply Boundary Resolver

## Status

This bundle promotes M11 from a pure defer gate into a scoped binding resolver.

M10.5 proved:

```text
provider candidate → sandbox → M11 gate → DEFER
```

M11 now needs the next boundary:

```text
safe scoped candidate → sandbox → M11 ALLOW → apply
unsafe/unclear candidate → DENY or DEFER
```

## What this resolver allows

A binding transition may return `ALLOW` only when all hard checks pass and the Triad resolves:

```text
GCAT/BCAT: authority is scoped and policy is safe
ECAT/ICAT: requester/entity are coherent
% Existence: resulting state is recoverable/non-destructive
```

## Safe auto-allow class

This first resolver intentionally allows only a narrow class:

```text
transition_class: documentation
target path: docs/* or outputs/*
operation: not delete
authority_ref: scoped/candidate/documentation/review/m10.5/m11 marker
policy_ref: triad/default-deny/no-broad-authority marker
requester: adapter-candidate-sandbox/* or other known SV002 requester
```

## Still denied

```text
README.md
bundle_manifest.json
.github/*
.git/*
dist/*
receipts/*
reports/*
broad authority such as root/admin/all/*
path escape attempts
invalid schema
```

## Still deferred

Tooling, policy, governance, schema, and repair candidates remain deferred unless future resolver logic explicitly proves their Triad state.

## Expected next run

The previous M10.5 proof candidate was documentation-only and safe. After this bundle is installed, the existing adapter run should move from:

```text
CANDIDATE_SANDBOXED_GATE_DEFERRED
```

to:

```text
CANDIDATE_APPLIED_AFTER_SANDBOX_AND_GATE
```

for the safe documentation candidate.
