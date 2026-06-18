# Prompt and Aides Progress Footer

## Purpose

This document records the current build-report footer format for StegVerse ecosystem build prompts.

Each build response should end with four progress/status lines.

## Required Footer

```text
Line 1: <ORG.NAME> - %complete
Line 2: <REPO.NAME> - %complete
Line 3: <REPO.NAME> - %complete TO GOAL ACTIVATION;
Line 4: Δ [<REPO.NAME>: <ACTUAL>vs<BUILT>] - EXPLANATION.
```

## Reset Rule

When a goal changes, completes, or a new goal is added, reset the displayed values for the new goal baseline.

## Line 4 Meaning

Line 4 compares the repo-completion claim in line 2 against a direct verification of the file structure within the repo.

```text
ACTUAL = verified structure percentage
BUILT  = reported repo build percentage
Δ      = ACTUAL - BUILT
```

## Verification Tool

```bash
python scripts/verify_repo_structure_delta.py --reported-repo-complete <line_2_percent>
```

Output:

```text
reports/current/repo_structure_delta_report.json
```

## Pending Case

If the verifier has not been run in the current response, line 4 must say the verification is pending or unavailable instead of guessing.
