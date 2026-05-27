# StegVerse Output Authority

## Purpose

This document establishes the output authority rule for `StegVerse-002/core-lite`:

> External LLMs may generate candidate evidence. StegVerse publishes the governed output.

The operational problem this solves is artifact and authority fan-out. When OpenAI, Claude, or any other provider emits separate visible artifacts, reviewers may treat those artifacts as parallel outputs from parallel authorities. That is not admissible for StegVerse.

## Rule

```text
No LLM publishes.
No LLM becomes the system voice.
No LLM output becomes consequence.
StegVerse synthesizes, governs, receipts, and exposes one official candidate output.
```

## Provider role

LLM providers are evidence sources only:

```text
reasoning witness
proposal generator
challenge agent
candidate evidence source
```

Their output may be preserved under `evidence/`, `outputs/`, `reports/`, and `receipts/`, but it must not become the official run-visible answer.

## StegVerse role

StegVerse is the output authority for governed runs. Its output is generated at:

```text
outputs/stegverse_output.md
outputs/stegverse_output.json
reports/current/stegverse_output_report.json
receipts/current/stegverse_output_receipt.jsonl
dist/run_artifacts/stegverse-governed-output.zip
```

The ZIP is the compact review artifact. It contains the StegVerse output first, with LLM evidence underneath.

## Consequence boundary

The StegVerse output remains a governed candidate unless separately approved for consequence-bearing execution.

```text
Candidate output is not publication.
Candidate output is not approval.
Candidate output is not deployment.
Candidate output is not repo mutation authority.
```

## Done condition

A run satisfies this authority rule when:

```text
outputs/stegverse_output.md exists
outputs/stegverse_output.json exists
reports/current/stegverse_output_report.json exists
receipts/current/stegverse_output_receipt.jsonl exists
dist/run_artifacts/stegverse-governed-output.zip exists
```

and the report declares:

```text
official_output_authority: StegVerse
llm_provider_outputs: candidate_evidence_only
human_required_for_consequence: true
```
