# StegVerse-002 / core-lite

**Version:** 1.0.0-sv002-m10  
**Entity:** StegVerse-002  
**Role:** Governed AI/intellect block — clean-slate successor to StegVerse-001  
**Status:** Production-candidate — all gates complete, intake proven live  

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

`StegVerse-002/core-lite` is the full governed deployment instance of the StegVerse
Core-Lite engine. It is a clean-slate instantiation — not a fork — aligned to the
StegVerse Governed Tiered Intellect Model and the Transition Table (Stages 1–31).

Proven capabilities:

- Full Core-Lite intake pipeline with CGE admissibility, receipts, and STOP enforcement
- Multimodal input engine (text, voice, image, screenshot, document, structured data, LLM output)
- KnowledgeVault context packet intake with memory-use receipts
- TV/TVC scoped authority token issuance and verification
- LLM Adapter Gate — external reasoning admitted as bounded instruction packets only
- StegVerse-001 repair — candidates for all known SV001-M3 blocker classes

This repo follows the **stable dispatcher** pattern:

```
github/workflows/bootstrap-core-lite.yml   — fires once, identity setup
github/workflows/core-lite-intake.yml      — stable dispatcher, calls tools/
```

No other workflow files exist. All capabilities live under `tools/`.

---

## Quick start

### On any device (iPhone, Android, desktop)

1. Create org `StegVerse-002` and repo `core-lite` on GitHub
2. Download **Releases → v1.0.0-sv002-m10** and push all contents to `main`
3. Set **Settings → Actions → General → Workflow permissions → Read and write**
4. **Actions → bootstrap-core-lite → Run workflow** → type `BOOTSTRAP`
5. **Actions → core-lite-intake → Run workflow** — leave all inputs blank
6. Tag `v1.0.0-sv002-m10` to produce the release tar.gz

### From CLI

```bash
pip install -e .
python -m core_lite.cli run --repo-root . --skip-tasks
```

---

## Dispatcher inputs

All capabilities are accessed through a single workflow with optional inputs:

| Input | Purpose | Example |
|-------|---------|---------|
| `task_id` | Run a declared task | `sv001.repair.intake.enablement` |
| `repair_target` | Repair a remote repo | `Data-Continuation/core-lite` |
| `input_type` | Process a multimodal input | `screenshot` |
| `kv_packet` | Ingest a KnowledgeVault context packet | `vault_template/context_packets/default_packet.json` |
| `dry_run` | Dry run only, no mutations | `true` |

Leave all blank for the default intake run.

---

## StegVerse-001 repair

Paste the failure text from `Data-Continuation/core-lite` Actions into
`tracking/sv001_repair_input.txt`, then run:

```
task_id: sv001.repair.intake.enablement
repair_target: Data-Continuation/core-lite
```

Or from CLI:

```bash
python -m tools.repair.sv001_repair \
  --target-repo Data-Continuation/core-lite \
  --failure-file tracking/sv001_repair_input.txt
```

Handles all four known SV001-M3 blocker classes automatically.
See `tools/repair/README.md` for full instructions.

---

## Repo structure

```
github/workflows/           2 workflow files only — stable dispatcher pattern
tools/
  tasks/task_catalog.json   all declared tasks — add capabilities here, not as workflows
  scripts/                  Python helpers (receipt emitter, stage resolver, LLM adapter gate)
  validators/               schema and receipt chain validators
  repair/                   StegVerse-001 repair tools
core_lite/
  cli.py                    entry point: python -m core_lite.cli
  cge.py                    CGE admissibility engine
  intake.py                 intake orchestrator
  ingest.py                 13-step ingestion pipeline
  receipts.py               append-only receipt chain
  multimodal/pipeline.py    multimodal input engine
  knowledgevault/intake.py  context packet intake + memory-use receipts
  tvc/verify.py             TVC registry authority + chainlog
  tv/policy.py              TV apply / verify / heal
config/
  package_registry.json     TVC package registry
  core_policy.json          default privacy and governance policy
  tv_manifest.yml           TV seed manifest
schemas/                    9 canonical JSON schemas
templates/                  context packet, receipt, manifest templates
tracking/stegverse-002/     stage map and state files
vault_template/             KnowledgeVault portable memory layer
docs/                       ecosystem invariants, glossary, integration guides
reports/current/            run evidence (committed by workflow)
receipts/current/           receipt chain (committed by workflow)
stegverse/                  CGE fingerprint and runtime receipts
data/summary/chainlog.jsonl TV/TVC append-only signing ledger
```

---

## Governance model

Every action declares:

```
governed_tier         what tier this action occupies
transition_stage      which SV002 stage this belongs to
active_gate           current gate and STOP condition
allowed_actions       explicit list — nothing else permitted
forbidden_actions     explicit list — enforced by CGE
required_evidence     what receipts and reports must be produced
STOP_condition        where this action ends — no open-ended stages
promotion_criteria    what evidence proves the stage is complete
```

No stage advances by claim. Evidence is required.

---

## Release tags

| Tag | Gate | Description |
|-----|------|-------------|
| v0.1.0-sv002-m0 | M0 | Identity declaration |
| v0.2.0-sv002-m3 | M3 | Remote inspection + repair candidates |
| v0.5.0-sv002-m5 | M5 | Core-Lite Intake STOP met ✓ proven live |
| v0.7.0-sv002-m7 | M7 | LLM Adapter Gate + KnowledgeVault packets |
| v1.0.0-sv002-m10 | M10 | Full governed deployment — production-candidate |

---

## Invariants

1. Memory is not authority
2. Context is not consent
3. Capability is not admissibility
4. Input is not execution
5. LLM reasoning is not authorization
6. Identity context is not identity proof
7. Local success is not composite success
8. Every consequence-bearing transition needs a receipt
9. Every stage needs a STOP condition
10. Unknown fails to review or fail-closed

---

## Site mirror

Public proof: https://stegverse-labs.github.io/Site/  
Stage 1–31 formalism: https://stegverse-labs.github.io/Site/formalism-tests-stage-1-to-31.html
