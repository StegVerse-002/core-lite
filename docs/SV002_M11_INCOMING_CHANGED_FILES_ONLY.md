# SV002 M11 Incoming Changed-Files-Only Ingestion

## Correction

This bundle fixes the incoming push route so it does not process every bundle already sitting in `incoming/`.

The workflow now processes only files under `incoming/` that changed in the triggering push.

## Why

`incoming/` can contain old bundles, retained bundles, failed bundles, superseded bundles, or already-processed bundles. A push-only workflow must not select `tail -n 1` from the whole directory because that can reprocess stale or unrelated files.

## Correct behavior

```text
push to main changing incoming/foo.zip
→ core-lite-intake runs
→ git diff identifies incoming/foo.zip as changed in this push
→ only incoming/foo.zip is processed
```

If multiple incoming files change in the same push, all changed incoming files are processed in sorted order.

Existing files in `incoming/` that were not changed by the push are ignored.

## Route

```text
declared-input-route(push:incoming-changed-only)
```
