#!/usr/bin/env python3
"""
Check whether the StegVerse-002 v0.1.3-gllm transition-bundle proof is complete.

This checker is intentionally read-only. It does not create bundles, ingest bundles,
modify repo state, or grant authority. It emits a machine-readable report that can
be used by autonomous workflows to decide whether a proof run is still required.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_FILES = [
    "dist/bundles/proposed_transition_bundle.json",
    "dist/bundles/proposed_transition_bundle.zip",
    "dist/bundles/proposed_transition_bundle.sha256",
    "receipts/current/proposed_transition_bundle_receipt.jsonl",
    "receipts/current/transition_bundle_ingest_receipt.jsonl",
]

OPTIONAL_CUSTODY_FILES = [
    "dist/master-records/pending_candidate_bundles/proposed_transition_bundle.zip",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_last_jsonl(path: Path) -> Dict[str, Any]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return {}
    return json.loads(lines[-1])


def check(repo_root: Path) -> Dict[str, Any]:
    missing: List[str] = []
    present: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []

    for rel in REQUIRED_FILES:
        p = repo_root / rel
        if p.exists() and p.is_file():
            present.append(rel)
        else:
            missing.append(rel)

    optional_present = []
    optional_missing = []
    for rel in OPTIONAL_CUSTODY_FILES:
        p = repo_root / rel
        if p.exists() and p.is_file():
            optional_present.append(rel)
        else:
            optional_missing.append(rel)

    bundle_manifest: Dict[str, Any] = {}
    bundle_sha_file_value = ""
    bundle_zip_sha = ""
    package_receipt: Dict[str, Any] = {}
    ingest_receipt: Dict[str, Any] = {}

    manifest_path = repo_root / "dist/bundles/proposed_transition_bundle.json"
    zip_path = repo_root / "dist/bundles/proposed_transition_bundle.zip"
    sha_path = repo_root / "dist/bundles/proposed_transition_bundle.sha256"
    package_receipt_path = repo_root / "receipts/current/proposed_transition_bundle_receipt.jsonl"
    ingest_receipt_path = repo_root / "receipts/current/transition_bundle_ingest_receipt.jsonl"

    if manifest_path.exists():
        try:
            bundle_manifest = read_json(manifest_path)
            if bundle_manifest.get("authority", {}).get("broad_authority") is True:
                errors.append("manifest authority.broad_authority is true")
            if bundle_manifest.get("authority", {}).get("canonical_authority") is True:
                errors.append("manifest authority.canonical_authority is true")
            if bundle_manifest.get("authority", {}).get("candidate_evidence_only") is not True:
                errors.append("manifest authority.candidate_evidence_only is not true")
        except Exception as exc:  # pragma: no cover - diagnostic path
            errors.append(f"failed to parse proposed_transition_bundle.json: {exc}")

    if zip_path.exists():
        bundle_zip_sha = sha256_file(zip_path)

    if sha_path.exists():
        try:
            bundle_sha_file_value = sha_path.read_text(encoding="utf-8").strip()
            if bundle_zip_sha and bundle_sha_file_value and bundle_zip_sha not in bundle_sha_file_value:
                warnings.append("bundle zip sha256 does not appear in proposed_transition_bundle.sha256")
        except Exception as exc:  # pragma: no cover
            errors.append(f"failed to read proposed_transition_bundle.sha256: {exc}")

    if package_receipt_path.exists():
        try:
            package_receipt = read_last_jsonl(package_receipt_path)
            if package_receipt.get("decision") != "PACKAGED_AS_CANDIDATE_EVIDENCE":
                warnings.append("package receipt decision is not PACKAGED_AS_CANDIDATE_EVIDENCE")
            if package_receipt.get("canonical_authority") is True:
                errors.append("package receipt canonical_authority is true")
            if package_receipt.get("broad_authority") is True:
                errors.append("package receipt broad_authority is true")
        except Exception as exc:  # pragma: no cover
            errors.append(f"failed to parse proposed_transition_bundle_receipt.jsonl: {exc}")

    if ingest_receipt_path.exists():
        try:
            ingest_receipt = read_last_jsonl(ingest_receipt_path)
            if ingest_receipt.get("decision") != "ADMITTED_AS_CANDIDATE_EVIDENCE":
                warnings.append("ingest receipt decision is not ADMITTED_AS_CANDIDATE_EVIDENCE")
            if ingest_receipt.get("canonical_authority") is True:
                errors.append("ingest receipt canonical_authority is true")
            if ingest_receipt.get("broad_authority") is True:
                errors.append("ingest receipt broad_authority is true")
        except Exception as exc:  # pragma: no cover
            errors.append(f"failed to parse transition_bundle_ingest_receipt.jsonl: {exc}")

    if errors:
        status = "PROOF_INVALID"
        needs_proof = True
    elif missing:
        status = "MISSING_PROOF" if len(missing) == len(REQUIRED_FILES) else "PARTIAL_PROOF"
        needs_proof = True
    else:
        status = "PROOF_COMPLETE"
        needs_proof = False

    return {
        "schema": "stegverse.transition_bundle_proof_check.v1",
        "checked_utc": utc_now(),
        "version": "0.1.3-gllm",
        "status": status,
        "needs_proof": needs_proof,
        "required_files": REQUIRED_FILES,
        "present": present,
        "missing": missing,
        "optional_custody_present": optional_present,
        "optional_custody_missing": optional_missing,
        "warnings": warnings,
        "errors": errors,
        "bundle_zip_sha256": bundle_zip_sha,
        "bundle_sha_file_value": bundle_sha_file_value,
        "package_receipt_decision": package_receipt.get("decision"),
        "ingest_receipt_decision": ingest_receipt.get("decision"),
        "authority": {
            "candidate_evidence_only": bundle_manifest.get("authority", {}).get("candidate_evidence_only"),
            "canonical_authority": bundle_manifest.get("authority", {}).get("canonical_authority"),
            "broad_authority": bundle_manifest.get("authority", {}).get("broad_authority"),
            "may_bind_repo_state": bundle_manifest.get("authority", {}).get("may_bind_repo_state"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--report", default="reports/current/transition_bundle_proof_check.json")
    parser.add_argument("--receipt", default="receipts/current/transition_bundle_proof_check_receipt.jsonl")
    parser.add_argument("--fail-if-incomplete", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    report = check(repo_root)

    report_path = repo_root / args.report
    receipt_path = repo_root / args.receipt
    report_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with receipt_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")

    print(json.dumps(report, indent=2, sort_keys=True))

    if args.fail_if_incomplete and report["status"] != "PROOF_COMPLETE":
        return 2
    if report["status"] == "PROOF_INVALID":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
