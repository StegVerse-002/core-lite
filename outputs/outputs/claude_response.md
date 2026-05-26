# Claude Code — Governed Collaboration Proposal

Run timestamp: 2026-05-26T18:11:21Z

Governance mode: propose-only

Capability version: 0.1.2-gllm

Task source: task.md

Directive: no broad authority is ever admissible under Transition Table, AE, or GCAT/BCAT enforcement.

---

## Current State Assessment

Substrate components observed in the repository at run time:

- `.github/workflows/core-lite-intake.yml` defines four jobs: `claude-agent`, `openai-agent`, `merge-and-commit`, `dispatch`. The first three constitute the governed LLM-LLM substrate. (Read-only here.)
- `governance/directives/no_broad_authority.directive.json` — schema `stegverse.governance_directive.v1`, version `0.1.2-gllm`, status `active`. Applies to human, ai, repo, org, workflow, agent, framework, ecosystem_component.
- `agent_policy/allowed_paths.json` — `outputs/**`, `reports/current/**`, `receipts/current/**`, `agent_history/**`, `candidates/**`.
- `agent_policy/forbidden_paths.json` — includes `governance/directives/**`, `schemas/**`, `core_lite/**`, `tools/**`, `tracking/**`, `config/**`, `README.md`, `task.md`, `CLAUDE.md`, `.env`, `secrets/**`, etc.
- `agent_history/version_state.json` — `current_version: 0.1.2-gllm`. Only one `versions[]` entry, with `decision: NO_PROVIDER_OUTPUT`, basis `Neither provider output was present.`
- `agent_history/llm_changelog.jsonl` — 4 entries. Two `coordination_synthesis` entries with empty `output_hashes.claude` and `output_hashes.openai`; two `coordination_run` entries with `decision: RECORDED`.
- `reports/current/agent_coordination_report.json` — `decision: NO_PROVIDER_OUTPUT`. Both providers `exists: false`, `bytes: 0`, every required section flagged `false`.
- `reports/current/agent_comparison_report.json` — `decision: REVIEW_REQUIRED`, `missing_providers: ["openai", "claude"]`.
- `reports/current/agent_boundary_report.json` — `decision: ALLOW_CANDIDATE_EVIDENCE`, `violations: []`, 9 changed paths, all within allowed patterns.
- `receipts/current/agent_*_receipt.jsonl` — three append-only chains present.
- `outputs/claude_response.md` (before this run) — preamble only, 282 bytes, no structured sections.
- `outputs/thread.md` — synthesized; explicitly shows both providers absent.

Observable state of last two coordination cycles (2026-05-26T18:07:04Z and 2026-05-26T18:08:02Z):

- Provider outputs: absent for both Claude and OpenAI.
- Coordination decision: `NO_PROVIDER_OUTPUT`.
- Version-state effect: `current_version: 0.1.2-gllm` recorded as the only operational version, even though no provider content was produced.
- Boundary effect: `ALLOW_CANDIDATE_EVIDENCE` — every write confined to `outputs/**`, `reports/current/**`, `receipts/current/**`, `agent_history/**`.

What is operational:

- The propose-only two-provider pattern (Job A + Job B) is wired.
- Deterministic synthesis (`scripts/merge_outputs.py`) executes regardless of provider presence.
- Path-boundary enforcement (`tools/agent_governance/enforce_agent_boundary.py`) executes and produces a receipt.
- Append-only changelog and version-state writers (`tools/agent_governance/record_llm_change.py`) execute and produce receipts.
- Authority flags (`broad_authority: false`, `canonical_authority: false`, `mode: propose_only`) are present in every report and receipt examined.

What is not yet observable as operational:

