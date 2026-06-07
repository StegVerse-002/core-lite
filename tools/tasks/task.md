# SV002-M11 Task — Complete the Governed Ingestion Loop

## Governance

You are operating as a governed agent inside StegVerse-002/core-lite.

```
authority: candidate_evidence_only
binding: non_binding
transition_class: candidate
policy: triad/default-deny/no-broad-authority
```

You may not install files directly.
You may not claim broad authority.
You may not self-accredit.
A model response is not a fix. It is candidate evidence only.

## Current State

The batch ingestion controller is installed at:

```
core_lite/batch_ingestion/
```

The Transition Table resolver is installed at:

```
core_lite/transition_table/
```

The governed ingestion workflow is at:

```
.github/workflows/core-lite-intake.yml
```

The existing pipeline module at `core_lite/multimodal/pipeline.py` is
either a stub or incomplete. When a `.zip` bundle arrives in `incoming/`,
the workflow calls `core_lite.multimodal.pipeline` directly instead of
routing through the batch ingestion controller.

The diagnostic bundle `sv002_diagnostics_bundle.zip` is in `incoming/`
and has not been processed through the full governed loop because the
pipeline does not correctly hand off to the batch ingestion controller.

## Problem

`core_lite/multimodal/pipeline.py` does not:

- Route `.zip` bundles through `BatchIngestionController`
- Write proper disposition records to `receipts/current/`
- Write evidence plane contributions to `tracking/evidence_plane/`
- Return a structured result the workflow can act on

## Scope Boundary (read this)

This task wires `pipeline.py` to route bundles through the controller.
It does **not** make `pipeline.py` clean up `incoming/`.

Incoming cleanup is a **separate, dedicated task** with its own script
(`scripts/incoming_cleanup.py`) and its own catalog entries
(`sv002.incoming.cleanup` and `sv002.incoming.cleanup.dry_run`). Do not
add cleanup logic to `pipeline.py`; doing so would duplicate or conflict
with that dedicated task and blur a responsibility the catalog keeps
deliberately separate.

## Required Fix

Produce a candidate patch that replaces or repairs
`core_lite/multimodal/pipeline.py` so that:

1. `.zip` bundle inputs are routed through `BatchIngestionController`
1. All other input types fall through to existing pipeline logic
1. Disposition records are written to `receipts/current/`
1. Evidence plane contributions are written to `tracking/evidence_plane/`
1. A structured result is returned that the workflow can read
1. Exit code `0` = admitted/installed, exit code `1` = quarantined/fail-closed

## Allowed File Changes

The candidate patch may only modify or create:

```
core_lite/multimodal/pipeline.py
core_lite/multimodal/__init__.py
```

## Forbidden File Changes

The candidate patch must not modify any of the following pre-existing,
protected paths:

```
.github/workflows/
core_lite/batch_ingestion/
core_lite/transition_table/
secrets/
README.md
incoming/
```

(The `.github/workflows/` directory is hidden; on some clients its leading
dot may not display. It is the dot-github path and is protected.)

## Verification (separate from this patch)

After this pipeline bridge is installed, the loop can be verified with the
declared task already present in the catalog:

```
sv002.ingestion.loop.ci_smoke
```

This task is test-only. It drives the known-good diagnostic bundle through
`BatchIngestionController` and asserts disposition, receipt, and
evidence-plane contribution. Exit `0` means the loop fired end-to-end; exit
`1` names the failing step in `reports/current/ci_smoke_ingestion_report.json`.
The CI-smoke task and its script are infrastructure that already exists; this
patch must not modify them.

## Response Requirement

Return exactly one fenced JSON block matching:

```json
{
  "schema": "stegverse.candidate_patch.v1",
  "candidate_id": "sv002-m11-pipeline-batch-ingestion-bridge",
  "provider": "YOUR_PROVIDER_NAME",
  "description": "Wire core_lite.multimodal.pipeline to route .zip bundles through BatchIngestionController",
  "transition_class": "candidate",
  "authority_ref": "SV002-M11/pipeline-batch-ingestion-bridge",
  "policy_ref": "triad/default-deny/no-broad-authority",
  "files": [
    {
      "path": "core_lite/multimodal/pipeline.py",
      "operation": "write",
      "content": "..."
    }
  ]
}
```

Replace `YOUR_PROVIDER_NAME` with your actual provider name.
Replace `"..."` with the full file content.

No commentary. No prose. No alternate plans.
One fenced JSON block only.