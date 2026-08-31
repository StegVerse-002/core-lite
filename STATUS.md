# STATUS.md — StegVerse-002/core-lite

```
works_today:           source implementation present; executed readiness proof pending
current_version:       0.1.28
current_entity:        StegVerse-002
current_gate:          reviewer-authority evidence reconstruction + experiment readiness
deployment_readiness:  source-ready candidate; runtime pending
runtime_state:         PENDING
activation_state:      PENDING
authority_effect:      NONE
last_reconciled:       2026-08-30
```

## Current governed result

Reviewer-authority submission structure and bounded AI-governance machinery are implemented. The 0.1.28 readiness lane adds independent reconstruction of identity, policy, delegation, revocation, and hash-bound evidence plus a one-command experiment-readiness verifier.

Source readiness, a passing workflow, or reconstructed reviewer evidence does **not** by itself form quorum, grant execution authority, bind repository state, activate a runtime, or prove public observation.

## Historical implementation gates

The historical M0–M10 stage map remains implementation evidence for the earlier Core-Lite build. It must not be interpreted as current runtime activation or release evidence.

## Current experiment gate

Expected machine command:

```bash
python tools/scripts/run_declared_task.py \
  --repo-root . \
  --task-id sv002.experiment.readiness.verify \
  --stage SV002-M12
```

Expected terminal source-readiness decision:

```
ALLOW_EXPERIMENT_READINESS
```

The reviewer-authority reconstruction lane may independently emit:

```
REVIEWER_AUTHORITY_EVIDENCE_PENDING
REVIEWER_AUTHORITY_EVIDENCE_ACCEPTED
REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED
```

No private or owner-authorized reviewer evidence is fabricated for experiment preparation.

## Remaining non-source gates

- observe exact-head validation/continuity workflow results
- merge admitted readiness change
- execute the readiness task on merged source
- obtain runtime evidence before claiming activation
- obtain public observation evidence before claiming live presentation success
- retain fail-closed behavior if reviewer authority evidence is absent, stale, revoked, tampered, or incomplete

## Node and FinCo boundary

```json
{
  "core_unit_installed": true,
  "node_participation_opt_in": false,
  "node_status": "NOT_A_NODE",
  "finco_participation_requested": false,
  "finco_participation_allowed": false
}
```

Core installation does not imply node participation.
Node participation does not imply FinCo eligibility.
