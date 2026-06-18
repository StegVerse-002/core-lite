#!/usr/bin/env python3
"""
SV002-M14 finalize-one execution preflight.

Design goal:
  Validate readiness for a future finalize-one execution lane without
  moving, deleting, replacing, cleaning, or otherwise mutating repository state.

Decision set:
  EXECUTION_PREFLIGHT_REVIEW_ONLY
  FAIL_CLOSED
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

EXPECTED_BUNDLE_PATH = "tracking/recovery_corrected/sv002_recovery_30d45378723de692_CHANGELOG.md.zip"
EXPECTED_BUNDLE_HASH = "sha256:17f224bca33c1a1cff197b1f06f76058f9d61fb0e399c3b034070137bec52b3e"
EXPECTED_CHANGELOG_HASH = "sha256:30d45378723de6921247377dd1bf79ec1f0dbd405237b4a33b222f11ed1c019d"

REQUIRED_REPORTS = {
    "m12_destination_plan": "reports/current/repo_recovery_destination_plan.json",
    "m12_finalize_check": "reports/current/repo_recovery_finalize_check.json",
    "m13_finalize_one_candidate": "reports/current/repo_recovery_finalize_one_candidate.json",
    "m11_to_m13_authority_boundary": "reports/current/recovery_authority_boundary_regression.json",
}

REQUIRED_RECEIPTS = {
    "m12_destination_plan": "receipts/current/repo_recovery_destination_plan_receipt.jsonl",
    "m12_finalize_check": "receipts/current/repo_recovery_finalize_check_receipt.jsonl",
    "m13_finalize_one_candidate": "receipts/current/repo_recovery_finalize_one_candidate_receipt.jsonl",
    "m11_to_m13_authority_boundary": "receipts/current/recovery_authority_boundary_regression_receipt.jsonl",
}

REQUIRED_DOCS = {
    "m14_design": "docs/recovery/SV002_M14_FINALIZE_ONE_EXECUTION_AUTHORITY_DESIGN.md",
    "m11_to_m13_non_execution_boundary": "docs/recovery/SV002_M11_TO_M13_NON_EXECUTION_BOUNDARY.md",
    "m11_to_m13_activation": "docs/recovery/SV002_M11_TO_M13_ACTIVATION_SUMMARY.md",
    "m11_to_m13_proof_map": "docs/recovery/SV002_M11_TO_M13_RECOVERY_FINALIZATION_PROOF_MAP.md",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def latest_jsonl(path: Path) -> Dict[str, Any]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"receipt file is empty: {path}")
    return json.loads(lines[-1])


def add_error(errors: List[str], code: str, detail: str) -> None:
    errors.append(f"{code}: {detail}")


def exists_check(repo_root: Path, mapping: Dict[str, str], errors: List[str]) -> Dict[str, bool]:
    result: Dict[str, bool] = {}
    for key, rel in mapping.items():
        path = repo_root / rel
        present = path.exists()
        result[key] = present
        if not present:
            add_error(errors, "MISSING_REQUIRED_ARTIFACT", rel)
    return result


def check_equals(errors: List[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        add_error(errors, "UNEXPECTED_VALUE", f"{label}: expected {expected!r}, got {actual!r}")


def check_none_authority(errors: List[str], report_name: str, data: Dict[str, Any]) -> None:
    candidates = [data]
    if isinstance(data.get("authority_boundary"), dict):
        candidates.append(data["authority_boundary"])
    if isinstance(data.get("guardrails"), dict):
        candidates.append(data["guardrails"])

    authority_keys = [
        "execution_authority",
        "cleanup_authority",
        "bulk_authority",
        "replacement_authority",
        "original_removal_authority",
    ]
    for obj in candidates:
        for key in authority_keys:
            if key in obj and obj[key] not in ("none", False, None):
                add_error(errors, "AUTHORITY_ESCALATION", f"{report_name}.{key}={obj[key]!r}")

    for obj in candidates:
        if "mutation_performed" in obj and obj["mutation_performed"] is not False:
            add_error(errors, "MUTATION_ALREADY_PERFORMED", f"{report_name}.mutation_performed={obj['mutation_performed']!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--report-dir", default="reports/current")
    parser.add_argument("--receipt-dir", default="receipts/current")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    report_dir = repo_root / args.report_dir
    receipt_dir = repo_root / args.receipt_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    receipt_dir.mkdir(parents=True, exist_ok=True)

    errors: List[str] = []
    warnings: List[str] = []

    report_presence = exists_check(repo_root, REQUIRED_REPORTS, errors)
    receipt_presence = exists_check(repo_root, REQUIRED_RECEIPTS, errors)
    doc_presence = exists_check(repo_root, REQUIRED_DOCS, errors)

    bundle_path = repo_root / EXPECTED_BUNDLE_PATH
    source_path = repo_root / "CHANGELOG.md"
    bundle_present = bundle_path.exists()
    source_present = source_path.exists()
    if not bundle_present:
        add_error(errors, "MISSING_EXPECTED_BUNDLE", EXPECTED_BUNDLE_PATH)
    if not source_present:
        add_error(errors, "MISSING_SOURCE_PATH", "CHANGELOG.md")

    bundle_hash = sha256_file(bundle_path) if bundle_present else None
    source_hash = sha256_file(source_path) if source_present else None
    if bundle_hash is not None:
        check_equals(errors, "bundle_hash", bundle_hash, EXPECTED_BUNDLE_HASH)
    if source_hash is not None:
        check_equals(errors, "source_hash", source_hash, EXPECTED_CHANGELOG_HASH)

    loaded_reports: Dict[str, Dict[str, Any]] = {}
    loaded_receipts: Dict[str, Dict[str, Any]] = {}

    for key, rel in REQUIRED_REPORTS.items():
        path = repo_root / rel
        if path.exists():
            try:
                loaded_reports[key] = load_json(path)
            except Exception as exc:
                add_error(errors, "REPORT_PARSE_ERROR", f"{rel}: {exc}")

    for key, rel in REQUIRED_RECEIPTS.items():
        path = repo_root / rel
        if path.exists():
            try:
                loaded_receipts[key] = latest_jsonl(path)
            except Exception as exc:
                add_error(errors, "RECEIPT_PARSE_ERROR", f"{rel}: {exc}")

    destination_plan = loaded_reports.get("m12_destination_plan", {})
    finalize_check = loaded_reports.get("m12_finalize_check", {})
    finalize_candidate = loaded_reports.get("m13_finalize_one_candidate", {})
    authority_boundary = loaded_reports.get("m11_to_m13_authority_boundary", {})

    if destination_plan:
        check_equals(errors, "m12_destination_plan.decision", destination_plan.get("decision"), "PLAN_ONLY")
        check_none_authority(errors, "m12_destination_plan", destination_plan)

    if finalize_check:
        check_equals(errors, "m12_finalize_check.decision", finalize_check.get("decision"), "REVIEW_ONLY")
        check_none_authority(errors, "m12_finalize_check", finalize_check)

    if finalize_candidate:
        check_equals(
            errors,
            "m13_finalize_one_candidate.decision",
            finalize_candidate.get("decision"),
            "FINALIZE_ONE_PROPOSED_REVIEW_ONLY",
        )
        check_equals(errors, "m13_finalize_one_candidate.mutation_performed", finalize_candidate.get("mutation_performed"), False)
        check_equals(errors, "m13_finalize_one_candidate.bundle_hash", finalize_candidate.get("bundle_hash"), EXPECTED_BUNDLE_HASH)
        check_equals(errors, "m13_finalize_one_candidate.source_hash_before", finalize_candidate.get("source_hash_before"), EXPECTED_CHANGELOG_HASH)
        check_equals(errors, "m13_finalize_one_candidate.destination_hash_before", finalize_candidate.get("destination_hash_before"), EXPECTED_CHANGELOG_HASH)
        check_none_authority(errors, "m13_finalize_one_candidate", finalize_candidate)

    if authority_boundary:
        check_equals(errors, "authority_boundary.decision", authority_boundary.get("decision"), "ALLOW")
        check_equals(errors, "authority_boundary.errors", authority_boundary.get("errors"), [])
        check_none_authority(errors, "authority_boundary", authority_boundary)

    # M14 is preflight-only. These remain absent until explicitly built as future artifacts.
    future_required = {
        "operator_mutation_intent_receipt": None,
        "transition_table_finalization_action_receipt": None,
        "cge_finalization_authority_receipt": None,
        "exact_mutation_plan_receipt": None,
        "rollback_dispute_readiness_receipt": None,
        "post_mutation_verification_receipt": None,
    }

    decision = "EXECUTION_PREFLIGHT_REVIEW_ONLY" if not errors else "FAIL_CLOSED"

    report: Dict[str, Any] = {
        "schema": "stegverse.repo_recovery.finalize_one_execution_preflight.v1",
        "entity": "StegVerse-002",
        "repository": "core-lite",
        "stage": "SV002-M14",
        "generated_at": utc_now(),
        "decision": decision,
        "errors": errors,
        "warnings": warnings,
        "candidate": {
            "bundle_path": EXPECTED_BUNDLE_PATH,
            "bundle_present": bundle_present,
            "bundle_hash": bundle_hash,
            "expected_bundle_hash": EXPECTED_BUNDLE_HASH,
            "source_path": "CHANGELOG.md",
            "source_present": source_present,
            "source_hash": source_hash,
            "expected_source_hash": EXPECTED_CHANGELOG_HASH,
            "destination_path": "CHANGELOG.md",
        },
        "checked_reports": REQUIRED_REPORTS,
        "checked_receipts": REQUIRED_RECEIPTS,
        "checked_docs": REQUIRED_DOCS,
        "presence": {
            "reports": report_presence,
            "receipts": receipt_presence,
            "docs": doc_presence,
        },
        "m11_to_m13_boundary": {
            "required_boundary_report_decision": authority_boundary.get("decision") if authority_boundary else None,
            "execution_authority": "none",
            "cleanup_authority": "none",
            "bulk_authority": "none",
            "replacement_authority": "none",
            "original_removal_authority": "none",
            "mutation_performed": False,
        },
        "future_execution_lane_requirements": future_required,
        "preflight_authority": {
            "execution_authority": "none",
            "cleanup_authority": "none",
            "bulk_authority": "none",
            "replacement_authority": "none",
            "original_removal_authority": "none",
            "mutation_performed": False,
            "may_execute_finalization": False,
            "may_move_files": False,
            "may_replace_files": False,
            "may_delete_files": False,
            "may_cleanup_recovery_bundles": False,
            "may_bulk_sequence": False,
        },
        "next_required_action": "Create explicit operator-intent, transition-table finalization, CGE finalization, mutation-plan, rollback, and post-verification lanes before any execution.",
    }

    report_path = report_dir / "repo_recovery_finalize_one_execution_preflight.json"
    receipt_path = receipt_dir / "repo_recovery_finalize_one_execution_preflight_receipt.jsonl"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema": "stegverse.repo_recovery.finalize_one_execution_preflight_receipt.v1",
        "stage": "SV002-M14",
        "decision": decision,
        "errors": errors,
        "report_path": str(report_path.relative_to(repo_root)),
        "report_sha256": sha256_file(report_path),
        "timestamp_utc": utc_now(),
    }
    receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")

    return 0 if decision == "EXECUTION_PREFLIGHT_REVIEW_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
