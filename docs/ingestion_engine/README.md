# StegVerse-002 Core-Lite Ingestion Engine

**Generated:** `2026-05-26T01:24:32Z`  
**Target repo:** `StegVerse-002/core-lite`  
**Install mode:** Manual upload / exact-path placement  
**Workflow policy:** No new workflow added  
**Root README policy:** No root `README.md` included in the ingestion bundle  
**Root manifest policy:** No root `bundle_manifest.json` included in the ingestion bundle  

---

## Assumptions

This document describes the ingestion-engine bundle for:

```text
StegVerse-002/core-lite
```

It assumes the existing repository already contains the stable dispatcher workflow:

```text
github/workflows/core-lite-intake.yml
```

> **Path display note:** `github/workflows/core-lite-intake.yml` means the actual GitHub path is `.github/workflows/core-lite-intake.yml`.

It also assumes the existing workflow already supports:

```text
input_type=bundle
input_path=<path>
```

This ingestion-engine bundle does **not** create or modify workflow topology. It plugs into the current Core-Lite intake path.

---

## Done means

This ingestion engine is considered installed and working when:

1. The bundle files are uploaded to their exact target paths.
2. No new workflow file is added.
3. No root `README.md` is added by the ingestion bundle.
4. No root `bundle_manifest.json` is added by the ingestion bundle.
5. `core_lite/multimodal/pipeline.py` routes `input_type=bundle` into the bundle ingestion engine.
6. Incoming bundle manifests are validated before installation.
7. Incoming file paths are checked against policy before installation.
8. Incoming file hashes are verified before installation.
9. Invalid bundles or files are quarantined instead of installed.
10. Receipts, ingestion events, and reports are emitted for review.

---

## Purpose

This bundle adds the functional bundle ingestion engine for `StegVerse-002/core-lite`.

It does **not** add a new workflow.

It does **not** include a root `README.md`.

It does **not** include a root `bundle_manifest.json`.

It plugs into the existing `core-lite-intake.yml` workflow path that already supports:

```text
input_type=bundle
input_path=<path>
```

The existing workflow calls:

```bash
python -m core_lite.multimodal.pipeline \
  --input-type bundle \
  --input-path "<path>" \
  --entity StegVerse-002 \
  --stage "<active_stage>"
```

This bundle replaces:

```text
core_lite/multimodal/pipeline.py
```

so that:

```text
input_type=bundle
```

routes into the new ingestion engine.

---

## Install / upload

Upload every file in this bundle to its exact path.

No root files are included.

Do not add a new workflow.

Do not add a root `README.md`.

Do not add a root `bundle_manifest.json`.

The ingestion engine is intended to extend the existing dispatcher path, not create a parallel execution path.

---

## Bundle intake flow

```text
incoming/<bundle>.zip
or
incoming/<expanded_bundle>/
â core_lite.multimodal.pipeline input_type=bundle
â core_lite.bundles.ingest.BundleIngestor
â manifest validation
â path policy check
â hash verification
â install allowed files
â quarantine rejected files/bundles
â receipt emission
â ingestion event
â report
```

---

## Existing workflow run

After upload, use the existing workflow only:

```text
Actions â core-lite-intake â Run workflow
```

Inputs:

```text
input_type: bundle
input_path: incoming/<your_bundle>.zip
dry_run: false
```

For a dry run:

```text
input_type: bundle
input_path: incoming/<your_bundle>.zip
dry_run: true
```

---

## Manifest contract

Incoming bundles should contain a manifest at one of:

```text
bundle_manifest.json
manifest.json
```

The manifest must include:

```json
{
  "schema": "stegverse.bundle_manifest.v1",
  "bundle_name": "example",
  "files": [
    {
      "path": "docs/example/README.md",
      "sha256": "<sha256 hex>",
      "bytes": 123
    }
  ]
}
```

---

## Manifest fields

| Field | Required | Purpose |
|-------|----------|---------|
| `schema` | Yes | Identifies the manifest contract version |
| `bundle_name` | Yes | Human-readable bundle name |
| `files` | Yes | Declares every installable file |
| `files[].path` | Yes | Target repo-relative install path |
| `files[].sha256` | Yes | Expected SHA-256 hash of the file content |
| `files[].bytes` | Yes | Expected byte size |
| `allow_root_readme` | Optional | Allows root `README.md` only when explicitly true |
| `allow_workflows` | Optional | Allows `github/workflows/*` only when explicitly true |

> **Path display note:** `github/workflows/*` means the actual GitHub path is `.github/workflows/*`.

---

## Guardrails

The ingestion engine denies:

```text
README.md at repo root unless manifest explicitly sets allow_root_readme=true
bundle_manifest.json at repo root
github/workflows/* unless manifest explicitly sets allow_workflows=true
incoming/* as a target path
absolute paths
paths containing ..
empty paths
```

> **Path display note:** `github/workflows/*` means the actual GitHub path is `.github/workflows/*`.

Invalid files are not installed.

Invalid bundles are quarantined under:

```text
quarantine/bundles/
```

Receipts, events, and reports are written under:

```text
receipts/current/
tracking/ingestion_events/
reports/current/
```

---

## Security model

The ingestion engine treats every incoming bundle as untrusted until proven admissible.

A bundle is not admissible merely because:

- it exists in `incoming/`
- it has a manifest
- it came from a known user
- it came from a known AI assistant
- it was generated by a StegVerse-related process
- it passes local extraction

