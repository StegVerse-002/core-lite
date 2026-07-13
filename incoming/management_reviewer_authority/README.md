# Management Reviewer Authority Intake

Place candidate-specific reviewer or quorum authority submissions in this directory.

Required schema:

```text
schemas/management_reviewer_authority_submission.schema.json
```

Validation command:

```bash
python tools/validate_management_reviewer_authority_submission.py --repo-root .
```

Declared task:

```text
sv002.management_reviewer_authority.validate
```

This intake does not grant review authority, execution authority, quorum status, or repository mutation authority. It validates whether submitted evidence is structurally complete, current, unrevoked, candidate-specific, and bounded to review-only scope.
