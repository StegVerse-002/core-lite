# Core-Lite Curiosity and Motive Execution Handoff

## Source of truth

This scoped lane governs the `StegVerse-002/core-lite` integration of replayable
curiosity/motive evidence. It is subordinate to `docs/CORE_LITE_MIRROR_HANDOFF.md`
and realizes the source-binding contract in
`contracts/curiosity-motive-governance-adoption.json`. It does not supersede the
current reviewer-authority workstream.

## Goal and state

```text
goal_id: SV002-CURIOSITY-MOTIVE-EXECUTION-001
repository_stage: SV002-M14
adoption_stage: SV002-CMG-02
state: IMPLEMENTED_PENDING_HOSTED_VALIDATION_AND_MERGE
base_commit: 9421aac52d21b0d11dfd5b0803c1a7569b486ce3
source implementation: StegVerse-Labs/StegCore@42231a3862c2fe9b5898e6f75d72cff0b44e7396
master anchor: master-records/core-lite@698d3dbd3d132ace168f5467a372c33852d30206
master receipt: master-records/core-lite@17d54c23ba5d42daed1a6d12ada155e0c4c706b7
```

## Installed surfaces

```text
contracts/curiosity-motive-governance-adoption.json
schemas/curiosity_motive_execution_witness.schema.json
incoming/curiosity_motive_governance/README.md
incoming/curiosity_motive_governance/example_unauthorized_curiosity.json
tools/validate_curiosity_motive_execution.py
tools/tasks/sv002.curiosity_motive_execution.validate.json
tests/test_curiosity_motive_execution.py
.github/workflows/curiosity-motive-execution-gate.yml
```

## Runtime contract

The gate reconstructs the hash-linked transition sequence, identifies the earliest
state at which an epistemic gap becomes a committed external action, attributes a
bounded functional motive from convergent evidence, and independently evaluates
commit-time authority.

```text
functional motive attribution != execution authority
observer description != actor motive
normative denial != motive disproof
reconstruction != occurrence
phenomenal status: NOT_INFERRED
verifier disagreement: FAIL_CLOSED
```

The gate may admit or deny a proposed execution transition. It never performs the
external action.

## Source anchors

```text
StegCore commit: 42231a3862c2fe9b5898e6f75d72cff0b44e7396
StegCore implementation blob: 0a333344492880044680de6a9325ba16112bbacd
master anchor commit: 698d3dbd3d132ace168f5467a372c33852d30206
master anchor blob: f328f68666e5629e950164a4a05eff8b0f93bd6e
master anchor hash: 769df23f3e66cc893690293c6eeddebafa3438585091cb830ba42c9127fa59bd
master receipt commit: 17d54c23ba5d42daed1a6d12ada155e0c4c706b7
master receipt blob: 54ccaf28e889294aa6be839be6e26003ab59c3c9
master receipt hash: 64d31728944ed70550ad709f7f45cecedff0eb6a069c260f947d54e227e7d22a
```

## Decisions

```text
EXECUTION_ADMISSIBLE
EXECUTION_DENIED_UNAUTHORIZED_CURIOSITY
EXECUTION_DENIED_UNAUTHORIZED
NO_EXECUTION_TRANSITION
FAIL_CLOSED
```

## Verification

```bash
python -m unittest tests.test_curiosity_motive_execution
python tools/scripts/run_declared_task.py \
  --task-id sv002.curiosity_motive_execution.validate \
  --stage SV002-M14
```

Expected example result:

```text
terminal decision: EXECUTION_DENIED_UNAUTHORIZED_CURIOSITY
functional curiosity: supported
execution authority: unauthorized
execution performed by gate: false
```

## Completion and continuation

```text
source-binding adoption contract preserved and advanced: true
implementation installed on branch: true
focused local tests: passed (8)
hosted gate: pending
pull request merge: pending
destination receipt: pending
GCAT/BCAT policy integration: separate transition
```

After merge, preserve the exact destination commit and hosted workflow evidence in
a successor receipt before this scoped lane is declared complete.
