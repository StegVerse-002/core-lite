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

from core_lite.incoming import IncomingMailbox

REPORT_PATH = Path("reports/current/m12_incoming_mailbox_validation_report.json")
RECEIPT_PATH = Path("receipts/current/m12_incoming_mailbox_validation_receipt.jsonl")
OUTPUT_PATH = Path("outputs/m12_incoming_mailbox_validation.md")
ARTIFACT_PATH = Path("dist/run_artifacts/m12-incoming-mailbox-validation.zip")


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def make_bundle(path: Path, *, schema: str) -> None:
    payload = b"m12 incoming mailbox validation payload\n"
    manifest = {
        "schema": schema,
        "bundle_name": "m12_incoming_mailbox_validation_bundle",
        "purpose": "standalone m12 incoming mailbox validation",
        "allow_root_readme": False,
        "allow_workflows": False,
        "files": [
            {
                "path": "outputs/m12_incoming_mailbox_probe.txt",
                "sha256": sha256_bytes(payload),
                "bytes": len(payload),
            }
        ],
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("outputs/m12_incoming_mailbox_probe.txt", payload)
        archive.writestr("bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    incoming = Path("tmp/m12_incoming_validation")
    if incoming.exists():
        for item in sorted(incoming.rglob("*"), reverse=True):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                item.rmdir()
    incoming.mkdir(parents=True, exist_ok=True)
    make_bundle(incoming / "good.zip", schema="stegverse.bundle_manifest.v1")
    make_bundle(incoming / "bad.zip", schema="bad.schema")

    report = IncomingMailbox(Path("."), incoming, stage="SV002-M12", dry_run=False).process()
    good_processed = (incoming / "processed" / "good.zip").exists()
    bad_rejected = (incoming / "rejected" / "bad.zip").exists()
    probe_exists = Path("outputs/m12_incoming_mailbox_probe.txt").exists()
    passed = report.get("decision") == "ALLOW" and good_processed and bad_rejected and probe_exists

    validation = {
        "schema": "stegverse.m12_incoming_mailbox_validation_report.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "decision": "ALLOW" if passed else "FAIL_CLOSED",
        "incoming_report": report,
        "checks": {
            "good_processed": good_processed,
            "bad_rejected": bad_rejected,
            "probe_exists": probe_exists,
        },
    }
    write_json(REPORT_PATH, validation)
    receipt = {
        "schema": "stegverse.m12_incoming_mailbox_validation_receipt.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "SV002-M12",
        "gate": "m12-incoming-mailbox-validation",
        "decision": validation["decision"],
        "passed": passed,
        "report_path": str(REPORT_PATH),
        "report_hash": sha256_bytes(json.dumps(validation, sort_keys=True).encode("utf-8")),
    }
    receipt["receipt_hash"] = sha256_bytes(json.dumps(receipt, sort_keys=True).encode("utf-8"))
    append_jsonl(RECEIPT_PATH, receipt)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        "# M12 Incoming Mailbox Validation\n\n"
        f"Passed: `{str(passed).lower()}`\n\n"
        f"Decision: `{validation['decision']}`\n\n"
        f"Good processed: `{good_processed}`\n\n"
        f"Bad rejected: `{bad_rejected}`\n\n"
        f"Probe exists: `{probe_exists}`\n",
        encoding="utf-8",
    )
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARTIFACT_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [REPORT_PATH, RECEIPT_PATH, OUTPUT_PATH, Path("reports/current/incoming_mailbox_report.json")]:
            if path.exists():
                archive.write(path, path.as_posix())
    print(json.dumps({"passed": passed, "decision": validation["decision"], "report": str(REPORT_PATH)}, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
