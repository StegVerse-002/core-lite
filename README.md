# StegVerse-002 / core-lite

**Version:** `1.0.0-sv002-m10`  
**Entity:** `StegVerse-002`  
**Role:** Governed AI/intellect block — clean-slate successor to `StegVerse-001`  
**Status:** Production-candidate — all gates complete, intake proven live  
**Primary proof target:** Clean Core-Lite instance for governed LLM / admissibility-at-commit proof  
**KnowledgeVault dependency:** Online / active dependency for continuity, portable memory, governed context, and state access  

---

## Assumptions

This README assumes the repository is installed at:

```text
StegVerse-002/core-lite
```

It also assumes this repo is a **manual-upload-ready Core-Lite instance**. There is no `incoming/` ingestion flow in this path. Files are placed directly into their intended repository locations.

Paths that normally begin with a leading period are displayed without that leading period where necessary for iOS/chat readability.

> **Path display note:** `github/workflows/...` means the actual GitHub path is `.github/workflows/...`.

---

## Done means

This repo is considered complete for `v1.0.0-sv002-m10` when the following are true:

1. Identity declaration exists and has all authority flags false.
2. Bootstrap receipt exists and establishes the receipt chain head.
3. Core-Lite intake runs successfully and reaches its STOP condition.
4. CGE returns an explicit admissibility decision.
5. Intake emits a receipt and advances the append-only chain.
6. Stage map shows M0–M10 complete.
7. Only the stable dispatcher workflow pattern is used.
8. LLM output, KnowledgeVault context, multimodal input, and TV/TVC authority remain bounded inputs unless admitted by governance.
9. No stage advances by claim alone; every stage requires evidence.

---

## Proven evidence

| Artifact | Result |
|----------|--------|
| Identity declaration | `SV002-M0` — all authority flags false |
| Bootstrap receipt | `sha256:35b749ae...` — chain head |
| Core-Lite Intake | `status: success` — `stop_condition_met: true` |
| CGE decision | `ALLOW` — `sha256:33aa60e7...` |
| Intake receipt | `sha256:a151deed...` — chain live |
| Stage map | M0–M10 complete — `last_run: 2026-05-24` |

---

## What this is

`StegVerse-002/core-lite` is the full governed deployment instance of the StegVerse Core-Lite engine.

It is a **clean-slate instantiation**, not a fork. It exists to serve as the clean proof target for what `StegVerse-001` was intended to become before `StegVerse-001/core-lite` became operationally compromised by loading additional bundles before repo condition was fully checked.

This repo is aligned to:

- StegVerse Governed Tiered Intellect Model
- Transition Table Stages 1–31
- Core-Lite / Core-Addons / Core-Master architecture
- Commit-time admissibility enforcement
- Receipt-bound state reconstruction
- LLM-as-bounded-input governance
- KnowledgeVault continuity and governed context intake

---

## Proven capabilities

- Full Core-Lite intake pipeline with CGE admissibility, receipts, and STOP enforcement
- Multimodal input engine for:
  - text
  - voice
  - image
  - screenshot
  - document
  - structured data
  - LLM output
- KnowledgeVault context packet intake with memory-use receipts
- TV/TVC scoped authority token issuance and verification
- LLM Adapter Gate for admitting external reasoning as bounded instruction packets only
- StegVerse-001 repair candidates for known `SV001-M3` blocker classes
- Stage-map evidence for M0–M10
- Receipt-chain continuity for execution evidence
- Manual-upload-ready repository structure for iPhone, desktop, or CLI workflows

---

## Stable dispatcher pattern

This repo follows the stable dispatcher pattern:

```text
github/workflows/bootstrap-core-lite.yml   — fires once, identity setup
github/workflows/core-lite-intake.yml      — stable dispatcher, calls tools/
```

> **Path display note:** the actual GitHub path is `.github/workflows/...`.

No additional workflow files should be added for ordinary capability expansion.

All new capabilities should be declared under:

```text
tools/tasks/task_catalog.json
```

and implemented under:

```text
tools/
core_lite/
config/
schemas/
templates/
docs/
```

The dispatcher remains stable. The task catalog and governed tools evolve.

---

## Quick start

### On any device

This path works from iPhone, Android, desktop, GitHub web upload, or CLI.

1. Create GitHub org `StegVerse-002`.
2. Create repo `core-lite`.
3. Download **Releases → `v1.0.0-sv002-m10`**.
4. Upload or push all contents to `main`.
5. Set GitHub Actions permissions:
   - **Settings → Actions → General → Workflow permissions**
   - Select **Read and write permissions**