A bundle becomes installable only after:

1. Manifest schema validation passes.
2. Declared files are present.
3. File byte counts match manifest claims.
4. File SHA-256 hashes match manifest claims.
5. Target paths pass policy.
6. Guardrails do not deny installation.
7. The ingestion engine emits evidence for the run.

---

## Dry-run behavior

When `dry_run=true`, the ingestion engine should evaluate the bundle without installing files.

Expected dry-run behavior:

```text
validate manifest
check target paths
verify hashes
identify installable files
identify rejected files
write report
write event/receipt if configured
do not mutate target files
```

Dry run is used to confirm admissibility before consequence-bearing installation.

---

## Failure behavior

Failure must be explicit and reviewable.

Expected failure behavior:

```text
invalid manifest
â deny bundle
â quarantine bundle
â write report
â write ingestion event
â preserve reason

invalid file hash
â reject file or deny bundle according to policy
â do not install invalid file
â write report
â preserve reason

forbidden target path
â reject file
â do not install invalid file
â write report
â preserve reason
```

Unknown conditions should fail to review or fail closed.

---

## Quarantine behavior

Rejected bundles and invalid materials are placed under:

```text
quarantine/bundles/
```

Quarantine exists for inspection and replay.

Quarantine does not mean approval, installation, or deferred execution.

A quarantined bundle should not be reintroduced without review.

---

## Receipt and report outputs

The ingestion engine should emit reviewable evidence under:

```text
receipts/current/
tracking/ingestion_events/
reports/current/
```

Minimum expected evidence:

```text
ingestion decision
bundle name
input path
dry-run flag
manifest path used
accepted files
rejected files
quarantine path when applicable
reason trail
timestamp
entity
stage
receipt hash when available
previous receipt hash when available
```

---

## Relationship to Core-Lite governance

This ingestion engine is not a replacement for Core-Lite governance.

It is an intake component that feeds governed state transitions.

The expected relationship is:

```text
bundle input
â ingestion validation
â path/hash policy enforcement
â report/receipt evidence
â CGE admissibility context
â bounded installation outcome
```

The ingestion engine should never become a general-purpose bypass around CGE, TV/TVC, receipts, or stage STOP conditions.

---

## Root-file policy

This ingestion-engine bundle intentionally avoids root files.

It does not include:

```text
README.md
bundle_manifest.json
```

This prevents accidental replacement of the repo-level README or creation of a root manifest that could be mistaken for an incoming-bundle manifest.

Incoming bundles may contain their own manifest internally, but the ingestion-engine bundle itself should be placed by exact target paths.

---

## Workflow policy

This ingestion-engine bundle does not add a workflow.

It relies on the existing dispatcher:

```text
github/workflows/core-lite-intake.yml
```

> **Path display note:** the actual GitHub path is `.github/workflows/core-lite-intake.yml`.

The stable dispatcher pattern remains:

```text
workflow stays stable
tools and core_lite modules evolve
task catalog declares capabilities
receipts and reports prove execution
```

---

## Verification checklist

After upload, verify:

```text
[ ] No new workflow file was added
[ ] No root README.md was added by the ingestion bundle
[ ] No root bundle_manifest.json was added by the ingestion bundle
[ ] core_lite/multimodal/pipeline.py exists
[ ] core_lite/multimodal/pipeline.py supports input_type=bundle
[ ] core_lite.bundles.ingest.BundleIngestor exists
[ ] incoming/<bundle>.zip can be evaluated
[ ] dry_run=true produces a report without installing files
[ ] dry_run=false installs only allowed files
[ ] forbidden files are rejected
[ ] invalid hashes are rejected
[ ] invalid bundles are quarantined
[ ] receipts/current/ receives evidence when configured
[ ] tracking/ingestion_events/ receives event records
[ ] reports/current/ receives reports
```

---

## Minimal test bundle shape

A minimal incoming bundle may look like:

```text
example_bundle/
  bundle_manifest.json
  docs/example/README.md
```

with manifest:

```json
{
  "schema": "stegverse.bundle_manifest.v1",
  "bundle_name": "example_bundle",
  "files": [
    {
      "path": "docs/example/README.md",
      "sha256": "<sha256 hex>",
      "bytes": 123
    }
  ]
}
```

Expected result:

```text
docs/example/README.md installs only if hash, byte count, and path policy pass.
```

---

## Invariants

1. An incoming bundle is input, not execution.
2. A manifest is a claim, not proof.
3. A file hash is required before installation.
4. A valid path is required before installation.
5. Root `README.md` is denied unless explicitly allowed.
6. Root `bundle_manifest.json` is denied.
7. Workflow files are denied unless explicitly allowed.
8. Invalid files are not installed.
9. Invalid bundles are quarantined.
10. Every ingestion run should leave reviewable evidence.
11. Dry run must not mutate target files.
12. Unknown conditions fail to review or fail closed.
13. The stable dispatcher remains the execution path.
14. Ingestion does not bypass CGE.
15. Receipt evidence is required for consequence-bearing transitions.

---

## Site / proof relationship

The ingestion engine may produce evidence that can later be mirrored publicly.

However:

```text
GitHub repo state
receipts
reports
ingestion events
release artifacts
replay evidence
```

remain the proof authority.

The Site is a mirror, not the source of execution truth.
