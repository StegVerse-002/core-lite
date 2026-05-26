# Governed Collaboration Substrate

Version: `0.1.2-gllm`

## Purpose

This package regenerates the collaboration files for `StegVerse-002/core-lite` around the corrected directive:

```text
There is never a valid StegVerse state in which any entity receives broad authority.
```

## Current Build Target

```text
governed LLM-LLM collaboration
machine-readable version history
human mediator support
repo-safe proposal outputs
future cross-repo/cross-org communication preparation
```

## Not Current Targets

```text
Rigel Randolph founder/user enrollment
Beta_Orionis counterpart enablement
```

Those are future transitions only after the ecosystem operates under scoped, staged, receipted governance.

## Installed Capability

```text
task.md
→ Claude proposal
→ OpenAI proposal
→ deterministic merge
→ comparison report
→ boundary enforcement
→ machine-readable changelog
→ receipts
→ outputs/history commit
→ normal Core-Lite dispatcher
```

## Authority Rule

Provider outputs are candidate evidence only.

```text
OpenAI may propose.
Claude may propose.
Rige mediates.
merge_outputs.py synthesizes.
agent_compare.py classifies evidence.
enforce_agent_boundary.py checks write boundaries.
record_llm_change.py records versioned LLM/human/coordinator changes.
Core-Lite governance decides what binds.
```

## Machine-Readable Directive

```text
governance/directives/no_broad_authority.directive.json
```

## Done Means

1. Workflow loads successfully.
2. `task.md` exists.
3. OpenAI job writes `outputs/chatgpt_response.md`.
4. Claude job writes `outputs/claude_response.md`, or a governed skipped file if Anthropic is not configured.
5. Merge job writes `outputs/thread.md`.
6. Comparison job writes report and receipt.
7. Boundary job fails closed if changed paths escape allowed collaboration outputs.
8. Changelog entries are appended to `agent_history/llm_changelog.jsonl`.
9. `agent_history/version_state.json` records current version and directive.
10. Only `outputs/`, `reports/current/`, `receipts/current/`, and `agent_history/` are committed by the coordination job.
