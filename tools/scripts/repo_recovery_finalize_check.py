#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def sha_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="SV002-M12 non-executing finalization authority check")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--plan", default="reports/current/repo_recovery_destination_plan.json")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    plan_path = (root / args.plan).resolve()
    reports = root / "reports" / "current"
    receipts = root / "receipts" / "current"
    reports.mkdir(parents=True, exist_ok=True)
    receipts.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings: list[str] = []
    plan = read_json(plan_path)

    if not plan:
        errors.append(f"destination plan missing or unreadable: {args.plan}")

    bundle_hash = plan.get("bundle_hash", "")
    proposed_destination = plan.get("proposed_destination_path", "")
    original_source = plan.get("original_source_path", "")

    if plan and plan.get("decision") != "PLAN_ONLY":
        errors.append("destination plan decision is not PLAN_ONLY")
    if plan and plan.get("execution_authority") != "none":
        errors.append("destination plan unexpectedly grants execution authority")
    if plan and plan.get("cleanup_authority") != "none":
        errors.append("destination plan unexpectedly grants cleanup authority")
    if plan and plan.get("bulk_authority") != "none":
        errors.append("destination plan unexpectedly grants bulk authority")
    if plan and plan.get("original_removal_status") != "NOT_AUTHORIZED":
        errors.append("destination plan unexpectedly authorizes original removal")
    if not proposed_destination:
        errors.append("proposed destination path missing")

    destination_exists = bool(proposed_destination and (root / proposed_destination).exists())
    original_exists = bool(original_source and (root / original_source).exists())

    if proposed_destination and ".." in Path(proposed_destination).parts:
        errors.append("proposed destination contains parent traversal")
    if proposed_destination.startswith("/"):
        errors.append("proposed destination is absolute")

    plan_receipts = read_jsonl(receipts / "repo_recovery_destination_plan_receipt.jsonl")
    matching_plan_receipts = [r for r in plan_receipts if r.get("bundle_hash") == bundle_hash and r.get("decision") == "PLAN_ONLY"]
    latest_plan_receipt = matching_plan_receipts[-1] if matching_plan_receipts else {}
    if plan and not latest_plan_receipt:
        errors.append("no PLAN_ONLY destination plan receipt found for bundle hash")

    finalization_status = "FINALIZATION_REVIEW_REQUIRED"
    if not errors:
        finalization_status = "FINALIZATION_ALLOWED_SINGLE_PROPOSAL_ONLY"

    report = {
        "schema": "stegverse.repo_recovery.finalization_check.v1",
        "generated_at": now(),
        "stage": "SV002-M12",
        "decision": "REVIEW_ONLY" if not errors else "FAIL_CLOSED",
        "finalization_status": finalization_status,
        "execution_authority": "none",
        "cleanup_authority": "none",
        "bulk_authority": "none",
        "original_removal_authority": "none",
        "bundle_hash": bundle_hash,
        "destination_plan_path": args.plan,
        "destination_plan_receipt_hash": latest_plan_receipt.get("plan_hash", ""),
        "original_source_path": original_source,
        "original_source_exists": original_exists,
        "proposed_destination_path": proposed_destination,
        "proposed_destination_exists": destination_exists,
        "guardrails": {
            "does_not_move_files": True,
            "does_not_delete_originals": True,
            "does_not_bulk_ingest": True,
            "does_not_grant_final_authority": True,
            "requires_future_explicit_finalize_one_receipt": True,
        },
        "errors": errors,
        "warnings": warnings,
    }

    report_path = reports / "repo_recovery_finalize_check.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    receipt = {
        "schema": "stegverse.repo_recovery.finalization_check_receipt.v1",
        "timestamp_utc": now(),
        "stage": "SV002-M12",
        "decision": report["decision"],
        "finalization_status": finalization_status,
        "bundle_hash": bundle_hash,
        "report_path": report_path.relative_to(root).as_posix(),
        "report_sha256": sha_file(report_path),
        "check_hash": sha_text(json.dumps(report, sort_keys=True)),
        "execution_authority": "none",
        "cleanup_authority": "none",
        "errors": errors,
    }
    with (receipts / "repo_recovery_finalize_check_receipt.jsonl").open("a") as f:
        f.write(json.dumps(receipt, sort_keys=True) + "\n")

    print(json.dumps({"decision": report["decision"], "finalization_status": finalization_status, "errors": errors, "report": receipt["report_path"]}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
