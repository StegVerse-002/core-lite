# Recovery Bundle Transition Requirement

Stage: `SV002-M11`

Recovery bundles are not install bundles. They are evidence-bearing recovery objects routed back through governed ingestion so the transition table and CGE boundary can determine the next admissible disposition.

## Required manifest shape

Every repo recovery bundle MUST include a root-level `bundle_manifest.json` with a `transition` block.

Required transition fields:

```json
{
  "transition_class": "evidence",
  "transition_cell": "B7",
  "authority_class": "evidence_only",
  "state_effect": "evidence_state",
  "binding_level": "non_binding",
  "target_scope": "repo_recovery_payload",
  "execution_scope": "none",
  "admissibility_gate": "transition_table_ingest_gate",
  "disposition_policy": "store_evidence_only"
}
```

The `task_ref` MUST identify the recovery id. The `task_hash` MUST bind to the original recovered source hash.

## Why this is required

The transition table ingestion gate fails closed when a manifest lacks `transition`. The first one-bundle proof correctly quarantined the recovery bundle because the old wrapper created a manifest without that block.

The repo wrapper has now been updated so future recovery bundles declare a non-binding evidence transition. This keeps recovery admissible without granting install authority.

## Guardrails

Recovery wrapping:

- does not install destination files;
- does not remove original source files;
- does not claim execution authority;
- does not perform bulk ingestion;
- only creates manifest-bearing recovery evidence.

Final cleanup/removal remains a later `SV002-M12` action that requires successful disposition receipts.
