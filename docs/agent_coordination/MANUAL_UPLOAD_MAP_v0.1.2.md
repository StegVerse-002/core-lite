# Manual Upload Map — Governed Collaboration Substrate v0.1.2-gllm

Actual GitHub placement:

```text
.github/workflows/core-lite-intake.yml
CLAUDE.md
task.md
scripts/openai_task.py
scripts/merge_outputs.py
tools/agent_governance/__init__.py
tools/agent_governance/agent_compare.py
tools/agent_governance/enforce_agent_boundary.py
tools/agent_governance/record_llm_change.py
agent_policy/allowed_paths.json
agent_policy/forbidden_paths.json
agent_history/llm_changelog.jsonl
agent_history/version_state.json
governance/directives/no_broad_authority.directive.json
schemas/llm_changelog_entry.v1.schema.json
schemas/governance_directive.v1.schema.json
docs/agent_coordination/GOVERNED_COLLABORATION_SUBSTRATE_v0.1.2.md
docs/agent_coordination/MANUAL_UPLOAD_MAP_v0.1.2.md
tracking/manifests/governed_collaboration_substrate_v0.1.2_manifest.json
iosnoperiod.md
```

iPhone display note:

The bundle contains the canonical workflow at:

```text
.github/workflows/core-lite-intake.yml
```

It also contains an iOS-safe mirror at:

```text
iosnoperiod/github/workflows/core-lite-intake-yml
```

The mirror is only for iOS-safe placement/reference. The actual GitHub workflow must live under `.github/workflows/core-lite-intake.yml`.

## Required Secrets

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
```

`OPENAI_API_KEY` is required for OpenAI output.
`ANTHROPIC_API_KEY` is optional for initial testing; if absent, Claude writes a governed skipped output.

## Optional Repo Variable

```text
OPENAI_MODEL=gpt-4o
```

## First Run

GitHub Actions → `core-lite-intake` → Run workflow.

Recommended input:

```text
agent_provider: both
dry_run: false
task_id: blank
input_type: blank
input_path: blank
```
