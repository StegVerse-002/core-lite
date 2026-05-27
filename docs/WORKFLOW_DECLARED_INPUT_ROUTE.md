# StegVerse-002 Workflow Declared Input Route Repair

## Purpose

This repair restores the missing workflow branch for declared non-LLM inputs.

When a workflow dispatch declares:

```text
agent_provider: none
input_type: bundle
input_path: incoming/<bundle>.zip
```

the workflow must route the declared input to the Core-Lite multimodal pipeline instead of running the governed LLM collaboration path.

## Correct route

```text
IF input_type is not blank AND input_path is not blank:
    run core_lite.multimodal.pipeline
    if input_type == bundle:
        route into BundleIngestor
    commit installed bundle files, reports, receipts, and tracking evidence

ELSE IF agent_provider is openai/claude/both:
    run governed LLM collaboration

ELSE:
    do nothing except normal workflow defaults
```

## Why this matters

The previous workflow exposed `input_type` and `input_path` in the UI but did not bind them to an execution step. This produced successful workflow runs that never installed the bundle.

## Done condition

After this replacement is committed:

1. Run `core-lite-intake`.
2. Set `agent_provider: none`.
3. Set `input_type: bundle`.
4. Set `input_path: incoming/sv002_core_lite_stegverse_output_authority_bundle.zip`.
5. Set `dry_run: false`.
6. Confirm `scripts/package_stegverse_governed_output.py` appears on `main`.