- A coordination run in which both providers produced structured output conforming to the required sections.
- A version-state entry whose decision is anything other than `NO_PROVIDER_OUTPUT`.
- A human-mediator primitive: there is no schema-defined field, file, or receipt type for a human counter-claim, override, or annotation against a coordination run.
- Cross-repo collaboration: only SV001 repair (`tools/repair/sv001_repair.py`) operates against a remote repo, and that is a one-direction repair flow, not a governed LLM-LLM packet exchange.

## Directive Alignment

- `no_broad_authority` directive `status: active` is honored by every artifact examined.
- All examined receipts include `broad_authority: false` and `canonical_authority: false`.
- All authority blocks show `mode: propose_only` (coordination_report) or `mode: candidate_evidence_only` (comparison_report).
- `enforce_agent_boundary.py` enforces `agent_policy/allowed_paths.json` and `agent_policy/forbidden_paths.json` and records a receipt. No violations recorded in the current chain.
- Rige founder/user enrollment, Beta_Orionis counterpart enablement, and AI-waiting-list implementation are not present, not staged, and not referenced as in-progress in any state file.

This proposal does not weaken any of those alignments.

## Ecosystem Stage Assessment

Stage 1 components vs. observed evidence:

- Cross-repo / cross-org communication substrate: PARTIAL. Workflow infrastructure exists; no cross-repo collaboration receipt has been emitted under `0.1.2-gllm`. SV001 repair is one-direction and predates the governed-collaboration version line.
- Governed LLM-LLM collaboration operational: PIPELINE-COMPLETE, CONTENT-EMPTY. The pipeline runs end-to-end. Both observed runs ended with `NO_PROVIDER_OUTPUT`. The substrate has not yet demonstrated a non-empty collaboration.
- Machine-readable version history: OPERATIONAL. `llm_changelog.jsonl` + `version_state.json` are produced, schema-stamped, and append-only.
- Human mediator support: NOT YET. No defined primitive for a human to enter the chain with a counter-claim, override, or annotation that is receipted alongside provider outputs.
- Repo-safe proposal outputs: OPERATIONAL. `outputs/**`-confined writes; boundary enforcer reports `ALLOW_CANDIDATE_EVIDENCE`; forbidden patterns include the directive directory itself.

Stage 1 is NOT yet complete. Specifically, two sub-conditions remain unmet:

1. No coordination run with both providers producing required-section-conformant output has been recorded.
2. No human-mediator primitive exists.

Stage 2 (AI presence in each framework, cooperation enforced across all ecosystem facets) is therefore not yet admissible from the available evidence. Stage 3 (Rige founder/user enrollment, Beta_Orionis counterpart enablement, AI-waiting-list) is explicitly out of scope for this run and is not addressed below.

## Next Collaboration Primitive

The next smallest admissible improvement is to make the substrate fail-closed against empty provider runs and to distinguish "pipeline ran" from "providers contributed" in the machine-readable history.

Rationale:

- The current behavior records `decision: RECORDED` in `llm_changelog.jsonl` for runs in which both providers were absent. This conflates pipeline execution with provider participation.
- Without this distinction, `version_state.json::current_version` advances by side effect of pipeline execution alone, masking the fact that no governed LLM-LLM collaboration has actually occurred.
- This is the smallest improvement that materially changes whether Stage 1 can be demonstrated as "operating correctly," because operating correctly requires that the empty-state be visibly empty in the chain rather than silently absorbed.

Why this is admissible under the directive:

- Scoped: touches only coordination synthesis scripts and machine-readable history.
- Staged: belongs to Stage 1, does not anticipate Stage 2 or 3.
- Explicit: a new enum value (`RECORDED_EMPTY`) and a new field (`last_operational_version`) — both named, both receipted.
- Receipted: changes flow through the existing receipt chain.
- Bounded by transition class: confined to the governed-collaboration substrate.
- Checked at execution/commit boundary: `enforce_agent_boundary.py` already checks the change set.
- Recoverable / revocable: a single revert undoes it; the chain remains intact.
- Denied by default unless specifically granted: introduces a default-deny on empty runs (current default-allow becomes default-mark-empty).

