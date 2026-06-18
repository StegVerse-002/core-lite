# Authority Decision Review Policy

Version: 0.1.11-gllm

Input result expected:

```text
AUTHORITY_DECISION_REQUEST_RECORDED
```

Review result:

```text
AUTHORITY_DECISION_REVIEW_PENDING_AUTHORIZED_QUORUM
```

Boundary:

```text
candidate_evidence_only: true
canonical_authority: false
broad_authority: false
may_bind_repo_state: false
```

This review does not grant authority, install anything, or bind repo state.
