# Claude Code — Governed Collaboration Proposal

Run timestamp: 2026-05-28T02:13:34Z

Governance mode: propose-only

Capability version: 0.1.3-gllm

Task source: task.md

Directive: no broad authority is ever admissible under Transition Table, AE, or GCAT/BCAT enforcement.

---

Understood — I'll deliver the full governed proposal inline as my response, in lieu of the file write that was not granted. This is the same content I would have written to `outputs/claude_response.md`.

---

# Claude Code — Governed Collaboration Proposal

Run timestamp: 2026-05-28T02:13:34Z
Governance mode: propose-only
Capability version: 0.1.3-gllm
Task source: task.md
Directive: no broad authority is ever admissible under Transition Table, AE, or GCAT/BCAT enforcement.

## Current State Assessment

`StegVerse-002/core-lite` on `main` already contains the packager (`scripts/package_stegverse_governed_output.py`), the catalog entry `stegverse.output.package`, the dispatcher (`tools/scripts/task_dispatcher.py`), and `.github/workflows/core-lite-intake.yml` with `workflow-summary`, `declared-input-route`, `claude-agent`, `openai-agent`, `merge-and-commit`. The reported failure is exact: **`core-lite-intake.yml` has no `declared-task-route` job**. `workflow-summary` *names* the route but no job's `if:` matches `task_id != '' && input_* == '' && agent_provider == 'none'`, so a task-only dispatch shows green with nothing executed.

## Directive Alignment

Compliant with the Absolute Directive. No broad authority granted. Execution is gated to one declared workflow_dispatch route, runs only through the existing dispatcher (which already enforces `allowed_stages` / `forbidden_actions` and writes `receipts/current/task_receipt.jsonl`), adds no secrets / deploy authority / release authority, and fails closed on missing declared artifacts. `scripts/package_stegverse_governed_output.py`, `tools/scripts/task_dispatcher.py`, and `tools/tasks/task_catalog.json` are unchanged.

## Ecosystem Stage Assessment

This change is entirely Stage 1 (collaboration substrate). Stage 2 (per-framework AI governance), Stage 3 (Rige enrollment / `Beta_Orionis` counterpart), and Stage 4 (cross-repo routed messaging) are not touched, prepared, simulated, or staged.

## Next Collaboration Primitive

A governed `declared-task-route` on `core-lite-intake.yml` that turns a `task_id` workflow_dispatch into a receipted, fail-closed task execution with machine-readable evidence (stdout/stderr/exit code), expected-artifact verification, a structured Actions summary, and committed outputs.

## Proposed Implementation

PROPOSE-ONLY run. Manual placement path:

```text
.github/workflows/core-lite-intake.yml
```

Complete replacement YAML (preserves existing `declared-input-route`, `claude-agent`, `openai-agent`, `merge-and-commit`; corrects `workflow-summary` route ordering; adds new `declared-task-route` job):

