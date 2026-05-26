# Manual Upload Map — v0.1.3-gllm Transition Bundle Packaging

Upload each file to the exact target path.

## Files

```text
task.md                                           → task.md
package_transition_bundle.py                     → scripts/package_transition_bundle.py
ingest_transition_bundle.py                      → scripts/ingest_transition_bundle.py
transition_bundle.v1.schema.json                 → schemas/transition_bundle.v1.schema.json
LLM_OUTPUT_TO_INGESTION_CHAIN.md                 → docs/methodology/LLM_OUTPUT_TO_INGESTION_CHAIN.md
TASK_AS_INTERFACE_METHODOLOGY.md                 → docs/methodology/TASK_AS_INTERFACE_METHODOLOGY.md
FOUNDER_FAMILY_PRESERVATION_BOUNDARY.md          → docs/methodology/FOUNDER_FAMILY_PRESERVATION_BOUNDARY.md
core-lite-intake.yml                             → .github/workflows/core-lite-intake.yml
iosnoperiod.md                                   → iosnoperiod.md
iosnoperiod/github/workflows/core-lite-intake-yml → iosnoperiod/github/workflows/core-lite-intake-yml
```

## Display Path Note

The actual workflow path is:

```text
.github/workflows/core-lite-intake.yml
```

The leading dot is preserved in the zip. The display path above omits the dot only where necessary for readability.
