#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

INTAKE_DIR = Path("incoming/management_reviewer_authority")
SCHEMA_PATH = Path("schemas/management_reviewer_authority_submission.schema.json")
REPORT_JSON = Path("reports/current/management_reviewer_authority_submission_report.json")
REPORT_MD = Path("reports/current/management_reviewer_authority_submission_report.md")
RECEIPT_PATH = Path("receipts/current/management_reviewer_authority_submission_receipt.jsonl")
ALLOWED_CANDIDATES = {"SV002-MGMT-001", "SV002-MGMT-002", "SV002-MGMT-003"}


def now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def validate_submission(data: dict[str, Any], current: dt.datetime) -> list[str]:
    errors: list[str] = []
    required = [
        "schema", "submission_id", "reviewer_identity", "authority_class",
        "candidate_ids", "scope", "policy_refs", "delegation_refs",
        "valid_from", "valid_until", "revocation_status", "evidence_hashes",
    ]
    for key in required:
        if key not in data:
            errors.append(f"missing required field: {key}")

    if errors:
        return errors

    if data.get("schema") != "stegverse.management_reviewer_authority_submission.v1":
        errors.append("schema value is not supported")

    identity = data.get("reviewer_identity")
    if not isinstance(identity, dict) or not identity.get("id"):
        errors.append("reviewer_identity.id is required")
    elif not identity.get("identity_evidence_refs"):
        errors.append("reviewer_identity.identity_evidence_refs must be non-empty")

    candidate_ids = data.get("candidate_ids")
    if not isinstance(candidate_ids, list) or not candidate_ids:
        errors.append("candidate_ids must be a non-empty array")
    else:
        unknown = sorted(set(map(str, candidate_ids)) - ALLOWED_CANDIDATES)
        if unknown:
            errors.append(f"unknown candidate_ids: {', '.join(unknown)}")

    scope = data.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
    else:
        actions = scope.get("actions", [])
        if "review" not in actions:
            errors.append("scope.actions must include review")
        forbidden = {"execute", "install", "mutate", "publish"} & set(map(str, actions))
        if forbidden:
            errors.append(f"scope contains forbidden execution actions: {', '.join(sorted(forbidden))}")
        if scope.get("repo") != "Data-Continuation/core-lite":
            errors.append("scope.repo must be Data-Continuation/core-lite for current candidates")

    if not data.get("policy_refs"):
        errors.append("policy_refs must be non-empty")
    if not data.get("delegation_refs"):
        errors.append("delegation_refs must be non-empty")

    try:
        valid_from = parse_time(str(data.get("valid_from")))
        valid_until = parse_time(str(data.get("valid_until")))
        if valid_until <= valid_from:
            errors.append("valid_until must be after valid_from")
        if current < valid_from:
            errors.append("authority evidence is not yet valid")
        if current > valid_until:
            errors.append("authority evidence is stale or expired")
    except Exception:
        errors.append("valid_from and valid_until must be valid ISO-8601 timestamps")

    if data.get("revocation_status") != "not_revoked":
        errors.append("revocation_status must be not_revoked")

    hashes = data.get("evidence_hashes")
    if not isinstance(hashes, list) or not hashes:
        errors.append("evidence_hashes must be a non-empty array")
    else:
        for index, item in enumerate(hashes):
            if not isinstance(item, dict):
                errors.append(f"evidence_hashes[{index}] must be an object")
                continue
            digest = str(item.get("sha256", ""))
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                errors.append(f"evidence_hashes[{index}].sha256 must be lowercase SHA-256")

    return errors


