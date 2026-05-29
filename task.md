# SV002-M11 Candidate Generation Task

Generate exactly one machine-actionable candidate patch packet for StegVerse-002/core-lite.

## Goal

Repair and harden the current incoming-disposition workflow so that StegVerse-002 can complete the end-to-end proof:

```text
incoming payload committed
→ workflow selects only payloads changed in the triggering push
→ payload is hashed
→ payload is staged outside incoming/
→ payload is evaluated
→ disposition receipt is written
→ accepted payload is removed from incoming/
→ rejected/failed payload is copied to quarantine before removal
→ legacy incoming payloads are inventoried but not mass-deleted
→ durable evidence is committed
```

## Current failure class

The repository has repeatedly drifted because the assistant and workflow logic have confused:

```text
installer files
workflow files
incoming payloads
legacy incoming payloads
dispositioned payloads
quarantined payloads
```

The candidate must make the workflow behavior explicit and bounded.

## Required behavior

The candidate must modify only the minimum files needed.

The candidate must preserve this invariant:

```text
incoming/README.md is the only intended steady-state file in incoming/
```

But it must not blindly mass-delete legacy files already present in incoming/.

### Changed payload handling

For a push event affecting `incoming/**`, the workflow must:

1. identify only incoming files changed by the triggering push;
2. exclude `incoming/README.md`;
3. process each changed incoming payload in sorted order;
4. compute a SHA-256 hash for each changed payload;
5. copy each payload into a durable staging path before evaluation:

```text
tracking/incoming_mailbox/<sha>/<filename>
```

6. run the existing ingestion/evaluation pipeline against the staged copy, not the incoming copy;
7. write one disposition record per changed payload:

```text
reports/current/incoming_disposition_summary.jsonl
receipts/current/incoming_disposition_receipt.jsonl
```

8. if evaluation succeeds, mark the payload:

```text
INSTALLED_OR_ACCEPTED
```

9. if evaluation fails, copy the staged payload to:

```text
quarantine/incoming/<sha>/<filename>
```

and mark the payload:

```text
QUARANTINED
```

10. remove only those incoming payloads that have received a disposition record in this run;
11. inventory legacy incoming payloads that were not part of the triggering push:

```text
reports/current/incoming_legacy_inventory.txt
```

12. never delete legacy incoming payloads merely because they exist.

## Required workflow trigger

The push trigger must be:

```yaml
push:
  branches: [main]
  paths:
    - "incoming/**"
```

The push route must not activate from normal source edits outside `incoming/`.

## Required manual dispatch support

Manual dispatch must still support:

```text
input_type
input_path
stage_override
dry_run
agent_provider
task_id
```

Manual run must support:

```text
input_type = bundle
input_path = incoming/<payload>.zip
agent_provider = none
dry_run = false
stage_override = SV002-M11
```

## Required outputs

At minimum, the candidate must ensure these outputs are created when a payload is evaluated:

```text
reports/current/incoming_changed_files.txt
reports/current/incoming_legacy_inventory.txt
reports/current/incoming_disposition_summary.jsonl
receipts/current/incoming_disposition_receipt.jsonl
reports/current/incoming_disposition_processed_files.txt
tracking/incoming_mailbox/<sha>/
```

If evaluation fails:

```text
quarantine/incoming/<sha>/
```

## Allowed files

The candidate may modify:

```text
.github/workflows/core-lite-intake.yml
docs/
tests/
```

The candidate may add a focused test if appropriate.

## Forbidden files

The candidate must not modify:

```text
README.md
incoming/
secrets/
.env
```

The candidate must not add any secret, token, private key, credential, deploy hook, or external service credential.

The candidate must not grant broad authority.

The candidate must not create or change root-level README.md.

The candidate must not create a new repo, new product, or new architecture.

## Machine-actionable response format

Return exactly one fenced JSON block using this schema:

```json
{
  "schema": "stegverse.candidate_patch.v1",
  "candidate_id": "sv002-m11-incoming-disposition-gate-repair",
  "provider": "openai-or-claude",
  "description": "Repair incoming disposition workflow to stage, evaluate, disposition, quarantine if needed, and clean only dispositioned changed payloads while inventorying legacy incoming payloads.",
  "transition_class": "workflow-repair",
  "authority_ref": "SV002-M11/scoped-workflow-repair-candidate",
  "policy_ref": "triad/default-deny/no-broad-authority",
  "files": [
    {
      "path": ".github/workflows/core-lite-intake.yml",
      "operation": "write",
      "content": "<complete replacement file content>"
    }
  ]
}
```

If tests or docs are included, include them as additional file objects in the same JSON packet.

## Done condition

The candidate is complete only if it preserves all of the following:

```text
incoming push trigger is incoming/** only
changed incoming payloads are processed in sorted order
incoming/README.md is excluded from payload processing
each processed payload gets a SHA-256-based staging directory
each processed payload gets a JSONL disposition record
failed payloads are copied to quarantine before incoming cleanup
only dispositioned changed payloads are removed from incoming/
legacy incoming payloads are inventoried but not deleted
manual dispatch still supports input_type/input_path
```

## Response rules

Return no prose outside the fenced JSON block.
Do not include multiple alternatives.
Do not include explanations.
Do not claim the patch was applied.
