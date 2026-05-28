# SV002-M10.5 Adapter Candidate Sandbox Executor — Existing Workflow Integration

This bundle does **not** add a new workflow.

It modifies the existing workflow:

```text
.github/workflows/core-lite-intake.yml
```

Displayed without the leading period for iOS readability:

```text
github/workflows/core-lite-intake.yml
```

Actual GitHub path keeps the leading dot.

## Purpose

Close the missing automation link:

```text
task.md
→ OpenAI / Anthropic candidate artifacts
→ candidate extraction
→ sandbox test
→ M11 apply gate
→ implement / deny / defer
→ receipts + diagnostics
```

## What changed

The existing `merge-and-commit` job now runs:

```text
python scripts/adapter_candidate_sandbox.py --repo-root . --apply-if-gate-allows
```

after downloading `openai-response` and `claude-response`.

No separate workflow is introduced.

## Safety

Provider output is candidate evidence only.

The sandbox executor ignores free-form prose and only acts on explicit fenced JSON packets with:

```text
schema: stegverse.candidate_patch.v1
```

The candidate is tested in a temporary sandbox first.

Then the M11 apply gate is run.

Only if the binding gate returns `ALLOW` and the sandbox passes does the script write candidate files into the real workspace.

Current expected M11 behavior remains `DEFER` when Triad stubs are unresolved, so normal current behavior is diagnostic evidence, not binding mutation.

## Done condition

A provider-generated candidate can now be processed inside the existing adapter workflow without manual upload of a validation bundle.
