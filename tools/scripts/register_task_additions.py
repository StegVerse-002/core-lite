#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_GLOBS = [
    "tools/tasks/*_task.json",
    "tasks/task_catalog.*_addition.json",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def discover_additions(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    seen = set()
    for pattern in patterns:
        for path in sorted(Path(".").glob(pattern)):
            if path.is_file() and path not in seen:
                paths.append(path)
                seen.add(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Register declared task addition files into tools/tasks/task_catalog.json")
    parser.add_argument("--catalog", default="tools/tasks/task_catalog.json")
    parser.add_argument("--addition", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    report_path = Path("reports/current/task_addition_registration_report.json")
    receipt_path = Path("receipts/current/task_addition_registration_receipt.jsonl")

    if not catalog_path.exists():
        report = {
            "schema": "stegverse.task_addition_registration_report.v1",
            "decision": "FAIL_CLOSED",
            "basis": "task_catalog_missing",
            "catalog": str(catalog_path),
            "merged": [],
            "skipped": [],
            "errors": ["task_catalog_missing"],
        }
        write_json(report_path, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    catalog = load_json(catalog_path)
    catalog.setdefault("tasks", [])
    existing = {task.get("task_id") for task in catalog["tasks"]}

    additions = [Path(p) for p in args.addition] if args.addition else discover_additions(DEFAULT_GLOBS)
    merged: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    errors: list[str] = []

    for path in additions:
        try:
            item = load_json(path)
        except Exception as exc:
            errors.append(f"load_failed:{path}:{exc}")
            continue
        task_id = item.get("task_id")
        if not task_id:
            skipped.append({"path": str(path), "reason": "task_id_missing"})
            continue
        if task_id in existing:
            skipped.append({"path": str(path), "task_id": task_id, "reason": "already_registered"})
            continue
        catalog["tasks"].append(item)
        existing.add(task_id)
        merged.append({"path": str(path), "task_id": task_id})

    catalog["updated_utc"] = datetime.now(timezone.utc).isoformat()
    if not args.dry_run and merged:
        write_json(catalog_path, catalog)

    decision = "ALLOW" if not errors else "FAIL_CLOSED"
    report = {
        "schema": "stegverse.task_addition_registration_report.v1",
        "decision": decision,
        "basis": "task_additions_registered" if decision == "ALLOW" else "task_addition_registration_errors",
        "catalog": str(catalog_path),
        "dry_run": args.dry_run,
        "merged": merged,
        "skipped": skipped,
        "errors": errors,
        "task_count": len(catalog["tasks"]),
    }
    write_json(report_path, report)

    receipt = {
        "schema": "stegverse.task_addition_registration_receipt.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "SV002-M12",
        "gate": "task-addition-registration",
        "decision": decision,
        "basis": report["basis"],
        "merged_count": len(merged),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "report_path": str(report_path),
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with receipt_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, sort_keys=True) + "\n")

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if decision == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