```yaml
name: core-lite-intake

on:
  workflow_dispatch:
    inputs:
      task_id:
        description: "Task ID (leave blank for default intake run)"
        required: false
        default: ""
      skip_tasks:
        description: "Skip declared task loop (true/false)"
        required: false
        default: "true"
      stage_override:
        description: "Override active stage (leave blank for current)"
        required: false
        default: ""
      repair_target:
        description: "Repair target repo (e.g. Data-Continuation/core-lite)"
        required: false
        default: ""
      input_type:
        description: "Multimodal input type (text/voice/image/screenshot/document/structured_data/llm_output/bundle)"
        required: false
        default: ""
      input_path:
        description: "Path to input file or manifest (relative to repo root)"
        required: false
        default: ""
      kv_packet:
        description: "KnowledgeVault context packet path"
        required: false
        default: ""
      dry_run:
        description: "Dry run only — no mutations (true/false)"
        required: false
        default: "false"
      agent_provider:
        description: "Governed LLM collaboration provider for task.md: none/openai/claude/both"
        required: false
        default: "none"

  push:
    branches: [main]
    paths:
      - ".github/workflows/core-lite-intake.yml"
      - "task.md"
      - "CLAUDE.md"
      - "scripts/openai_task.py"
      - "scripts/merge_outputs.py"
      - "scripts/package_transition_bundle.py"
      - "scripts/ingest_transition_bundle.py"
      - "agent_policy/**"
      - "agent_history/**"
      - "governance/directives/**"
      - "schemas/**"
      - "docs/methodology/**"
      - "tools/agent_governance/**"
      - "tools/tasks/**"
      - "core_lite/**"
      - "config/**"

permissions:
  contents: write
  actions: read

env:
  STEGVERSE_ENTITY: StegVerse-002
  STEGVERSE_REPO: StegVerse-002/core-lite
  STEGVERSE_VERSION: 1.0.0-sv002-m10
  GOVERNED_LLM_LLM_VERSION: 0.1.3-gllm
  OPENAI_MODEL: ${{ vars.OPENAI_MODEL || 'gpt-4o' }}
  AGENT_PROVIDER: ${{ github.event_name == 'push' && 'both' || inputs.agent_provider }}

jobs:
  workflow-summary:
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Write route summary
        run: |
          set -euo pipefail
          EVENT="${{ github.event_name }}"
          TASK_ID="${{ inputs.task_id }}"
          INPUT_TYPE="${{ inputs.input_type }}"
          INPUT_PATH="${{ inputs.input_path }}"
          AGENT_PROVIDER_IN="${{ inputs.agent_provider }}"
          DRY_RUN="${{ inputs.dry_run }}"
          STAGE="${{ inputs.stage_override }}"
          if [ -z "${STAGE}" ]; then STAGE="SV002-M10"; fi

          ROUTE="default/no-op"
          EXPECTED="No declared bundle, task, or LLM provider route selected."
          if [ "${EVENT}" = "push" ]; then
            ROUTE="llm-collaboration(push)"
            EXPECTED="Run OpenAI/Claude proposal path and commit coordination evidence."
          elif [ "${AGENT_PROVIDER_IN}" = "none" ] && [ -n "${INPUT_TYPE}" ] && [ -n "${INPUT_PATH}" ]; then
            ROUTE="declared-input-route"
            EXPECTED="Validate input_type/input_path, process bundle/input, commit installed outputs."
          elif [ "${AGENT_PROVIDER_IN}" = "none" ] && [ -n "${TASK_ID}" ] && [ -z "${INPUT_TYPE}" ] && [ -z "${INPUT_PATH}" ]; then
            ROUTE="declared-task-route"
            EXPECTED="Dispatch task_id through tools.scripts.task_dispatcher; capture stdout/stderr/exit; check expected artifacts; commit; fail closed if missing."
          elif [ "${AGENT_PROVIDER_IN}" != "none" ] && [ -n "${AGENT_PROVIDER_IN}" ]; then
            ROUTE="llm-collaboration(${AGENT_PROVIDER_IN})"
            EXPECTED="Run selected LLM provider path; do not process declared bundle or task unless separately routed."
          fi

          {
            echo "## StegVerse Core-Lite Intake — Route Summary"
            echo
            echo "| Field | Value |"
            echo "|---|---|"
            echo "| event | \`${EVENT}\` |"
            echo "| route | \`${ROUTE}\` |"
            echo "| expected behavior | ${EXPECTED} |"
            echo "| task_id | \`${TASK_ID:-[blank]}\` |"
            echo "| input_type | \`${INPUT_TYPE:-[blank]}\` |"
            echo "| input_path | \`${INPUT_PATH:-[blank]}\` |"
            echo "| stage | \`${STAGE}\` |"
            echo "| dry_run | \`${DRY_RUN:-false}\` |"
            echo "| agent_provider | \`${AGENT_PROVIDER_IN:-none}\` |"
            echo
            echo "### Quick Diagnosis"
            case "${ROUTE}" in
              declared-input-route)
                echo "- Declared input route selected. The run should show a bundle/input report and a persistence check."
                ;;
              declared-task-route)
                echo "- Declared task route selected. The run should show dispatcher exit code, expected output checks, and commit status."
                ;;
              llm-collaboration*)
                echo "- LLM collaboration route selected: \`${ROUTE}\`. LLM outputs are candidate evidence only."
                ;;
              default/no-op)
                echo "- No actionable route selected. Fill input_type/input_path for a bundle, task_id for a task, or agent_provider for LLM collaboration."
                ;;
            esac
          } >> "${GITHUB_STEP_SUMMARY}"

  declared-input-route:
    runs-on: ubuntu-latest
    if: ${{ github.event_name == 'workflow_dispatch' && inputs.agent_provider == 'none' && (inputs.input_type != '' || inputs.input_path != '') }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Validate declared input route
        run: |
          set -euo pipefail
          mkdir -p reports/current receipts/current tracking/ingestion_events
          INPUT_TYPE="${{ inputs.input_type }}"
          INPUT_PATH="${{ inputs.input_path }}"
          STAGE="${{ inputs.stage_override }}"
          if [ -z "${STAGE}" ]; then STAGE="SV002-M10"; fi

          {
            echo "## Declared Input Route — Preflight"
            echo
            echo "| Check | Result |"
            echo "|---|---|"
            echo "| input_type present | \`${INPUT_TYPE:+yes}${INPUT_TYPE:-no}\` |"
            echo "| input_path present | \`${INPUT_PATH:+yes}${INPUT_PATH:-no}\` |"
            echo "| stage | \`${STAGE}\` |"
          } >> "${GITHUB_STEP_SUMMARY}"

          if [ -z "${INPUT_TYPE}" ]; then
            echo "::error::Declared input route selected but input_type is blank."
            echo "- ❌ input_type is blank; set it to \`bundle\` (or another declared type)." >> "${GITHUB_STEP_SUMMARY}"
            exit 1
          fi
          if [ -z "${INPUT_PATH}" ]; then
            echo "::error::Declared input route selected but input_path is blank."
            echo "- ❌ input_path is blank; set it to the incoming ZIP path." >> "${GITHUB_STEP_SUMMARY}"
            exit 1
          fi
          if [ ! -f "${INPUT_PATH}" ]; then
            echo "::error::Declared input path does not exist: ${INPUT_PATH}"
            {
              echo "- ❌ input_path does not exist: \`${INPUT_PATH}\`."
              echo
              echo "### incoming/ listing"
              echo '```text'
              find incoming -maxdepth 2 -type f 2>/dev/null | sort || true
              echo '```'
            } >> "${GITHUB_STEP_SUMMARY}"
            exit 1
          fi
          echo "- ✅ Declared input preflight passed for \`${INPUT_PATH}\`." >> "${GITHUB_STEP_SUMMARY}"

      - name: Process declared input route
        run: |
          set -euo pipefail
          STAGE="${{ inputs.stage_override }}"
          if [ -z "${STAGE}" ]; then STAGE="SV002-M10"; fi
          DRY_RUN_ARG=""
          if [ "${{ inputs.dry_run }}" = "true" ]; then DRY_RUN_ARG="--dry-run"; fi

          echo "Declared input route selected."
          echo "input_type=${{ inputs.input_type }}"
          echo "input_path=${{ inputs.input_path }}"
          echo "stage=${STAGE}"
          echo "dry_run=${{ inputs.dry_run }}"
          echo "agent_provider=${{ inputs.agent_provider }}"

          python -m core_lite.multimodal.pipeline \
            --repo-root . \
            --input-type "${{ inputs.input_type }}" \
            --input-path "${{ inputs.input_path }}" \
            --entity "${STEGVERSE_ENTITY}" \
            --stage "${STAGE}" \
            ${DRY_RUN_ARG}

      - name: Summarize declared input result
        if: always()
        run: |
          set -euo pipefail
          {
            echo "## Declared Input Route — Result"
            echo
          } >> "${GITHUB_STEP_SUMMARY}"
          python - <<'PY' >> "${GITHUB_STEP_SUMMARY}"
          import json
          from pathlib import Path
          report = Path('reports/current/bundle_ingest_report.json')
          print('| Field | Value |')
          print('|---|---|')
          if report.exists():
              data = json.loads(report.read_text())
              print(f"| report | `reports/current/bundle_ingest_report.json` |")
              print(f"| input_path | `{data.get('input_path','')}` |")
              print(f"| status | `{data.get('status','')}` |")
              print(f"| decision | `{data.get('decision','')}` |")
              print(f"| installed_count | `{len(data.get('installed', []))}` |")
              print(f"| rejected_count | `{len(data.get('rejected', []))}` |")
              errs = data.get('errors', [])
              print(f"| errors | `{errs if errs else '[]'}` |")
          else:
              print('| report | `missing` |')
          print('\n### Key file presence')
          print('| Path | Exists |')
          print('|---|---|')
          for p in [
              'scripts/package_stegverse_governed_output.py',
              'docs/STEGVERSE_OUTPUT_AUTHORITY.md',
              'tools/tasks/task_catalog.json',
              'reports/current/bundle_ingest_report.json',
              'receipts/current/ingestion_receipt.jsonl',
              'tracking/ingestion_events/bundle_ingest_events.jsonl',
          ]:
              print(f"| `{p}` | `{'yes' if Path(p).exists() else 'no'}` |")
          PY

      - name: Commit declared input outputs
        if: ${{ inputs.dry_run != 'true' && success() }}
        run: |
          set -euo pipefail
          git config user.name "StegVerse-002 Declared Input Router"
          git config user.email "sv002-declared-input-router@stegverse"

          git add -A \
            .github/workflows/ \
            core_lite/ \
            scripts/ \
            schemas/ \
            examples/ \
            docs/ \
            tests/ \
            tools/ \
            config/ \
            machine/ \
            outputs/ \
            reports/current/ \
            receipts/current/ \
            tracking/ \
            dist/ \
            agent_history/ \
            vault_template/ || true

          if git diff --staged --quiet; then
            echo "No declared input changes to commit."
            echo "- ⚠️ No declared input changes were staged for commit." >> "${GITHUB_STEP_SUMMARY}"
          else
            git commit -m "sv002: process declared input route — ${{ inputs.input_type }} ${{ inputs.input_path }}"
            git push
            echo "- ✅ Declared input outputs committed and pushed." >> "${GITHUB_STEP_SUMMARY}"
          fi

      - name: Upload declared input evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: declared-input-route-evidence
          path: |
            reports/current/
            receipts/current/
            tracking/
            dist/
          if-no-files-found: warn

  declared-task-route:
    runs-on: ubuntu-latest
    if: ${{ github.event_name == 'workflow_dispatch' && inputs.task_id != '' && inputs.input_type == '' && inputs.input_path == '' && inputs.agent_provider == 'none' }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Python requirements
        run: |
          set -euo pipefail
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then
            pip install -r requirements.txt
          fi
          pip install -e . || true

      - name: Preflight declared task route
        id: preflight
        run: |
          set -euo pipefail
          mkdir -p reports/current receipts/current tracking outputs dist/run_artifacts agent_history
          TASK_ID="${{ inputs.task_id }}"
          STAGE="${{ inputs.stage_override }}"
          if [ -z "${STAGE}" ]; then STAGE="SV002-M10"; fi
          DRY_RUN="${{ inputs.dry_run }}"

          {
            echo "## Declared Task Route — Preflight"
            echo
            echo "| Field | Value |"
            echo "|---|---|"
            echo "| task_id | \`${TASK_ID}\` |"
            echo "| stage | \`${STAGE}\` |"
            echo "| dry_run | \`${DRY_RUN:-false}\` |"
            echo "| catalog | \`tools/tasks/task_catalog.json\` |"
          } >> "${GITHUB_STEP_SUMMARY}"

          if [ ! -f tools/tasks/task_catalog.json ]; then
            echo "::error::Task catalog missing: tools/tasks/task_catalog.json"
            echo "- ❌ Task catalog missing." >> "${GITHUB_STEP_SUMMARY}"
            exit 1
          fi

          CATALOG_HAS_TASK="$(python -c "import json,sys; c=json.load(open('tools/tasks/task_catalog.json')); ids=[t['task_id'] for t in c.get('tasks',[])]; sys.stdout.write('yes' if '${TASK_ID}' in ids else 'no')")"
          echo "catalog_has_task=${CATALOG_HAS_TASK}" >> "${GITHUB_OUTPUT}"
          if [ "${CATALOG_HAS_TASK}" != "yes" ]; then
            echo "::error::task_id not in catalog: ${TASK_ID}"
            echo "- ❌ task_id \`${TASK_ID}\` not in catalog." >> "${GITHUB_STEP_SUMMARY}"
            exit 1
          fi
          echo "- ✅ Preflight passed for task \`${TASK_ID}\`." >> "${GITHUB_STEP_SUMMARY}"
          echo "stage=${STAGE}" >> "${GITHUB_OUTPUT}"

      - name: Dispatch declared task
        id: dispatch
        run: |
          set +e
          TASK_ID="${{ inputs.task_id }}"
          STAGE="${{ steps.preflight.outputs.stage }}"
          DRY_RUN_ARG=""
          if [ "${{ inputs.dry_run }}" = "true" ]; then DRY_RUN_ARG="--dry-run"; fi

          python -m tools.scripts.task_dispatcher \
            --task-id "${TASK_ID}" \
            --task-catalog tools/tasks/task_catalog.json \
            --entity "${STEGVERSE_ENTITY}" \
            --stage "${STAGE}" \
            ${DRY_RUN_ARG} \
            >reports/current/task_dispatcher_result.json \
            2>reports/current/task_dispatcher_stderr.txt
          EXIT_CODE=$?
          echo "${EXIT_CODE}" > reports/current/task_dispatcher_exit_code.txt
          echo "exit_code=${EXIT_CODE}" >> "${GITHUB_OUTPUT}"
          exit 0

      - name: Evaluate expected output artifacts
        id: expected
        run: |
          set -euo pipefail
          TASK_ID="${{ inputs.task_id }}"
          DRY_RUN="${{ inputs.dry_run }}"
          EXIT_CODE="${{ steps.dispatch.outputs.exit_code }}"

          EXPECTED=""
          case "${TASK_ID}" in
            stegverse.output.package)
              EXPECTED="outputs/stegverse_output.md outputs/stegverse_output.json reports/current/stegverse_output_report.json receipts/current/stegverse_output_receipt.jsonl dist/run_artifacts/stegverse-governed-output.zip"
              ;;
          esac

          MISSING=""
          PRESENT=""
          if [ -n "${EXPECTED}" ]; then
            for f in ${EXPECTED}; do
              if [ -f "$f" ]; then
                PRESENT="${PRESENT} $f"
              else
                MISSING="${MISSING} $f"
              fi
            done
          fi

          echo "expected_declared=$([ -n "${EXPECTED}" ] && echo yes || echo no)" >> "${GITHUB_OUTPUT}"
          echo "missing=${MISSING# }" >> "${GITHUB_OUTPUT}"
          echo "present=${PRESENT# }" >> "${GITHUB_OUTPUT}"

          {
            echo "## Declared Task Route — Dispatch Result"
            echo
            echo "| Field | Value |"
            echo "|---|---|"
            echo "| task_id | \`${TASK_ID}\` |"
            echo "| dry_run | \`${DRY_RUN:-false}\` |"
            echo "| exit_code | \`${EXIT_CODE}\` |"
            echo "| stdout_path | \`reports/current/task_dispatcher_result.json\` |"
            echo "| stderr_path | \`reports/current/task_dispatcher_stderr.txt\` |"
            echo "| exit_code_path | \`reports/current/task_dispatcher_exit_code.txt\` |"
          } >> "${GITHUB_STEP_SUMMARY}"

          if [ -s reports/current/task_dispatcher_result.json ]; then
            {
              echo
              echo "<details><summary>dispatcher stdout (JSON)</summary>"
              echo
              echo '```json'
              cat reports/current/task_dispatcher_result.json
              echo
              echo '```'
              echo "</details>"
            } >> "${GITHUB_STEP_SUMMARY}"
          fi

          if [ -s reports/current/task_dispatcher_stderr.txt ]; then
            {
              echo
              echo "<details><summary>dispatcher stderr</summary>"
              echo
              echo '```text'
              tail -c 4000 reports/current/task_dispatcher_stderr.txt
              echo
              echo '```'
              echo "</details>"
            } >> "${GITHUB_STEP_SUMMARY}"
          fi

          if [ -n "${EXPECTED}" ]; then
            {
              echo
              echo "### Expected output checks"
              echo "| Path | Exists |"
              echo "|---|---|"
              for f in ${EXPECTED}; do
                if [ -f "$f" ]; then
                  echo "| \`$f\` | ✅ yes |"
                else
                  echo "| \`$f\` | ❌ no |"
                fi
              done
            } >> "${GITHUB_STEP_SUMMARY}"
          else
            echo -e "\n_No expected output artifacts declared for task \`${TASK_ID}\` in this workflow._" >> "${GITHUB_STEP_SUMMARY}"
          fi

      - name: Commit declared task outputs
        id: commit
        if: ${{ inputs.dry_run != 'true' }}
        run: |
          set -euo pipefail
          git config user.name "StegVerse-002 Declared Task Router"
          git config user.email "sv002-declared-task-router@stegverse"

          git add -A \
            outputs/ \
            reports/current/ \
            receipts/current/ \
            tracking/ \
            dist/ \
            agent_history/ || true

          if git diff --staged --quiet; then
            echo "commit_status=no_changes" >> "${GITHUB_OUTPUT}"
            echo "- ⚠️ No declared task outputs were staged for commit." >> "${GITHUB_STEP_SUMMARY}"
          else
            git commit -m "sv002: declared task route — ${{ inputs.task_id }}"
            if git push; then
              echo "commit_status=pushed" >> "${GITHUB_OUTPUT}"
              echo "- ✅ Declared task outputs committed and pushed." >> "${GITHUB_STEP_SUMMARY}"
            else
              echo "commit_status=push_failed" >> "${GITHUB_OUTPUT}"
              echo "- ❌ Declared task outputs committed but push failed." >> "${GITHUB_STEP_SUMMARY}"
              exit 1
            fi
          fi

      - name: Upload declared task evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: declared-task-route-evidence
          path: |
            outputs/
            reports/current/
            receipts/current/
            tracking/
            dist/
          if-no-files-found: warn

      - name: Fail closed on dispatcher error or missing expected artifacts
        run: |
          set -euo pipefail
          EXIT_CODE="${{ steps.dispatch.outputs.exit_code }}"
          MISSING="${{ steps.expected.outputs.missing }}"
          EXPECTED_DECLARED="${{ steps.expected.outputs.expected_declared }}"
          DRY_RUN="${{ inputs.dry_run }}"

          if [ "${EXIT_CODE}" != "0" ]; then
            echo "::error::Task dispatcher exited with code ${EXIT_CODE} for task ${{ inputs.task_id }}."
            echo "- ❌ Task dispatcher exited with code \`${EXIT_CODE}\`." >> "${GITHUB_STEP_SUMMARY}"
            exit 1
          fi

          if [ "${DRY_RUN}" != "true" ] && [ "${EXPECTED_DECLARED}" = "yes" ] && [ -n "${MISSING}" ]; then
            echo "::error::Declared task executed but expected StegVerse output artifacts are missing: ${MISSING}"
            {
              echo "- ❌ Declared task executed but expected StegVerse output artifacts are missing."
              echo
              echo "**Missing:**"
              for f in ${MISSING}; do
                echo "  - \`$f\`"
              done
            } >> "${GITHUB_STEP_SUMMARY}"
            exit 1
          fi

          echo "- ✅ Declared task route completed without fail-closed conditions." >> "${GITHUB_STEP_SUMMARY}"

  claude-agent:
    runs-on: ubuntu-latest
    if: ${{ github.event_name == 'push' || (github.event_name == 'workflow_dispatch' && (inputs.agent_provider == 'claude' || inputs.agent_provider == 'both')) }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run Claude Code propose-only task
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          mkdir -p outputs reports/current receipts/current

          if [ ! -f task.md ]; then
            cat > outputs/claude_response.md <<'EOF'
          # Claude Code — Skipped

          No task.md was present. No Claude proposal was generated.
          EOF
            exit 0
          fi

          if [ "${AGENT_PROVIDER}" != "claude" ] && [ "${AGENT_PROVIDER}" != "both" ]; then
            cat > outputs/claude_response.md <<EOF
          # Claude Code — Skipped

          AGENT_PROVIDER=${AGENT_PROVIDER}; Claude was not selected for this run.
          EOF
            exit 0
          fi

          if [ -z "${ANTHROPIC_API_KEY}" ]; then
            cat > outputs/claude_response.md <<'EOF'
          # Claude Code — Skipped

          ANTHROPIC_API_KEY is not configured. Claude proposal was not generated.
          EOF
            exit 0
          fi

          npm install -g @anthropic-ai/claude-code

          {
            echo "# Claude Code — Governed Collaboration Proposal"
            echo
            echo "Run timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
            echo
            echo "Governance mode: propose-only"
            echo
            echo "Capability version: ${GOVERNED_LLM_LLM_VERSION}"
            echo
            echo "Task source: task.md"
            echo
            echo "Directive: no broad authority is ever admissible under Transition Table, AE, or GCAT/BCAT enforcement."
            echo
            echo "---"
            echo
          } > outputs/claude_response.md

          claude -p \
            "$(cat task.md)" >> outputs/claude_response.md 2>&1 || true

          cat > reports/current/claude_task_summary.json <<JSON
          {
            "schema": "stegverse.claude_task_summary.v1",
            "version": "${GOVERNED_LLM_LLM_VERSION}",
            "provider": "claude",
            "status": "completed",
            "mode": "propose_only",
            "output_path": "outputs/claude_response.md",
            "authority": "candidate_evidence_only"
          }
          JSON

      - name: Upload Claude output
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: claude-response
          path: |
            outputs/claude_response.md
            reports/current/claude_task_summary.json
          if-no-files-found: warn

  openai-agent:
    runs-on: ubuntu-latest
    if: ${{ github.event_name == 'push' || (github.event_name == 'workflow_dispatch' && (inputs.agent_provider == 'openai' || inputs.agent_provider == 'both')) }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run OpenAI propose-only task
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          mkdir -p outputs reports/current receipts/current
          python scripts/openai_task.py

      - name: Upload OpenAI output
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: openai-response
          path: |
            outputs/chatgpt_response.md
            reports/current/openai_task_summary.json
            receipts/current/openai_task_receipt.jsonl
          if-no-files-found: warn

  merge-and-commit:
    runs-on: ubuntu-latest
    needs: [claude-agent, openai-agent]
    if: ${{ always() && (github.event_name == 'push' || (github.event_name == 'workflow_dispatch' && (inputs.agent_provider == 'openai' || inputs.agent_provider == 'claude' || inputs.agent_provider == 'both'))) }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Download Claude output
        uses: actions/download-artifact@v4
        continue-on-error: true
        with:
          name: claude-response
          path: .

      - name: Download OpenAI output
        uses: actions/download-artifact@v4
        continue-on-error: true
        with:
          name: openai-response
          path: .

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run deterministic synthesis
        run: |
          mkdir -p outputs reports/current receipts/current agent_history
          python scripts/merge_outputs.py

      - name: Compare agent outputs
        run: |
          python tools/agent_governance/agent_compare.py --fail-on-high

      - name: Enforce coordination boundary
        run: |
          python tools/agent_governance/enforce_agent_boundary.py \
            --allowed agent_policy/allowed_paths.json \
            --forbidden agent_policy/forbidden_paths.json \
            --report reports/current/agent_boundary_report.json \
            --receipt receipts/current/agent_boundary_receipt.jsonl

      - name: Record LLM-LLM coordination change
        run: |
          python tools/agent_governance/record_llm_change.py \
            --provider coordinator \
            --conversation current-workflow-run \
            --version "${GOVERNED_LLM_LLM_VERSION}" \
            --change-type coordination_run \
            --summary "Recorded governed LLM-LLM collaboration outputs, comparison evidence, no-broad-authority directive, and boundary enforcement." \
            --files outputs/thread.md reports/current/agent_coordination_report.json reports/current/agent_comparison_report.json reports/current/agent_boundary_report.json receipts/current/agent_coordination_receipt.jsonl receipts/current/agent_comparison_receipt.jsonl receipts/current/agent_boundary_receipt.jsonl

      - name: Package proposed-transition bundle
        run: |
          python scripts/package_transition_bundle.py

      - name: Commit governed coordination outputs
        run: |
          git config user.name "StegVerse-002 Agent Coordinator"
          git config user.email "sv002-agent-coordinator@stegverse"

          git add -A \
            outputs/ \
            reports/current/ \
            receipts/current/ \
            agent_history/ \
            dist/bundles/ || true

          git diff --staged --quiet || git commit -m "sv002: governed transition bundle v0.1.3 — $(head -1 task.md 2>/dev/null || echo no-task)"
          git push || true
```

### Key changes vs. `main`

1. **New `declared-task-route` job** between `declared-input-route` and `claude-agent`. Gated on `workflow_dispatch && task_id != '' && input_type == '' && input_path == '' && agent_provider == 'none'`. Checks out, installs deps, preflights catalog, dispatches via `python -m tools.scripts.task_dispatcher` capturing stdout → `reports/current/task_dispatcher_result.json`, stderr → `reports/current/task_dispatcher_stderr.txt`, exit code → `reports/current/task_dispatcher_exit_code.txt`. Writes full structured Actions summary (task_id, stage, dry_run, exit code, report paths, dispatcher JSON, stderr tail, expected output table, commit status). Commits `outputs/ reports/current/ receipts/current/ tracking/ dist/ agent_history/` on non-dry-run. Uploads single artifact `declared-task-route-evidence`. Final step **fails closed** when dispatcher exit ≠ 0 or any declared expected artifact is missing (message exactly: `Declared task executed but expected StegVerse output artifacts are missing.`).
2. **`workflow-summary` route detection corrected.** New ordering: push → declared-input → declared-task → llm-collaboration(provider) → default/no-op. Previous file evaluated `agent_provider != none` before checking inputs, which mis-labeled task-only runs. Adds the `declared-task-route` quick-diagnosis branch.
3. **`declared-input-route`, `claude-agent`, `openai-agent`, `merge-and-commit` unchanged** from `main`. Repair is strictly additive (one new job) + summary correction.

### Optional secondary file `docs/WORKFLOW_SUMMARY_DIAGNOSTICS.md`

Not required for function. Suggested content:

```markdown
# Workflow Summary Diagnostics — core-lite-intake.yml

## Routes
| Inputs | Selected route | Evidence |
|---|---|---|
| `input_type`+`input_path` set, `agent_provider=none` | `declared-input-route` | `reports/current/bundle_ingest_report.json`, installed paths committed |
| `task_id` set, `input_*` blank, `agent_provider=none` | `declared-task-route` | `reports/current/task_dispatcher_*`, expected output checks per task, evidence artifact `declared-task-route-evidence` |
| `agent_provider` in `openai/claude/both` | `claude-agent`/`openai-agent` then `merge-and-commit` | `outputs/claude_response.md`, `outputs/chatgpt_response.md`, `outputs/thread.md`, agent reports/receipts |
| push to `main` on listed paths | `llm-collaboration(push)` | same as above |
| otherwise | `default/no-op` | summary only |

## Expected outputs by task_id
- `stegverse.output.package`
  - `outputs/stegverse_output.md`
  - `outputs/stegverse_output.json`
  - `reports/current/stegverse_output_report.json`
  - `receipts/current/stegverse_output_receipt.jsonl`
  - `dist/run_artifacts/stegverse-governed-output.zip`
```

## Authority Boundaries

Does: proposes one bounded job + one summary correction; routes through existing dispatcher (which enforces `allowed_stages`/`forbidden_actions` and writes `receipts/current/task_receipt.jsonl`); captures candidate evidence; fails closed.

Does NOT: modify `README.md`, `task.md`, `CLAUDE.md`, `core_lite/`, `tools/`, `config/`, `tracking/`, `receipts/`, `dist/`, `machine/`; add/expose/rotate secrets; deploy or release; grant broad authority; prepare Rige enrollment or `Beta_Orionis`; bind LLM output as authoritative; commit anything in this run (propose-only).

## Receipts and Version History

Consult: `governance/directives/no_broad_authority.directive.json`, `agent_history/llm_changelog.jsonl` (append a `coordination_run` entry after operator placement), `agent_history/version_state.json` (capability version remains `0.1.3-gllm`; this is an in-version repair). After first successful non-dry-run `stegverse.output.package` dispatch, expect new entries in `receipts/current/task_receipt.jsonl` and `receipts/current/stegverse_output_receipt.jsonl`, plus the five declared artifacts.

## Risks & Dependencies

- `tools.scripts.task_dispatcher` imports `core_lite.receipts.append_receipt`; the job runs `pip install -e .` best-effort. If editable install fails in CI, dispatch fails closed with clear stderr (correct behavior — surfaces the gap instead of masking it).
- Expected outputs are hard-coded per task in the workflow's `case`. Adding a new task with expected outputs requires updating the workflow. Follow-up: extend `tools/tasks/task_catalog.json` with a `produces` array (out of scope here — that touches `tools/`).
- `git push` without retry: concurrent push fails closed. Operators may add a `concurrency:` group later.
- `set +e` around dispatch is necessary so downstream eval / summary / commit / upload / fail-closed steps all run; the final fail-closed step re-asserts exit code as the job's exit status, so coverage is preserved.
- No existing reports are deleted; current-run report files under `reports/current/` are overwritten as documented.

## Confidence

**High** on route topology, gating, fail-closed behavior, summary content — these match the spec line by line.

**Medium** on first-run CI executability of the dispatcher invocation due to `pip install -e .` resolution; if editable install fails, the job fails closed with clear stderr — a strict improvement over the silent-pass status quo.

**High** on directive compliance: no broad authority, no Stage-3 staging, no governed-path mutation, text-only delivery; operator placement is the act of admission.

---

**Summary**: Write to `outputs/claude_response.md` was not granted, so the full governed proposal — including the complete replacement YAML for `.github/workflows/core-lite-intake.yml` — is delivered inline above. The proposal adds one new `declared-task-route` job and corrects the `workflow-summary` route-ordering bug; all other jobs are preserved verbatim. Manual placement path is `.github/workflows/core-lite-intake.yml` on `main`.