What this primitive is not:

- Not a new authority grant to any entity.
- Not an enrollment of any human or AI counterpart.
- Not a cross-repo write.
- Not a schema relaxation; if anything it tightens the changelog enum.
- Not a Stage 2 step. It does not establish AI presence in any framework.

## Proposed Implementation

The following are proposals as text. This run does not apply them. They sit in `outputs/claude_response.md` as candidate evidence only and require a separately authorized, scoped, receipted change to land.

### Proposed file edits (text-only)

1) `tools/agent_governance/record_llm_change.py` — accept `--coordination-report PATH` and choose decision per the report.

Pseudo-diff:

```python
# new flag
parser.add_argument("--coordination-report", type=Path, default=None)

coord_decision = "UNKNOWN"
if args.coordination_report and args.coordination_report.exists():
    coord_decision = json.loads(args.coordination_report.read_text(encoding="utf-8")).get(
        "decision", "UNKNOWN"
    )

entry_decision = (
    "RECORDED_EMPTY"
    if coord_decision == "NO_PROVIDER_OUTPUT"
    else "RECORDED"
)
entry["decision"] = entry_decision

# version_state update
if entry_decision == "RECORDED":
    state["last_operational_version"] = args.version
# else: leave state["last_operational_version"] unchanged
```

2) `tools/agent_governance/agent_compare.py` — add `--fail-on-empty` (off by default), exit 2 when both providers are absent, else preserve current behavior.

Pseudo-diff:

```python
parser.add_argument("--fail-on-empty", action="store_true", default=False)

both_missing = (not claude_info["exists"]) and (not openai_info["exists"])
if both_missing and args.fail_on_empty:
    sys.exit(2)
```

3) `schemas/llm_changelog_entry.v1.schema.json` — extend the `decision` enum.

Pseudo-diff:

```json
{
  "properties": {
    "decision": {
      "type": "string",
      "enum": ["RECORDED", "RECORDED_EMPTY", "REVIEW_REQUIRED", "NO_PROVIDER_OUTPUT"]
    }
  }
}
```

4) `agent_history/version_state.json` — add `last_operational_version` field (null until a non-empty coordination run occurs).

Initial shape (when first written by the updated script):

```json
{
  "schema": "stegverse.llm_version_state.v1",
  "capability": "governed_collaboration",
  "current_version": "0.1.2-gllm",
  "last_operational_version": null,
  "versions": [ ... ]
}
```

5) `.github/workflows/core-lite-intake.yml` — pass new flags through.

Pseudo-diff:

```yaml
- name: Compare agent outputs
  run: |
    python tools/agent_governance/agent_compare.py --fail-on-high --fail-on-empty || true
    # exit-2 from --fail-on-empty is observed but not fatal to the commit step;
    # the receipt chain still writes; the workflow result is informational

- name: Record LLM-LLM coordination change
  run: |
    python tools/agent_governance/record_llm_change.py \
      --provider coordinator \
      --conversation current-workflow-run \
      --version "${GOVERNED_LLM_LLM_VERSION}" \
      --change-type coordination_run \
      --coordination-report reports/current/agent_coordination_report.json \
      --summary "Recorded governed LLM-LLM collaboration outputs, comparison evidence, no-broad-authority directive, and boundary enforcement." \
      --files outputs/thread.md reports/current/agent_coordination_report.json reports/current/agent_comparison_report.json reports/current/agent_boundary_report.json receipts/current/agent_coordination_receipt.jsonl receipts/current/agent_comparison_receipt.jsonl receipts/current/agent_boundary_receipt.jsonl
```

### Files NOT modified by this run

This Claude propose-only run writes only `outputs/claude_response.md`. All other files listed in the task's expected-output block are produced by the workflow's `merge-and-commit` job:

