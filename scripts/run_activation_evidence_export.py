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

REPORT_PATH = Path("reports/current/core_lite_activation_evidence_report.json")
RECEIPT_PATH = Path("receipts/current/core_lite_activation_evidence_receipt.jsonl")
OUTPUT_PATH = Path("outputs/core_lite_activation_evidence.md")
ARTIFACT_PATH = Path("dist/run_artifacts/core-lite-activation-evidence.zip")

REQUIRED_PATHS = [
    "README.md",
    "core_lite/bundles/ingest.py",
    "core_lite/incoming/mailbox.py",
    "core_lite/candidates/review.py",
    "core_lite/candidates/apply.py",
    "core_lite/transition_table/resolver.py",
    "core_lite/transition_table/formalism_refs.py",
    "core_lite/sdk/client.py",
    "scripts/run_bundle_ingestion_smoke_test.py",
    "scripts/run_m12_incoming_mailbox_tests.py",
    "scripts/run_m13_candidate_review_apply_tests.py",
    "scripts/run_m14_formalism_linkage_check.py",
    "scripts/run_m15_sdk_cli_tests.py",
    "tools/tasks/task_catalog.json",
]

EXPECTED_REPORTS = [
    "reports/current/bundle_ingestion_smoke_test_report.json",
    "reports/current/m12_incoming_mailbox_validation_report.json",
    "reports/current/m13_candidate_review_apply_validation_report.json",
    "reports/current/m14_formalism_linkage_report.json",
    "reports/current/m15_sdk_cli_validation_report.json",
]


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def inspect_path(rel: str) -> dict:
    path = Path(rel)
    exists = path.exists()
    return {
        "path": rel,
        "exists": exists,
        "sha256": sha256_file(path) if exists and path.is_file() else "",
        "bytes": path.stat().st_size if exists and path.is_file() else 0,
    }


def inspect_report(rel: str) -> dict:
    path = Path(rel)
    item = inspect_path(rel)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            item["decision"] = payload.get("decision")
            item["passed"] = payload.get("passed", payload.get("success"))
        except Exception as exc:
            item["parse_error"] = str(exc)
    return item


def main() -> int:
    required = [inspect_path(p) for p in REQUIRED_PATHS]
    reports = [inspect_report(p) for p in EXPECTED_REPORTS]
    missing_required = [p["path"] for p in required if not p["exists"]]
    missing_reports = [p["path"] for p in reports if not p["exists"]]
    failed_reports = [p["path"] for p in reports if p.get("exists") and p.get("decision") not in {"ALLOW", None} and p.get("passed") is not True]

    activation_ready = not missing_required and not missing_reports and not failed_reports
    evidence_manifest = {
        "schema": "stegverse.core_lite_activation_evidence_report.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "entity": "StegVerse-002",
        "repo": "StegVerse-002/core-lite",
        "decision": "ALLOW" if activation_ready else "REVIEW",
        "activation_ready": activation_ready,
        "missing_required_paths": missing_required,
        "missing_expected_reports": missing_reports,
        "failed_expected_reports": failed_reports,
        "required_paths": required,
        "expected_reports": reports,
        "activation_boundary": {
            "candidate_output_is_evidence_not_authority": True,
            "incoming_is_mailbox_not_durable_state": True,
            "sdk_cli_no_raw_mutation_api": True,
            "formalism_authority_repo": "Data-Continuation/formalism-tests",
        },
    }
    write_json(REPORT_PATH, evidence_manifest)

    receipt = {
        "schema": "stegverse.core_lite_activation_evidence_receipt.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "SV002-M16",
        "gate": "activation-evidence-export",
        "decision": evidence_manifest["decision"],
        "activation_ready": activation_ready,
        "report_path": str(REPORT_PATH),
        "report_hash": sha256_bytes(json.dumps(evidence_manifest, sort_keys=True).encode("utf-8")),
    }
    receipt["receipt_hash"] = sha256_bytes(json.dumps(receipt, sort_keys=True).encode("utf-8"))
    append_jsonl(RECEIPT_PATH, receipt)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        "# Core-Lite Activation Evidence\n\n"
        f"Decision: `{evidence_manifest['decision']}`\n\n"
        f"Activation ready: `{str(activation_ready).lower()}`\n\n"
        f"Missing required paths: `{missing_required}`\n\n"
        f"Missing expected reports: `{missing_reports}`\n\n"
        f"Failed expected reports: `{failed_reports}`\n",
        encoding="utf-8",
    )

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARTIFACT_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [REPORT_PATH, RECEIPT_PATH, OUTPUT_PATH]:
            if path.exists():
                archive.write(path, path.as_posix())
        for item in required + reports:
            path = Path(item["path"])
            if path.exists() and path.is_file():
                archive.write(path, path.as_posix())

    print(json.dumps({
        "decision": evidence_manifest["decision"],
        "activation_ready": activation_ready,
        "missing_required_paths": missing_required,
        "missing_expected_reports": missing_reports,
        "report": str(REPORT_PATH),
        "artifact": str(ARTIFACT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if activation_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
