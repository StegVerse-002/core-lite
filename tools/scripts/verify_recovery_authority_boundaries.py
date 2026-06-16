#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_BUNDLE_HASH = "sha256:17f224bca33c1a1cff197b1f06f76058f9d61fb0e399c3b034070137bec52b3e"
EXPECTED_DESTINATION_HASH = "sha256:30d45378723de6921247377dd1bf79ec1f0dbd405237b4a33b222f11ed1c019d"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def read_last_jsonl(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows[-1] if rows else {}


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def check_none_authority(obj: dict[str, Any], errors: list[str], label: str) -> None:
    for key in ["execution_authority", "cleanup_authority", "bulk_authority", "original_removal_authority"]:
        if key in obj:
            require(obj.get(key) == "none", errors, f"{label}.{key} is not none")


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify M11-M13 recovery/finalization authority boundaries")
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    reports = root / "reports" / "current"
    receipts = root / "receipts" / "current"
    reports.mkdir(parents=True, exist_ok=True)
    receipts.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings: list[str] = []

    destination_plan = read_json(reports / "repo_recovery_destination_plan.json")
    finalize_check = read_json(reports / "repo_recovery_finalize_check.json")
    finalize_candidate = read_json(reports / "repo_recovery_finalize_one_candidate.json")

    destination_plan_receipt = read_last_jsonl(receipts / "repo_recovery_destination_plan_receipt.jsonl")
    finalize_check_receipt = read_last_jsonl(receipts / "repo_recovery_finalize_check_receipt.jsonl")
    finalize_candidate_receipt = read_last_jsonl(receipts / "repo_recovery_finalize_one_candidate_receipt.jsonl")

    require(bool(destination_plan), errors, "destination plan report missing")
    require(bool(finalize_check), errors, "finalization check report missing")
    require(bool(finalize_candidate), errors, "finalize-one candidate report missing")
    require(bool(destination_plan_receipt), errors, "destination plan receipt missing")
    require(bool(finalize_check_receipt), errors, "finalization check receipt missing")
    require(bool(finalize_candidate_receipt), errors, "finalize-one candidate receipt missing")

    if destination_plan:
        require(destination_plan.get("decision") == "PLAN_ONLY", errors, "destination plan decision drifted from PLAN_ONLY")
        require(destination_plan.get("destination_mapping_status") == "PROPOSED_NOT_EXECUTABLE", errors, "destination plan mapping is executable")
        require(destination_plan.get("original_removal_status") == "NOT_AUTHORIZED", errors, "destination plan authorizes original removal")
        require(destination_plan.get("bundle_hash") == EXPECTED_BUNDLE_HASH, errors, "destination plan bundle hash mismatch")
        check_none_authority(destination_plan, errors, "destination_plan")
        guard = destination_plan.get("guardrails", {})
        for key in ["does_not_bulk_ingest", "does_not_delete_originals", "does_not_move_files", "requires_future_finalization_receipt_before_action", "requires_m11_allow_receipts"]:
            require(guard.get(key) is True, errors, f"destination_plan guardrail missing: {key}")

    if finalize_check:
        require(finalize_check.get("decision") == "REVIEW_ONLY", errors, "finalization check decision drifted from REVIEW_ONLY")
        require(finalize_check.get("finalization_status") == "FINALIZATION_ALLOWED_SINGLE_PROPOSAL_ONLY", errors, "finalization check status drifted")
        require(finalize_check.get("bundle_hash") == EXPECTED_BUNDLE_HASH, errors, "finalization check bundle hash mismatch")
        check_none_authority(finalize_check, errors, "finalize_check")
        require(finalize_check.get("original_removal_authority") == "none", errors, "finalization check original removal authority drifted")
        guard = finalize_check.get("guardrails", {})
        for key in ["does_not_move_files", "does_not_delete_originals", "does_not_bulk_ingest", "does_not_grant_final_authority", "requires_future_explicit_finalize_one_receipt"]:
            require(guard.get(key) is True, errors, f"finalize_check guardrail missing: {key}")

    if finalize_candidate:
        require(finalize_candidate.get("decision") == "FINALIZE_ONE_PROPOSED_REVIEW_ONLY", errors, "finalize-one candidate decision drifted")
        require(finalize_candidate.get("mutation_performed") is False, errors, "finalize-one candidate performed mutation")
        require(finalize_candidate.get("bundle_hash") == EXPECTED_BUNDLE_HASH, errors, "finalize-one candidate bundle hash mismatch")
        require(finalize_candidate.get("destination_hash_before") == EXPECTED_DESTINATION_HASH, errors, "destination pre-mutation hash mismatch")
        require(finalize_candidate.get("source_hash_before") == EXPECTED_DESTINATION_HASH, errors, "source pre-mutation hash mismatch")
        check_none_authority(finalize_candidate, errors, "finalize_candidate")
        require(finalize_candidate.get("original_removal_authority") == "none", errors, "finalize candidate original removal authority drifted")
        guard = finalize_candidate.get("guardrails", {})
        for key in ["proposal_only", "does_not_move_files", "does_not_delete_originals", "does_not_bulk_ingest", "does_not_replace_destination", "requires_future_execution_lane", "requires_future_post_finalization_verification"]:
            require(guard.get(key) is True, errors, f"finalize_candidate guardrail missing: {key}")
        defaults = finalize_candidate.get("operator_intent_defaults", {})
        require(defaults.get("bulk_requested") is False, errors, "bulk requested default drifted")
        require(defaults.get("original_removal_requested") is False, errors, "original removal requested default drifted")
        require(defaults.get("replacement_requested") is False, errors, "replacement requested default drifted")
        require(defaults.get("rollback_required") is True, errors, "rollback required default drifted")

    if finalize_candidate_receipt:
        require(finalize_candidate_receipt.get("mutation_performed") is False, errors, "finalize-one receipt says mutation performed")
        require(finalize_candidate_receipt.get("execution_authority") == "none", errors, "finalize-one receipt execution authority drifted")
        require(finalize_candidate_receipt.get("cleanup_authority") == "none", errors, "finalize-one receipt cleanup authority drifted")

    report = {
        "schema": "stegverse.recovery_authority_boundary_regression.v1",
        "generated_at": now(),
        "stage_scope": "SV002-M11_TO_M13",
        "decision": "ALLOW" if not errors else "FAIL_CLOSED",
        "expected_bundle_hash": EXPECTED_BUNDLE_HASH,
        "expected_destination_hash": EXPECTED_DESTINATION_HASH,
        "checked_reports": [
            "reports/current/repo_recovery_destination_plan.json",
            "reports/current/repo_recovery_finalize_check.json",
            "reports/current/repo_recovery_finalize_one_candidate.json",
        ],
        "checked_receipts": [
            "receipts/current/repo_recovery_destination_plan_receipt.jsonl",
            "receipts/current/repo_recovery_finalize_check_receipt.jsonl",
            "receipts/current/repo_recovery_finalize_one_candidate_receipt.jsonl",
        ],
        "authority_boundary": {
            "execution_authority": "none",
            "cleanup_authority": "none",
            "bulk_authority": "none",
            "replacement_authority": "none",
            "original_removal_authority": "none",
            "mutation_performed": False,
        },
        "errors": errors,
        "warnings": warnings,
    }

    report_path = reports / "recovery_authority_boundary_regression.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    receipt = {
        "schema": "stegverse.recovery_authority_boundary_regression_receipt.v1",
        "timestamp_utc": now(),
        "stage_scope": "SV002-M11_TO_M13",
        "decision": report["decision"],
        "report_path": report_path.relative_to(root).as_posix(),
        "report_sha256": sha_file(report_path),
        "errors": errors,
    }
    with (receipts / "recovery_authority_boundary_regression_receipt.jsonl").open("a") as f:
        f.write(json.dumps(receipt, sort_keys=True) + "\n")

    print(json.dumps({"decision": report["decision"], "errors": errors, "report": receipt["report_path"]}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