- `outputs/thread.md` — written by `scripts/merge_outputs.py`.
- `outputs/chatgpt_response.md` — written by `scripts/openai_task.py` from Job B (not this job).
- `reports/current/agent_coordination_report.json` — written by `scripts/merge_outputs.py`.
- `reports/current/agent_comparison_report.json` — written by `tools/agent_governance/agent_compare.py`.
- `reports/current/agent_boundary_report.json` — written by `tools/agent_governance/enforce_agent_boundary.py`.
- `receipts/current/agent_coordination_receipt.jsonl` — appended by `scripts/merge_outputs.py`.
- `receipts/current/agent_comparison_receipt.jsonl` — appended by `tools/agent_governance/agent_compare.py`.
- `receipts/current/agent_boundary_receipt.jsonl` — appended by `tools/agent_governance/enforce_agent_boundary.py`.
- `agent_history/llm_changelog.jsonl` — appended by `tools/agent_governance/record_llm_change.py`.
- `agent_history/version_state.json` — overwritten by `tools/agent_governance/record_llm_change.py`.

Per the run's allowed/forbidden path policy, Claude has no write authority over `tools/**`, `schemas/**`, `governance/directives/**`, `.github/workflows/**`, or `agent_history/**`. The proposals above are text only.

## Authority Boundaries

- Mode: `propose_only`.
- `broad_authority`: false.
- `canonical_authority`: false.
- `may_bind_repo_state`: false.
- This proposal does not enroll any human or AI as founder, user, counterpart, or framework participant.
- This proposal does not grant any entity (human, AI, repo, org, workflow, agent, framework, ecosystem component) any authority beyond what it already had.
- This proposal does not enable Beta_Orionis.
- This proposal does not implement an AI waiting list.
- This proposal does not declare any unilateral authority for the Claude agent, the OpenAI agent, the coordinator, or any other entity.
- This proposal does not bypass any stage of the build sequence. It is bounded to Stage 1 substrate hardening.
- The proposed script and schema changes themselves require a separately authorized, scoped run to apply. They are not applied by this run.

## Receipts and Version History

This run, when committed by the workflow's `merge-and-commit` job, expects to produce:

- `outputs/claude_response.md` — this file, written by Claude.
- `outputs/chatgpt_response.md` — written by Job B (OpenAI).
- `outputs/thread.md` — written by deterministic synthesis.
- `reports/current/agent_coordination_report.json` — written by synthesis. Expected `decision`: `REVIEW_REQUIRED` or `NO_PROVIDER_OUTPUT` depending on whether Job B produced output.
- `reports/current/agent_comparison_report.json` — written by `agent_compare.py`. Expected `decision`: `REVIEW_REQUIRED` if either provider is incomplete.
- `reports/current/agent_boundary_report.json` — written by `enforce_agent_boundary.py`. Expected `decision`: `ALLOW_CANDIDATE_EVIDENCE` so long as writes remain within the allowed-paths set.
- `receipts/current/agent_coordination_receipt.jsonl` — appended.
- `receipts/current/agent_comparison_receipt.jsonl` — appended.
- `receipts/current/agent_boundary_receipt.jsonl` — appended.
- `agent_history/llm_changelog.jsonl` — appended with one new `coordination_run` entry.
- `agent_history/version_state.json` — overwritten with `current_version: 0.1.2-gllm` and one additional `versions[]` entry.

If the proposal described in the previous section were later applied under a separately authorized run, the version-history effect would be:

- `agent_history/llm_changelog.jsonl` entries for `NO_PROVIDER_OUTPUT` coordination runs would carry `decision: RECORDED_EMPTY` rather than `decision: RECORDED`.
- `agent_history/version_state.json` would expose a `last_operational_version` field. It would remain `null` until a coordination run records non-empty provider output.
- Prior entries (the four already in `llm_changelog.jsonl`) are append-only and would not be rewritten. The chain remains continuous.

## Risks & Dependencies

Risks:

