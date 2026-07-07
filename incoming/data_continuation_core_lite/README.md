# Data-Continuation/core-lite Intake Package

This directory is the governed candidate-evidence intake location for the StegVerse-001 management package exported from `Data-Continuation/core-lite`.

Expected package root:

```text
incoming/data_continuation_core_lite/
```

Expected files:

```text
reports/ecosystem_maintainer_scan.json
reports/auto_fix_eligibility.json
reports/friction_avoided.json
reports/bundle_registry.json
reports/capability_gap_plan.json
```

Validation command:

```bash
python tools/validate_management_package_intake.py --root .
```

Boundary:

```text
candidate_evidence_only: true
canonical_authority: false
may_bind_repo_state: false
```

This directory does not grant authority, form quorum, or bind repository state.
