# SV002 M11 Push-Activated Ingestion Bundle

## Purpose

This bundle corrects the M11 automated ingestion package so the manifest declares the optional workflow inputs and the installed `core-lite-intake.yml` is explicitly push-activated.

## Push activation

`core-lite-intake.yml` now treats a push to `main` affecting the governed paths as an automatic LLM collaboration route:

```text
push → agent_provider=both → OpenAI + Claude → adapter candidate sandbox → M11 gate → governed commit evidence
```

## Optional workflow inputs declared in manifest

The bundle manifest now declares the optional dispatch inputs:

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

## Done condition

After installation, a push touching the governed paths should activate the existing collaboration route without requiring manual dispatch inputs.
