# SV002 Adapter Sandbox Pytest Scope Repair

This bundle does **not** add or modify any workflow.

It replaces:

```text
scripts/adapter_candidate_sandbox.py
```

## Repair

The previous sandbox executor ran full repo `pytest` even for documentation-only candidates.

That caused a documentation-only proof candidate to fail closed before reaching the M11 gate.

This repair changes sandbox testing so:

```text
documentation-only candidate
→ skip unrelated full-repo pytest
→ continue to M11 apply gate
```

Executable candidates still run stronger checks:

```text
changed *.py / tests / tools / scripts / core_lite
→ py_compile where relevant
→ pytest
→ M11 apply gate
```

## Expected next proof result

After installing this replacement and rerunning the existing `core-lite-intake` workflow with:

```text
agent_provider: both
stage_override: SV002-M10.5
dry_run: false
```

the expected one-file result is:

```text
outputs/SV002_AUTOMATION_PROOF_RESULT.md
```

with likely result:

```text
DEFER
```

That means the adapter path worked, the documentation candidate passed sandbox, and the M11 binding gate correctly held the boundary.
