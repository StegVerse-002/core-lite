#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

SUBMISSION_DIR = Path("incoming/management_reviewer_authority")
REPORT_PATH = Path("reports/current/management_reviewer_authority_reconstruction_report.json")
RECEIPT_PATH = Path("receipts/current/management_reviewer_authority_reconstruction_receipt.jsonl")
SUBMISSION_SCHEMA = "stegverse.management_reviewer_authority_submission.v1"
EVIDENCE_SCHEMA = "stegverse.management_reviewer_authority_evidence.v1"
ALLOWED_CANDIDATES = {"SV002-MGMT-001", "SV002-MGMT-002", "SV002-MGMT-003"}
REQUIRED_EVIDENCE_TYPES = {"identity", "policy", "delegation", "revocation"}


class ReconstructionError(ValueError):
    pass


def canonical_hash(payload: dict[str, Any], field: str | None = None) -> str:
    clean = dict(payload)
    if field:
        clean.pop(field, None)
    raw = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReconstructionError(f"object_required:{path.as_posix()}")
    return value


def safe_repo_path(root: Path, ref: str) -> Path:
    rel = Path(ref)
    if rel.is_absolute() or ".." in rel.parts or not ref:
        raise ReconstructionError(f"unsafe_evidence_ref:{ref}")
    resolved = (root / rel).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ReconstructionError(f"evidence_ref_outside_repo:{ref}") from exc
    return resolved


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_index(submission: dict[str, Any]) -> dict[str, str]:
    index: dict[str, str] = {}
    for item in submission.get("evidence_hashes", []):
        if not isinstance(item, dict):
            continue
        ref = str(item.get("ref", ""))
        digest = str(item.get("sha256", ""))
        if ref:
            index[ref] = digest
    return index


def load_verified_evidence(root: Path, ref: str, expected_hash: str) -> dict[str, Any]:
    path = safe_repo_path(root, ref)
    if not path.is_file():
        raise ReconstructionError(f"evidence_missing:{ref}")
    observed = file_sha256(path)
    if observed != expected_hash:
        raise ReconstructionError(f"evidence_hash_mismatch:{ref}")
    data = read_object(path)
    if data.get("schema") != EVIDENCE_SCHEMA:
        raise ReconstructionError(f"evidence_schema_invalid:{ref}")
    return data


def reconstruct_submission(root: Path, submission_path: Path) -> dict[str, Any]:
    failures: list[str] = []
    try:
        submission = read_object(submission_path)
    except Exception as exc:
        return {
            "submission_path": submission_path.relative_to(root).as_posix(),
            "decision": "REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED",
            "failures": [f"submission_unreadable:{type(exc).__name__}"],
            "evidence": [],
        }

    if submission.get("schema") != SUBMISSION_SCHEMA:
        failures.append("submission_schema_invalid")

    reviewer = submission.get("reviewer_identity")
    reviewer_id = reviewer.get("id") if isinstance(reviewer, dict) else None
    if not reviewer_id:
        failures.append("reviewer_identity_missing")

    candidates = set(map(str, submission.get("candidate_ids", [])))
    if not candidates or not candidates.issubset(ALLOWED_CANDIDATES):
        failures.append("candidate_scope_invalid")

    scope = submission.get("scope")
    if not isinstance(scope, dict) or scope.get("repo") != "Data-Continuation/core-lite":
        failures.append("repository_scope_invalid")
    actions = set(map(str, scope.get("actions", []))) if isinstance(scope, dict) else set()
    if "review" not in actions or actions & {"execute", "install", "mutate", "publish"}:
        failures.append("action_scope_invalid")

    hashes = evidence_index(submission)
    required_refs: list[str] = []
    if isinstance(reviewer, dict):
        required_refs.extend(map(str, reviewer.get("identity_evidence_refs", [])))
    required_refs.extend(map(str, submission.get("policy_refs", [])))
    required_refs.extend(map(str, submission.get("delegation_refs", [])))
    for ref in required_refs:
        if ref not in hashes:
            failures.append(f"required_ref_missing_hash:{ref}")

    evidence_rows: list[dict[str, Any]] = []
    typed: dict[str, list[dict[str, Any]]] = {key: [] for key in REQUIRED_EVIDENCE_TYPES}
    for ref, digest in sorted(hashes.items()):
        try:
            evidence = load_verified_evidence(root, ref, digest)
            etype = str(evidence.get("evidence_type", ""))
            if etype not in REQUIRED_EVIDENCE_TYPES:
                raise ReconstructionError(f"unsupported_evidence_type:{ref}:{etype}")
            typed[etype].append(evidence)
            evidence_rows.append({"ref": ref, "sha256": digest, "evidence_type": etype, "verified": True})
        except Exception as exc:
            failures.append(str(exc))
            evidence_rows.append({"ref": ref, "sha256": digest, "verified": False})

    missing_types = sorted(kind for kind in REQUIRED_EVIDENCE_TYPES if not typed[kind])
    failures.extend(f"required_evidence_type_missing:{kind}" for kind in missing_types)

    if reviewer_id:
        identities = typed["identity"]
        if identities and not any(
            item.get("subject_id") == reviewer_id and item.get("status") == "valid"
            for item in identities
        ):
            failures.append("identity_evidence_does_not_validate_reviewer")

        policies = typed["policy"]
        if policies and not any(
            item.get("status") == "active"
            and item.get("repo") == "Data-Continuation/core-lite"
            and candidates.issubset(set(map(str, item.get("candidate_ids", []))))
            and "review" in set(map(str, item.get("actions", [])))
            for item in policies
        ):
            failures.append("policy_evidence_does_not_authorize_scope")

        delegations = typed["delegation"]
        if delegations and not any(
            item.get("status") == "active"
            and item.get("delegate_id") == reviewer_id
            and item.get("repo") == "Data-Continuation/core-lite"
            and candidates.issubset(set(map(str, item.get("candidate_ids", []))))
            and "review" in set(map(str, item.get("actions", [])))
            for item in delegations
        ):
            failures.append("delegation_evidence_does_not_authorize_reviewer")

        revocations = typed["revocation"]
        if revocations:
            matching = [item for item in revocations if item.get("subject_id") == reviewer_id]
            if not matching:
                failures.append("revocation_evidence_subject_mismatch")
            elif any(item.get("revoked") is not False for item in matching):
                failures.append("reviewer_revoked_or_revocation_unknown")

    decision = (
        "REVIEWER_AUTHORITY_EVIDENCE_ACCEPTED"
        if not failures
        else "REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED"
    )
    return {
        "submission_path": submission_path.relative_to(root).as_posix(),
        "submission_id": submission.get("submission_id"),
        "reviewer_id": reviewer_id,
        "candidate_ids": sorted(candidates),
        "decision": decision,
        "failures": sorted(set(failures)),
        "evidence": evidence_rows,
        "authority_boundary": {
            "review_evidence_reconstructed": decision == "REVIEWER_AUTHORITY_EVIDENCE_ACCEPTED",
            "quorum_formed": False,
            "execution_authority_granted": False,
            "repository_binding_granted": False,
            "runtime_activation_granted": False,
        },
    }


