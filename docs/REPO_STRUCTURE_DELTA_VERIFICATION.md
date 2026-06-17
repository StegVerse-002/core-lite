# Repo Structure Delta Verification

## Purpose

This document adds the fourth progress line requested for build reports.

The fourth line compares line 2 (`REPO NAME: core-lite: ...`) against a direct file-structure verification of the repo.

## Command

```bash
python scripts/verify_repo_structure_delta.py --reported-repo-complete 83
```

## Output

```text
reports/current/repo_structure_delta_report.json
```

## Interpretation

```text
verified_structure_percent - reported_repo_complete_percent = delta_percent
```

- Positive delta: repo file structure is ahead of the reported repo-completion line.
- Zero delta: repo file structure matches the reported repo-completion line.
- Negative delta: reported repo-completion line is ahead of verified file structure.

## Scope

This verifier checks the M11-M16 activation surface only. It does not validate runtime behavior by itself. Runtime validation remains covered by the individual M11-M16 validation runners and reports.
