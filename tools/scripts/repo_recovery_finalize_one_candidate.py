#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_BUNDLE = "tracking/recovery_corrected/sv002_recovery_30d45378723de692_CHANGELOG.md.zip"
EXPECTED_BUNDLE_HASH = "sha256:17f224bca33c1a1cff197b1f06f76058f9d61fb0e399c3b034070137bec52b3e"
EXPECTED_DESTINATION = "CHANGELOG.md"
EXPECTED_SOURCE = "CHANGELOG.md"


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


def latest_matching(rows: list[dict[str, Any]], **expected: Any) -> dict[str, Any]:
    matches = []
    for row in rows:
        if all(row.get(k) == v for k, v in expected.items()):
            matches.append(row)
    return matches[-1] if matches else {}


def main() -> int:
    ap = argparse.ArgumentParser(description="SV002-M13 non-executing finalize-one candidate proposal")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--bundle", default=EXPECTED_BUNDLE)
    ap.add_argument("--destination", default=EXPECTED_DESTINATION)
    ap.add_argument("--source", default=EXPECTED_SOURCE)
    ap.add_argument("--replacement-requested", action="store_true")
    ap.add_argument("--original-removal-requested", action="store_true")
    ap.add_argument("--bulk-requested", action="store_true")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    reports = root / "reports" / "current"
    receipts = root / "receipts" / "current"
    reports.mkdir(parents=True, exist_ok=True)
    receipts.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings: list[str] = []

    bundle_path = (root / args.bundle).resolve()
    destination_path = (root / args.destination).resolve()
    source_path = (root / args.source).resolve()

    if args.bundle != EXPECTED_BUNDLE:
        errors.append("bundle path is not the first allowed M13 candidate bundle")
    if args.destination != EXPECTED_DESTINATION:
        errors.append("destination path is not the first allowed M13 candidate destination")
    if args.source != EXPECTED_SOURCE:
        errors.append("source path is not the first allowed M13 candidate source")
    if args.bulk_requested:
        errors.append("bulk finalization requested; M13 candidate is single-bundle only")
    if args.original_removal_requested:
        errors.append("original removal requested; not authorized in M13 candidate")
    if args.replacement_requested:
        warnings.append("replacement requested; candidate remains proposal-only and non-executing")

    if not bundle_path.exists():
        errors.append(f"bundle missing: {args.bundle}")
        bundle_hash = "sha256:missing"
    else:
        bundle_hash = sha_file(bundle_path)
        if bundle_hash != EXPECTED_BUNDLE_HASH:
            errors.append("bundle hash does not match expected first candidate hash")

    if ".." in Path(args.destination).parts:
        errors.append("destination contains parent traversal")
    if Path(args.destination).is_absolute():
        errors.append("destination is absolute")

    destination_exists = destination_path.exists()
    source_exists = source_path.exists()
    destination_hash = sha_file(destination_path) if destination_exists and destination_path.is_file() else ""
    source_hash = sha_file(source_path) if source_exists and source_path.is_file() else ""

    destination_plan = read_json(reports / "repo_recovery_destination_plan.json")
    finalize_check = read_json(reports / "repo_recovery_finalize_check.json")

    if destination_plan.get("decision") != "PLAN_ONLY":
        errors.append("M12 destination plan is missing or not PLAN_ONLY")
    if destination_plan.get("bundle_hash") != EXPECTED_BUNDLE_HASH:
        errors.append("M12 destination plan bundle hash mismatch")
    if destination_plan.get("proposed_destination_path") != EXPECTED_DESTINATION:
        errors.append("M12 destination plan destination mismatch")

    if finalize_check.get("decision") != "REVIEW_ONLY":
        errors.append("M12 finalization check is missing or not REVIEW_ONLY")
    if finalize_check.get("finalization_status") != "FINALIZATION_ALLOWED_SINGLE_PROPOSAL_ONLY":
        errors.append("M12 finalization check does not allow single proposal review")
    if finalize_check.get("execution_authority") != "none":
        errors.append("M12 finalization check unexpectedly grants execution authority")
    if finalize_check.get("cleanup_authority") != "none":
        errors.append("M12 finalization check unexpectedly grants cleanup authority")
    if finalize_check.get("original_removal_authority") != "none":
        errors.append("M12 finalization check unexpectedly grants original-removal authority")

    transition_receipt = latest_matching(
        read_jsonl(receipts / "transition_table_receipt.jsonl"),
        bundle_hash=EXPECTED_BUNDLE_HASH,
        transition_table_decision="ALLOW",
        cge_decision="ALLOW",
        final_decision="ALLOW",
    )
    if not transition_receipt:
        errors.append("M11 transition+CGE ALLOW receipt missing")

    regression_receipt = latest_matching(
        read_jsonl(receipts / "cge_recovery_proof_regression_receipt.jsonl"),
        expected_bundle_hash=EXPECTED_BUNDLE_HASH,
        decision="ALLOW",
    )
    if not regression_receipt:
        errors.append("M11 CGE regression ALLOW receipt missing")

    proposal_status = "FAIL_CLOSED" if errors else "FINALIZE_ONE_PROPOSED_REVIEW_ONLY"
    report = {
        "schema": "stegverse.repo_recovery.finalize_one_candidate.v1",
        "generated_at": now(),
        "stage": "SV002-M13",
        "decision": proposal_status,
        "execution_authority": "none",
        "cleanup_authority": "none",
        "bulk_authority": "none",
        "original_removal_authority": "none",
        "mutation_performed": False,
        "bundle_path": args.bundle,
        "bundle_hash": bundle_hash,
        "destination_path": args.destination,
        "destination_exists": destination_exists,
        "destination_hash_before": destination_hash,
        "source_path": args.source,
        "source_exists": source_exists,
        "source_hash_before": source_hash,
        "operator_intent_defaults": {
            "replacement_requested": bool(args.replacement_requested),
            "original_removal_requested": bool(args.original_removal_requested),
            "bulk_requested": bool(args.bulk_requested),
            "rollback_required": True,
        },
        "m11_receipt_bindings": {
            "transition_receipt_hash": transition_receipt.get("receipt_hash", ""),
            "cge_regression_report_hash": regression_receipt.get("report_sha256", ""),
        },
        "m12_receipt_bindings": {
            "destination_plan_decision": destination_plan.get("decision", ""),
            "finalization_check_decision": finalize_check.get("decision", ""),
            "finalization_status": finalize_check.get("finalization_status", ""),
        },
        "guardrails": {
            "proposal_only": True,
            "does_not_move_files": True,
            "does_not_delete_originals": True,
            "does_not_bulk_ingest": True,
            "does_not_replace_destination": True,
            "requires_future_execution_lane": True,
            "requires_future_post_finalization_verification": True,
        },
        "errors": errors,
        "warnings": warnings,
    }

    report_path = reports / "repo_recovery_finalize_one_candidate.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    receipt = {
        "schema": "stegverse.repo_recovery.finalize_one_candidate_receipt.v1",
        "timestamp_utc": now(),
        "stage": "SV002-M13",
        "decision": proposal_status,
        "bundle_hash": bundle_hash,
        "report_path": report_path.relative_to(root).as_posix(),
        "report_sha256": sha_file(report_path),
        "proposal_hash": sha_text(json.dumps(report, sort_keys=True)),
        "execution_authority": "none",
        "cleanup_authority": "none",
        "mutation_performed": False,
        "errors": errors,
    }
    with (receipts / "repo_recovery_finalize_one_candidate_receipt.jsonl").open("a") as f:
        f.write(json.dumps(receipt, sort_keys=True) + "\n")

    print(json.dumps({"decision": proposal_status, "errors": errors, "report": receipt["report_path"]}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
