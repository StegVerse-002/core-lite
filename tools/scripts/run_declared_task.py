#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

TASK_DIRS = [Path("tools/tasks")]
REPORT_PATH = Path("reports/current/declared_task_dispatch_report.json")
RECEIPT_PATH = Path("receipts/current/declared_task_dispatch_receipt.jsonl")


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def iter_task_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for task_dir in TASK_DIRS:
        directory = root / task_dir
        if directory.exists():
            out.extend(sorted(directory.glob("*.json")))
    return out


def catalog_tasks(root: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for path in iter_task_files(root):
        data = load_json(path)
        if "tasks" in data and isinstance(data["tasks"], list):
            for task in data["tasks"]:
                if isinstance(task, dict):
                    tasks.append({**task, "_source_path": path.as_posix()})
        elif "task_id" in data:
            tasks.append({**data, "_source_path": path.as_posix()})
    return tasks


def find_task(root: Path, task_id: str) -> dict[str, Any]:
    matches = [task for task in catalog_tasks(root) if task.get("task_id") == task_id]
    if not matches:
        raise KeyError(f"Unknown task_id: {task_id}")
    if len(matches) > 1:
        raise ValueError(f"Duplicate task_id declarations: {task_id}")
    return matches[0]


def write_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a declared StegVerse task by task_id.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--stage", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    task_id = args.task_id.strip()
    report: dict[str, Any] = {
        "schema": "stegverse.declared_task_dispatch_report.v1",
        "generated_at": now(),
        "repo_root": root.as_posix(),
        "task_id": task_id,
        "stage": args.stage,
        "dry_run": bool(args.dry_run),
        "result": "FAIL_CLOSED",
        "exit_code": 2,
        "mutation_count": 0,
    }

    try:
        task = find_task(root, task_id)
        report["task"] = {
            "source_path": task.get("_source_path"),
            "authority": task.get("authority"),
            "transition_class": task.get("transition_class"),
            "expected_outputs": task.get("expected_outputs", []),
            "governance": task.get("governance", {}),
        }
        command = str(task.get("command") or "").strip()
        if not command:
            raise ValueError(f"Task has no command: {task_id}")
        if args.dry_run:
            report["result"] = "DECLARED_TASK_DRY_RUN"
            report["exit_code"] = 0
            report["command"] = command
        else:
            completed = subprocess.run(command, cwd=root, shell=True, text=True)
            report["command"] = command
            report["exit_code"] = int(completed.returncode)
            report["result"] = "DECLARED_TASK_COMPLETED" if completed.returncode == 0 else "FAIL_CLOSED"
    except Exception as exc:
        report["error"] = str(exc)
        report["result"] = "FAIL_CLOSED"
        report["exit_code"] = 2

    (root / REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_PATH).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_jsonl(root / RECEIPT_PATH, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