def append_receipt(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    path = root / RECEIPT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = None
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            try:
                previous_hash = json.loads(lines[-1]).get("hash")
            except json.JSONDecodeError:
                previous_hash = None
    payload = {
        "schema": "stegverse.management_reviewer_authority_submission_receipt.v1",
        "version": report["version"],
        "repo": report["repo"],
        "result": report["result"],
        "submission_count": report["submission_count"],
        "accepted_count": report["accepted_count"],
        "rejected_count": report["rejected_count"],
        "may_grant_authority": False,
        "may_execute_actions": False,
        "previous_hash": previous_hash,
    }
    receipt = {**payload, "hash": stable_hash(payload)}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, sort_keys=True) + "\n")
    return receipt


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Management Reviewer Authority Submission Validation",
        "",
        f"Generated: `{report['checked_utc']}`",
        f"Result: `{report['result']}`",
        "",
        "## Summary",
        "",
        f"- submissions: `{report['submission_count']}`",
        f"- structurally accepted: `{report['accepted_count']}`",
        f"- rejected: `{report['rejected_count']}`",
        "",
        "Structural acceptance does not grant reviewer, quorum, or execution authority.",
        "",
        "## Submissions",
        "",
    ]
    if not report["submissions"]:
        lines.append("- No submissions found")
    for item in report["submissions"]:
        lines.append(f"- `{item['path']}`: `{item['status']}`")
        for error in item.get("errors", []):
            lines.append(f"  - {error}")
    lines.extend(["", "## Receipt", "", f"- `{report['receipt']['hash']}`", ""])
    return "\n".join(lines)


def build_report(root: Path) -> dict[str, Any]:
    current = now()
    intake = root / INTAKE_DIR
    files = sorted(path for path in intake.glob("*.json") if path.name != "README.md") if intake.exists() else []
    submissions: list[dict[str, Any]] = []
    for path in files:
        try:
            data = read_json(path)
            errors = validate_submission(data, current)
        except Exception as exc:
            errors = [str(exc)]
            data = {}
        submissions.append({
            "path": path.relative_to(root).as_posix(),
            "submission_id": data.get("submission_id"),
            "candidate_ids": data.get("candidate_ids", []),
            "status": "STRUCTURALLY_ACCEPTED" if not errors else "REJECTED",
            "errors": errors,
        })

    accepted = sum(1 for item in submissions if item["status"] == "STRUCTURALLY_ACCEPTED")
    rejected = len(submissions) - accepted
    if not submissions:
        result = "REVIEWER_AUTHORITY_SUBMISSION_PENDING"
    elif rejected:
        result = "REVIEWER_AUTHORITY_SUBMISSION_FAIL_CLOSED"
    else:
        result = "REVIEWER_AUTHORITY_SUBMISSION_STRUCTURALLY_ACCEPTED"

    report: dict[str, Any] = {
        "schema": "stegverse.management_reviewer_authority_submission_report.v1",
        "version": "0.1.27-gllm",
        "repo": "StegVerse-002/core-lite",
        "checked_utc": current.isoformat(timespec="seconds"),
        "schema_path": SCHEMA_PATH.as_posix(),
        "intake_path": INTAKE_DIR.as_posix(),
        "submission_count": len(submissions),
        "accepted_count": accepted,
        "rejected_count": rejected,
        "submissions": submissions,
        "result": result,
        "authority_boundary": {
            "structural_acceptance_grants_review_authority": False,
            "structural_acceptance_forms_quorum": False,
            "structural_acceptance_grants_execution_authority": False,
            "may_bind_repo_state": False,
        },
        "next_candidate_goal": "reconstruct and verify submitted authority evidence before rerunning management action review",
    }
    report["receipt"] = append_receipt(root, report)
    (root / REPORT_JSON).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (root / REPORT_MD).write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate management reviewer authority submissions.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = build_report(Path(args.repo_root).resolve())
    except Exception as exc:
        print(f"Reviewer authority submission validation failed: {exc}")
        return 2
    print(f"Wrote {REPORT_MD.as_posix()}")
    print(f"Wrote {REPORT_JSON.as_posix()}")
    print(f"Wrote {RECEIPT_PATH.as_posix()}")
    print(f"Result: {report['result']}")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
