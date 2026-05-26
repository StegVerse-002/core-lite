# Task: v0.1.3-gllm — Transition Bundle Packaging and Ingestion Handoff

## Version

`0.1.3-gllm`

## Absolute Directive

There is never a valid StegVerse state in which any entity receives broad authority.

No exceptions. No temporary grants. No bootstrap shortcuts.

All authority must remain scoped, staged, explicit, receipted, bounded by transition class, checked at the commit/execution boundary, recoverable, containable, and denied by default unless specifically granted.

## Ecosystem Build Sequence

### Stage 1 — Current Target

```text
Cross-repo and cross-org communication substrate
→ Governed LLM-LLM collaboration operational
→ Machine-readable version history
→ Human mediator support
→ Repo-safe proposal outputs
→ Proposed-transition bundle packaging             ← THIS TASK
→ Ingestion gate operational
→ Cross-repo routing through ingestion only
```

### Stage 2 — Next

```text
AI presence in each framework / repo / org as scoped candidate-evidence producers
```

### Stage 3 — Future

```text
Rigel founder/user enrollment
Beta_Orionis enabled as counterpart
```

Stage 3 is not part of this task.

## What This Task Is

The collaboration chain does not end at `outputs/thread.md`.

Every successful governed LLM collaboration run produces proposed-transition evidence. That evidence must be packaged into a self-contained, self-verifying transition bundle before it can move, be reviewed, be routed, or be considered by another repo/org.

The bundle is the universal transport object for proposed state transitions inside StegVerse.

Ingestion is the only admissible mechanism for admitting, routing, transferring, or binding proposed state changes across repo/org boundaries.

There is no direct write across org boundaries.

There is no privileged channel.

The bundle format plus ingestion receipt chain is the protocol.

## Current State

The v0.1.2-gllm collaboration gate proved:

```text
outputs/thread.md                         produced
outputs/claude_response.md                produced
outputs/chatgpt_response.md               produced
reports/current/*                         produced
receipts/current/*                        produced
agent_history/llm_changelog.jsonl         operational
agent_history/version_state.json          operational
```

The next missing link is:

```text
governed collaboration outputs
→ proposed-transition bundle
→ bundle hash
→ evidence-chain link
→ ingestion intake
→ candidate admission / repair / denial / quarantine
→ next receipt-bearing chain link
```

## Required Files

```text
scripts/package_transition_bundle.py
scripts/ingest_transition_bundle.py
schemas/transition_bundle.v1.schema.json
docs/methodology/LLM_OUTPUT_TO_INGESTION_CHAIN.md
docs/methodology/TASK_AS_INTERFACE_METHODOLOGY.md
docs/methodology/FOUNDER_FAMILY_PRESERVATION_BOUNDARY.md
```

## Required Workflow Wiring

After the `Record LLM-LLM coordination change` step in `github/workflows/core-lite-intake.yml` — actual repo path has a leading dot: `.github/workflows/core-lite-intake.yml` — run:

```bash
python scripts/package_transition_bundle.py
```

Then include `dist/bundles/` in the coordination commit and coordination artifact.

## Constraints

- PROPOSE-ONLY for LLM provider runs.
- No direct cross-repo/org mutation.
- No founder/user enrollment.
- No Beta_Orionis enablement.
- No broad authority.
- No canonical authority from ingestion intake alone.
- Ingestion intake may only admit as candidate evidence, route to repair, deny, quarantine, or fail closed.

## Expected Runtime Outputs

```text
dist/bundles/proposed_transition_bundle.json
dist/bundles/proposed_transition_bundle.zip
dist/bundles/proposed_transition_bundle.sha256
receipts/current/proposed_transition_bundle_receipt.jsonl
receipts/current/transition_bundle_ingest_receipt.jsonl
```

## Done Condition

This task is complete when the repo can produce a proposed-transition bundle whose manifest hash verifies under ingestion and whose contents include:

```text
outputs/thread.md
outputs/claude_response.md
outputs/chatgpt_response.md
reports/current/agent_coordination_report.json
reports/current/agent_comparison_report.json
reports/current/agent_boundary_report.json
receipts/current/agent_coordination_receipt.jsonl
receipts/current/agent_comparison_receipt.jsonl
receipts/current/agent_boundary_receipt.jsonl
agent_history/llm_changelog.jsonl
agent_history/version_state.json
```

The bundle must preserve path structure and must not grant canonical authority.