def append_receipt(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    path = root / RECEIPT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = None
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            try:
                previous = json.loads(lines[-1]).get("receipt_hash")
            except json.JSONDecodeError:
                previous = None
    payload = {
        "schema": "stegverse.management_reviewer_authority_reconstruction_receipt.v1",
        "repository": report["repository"],
        "decision": report["decision"],
        "submission_count": report["submission_count"],
        "accepted_count": report["accepted_count"],
        "fail_closed_count": report["fail_closed_count"],
        "previous_receipt_hash": previous,
        "authority_effect": "NONE",
    }
    receipt = {**payload, "receipt_hash": canonical_hash(payload)}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, sort_keys=True) + "\n")
    return receipt


def build_report(root: Path) -> dict[str, Any]:
    directory = root / SUBMISSION_DIR
    paths = sorted(directory.glob("*.json")) if directory.exists() else []
    results = [reconstruct_submission(root, path) for path in paths]
    accepted = sum(row["decision"] == "REVIEWER_AUTHORITY_EVIDENCE_ACCEPTED" for row in results)
    failed = sum(row["decision"] == "REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED" for row in results)
    if not results:
        decision = "REVIEWER_AUTHORITY_EVIDENCE_PENDING"
    elif failed:
        decision = "REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED"
    else:
        decision = "REVIEWER_AUTHORITY_EVIDENCE_ACCEPTED"
    report = {
        "schema": "stegverse.management_reviewer_authority_reconstruction_report.v1",
        "repository": "StegVerse-002/core-lite",
        "decision": decision,
        "submission_count": len(results),
        "accepted_count": accepted,
        "fail_closed_count": failed,
        "results": results,
        "authority_boundary": {
            "reconstruction_is_review_evidence_only": True,
            "forms_quorum": False,
            "grants_execution_authority": False,
            "binds_repository_state": False,
            "activates_runtime": False,
        },
    }
    report["report_hash"] = canonical_hash(report, "report_hash")
    report["receipt"] = append_receipt(root, report)
    target = root / REPORT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconstruct and verify reviewer-authority evidence.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    try:
        report = build_report(root)
    except Exception as exc:
        print(f"REVIEWER AUTHORITY RECONSTRUCTION: FAIL_CLOSED ({exc})")
        return 2
    print(f"Decision: {report['decision']}")
    print(f"Wrote {REPORT_PATH.as_posix()}")
    print(f"Wrote {RECEIPT_PATH.as_posix()}")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["decision"] == "REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