- Schema change to `schemas/llm_changelog_entry.v1.schema.json` falls under `forbidden_paths.json` (`schemas/**`). It cannot be applied by the LLM-LLM substrate under current policy and would require a separate, schema-track approval path. If only the script changes are applied without the schema change, validators that strict-enum the `decision` field will fail-closed. This is the intended behavior but should be staged so the schema change lands first or alongside.
- Script changes to `tools/agent_governance/**` also fall under `forbidden_paths.json` (`tools/**`). They cannot be applied by the LLM-LLM substrate. A separate, scoped run with explicit authority to modify `tools/**` is required.
- A new `last_operational_version` field defaulting to `null` may break downstream consumers that assume non-null version strings. Mitigation: treat `null` as "no operational baseline yet"; document the field in `schemas/llm_changelog_entry.v1.schema.json` companion schema or a new `stegverse.llm_version_state.v1` extension.
- `--fail-on-empty` returning exit code 2 could prevent subsequent steps from running in the `merge-and-commit` job. Mitigation: gate behind the flag; in the workflow, append `|| true` only to that step, so the receipt chain continues to write but the workflow result clearly indicates the empty state.
- Two prior `llm_changelog.jsonl` entries already record empty runs as `decision: RECORDED`. These are immutable. The chain will reflect a transition from `RECORDED` to `RECORDED_EMPTY` semantics at the point the change lands. Readers must tolerate this.

Dependencies:

- `tools/agent_governance/record_llm_change.py`, `tools/agent_governance/agent_compare.py`, `tools/agent_governance/enforce_agent_boundary.py` continue to exist with their current entry-point shapes. (Not read in this run — inferred from `.github/workflows/core-lite-intake.yml`.)
- `scripts/merge_outputs.py` continues to produce `reports/current/agent_coordination_report.json` with a `decision` field that maps to `RECORDED` / `RECORDED_EMPTY` cleanly.
- A separately authorized run must apply changes to `tools/**` and `schemas/**`. The LLM-LLM substrate cannot self-apply these under its current `agent_policy/forbidden_paths.json`.
- The OpenAI counterpart agent (`scripts/openai_task.py`) must, in a future run, also produce a section-conformant output so the substrate can demonstrate a non-empty coordination cycle and exercise the `RECORDED` (not `RECORDED_EMPTY`) path.

External dependencies untouched by this proposal:

- No third-party services contacted.
- No new secrets required.
- No cross-repo writes required.
- No changes to `core_lite/**`, `config/**`, `tracking/**`, `dist/**`, `machine/**`, `incoming/**`, `quarantine/**`, `README.md`, `task.md`, `CLAUDE.md`.

## Confidence

- Current-state assessment: HIGH. Read directly from `agent_history/`, `reports/current/`, `receipts/current/`, `outputs/`, `.github/workflows/`, `governance/directives/`, `agent_policy/` in this run.
- Directive alignment: HIGH. Every examined artifact carries `broad_authority: false` and `canonical_authority: false`.
- Stage-1-completion gap: MEDIUM-HIGH. The empty-run interpretation depends on whether "operating correctly" allows for runs with no provider content; this proposal interprets it as "no, an empty run is not an operational run."
- Proposed implementation specifics: MEDIUM. Script-level pseudo-diffs are inferred from workflow invocations; `tools/agent_governance/*.py` were not read in this run (they fall under `forbidden_paths.json`). The intended behavior is clear; the exact argparse and json-update sites are not directly observed.
- Authority-boundary safety: HIGH. The proposal does not move the boundary outward; it tightens the default behavior on empty runs.
- Stage-2-readiness: LOW. Multiple Stage 1 sub-conditions remain unmet, including a human-mediator primitive that is out of scope for this minimum-step proposal but is the natural next candidate primitive after this one lands.

This proposal is candidate evidence only. It does not bind repository state, does not approve any change, and does not grant any authority. It awaits human-mediator review before any of the proposed file modifications may be made under a separate, scoped, receipted change.