6. Run bootstrap:
   - **Actions → bootstrap-core-lite → Run workflow**
   - Type `BOOTSTRAP`
7. Run intake:
   - **Actions → core-lite-intake → Run workflow**
   - Leave all inputs blank for the default intake run
8. Tag release:
   - `v1.0.0-sv002-m10`

---

## CLI quick start

```bash
pip install -e .
python -m core_lite.cli run --repo-root . --skip-tasks
```

Expected result:

```text
Core-Lite intake completes.
CGE emits an admissibility result.
STOP condition is reached.
Receipt/report artifacts are written.
```

---

## Dispatcher inputs

All capabilities are accessed through one workflow with optional inputs.

| Input | Purpose | Example |
|-------|---------|---------|
| `task_id` | Run a declared task | `sv001.repair.intake.enablement` |
| `repair_target` | Repair a remote repo | `Data-Continuation/core-lite` |
| `input_type` | Process a multimodal input | `screenshot` |
| `kv_packet` | Ingest a KnowledgeVault context packet | `vault_template/context_packets/default_packet.json` |
| `dry_run` | Dry run only, no mutations | `true` |

Leave all inputs blank for the default intake run.

---

## StegVerse-001 repair

`StegVerse-001/core-lite` should not be treated as the primary clean proof target until its condition has been inspected and remediated.

To prepare repair input:

1. Open `Data-Continuation/core-lite` Actions.
2. Copy the relevant failure text.
3. Paste it into:

```text
tracking/sv001_repair_input.txt
```

Then run the dispatcher with:

```text
task_id: sv001.repair.intake.enablement
repair_target: Data-Continuation/core-lite
```

Or run from CLI:

```bash
python -m tools.repair.sv001_repair \
  --target-repo Data-Continuation/core-lite \
  --failure-file tracking/sv001_repair_input.txt
```

This handles the four known `SV001-M3` blocker classes automatically.

See:

```text
tools/repair/README.md
```

---

## Repo structure

```text
github/workflows/
  bootstrap-core-lite.yml        fires once, identity setup
  core-lite-intake.yml           stable dispatcher

tools/
  tasks/task_catalog.json        declared tasks; add capabilities here, not as workflows
  scripts/                       receipt emitter, stage resolver, LLM adapter gate
  validators/                    schema and receipt-chain validators
  repair/                        StegVerse-001 repair tools

core_lite/
  cli.py                         entry point: python -m core_lite.cli
  cge.py                         CGE admissibility engine
  intake.py                      intake orchestrator
  ingest.py                      13-step ingestion pipeline
  receipts.py                    append-only receipt chain
  multimodal/pipeline.py         multimodal input engine
  knowledgevault/intake.py       context packet intake + memory-use receipts
  tvc/verify.py                  TVC registry authority + chainlog
  tv/policy.py                   TV apply / verify / heal

config/
  package_registry.json          TVC package registry
  core_policy.json               default privacy and governance policy
  tv_manifest.yml                TV seed manifest

schemas/
  *.schema.json                  canonical JSON schemas

templates/
  context packet, receipt, and manifest templates

tracking/stegverse-002/
  stage map and state files

vault_template/
  KnowledgeVault portable memory layer

docs/
  ecosystem invariants, glossary, and integration guides

reports/current/
  run evidence committed by workflow

receipts/current/
  receipt chain committed by workflow

stegverse/
  CGE fingerprint and runtime receipts

data/summary/
  chainlog.jsonl                 TV/TVC append-only signing ledger
```

> **Path display note:** `github/workflows/` above means `.github/workflows/` in the actual repository.

---

## Governance model

Every consequence-bearing action must declare:

```text
governed_tier         what tier this action occupies
transition_stage      which SV002 stage this belongs to
active_gate           current gate and STOP condition
allowed_actions       explicit list — nothing else permitted
forbidden_actions     explicit list — enforced by CGE
required_evidence     what receipts and reports must be produced
STOP_condition        where this action ends — no open-ended stages
promotion_criteria    what evidence proves the stage is complete
```

No stage advances by claim.

A stage advances only when its required evidence is present and the STOP condition has been met.

---

## LLM Adapter Gate

The LLM Adapter Gate admits external model reasoning only as bounded input.

LLM output is never treated as:

- authority
- consent
- proof of identity
- final execution permission
- replacement for CGE
- replacement for TV/TVC authority checks
- replacement for receipt evidence

The expected path is:

```text
LLM output
→ bounded instruction packet
→ TV/TVC boundary check
→ CGE admissibility evaluation
→ receipt/report emission
→ STOP condition
```

