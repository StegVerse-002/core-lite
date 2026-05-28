# Claude Code — Governed Collaboration Proposal

Run timestamp: 2026-05-28T02:35:50Z

Governance mode: propose-only

Capability version: 0.1.3-gllm

Task source: task.md

Directive: no broad authority is ever admissible under Transition Table, AE, or GCAT/BCAT enforcement.

---

Permission to write `outputs/claude_response.md` was not granted. The proposal is fully drafted and ready to be written to `outputs/claude_response.md` — please approve the write (or run me with that path allowed) and I will commit the file. No other files would be touched, in keeping with the propose-only directive.

Summary of what the drafted proposal says (so nothing is lost if you'd rather act on it directly):

- **Diagnosis:** `.github/workflows/core-lite-intake.yml` has no job whose `if:` matches `agent_provider=none` + non-blank `task_id` + blank `input_type`/`input_path`. The `workflow-summary` step only *labels* a phantom "declared-task-route"; no job actually invokes `tools.scripts.task_dispatcher`. That is why a green run can occur without the five required files on `main`.
- **Proposed fix (text-only patch):** add one additive job `declared-task-route` after `declared-input-route`, gated by that exact input shape. The job: checks out, sets up Python 3.11, best-effort installs `requirements.txt`, runs `python -m tools.scripts.task_dispatcher --task-id … --task-catalog tools/tasks/task_catalog.json --entity "${STEGVERSE_ENTITY}" --stage "${STAGE}"`, captures stdout/stderr/exit-code under `reports/current/`, validates the five-file shape when `task_id=='stegverse.output.package'` (fails the workflow on any miss), commits only `outputs/ reports/current/ receipts/current/ dist/ tracking/ agent_history/` and pushes, then writes a step-summary table (route, task_id, command, exit code, per-file present/missing, commit status).
- **`if:` exclusivity** with the existing `declared-input-route` and provider jobs is preserved; no existing jobs or scripts are modified; no new permissions; no broad authority granted; provider outputs remain candidate-evidence-only.
