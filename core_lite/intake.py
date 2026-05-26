"""
core_lite.intake — Intake orchestrator for StegVerse-002.

Orchestrates the full intake run:
- CGE fingerprint generation
- Ingest pipeline (if inputs provided)
- Declared task execution (if task_id provided)
- Receipt chain
- Run summary and ingest report output

STOP condition:
    Core-Lite Intake succeeds with task_id blank and skip_tasks true
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core_lite.cge import CGEEngine, CGERequest, generate_cge_fingerprint
from core_lite.receipts import ReceiptRecorder, append_receipt

log = logging.getLogger("core_lite.intake")


class IntakeOrchestrator:

    def __init__(
        self,
        repo_root: Path,
        entity: str = "StegVerse-002",
        stage: str = "SV002-M5",
        skip_tasks: bool = True,
        task_id: str = "",
        dry_run: bool = False,
    ):
        self.repo_root = repo_root
        self.entity = entity
        self.stage = stage
        self.skip_tasks = skip_tasks
        self.task_id = task_id
        self.dry_run = dry_run

        self.receipts_path = repo_root / ".stegverse" / "receipts" / "core_lite_receipts.jsonl"
        self.recorder = ReceiptRecorder(self.receipts_path)
        self.cge = CGEEngine(repo_root=repo_root)

        self._started = datetime.now(timezone.utc).isoformat()

    def run(self) -> dict:
        log.info("Intake orchestrator: entity=%s stage=%s task_id=%s skip_tasks=%s",
                 self.entity, self.stage, self.task_id, self.skip_tasks)

        result = {
            "schema": "stegverse_core_lite_run_summary.v1",
            "entity": self.entity,
            "stage": self.stage,
            "task_id": self.task_id,
            "skip_tasks": self.skip_tasks,
            "started": self._started,
            "status": "unknown",
            "steps": [],
        }

        try:
            # Step 1 — CGE fingerprint
            fingerprint = generate_cge_fingerprint(
                actor=self.entity,
                stage=self.stage,
                action="intake",
                target_scope="core-lite",
            )
            result["steps"].append({"step": "cge_fingerprint", "status": "ok", "fingerprint": fingerprint})
            log.info("CGE fingerprint: %s", fingerprint)

            # Step 2 — CGE admissibility check
            cge_request = CGERequest(
                actor=self.entity,
                stage=self.stage,
                target_scope="core-lite",
                action="intake",
                input_type="text",
                privacy_class="private",
                allowed_use=["context", "report", "candidate_preparation"],
                forbidden_use=["training", "publication", "production_mutation"],
                stop_condition="Core-Lite Intake succeeds with task_id blank and skip_tasks true",
            )
            cge_result = self.cge.decide(cge_request)
            result["steps"].append({
                "step": "cge_admissibility",
                "status": "ok",
                "decision": cge_result.decision,
                "basis": cge_result.basis,
            })

            if cge_result.decision == "FAIL_CLOSED":
                raise RuntimeError(f"CGE FAIL_CLOSED: {cge_result.basis}")

            if cge_result.decision == "DENY":
                raise RuntimeError(f"CGE DENY: {cge_result.basis}")

            # Step 3 — Task handling
            if self.task_id and not self.skip_tasks:
                task_result = self._run_declared_task()
                result["steps"].append({"step": "declared_task", "status": task_result.get("status"), "task_id": self.task_id})
            else:
                result["steps"].append({"step": "declared_task", "status": "skipped",
                                         "reason": "skip_tasks=true or task_id blank"})

            # Step 4 — Ingest report
            ingest_report = self._generate_ingest_report(cge_result)
            ingest_path = self.repo_root / "reports" / "current" / "core_lite_ingest_report.json"
            ingest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(ingest_path, "w") as f:
                json.dump(ingest_report, f, indent=2)
            result["steps"].append({"step": "ingest_report", "status": "ok", "path": str(ingest_path)})

            # Step 5 — Receipt
            receipt = self.recorder.record(
                actor=self.entity,
                stage=self.stage,
                gate="core-lite-intake",
                task_id=self.task_id,
                action="intake",
                decision=cge_result.decision,
                basis="Intake orchestrator completed successfully",
                allowed_use=["context", "report", "candidate_preparation"],
                forbidden_use=["training", "publication", "production_mutation"],
                stop_condition="Core-Lite Intake succeeds with task_id blank and skip_tasks true",
                outputs=["core_lite_run_summary.json", "core_lite_ingest_report.json",
                         ".stegverse/cge_fingerprint.json"],
            )
            result["steps"].append({
                "step": "receipt",
                "status": "ok",
                "receipt_hash": receipt.receipt_hash,
            })

            result["status"] = "success"
            result["cge_decision"] = cge_result.decision
            result["receipt_hash"] = receipt.receipt_hash
            result["completed"] = datetime.now(timezone.utc).isoformat()
            result["stop_condition_met"] = (self.task_id == "" and self.skip_tasks)

            log.info("Intake COMPLETE — status=success stop_condition_met=%s",
                     result["stop_condition_met"])

        except Exception as exc:
            log.error("Intake FAILED: %s", exc, exc_info=True)
            result["status"] = "failure"
            result["error"] = str(exc)
            self.recorder.record(
                actor=self.entity,
                stage=self.stage,
                gate="core-lite-intake",
                action="intake",
                decision="FAIL_CLOSED",
                basis=f"Intake exception: {exc}",
            )

        return result

    def _run_declared_task(self) -> dict:
        from tools.scripts.task_dispatcher import TaskDispatcher
        dispatcher = TaskDispatcher(
            task_id=self.task_id,
            catalog_path=self.repo_root / "tools" / "tasks" / "task_catalog.json",
            entity=self.entity,
            stage=self.stage,
            dry_run=self.dry_run,
        )
        return dispatcher.run()

    def _generate_ingest_report(self, cge_result) -> dict:
        return {
            "schema": "stegverse_core_lite_ingest_report.v1",
            "entity": self.entity,
            "stage": self.stage,
            "task_id": self.task_id,
            "skip_tasks": self.skip_tasks,
            "started": self._started,
            "cge_decision": cge_result.decision,
            "cge_basis": cge_result.basis,
            "cge_fingerprint": cge_result.fingerprint,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
