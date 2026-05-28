# SV002 M11 Incoming-Only Push Ingestion

## Correction

Push activation is intentionally narrowed to the incoming directory only.

```text
push to main + incoming/** changed
→ core-lite-intake runs
→ declared-input-route(push:incoming)
→ latest incoming file is discovered
→ bundle/document/structured input is processed
```

## What does not happen

A push to normal source paths no longer activates the workflow.

```text
scripts/**
schemas/**
docs/**
tests/**
task.md
.github/workflows/**
```

Those paths are no longer push triggers.

## Manual dispatch remains available

`workflow_dispatch` still supports the optional inputs:

```text
task_id
skip_tasks
stage_override
repair_target
input_type
input_path
kv_packet
dry_run
agent_provider
```

## Push default

On incoming push:

```text
input_path = latest file under incoming/
input_type = bundle for *.zip, structured_data for json/yaml, document otherwise
stage = SV002-M11
dry_run = false
agent_provider = none
```
