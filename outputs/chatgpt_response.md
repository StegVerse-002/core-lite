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
