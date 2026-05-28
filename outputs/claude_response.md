# Claude Code — Governed Collaboration Proposal

Run timestamp: 2026-05-28T21:44:12Z

Governance mode: propose-only

Capability version: 0.1.3-gllm

Task source: task.md

Directive: no broad authority is ever admissible under Transition Table, AE, or GCAT/BCAT enforcement.

---

This task asks for a single machine-actionable candidate packet, not multi-agent orchestration — the "workflow" keyword here comes from the governance text about `.github/workflows/`, not a request to fan out agents. I'll produce the packet directly.

The candidate is documentation-only, writes solely under `docs/`, and touches no workflows, root README, secrets, deploy config, or authority policy — consistent with the PROPOSE-ONLY directive and `review-only` scope.

```json
{
  "schema": "stegverse.candidate_patch.v1",
  "candidate_id": "sv002-m105-sandbox-proof",
  "provider": "openai-or-claude",
  "description": "Minimal documentation-only candidate to prove adapter sandbox routing.",
  "transition_class": "documentation",
  "authority_ref": "SV002-M10.5/scoped-candidate-review-only",
  "policy_ref": "triad/default-deny/no-broad-authority/review-only",
  "files": [
    {
      "path": "docs/SV002_M10_5_SANDBOX_PROOF_OUTPUT.md",
      "operation": "write",
      "content": "# SV002 M10.5 Sandbox Proof Output\n\nThis file is a documentation-only candidate generated to prove that provider output can be sandbox-tested and routed through the M11 gate without manual bundle transport.\n"
    }
  ]
}
```

**Authority boundary note:** This packet is a *proposal only*. It does not approve, bind, or apply the patch — the candidate remains subject to M11 gate review under default-deny. No file was written to the repository by emitting this packet; applying it requires a separately receipted, scoped grant.
