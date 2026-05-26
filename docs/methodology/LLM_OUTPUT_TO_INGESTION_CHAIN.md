# LLM Output to Ingestion Chain

## Version

`0.1.3-gllm`

## Purpose

This document defines the StegVerse rule that governed LLM collaboration output is not an endpoint.

Every non-empty output from the LLM collaboration gate is proposed-transition evidence. It must either be packaged into a proposed-transition bundle or explicitly receipted as empty, partial, blocked, denied, quarantined, or failed closed.

## Core Rule

```text
LLMs may propose.
Ingestion transports.
Admissibility binds.
Receipts preserve.
Master-records reconstructs.
```

## Chain

```text
task.md
→ OpenAI candidate evidence
→ Claude candidate evidence
→ deterministic coordination thread
→ comparison report
→ boundary report
→ proposed-transition bundle
→ ingestion intake
→ ingestion receipt
→ destination admissibility decision
→ destination receipt
→ master-records export / reconstruction pointer
```

## Cross-Repo / Cross-Org Rule

No LLM collaboration output may directly cross repo or org boundaries as an effective state change.

If the destination repo or destination org differs from the current repo/org, then:

```text
transport_mechanism MUST equal ingestion
```

Otherwise the transition must fail closed.

## Intake Is Not Canonical Authority

Ingestion intake may admit a bundle only as candidate evidence.

It may not grant canonical authority.

Canonical authority can only arise later from a destination-side admissibility/install decision that is independently receipted.

## Valid Intake Outcomes

```text
ADMITTED_AS_CANDIDATE_EVIDENCE
REPAIR_REQUIRED
DENIED
QUARANTINED
FAIL_CLOSED
```

## Invalid Outcomes

```text
ADMITTED_AS_CANONICAL
INSTALLED_BY_SOURCE
CROSS_REPO_DIRECT_WRITE
BROAD_AUTHORITY_GRANTED
UNRECEIPTED_TRANSFER
```

## No Silent Termination

A collaboration run must not silently terminate at:

```text
outputs/thread.md
```

It must produce one of:

```text
proposed-transition bundle
RECORDED_EMPTY receipt
PARTIAL_PROVIDER_OUTPUT receipt
PROVIDER_WRITE_BLOCKED receipt
REPAIR_REQUIRED receipt
DENIED receipt
FAIL_CLOSED receipt
```
