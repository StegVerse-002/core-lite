# SV002 Core-Lite Transition Table + CGE Gate Bundle

## Purpose

This bundle installs the first core-lite runtime consumer layer for the Stage 32–34 formalism-test surface.

It adds:

```text
core_lite/transition_table/__init__.py
core_lite/transition_table/attributes.py
core_lite/transition_table/resolver.py
core_lite/transition_table/policy.json
core_lite/transition_table/ingest_gate.py
tests/test_transition_table_resolver.py
tests/test_bundle_ingest_cge_transition_gate.py
formalisms/transition-table/reports/stage32_admissibility_space_report.json
formalisms/transition-table/reports/stage33_transition_graph_geometry_report.json
formalisms/transition-table/reports/stage34_repair_nearest_admissible_transition_report.json
```

## Important boundary

The gate classifies and records transition admissibility. It does not directly install files.

Candidate bundles are routed as candidate evidence.
Install/repair bundles may be marked as code-install-capable only when the Transition Table resolver permits that class.

## Verify

Run:

```bash
python tests/test_transition_table_resolver.py
python tests/test_bundle_ingest_cge_transition_gate.py
```

Expected generated reports:

```text
reports/current/transition_table_resolver_test_report.json
reports/current/bundle_ingest_cge_transition_gate_test_report.json
```
