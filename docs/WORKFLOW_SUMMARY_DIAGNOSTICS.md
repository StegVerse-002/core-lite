# Workflow Summary Diagnostics

This repair adds quick-glance GitHub Actions summaries to `core-lite-intake`.

## Purpose

The workflow should not require opening multiple step logs to determine whether a run selected:

- declared input / bundle ingestion;
- declared task execution;
- governed LLM collaboration;
- no actionable route.

The workflow summary now prints the route, core inputs, expected behavior, preflight result, bundle ingest decision, installed/rejected counts, error list, key file presence, and whether declared-input outputs were committed.

## Expected declared bundle route

Use:

```text
task_id: [blank]
skip_tasks: false
stage_override: SV002-M10
input_type: bundle
input_path: incoming/sv002_core_lite_stegverse_output_authority_bundle.zip
dry_run: false
agent_provider: none
```

The summary should show:

```text
route: declared-input-route
status: success
decision: ALLOW
installed_count: 5
scripts/package_stegverse_governed_output.py: yes
```

If a field is missing or the input path is wrong, the summary fails closed and lists the relevant missing value or available `incoming/` files.
