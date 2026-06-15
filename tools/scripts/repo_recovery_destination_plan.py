#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

DEFAULT_BUNDLE = "tracking/recovery_corrected/sv002_recovery_30d45378723de692_CHANGELOG.md.zip"


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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_bundle_manifest(bundle_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(bundle_path) as zf:
        return json.loads(zf.read("bundle_manifest.json"))


def read_recovery_manifest(bundle_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(bundle_path) as zf:
        return json.loads(zf.read("recovery_manifest.json"))


def main() -> int:
    ap = argparse.ArgumentParser(description="SV002-M12 non-executing recovery destination planner")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--bundle", default=DEFAULT_BUNDLE)
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    bundle_path = (root / args.bundle).resolve()
    reports = root / "reports" / "current"
    receipts = root / "receipts" / "current"
    reports.mkdir(parents=True, exist_ok=True)
    receipts.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings: list[str] = []

    if not bundle_path.exists():
        errors.append(f"bundle missing: {args.bundle}")
        bundle_hash = "sha256:missing"
        bundle_manifest: dict[str, Any] = {}
        recovery_manifest: dict[str, Any] = {}
    else:
        bundle_hash = sha_file(bundle_path)
        try:
            bundle_manifest = read_bundle_manifest(bundle_path)
        except Exception as exc:
            bundle_manifest = {}
            errors.append(f"bundle_manifest unreadable: {exc}")
        try:
            recovery_manifest = read_recovery_manifest(bundle_path)
        except Exception as exc:
            recovery_manifest = {}
            errors.append(f"recovery_manifest unreadable: {exc}")

    transition_receipts = read_jsonl(receipts / "transition_table_receipt.jsonl")
    cge_regression = read_jsonl(receipts / "cge_recovery_proof_regression_receipt.jsonl")

    matching_transition_receipts = [
        row for row in transition_receipts
        if row.get("bundle_hash") == bundle_hash
        and row.get("transition_class") == "evidence"
        and row.get("authority_class") == "evidence_only"
        and row.get("transition_table_decision") == "ALLOW"
        and row.get("cge_decision") == "ALLOW"
        and row.get("final_decision") == "ALLOW"
    ]
    latest_transition_receipt = matching_transition_receipts[-1] if matching_transition_receipts else {}

    matching_regression_receipts = [
        row for row in cge_regression
        if row.get("expected_bundle_hash") == bundle_hash and row.get("decision") == "ALLOW"
    ]
    latest_regression_receipt = matching_regression_receipts[-1] if matching_regression_receipts else {}

    if bundle_hash != "sha256:missing" and not latest_transition_receipt:
        errors.append("no ALLOW transition+CGE receipt found for bundle hash")
    if bundle_hash != "sha256:missing" and not latest_regression_receipt:
        errors.append("no ALLOW CGE regression guard receipt found for bundle hash")

    original_source = recovery_manifest.get("source_path") or recovery_manifest.get("original_path") or recovery_manifest.get("path") or ""
    recovery_id = recovery_manifest.get("recovery_id") or bundle_manifest.get("task_ref") or bundle_path.stem
    payload_members: list[str] = []
    if bundle_path.exists():
        try:
            with zipfile.ZipFile(bundle_path) as zf:
                payload_members = sorted(name for name in zf.namelist() if name.startswith("payload/") and not name.endswith("/"))
        except Exception as exc:
            warnings.append(f"payload member scan failed: {exc}")

    if not payload_members:
        warnings.append("no payload member found; destination remains review-only")

    proposed_destination = ""
    if original_source:
        proposed_destination = original_source
    elif payload_members:
        proposed_destination = payload_members[0].replace("payload/", "", 1)

    plan = {
        "schema": "stegverse.repo_recovery.destination_plan.v1",
        "generated_at": now(),
        "stage": "SV002-M12",
        "decision": "PLAN_ONLY" if not errors else "FAIL_CLOSED",
        "execution_authority": "none",
        "cleanup_authority": "none",
        "bulk_authority": "none",
        "bundle_path": args.bundle,
        "bundle_hash": bundle_hash,
        "recovery_id": recovery_id,
        "original_source_path": original_source,
        "payload_members": payload_members,
        "proposed_destination_path": proposed_destination,
        "destination_mapping_status": "PROPOSED_NOT_EXECUTABLE" if proposed_destination and not errors else "REVIEW_REQUIRED",
        "original_removal_status": "NOT_AUTHORIZED",
        "finalization_status": "PENDING_FINALIZATION_REVIEW",
        "m11_receipt_bindings": {
            "transition_receipt_hash": latest_transition_receipt.get("receipt_hash", ""),
            "transition_table_decision": latest_transition_receipt.get("transition_table_decision", ""),
            "cge_decision": latest_transition_receipt.get("cge_decision", ""),
            "final_decision": latest_transition_receipt.get("final_decision", ""),
            "cge_regression_decision": latest_regression_receipt.get("decision", ""),
        },
        "guardrails": {
            "does_not_move_files": True,
            "does_not_delete_originals": True,
            "does_not_bulk_ingest": True,
            "requires_m11_allow_receipts": True,
            "requires_future_finalization_receipt_before_action": True,
        },
        "errors": errors,
        "warnings": warnings,
    }

    report_path = reports / "repo_recovery_destination_plan.json"
    report_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    receipt = {
        "schema": "stegverse.repo_recovery.destination_plan_receipt.v1",
        "timestamp_utc": now(),
        "stage": "SV002-M12",
        "decision": plan["decision"],
        "bundle_hash": bundle_hash,
        "report_path": report_path.relative_to(root).as_posix(),
        "report_sha256": sha_file(report_path),
        "plan_hash": sha_text(json.dumps(plan, sort_keys=True)),
        "execution_authority": "none",
        "cleanup_authority": "none",
        "errors": errors,
    }
    with (receipts / "repo_recovery_destination_plan_receipt.jsonl").open("a") as f:
        f.write(json.dumps(receipt, sort_keys=True) + "\n")

    print(json.dumps({"decision": plan["decision"], "errors": errors, "report": receipt["report_path"]}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
