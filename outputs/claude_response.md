# Claude Code — Governed Collaboration Proposal

Run timestamp: 2026-05-26T21:07:18Z

Governance mode: propose-only

Capability version: 0.1.3-gllm

Task source: task.md

Directive: no broad authority is ever admissible under Transition Table, AE, or GCAT/BCAT enforcement.

---

The write/edit to `outputs/claude_response.md` requires your permission. The proposal is ready to commit to that file — please approve the write, or let me know if you'd prefer the response delivered another way (different path under `outputs/`, inline in chat, etc.).

Summary of what the proposal contains:

- **Current state**: v0.1.3-gllm packaging side is operational (scripts, schema, methodology docs, workflow wiring at `.github/workflows/core-lite-intake.yml:232-244`, two prior `PACKAGED_AS_CANDIDATE_EVIDENCE` receipts present). Manifest hash projection bug from v0.1.2 is fixed and shared between package/ingest. Required-contents list matches task.md's Done Condition exactly.
- **Concrete gap**: workflow never invokes `scripts/ingest_transition_bundle.py`, so `receipts/current/transition_bundle_ingest_receipt.jsonl` (listed in task.md Expected Runtime Outputs) is not produced.
- **Proposed change**: insert one new workflow step ("Ingest proposed-transition bundle (local intake)") between the existing package step and the coordination-commit step, with `if: hashFiles(...)` guard and `continue-on-error: true` so all five intake decisions are receipted. No script, schema, or directive changes proposed.
- **Authority**: scoped, staged, explicit, receipted, intake-only, candidate-evidence-only, no canonical/broad authority anywhere. No founder/user enrollment, no Beta_Orionis, no cross-repo dispatch.
