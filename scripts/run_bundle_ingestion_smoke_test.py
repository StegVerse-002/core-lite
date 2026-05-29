#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPORT_PATH = Path("reports/current/bundle_ingestion_smoke_test_report.json")
RECEIPT_PATH = Path("receipts/current/bundle_ingestion_smoke_test_receipt.jsonl")
OUTPUT_PATH = Path("outputs/bundle_ingestion_smoke_test.md")
ARTIFACT_PATH = Path("dist/run_artifacts/bundle-ingestion-smoke-test.zip")
FIXTURE_DIR = Path("tests/fixtures/bundles")
FIXTURE_ZIP = FIXTURE_DIR / "minimal_ingestible_bundle.zip"
PROBE_PATH = Path("outputs/bundle_ingestion_smoke_probe.txt")

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

def build_fixture() -> dict:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    payload_text = (
        "SV002 bundle ingestion smoke-test probe\n"
        f"generated_at={utc_now()}\n"
        "purpose=verify BundleIngestor direct fixture path\n"
    )
    payload_bytes = payload_text.encode("utf-8")
    payload_sha = sha256_bytes(payload_bytes)
    manifest = {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "sv002_bundle_ingestion_smoke_test_minimal",
        "purpose": "Controlled direct BundleIngestor smoke test outside incoming mailbox",
        "allow_root_readme": False,
        "allow_workflows": False,
        "files": [
            {
                "path": str(PROBE_PATH),
                "sha256": "sha256:" + payload_sha,
                "bytes": len(payload_bytes),
            }
        ],
    }
    with zipfile.ZipFile(FIXTURE_ZIP, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(str(PROBE_PATH), payload_bytes)
        archive.writestr("bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return {
        "fixture_zip": str(FIXTURE_ZIP),
        "payload_path": str(PROBE_PATH),
        "payload_sha256": "sha256:" + payload_sha,
        "manifest": manifest,
    }

def run_ingestor(fixture_zip: Path) -> dict:
    from core_lite.bundles.ingest import BundleIngestor
    ingestor = BundleIngestor(Path("."), entity="StegVerse-002", stage="SV002-M11", dry_run=False)
    return ingestor.ingest(fixture_zip)

def main() -> int:
    started_at = utc_now()
    fixture_info = build_fixture()
    exception_text = ""
    ingest_report = None

    try:
        ingest_report = run_ingestor(FIXTURE_ZIP)
    except Exception:
        exception_text = traceback.format_exc()

    probe_exists = PROBE_PATH.exists()
    probe_text = PROBE_PATH.read_text(encoding="utf-8") if probe_exists else ""

    success = (
        ingest_report is not None
        and ingest_report.get("status") == "success"
        and ingest_report.get("decision") == "ALLOW"
        and probe_exists
    )

    if success:
        failure_class = "none"
    elif exception_text:
        failure_class = "bundle_ingestor_exception"
    elif ingest_report is None:
        failure_class = "bundle_ingestor_returned_no_report"
    elif ingest_report.get("errors"):
        failure_class = "bundle_ingestor_reported_errors"
    elif ingest_report.get("status") != "success":
        failure_class = "bundle_ingestor_non_success_status"
    elif not probe_exists:
        failure_class = "probe_file_not_installed"
    else:
        failure_class = "unknown"

    report = {
        "schema": "stegverse.bundle_ingestion_smoke_test_report.v1",
        "success": success,
        "decision": "ALLOW" if success else "FAIL_CLOSED",
        "started_at": started_at,
        "finished_at": utc_now(),
        "failure_class": failure_class,
        "fixture": fixture_info,
        "ingest_report": ingest_report,
        "exception": exception_text,
        "probe": {
            "path": str(PROBE_PATH),
            "exists": probe_exists,
            "sha256": "sha256:" + sha256_bytes(probe_text.encode("utf-8")) if probe_exists else "",
            "text_preview": probe_text[:500] if probe_exists else "",
        },
        "diagnostic_notes": [
            "This smoke test does not use incoming/.",
            "This smoke test creates a minimal stegverse.bundle_manifest.v1 zip fixture.",
            "This smoke test calls core_lite.bundles.ingest.BundleIngestor directly.",
            "If this passes, the remaining bundle problem is likely workflow/incoming routing or manifest-schema mismatch in user bundles.",
            "If this fails, the failure_class and ingest_report errors identify the BundleIngestor-level repair target."
        ],
        "expected_outputs": {
            "reports/current/bundle_ingestion_smoke_test_report.json": True,
            "receipts/current/bundle_ingestion_smoke_test_receipt.jsonl": True,
            "outputs/bundle_ingestion_smoke_test.md": True,
            "dist/run_artifacts/bundle-ingestion-smoke-test.zip": True,
        },
    }

    write_outputs(report)
    print(json.dumps({
        "success": report["success"],
        "decision": report["decision"],
        "failure_class": report["failure_class"],
        "fixture_zip": fixture_info["fixture_zip"],
        "ingest_status": ingest_report.get("status") if isinstance(ingest_report, dict) else None,
        "ingest_decision": ingest_report.get("decision") if isinstance(ingest_report, dict) else None,
        "ingest_errors": ingest_report.get("errors") if isinstance(ingest_report, dict) else None,
        "probe_exists": probe_exists,
        "report_path": str(REPORT_PATH),
        "receipt_path": str(RECEIPT_PATH),
        "artifact_path": str(ARTIFACT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if success else 1

def write_outputs(report: dict) -> None:
    write_json(REPORT_PATH, report)
    report_text = json.dumps(report, sort_keys=True)
    receipt = {
        "schema": "stegverse.bundle_ingestion_smoke_test_receipt.v1",
        "timestamp_utc": utc_now(),
        "stage": "SV002-M11",
        "gate": "bundle_ingestion_smoke_test",
        "decision": report["decision"],
        "success": report["success"],
        "failure_class": report["failure_class"],
        "report_path": str(REPORT_PATH),
        "report_hash": sha256_text(report_text),
        "fixture_zip": report["fixture"]["fixture_zip"],
    }
    receipt["receipt_hash"] = sha256_text(json.dumps(receipt, sort_keys=True))
    append_jsonl(RECEIPT_PATH, receipt)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ingest_summary = {}
    if isinstance(report.get("ingest_report"), dict):
        ingest_summary = {
            "status": report["ingest_report"].get("status"),
            "decision": report["ingest_report"].get("decision"),
            "errors": report["ingest_report"].get("errors"),
            "installed": report["ingest_report"].get("installed"),
            "rejected": report["ingest_report"].get("rejected"),
        }

    OUTPUT_PATH.write_text(
        "\n".join([
            "# Bundle Ingestion Smoke Test",
            "",
            f"Decision: `{report['decision']}`",
            f"Success: `{str(report['success']).lower()}`",
            f"Failure class: `{report['failure_class']}`",
            f"Fixture: `{report['fixture']['fixture_zip']}`",
            f"Report: `{REPORT_PATH}`",
            f"Receipt: `{RECEIPT_PATH}`",
            "",
            "## Ingest Report Summary",
            "",
            "```json",
            json.dumps(ingest_summary, indent=2, sort_keys=True),
            "```",
            "",
            "## Exception",
            "",
            "```text",
            report.get("exception", ""),
            "```",
            "",
            "## Probe",
            "",
            "```json",
            json.dumps(report["probe"], indent=2, sort_keys=True),
            "```",
            "",
        ]) + "\n",
        encoding="utf-8",
    )

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARTIFACT_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [REPORT_PATH, RECEIPT_PATH, OUTPUT_PATH, FIXTURE_ZIP]:
            if path.exists():
                archive.write(path, path.as_posix())
        if Path("reports/current/bundle_ingest_report.json").exists():
            archive.write("reports/current/bundle_ingest_report.json")
        if PROBE_PATH.exists():
            archive.write(PROBE_PATH, PROBE_PATH.as_posix())

if __name__ == "__main__":
    raise SystemExit(main())
