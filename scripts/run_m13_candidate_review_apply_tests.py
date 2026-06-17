#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core_lite.candidates import CandidateApplier, CandidateReviewer

REPORT_PATH = Path("reports/current/m13_candidate_review_apply_validation_report.json")
RECEIPT_PATH = Path("receipts/current/m13_candidate_review_apply_validation_receipt.jsonl")
OUTPUT_PATH = Path("outputs/m13_candidate_review_apply_validation.md")
ARTIFACT_PATH = Path("dist/run_artifacts/m13-candidate-review-apply-validation.zip")


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def make_bundle(path: Path) -> None:
    payload = b"m13 candidate apply validation payload\n"
    manifest = {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "m13_candidate_apply_validation_bundle",
        "purpose": "standalone m13 candidate review apply validation",
        "allow_root_readme": False,
        "allow_workflows": False,
        "files": [
            {
                "path": "outputs/m13_candidate_apply_probe.txt",
                "sha256": sha256_bytes(payload),
                "bytes": len(payload),
            }
        ],
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("outputs/m13_candidate_apply_probe.txt", payload)
        archive.writestr("bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    tmp = Path("tmp/m13_candidate_validation")
    tmp.mkdir(parents=True, exist_ok=True)
    bundle_path = tmp / "candidate_bundle.zip"
    candidate_ref = tmp / "candidate_ref.json"
    make_bundle(bundle_path)
    candidate_ref.write_text(json.dumps({
        "schema": "stegverse.candidate_ref.v1",
        "candidate_id": "m13-candidate-apply-validation",
        "task_id": "stegverse.candidate.intake.apply",
        "bundle_path": str(bundle_path),
        "proposed_files": ["outputs/m13_candidate_apply_probe.txt"]
    }, indent=2) + "\n", encoding="utf-8")

    review = CandidateReviewer(REPO_ROOT).review(candidate_ref)
    apply_report = CandidateApplier(REPO_ROOT).apply(candidate_ref, Path("reports/current/candidate_bundle_review_report.json"))
    probe_exists = Path("outputs/m13_candidate_apply_probe.txt").exists()
    passed = review.get("decision") == "ALLOW_CANDIDATE_REVIEW" and apply_report.get("decision") == "ALLOW_INSTALL" and probe_exists

    validation = {
        "schema": "stegverse.m13_candidate_review_apply_validation_report.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "decision": "ALLOW" if passed else "FAIL_CLOSED",
        "review_decision": review.get("decision"),
        "apply_decision": apply_report.get("decision"),
        "probe_exists": probe_exists,
        "review_report": review,
        "apply_report": apply_report,
    }
    write_json(REPORT_PATH, validation)
    receipt = {
        "schema": "stegverse.m13_candidate_review_apply_validation_receipt.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "SV002-M13",
        "gate": "m13-candidate-review-apply-validation",
        "decision": validation["decision"],
        "passed": passed,
        "report_path": str(REPORT_PATH),
        "report_hash": sha256_bytes(json.dumps(validation, sort_keys=True).encode("utf-8")),
    }
    receipt["receipt_hash"] = sha256_bytes(json.dumps(receipt, sort_keys=True).encode("utf-8"))
    append_jsonl(RECEIPT_PATH, receipt)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        "# M13 Candidate Review / Apply Validation\n\n"
        f"Passed: `{str(passed).lower()}`\n\n"
        f"Review decision: `{review.get('decision')}`\n\n"
        f"Apply decision: `{apply_report.get('decision')}`\n\n"
        f"Probe exists: `{probe_exists}`\n",
        encoding="utf-8",
    )
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARTIFACT_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [REPORT_PATH, RECEIPT_PATH, OUTPUT_PATH, Path("reports/current/candidate_bundle_review_report.json"), Path("reports/current/candidate_bundle_apply_report.json")]:
            if path.exists():
                archive.write(path, path.as_posix())
    print(json.dumps({"passed": passed, "decision": validation["decision"], "review_decision": review.get("decision"), "apply_decision": apply_report.get("decision"), "report": str(REPORT_PATH)}, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