---

## KnowledgeVault role

KnowledgeVault is an active dependency for this repo.

It provides:

- portable continuity context
- governed memory packets
- identity-adjacent context without identity proof
- contextual state for review
- bounded input into Core-Lite intake
- memory-use receipts

KnowledgeVault does **not** provide execution authority by itself.

Memory can inform review. It cannot authorize consequence-bearing transitions.

---

## TV/TVC role

TV/TVC provides scoped token and package authority boundaries.

Expected behavior:

```text
apply
→ verify
→ heal only when admissible
→ append chainlog
→ emit receipt
```

TV/TVC is responsible for:

- scoped authority token issuance
- registry verification
- policy-bounded access
- chainlog continuity
- fail-closed behavior when authority is unknown or expired

---

## Release tags

| Tag | Gate | Description |
|-----|------|-------------|
| `v0.1.0-sv002-m0` | M0 | Identity declaration |
| `v0.2.0-sv002-m3` | M3 | Remote inspection + repair candidates |
| `v0.5.0-sv002-m5` | M5 | Core-Lite Intake STOP met — proven live |
| `v0.7.0-sv002-m7` | M7 | LLM Adapter Gate + KnowledgeVault packets |
| `v1.0.0-sv002-m10` | M10 | Full governed deployment — production-candidate |

---

## Core invariants

1. Memory is not authority.
2. Context is not consent.
3. Capability is not admissibility.
4. Input is not execution.
5. LLM reasoning is not authorization.
6. Identity context is not identity proof.
7. Local success is not composite success.
8. Every consequence-bearing transition needs a receipt.
9. Every stage needs a STOP condition.
10. Unknown fails to review or fail-closed.
11. A clean proof target must remain clean until its condition is checked.
12. External reasoning must be bounded before it can influence execution.
13. Manual upload is placement, not ingestion.
14. Evidence packets support review; they do not become approval authority.
15. Commit-time validity must be re-bound against current authority, policy, evidence, and context state.

---

## Current status

`StegVerse-002/core-lite` is the clean production-candidate Core-Lite target.

It is ready to serve as:

- the first functioning governed Core-Lite proof target
- the admissibility-at-commit demonstration repo
- the clean successor path for `StegVerse-001`
- the LLM Adapter Gate proof surface
- the KnowledgeVault-context intake proof surface
- the manual-upload-ready foundation for the next Core-Lite stage

---

## Next stage direction

The next stage should avoid broad restructuring.

Minimum next work:

1. Verify `v1.0.0-sv002-m10` release contents against this README.
2. Confirm both dispatcher workflows exist in the actual `.github/workflows/` path.
3. Confirm no extra workflow files exist.
4. Run default `core-lite-intake`.
5. Confirm reports and receipts are emitted.
6. Confirm KnowledgeVault packet intake can run through the dispatcher.
7. Confirm LLM Adapter Gate remains dry-run / bounded-input only unless explicitly admitted by governance.
8. Export or mirror proof artifacts to the Site only after receipt evidence exists.

---

## Site mirror

Public proof:

```text
https://stegverse-labs.github.io/Site/
```

Stage 1–31 formalism:

```text
https://stegverse-labs.github.io/Site/formalism-tests-stage-1-to-31.html
```

The Site is a public visual mirror.

The repos, tests, receipts, release artifacts, and replay evidence remain the proof authority.

---

## Verification checklist

Use this checklist after upload or release creation.

```text
[ ] Repo is StegVerse-002/core-lite
[ ] README.md is present at repo root
[ ] Actual workflow path is .github/workflows/
[ ] bootstrap-core-lite.yml exists
[ ] core-lite-intake.yml exists
[ ] No other workflow files exist
[ ] tools/tasks/task_catalog.json exists
[ ] core_lite/cli.py exists
[ ] core_lite/cge.py exists
[ ] core_lite/intake.py exists
[ ] core_lite/receipts.py exists
[ ] config/core_policy.json exists
[ ] config/package_registry.json exists
[ ] vault_template/ exists
[ ] tracking/stegverse-002/ exists
[ ] Default intake run reaches STOP condition
[ ] CGE emits explicit decision
[ ] Receipt chain updates
[ ] Reports are written
[ ] Stage map still shows M0–M10 complete
```

---

## License / rights note

This repository is part of the StegVerse governed AI/intellect ecosystem.

Public mirrors and documentation may be visible, but execution authority, admissibility, receipts, and governed transitions remain bound to the repository evidence chain and current policy state.
