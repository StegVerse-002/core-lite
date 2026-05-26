"""
tools.scripts.task_dispatcher — Declared task dispatcher for StegVerse-002.

All workflow task_id inputs route through here.
Tasks are defined in tools/tasks/task_catalog.json.
No new workflow files are needed for new tasks.
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from core_lite.receipts import append_receipt

log = logging.getLogger("tools.task_dispatcher")


class TaskDispatcher:

    def __init__(
        self,
        task_id: str,
        catalog_path: Path,
        entity: str = "StegVerse-002",
        stage: str = "SV002-M5",
        dry_run: bool = False,
    ):
        self.task_id = task_id
        self.catalog_path = Path(catalog_path)
        self.entity = entity
        self.stage = stage
        self.dry_run = dry_run

    def run(self) -> dict:
        catalog = self._load_catalog()

        if self.task_id not in catalog:
            log.error("Unknown task_id: %s", self.task_id)
            append_receipt(
                "receipts/current/task_receipt.jsonl",
                actor=self.entity,
                stage=self.stage,
                gate="task_dispatcher",
                task_id=self.task_id,
                decision="DENY",
                basis=f"task_id {self.task_id} not in catalog",
            )
            return {"status": "deny", "reason": f"task_id {self.task_id} not in catalog"}

        task = catalog[self.task_id]
        log.info("Dispatching task: %s — %s", self.task_id, task.get("description", ""))

        # Validate stage
        allowed_stages = task.get("allowed_stages", [])
        if allowed_stages and self.stage not in allowed_stages:
            return {
                "status": "deny",
                "reason": f"Stage {self.stage} not in allowed_stages for {self.task_id}",
            }

        # Check forbidden actions
        forbidden = task.get("forbidden_actions", [])
        action = task.get("action", "run")
        if action in forbidden:
            return {"status": "deny", "reason": f"action {action} is forbidden for {self.task_id}"}

        if self.dry_run:
            log.info("DRY RUN — would execute: %s", task.get("command", ""))
            return {"status": "dry_run", "task_id": self.task_id, "command": task.get("command")}

        # Execute
        command = task.get("command", "")
        if not command:
            return {"status": "fail", "reason": "No command defined for task"}

        result = self._execute(command, task)

        # Receipt
        decision = "ALLOW" if result["returncode"] == 0 else "FAIL_CLOSED"
        append_receipt(
            "receipts/current/task_receipt.jsonl",
            actor=self.entity,
            stage=self.stage,
            gate="task_dispatcher",
            task_id=self.task_id,
            action=action,
            decision=decision,
            basis=f"Task exit code: {result['returncode']}",
            stop_condition=task.get("stop_condition", ""),
        )

        return {
            "status": "success" if result["returncode"] == 0 else "failure",
            "task_id": self.task_id,
            "returncode": result["returncode"],
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
        }

    def _load_catalog(self) -> dict:
        if not self.catalog_path.exists():
            log.warning("Task catalog not found: %s", self.catalog_path)
            return {}
        with open(self.catalog_path) as f:
            data = json.load(f)
        return {t["task_id"]: t for t in data.get("tasks", [])}

    def _execute(self, command: str, task: dict) -> dict:
        timeout = task.get("timeout_seconds", 300)
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "returncode": proc.returncode,
                "stdout": proc.stdout[-4000:] if proc.stdout else "",
                "stderr": proc.stderr[-2000:] if proc.stderr else "",
            }
        except subprocess.TimeoutExpired:
            return {"returncode": 1, "stdout": "", "stderr": f"Timeout after {timeout}s"}
        except Exception as e:
            return {"returncode": 1, "stdout": "", "stderr": str(e)}


def main():
    parser = argparse.ArgumentParser(prog="tools.scripts.task_dispatcher")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--task-catalog", default="tools/tasks/task_catalog.json")
    parser.add_argument("--entity", default="StegVerse-002")
    parser.add_argument("--stage", default="SV002-M5")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    dispatcher = TaskDispatcher(
        task_id=args.task_id,
        catalog_path=Path(args.task_catalog),
        entity=args.entity,
        stage=args.stage,
        dry_run=args.dry_run,
    )
    result = dispatcher.run()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") in ("success", "dry_run") else 1)


if __name__ == "__main__":
    main()
