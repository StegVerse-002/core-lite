#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core_lite.sdk import CoreLiteClient

REPORT_PATH = Path("reports/current/m15_sdk_cli_validation_report.json")
RECEIPT_PATH = Path("receipts/current/m15_sdk_cli_validation_receipt.jsonl")
OUTPUT_PATH = Path("outputs/m15_sdk_cli_validation.md")
ARTIFACT_PATH = Path("dist/run_artifacts/m15-sdk-cli-validation.zip")


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
    payload = b"m15 sdk cli validation payload\n"
    manifest = {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "m15_sdk_cli_validation_bundle",
        "purpose": "standalone m15 SDK/CLI validation",
        "allow_root_readme": False,
        "allow_workflows": False,
        "files": [{"path": "outputs/m15_sdk_cli_probe.txt", "sha256": sha256_bytes(payload), "bytes": len(payload)}],
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("outputs/m15_sdk_cli_probe.txt", payload)
        archive.writestr("bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    tmp = Path("tmp/m15_sdk_cli_validation")
    tmp.mkdir(parents=True, exist_ok=True)
    bundle_path = tmp / "sdk_cli_bundle.zip"
    make_bundle(bundle_path)

    client = CoreLiteClient(Path("."))
    sdk_report = client.ingest_bundle(bundle_path)
    cli_proc = subprocess.run([sys.executable, "scripts/core_lite_cli.py", "ingest-bundle", str(bundle_path)], text=True, capture_output=True)
    probe_exists = Path("outputs/m15_sdk_cli_probe.txt").exists()
    passed = sdk_report.get("decision") == "ALLOW" and cli_proc.returncode == 0 and probe_exists

    validation = {
        "schema": "stegverse.m15_sdk_cli_validation_report.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "decision": "ALLOW" if passed else "FAIL_CLOSED",
        "sdk_decision": sdk_report.get("decision"),
        "cli_returncode": cli_proc.returncode,
        "cli_stdout_tail": cli_proc.stdout[-2000:],
        "cli_stderr_tail": cli_proc.stderr[-2000:],
        "probe_exists": probe_exists,
    }
    write_json(REPORT_PATH, validation)
    receipt = {
        "schema": "stegverse.m15_sdk_cli_validation_receipt.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "SV002-M15",
        "gate": "m15-sdk-cli-validation",
        "decision": validation["decision"],
        "passed": passed,
        "report_path": str(REPORT_PATH),
        "report_hash": sha256_bytes(json.dumps(validation, sort_keys=True).encode("utf-8")),
    }
    receipt["receipt_hash"] = sha256_bytes(json.dumps(receipt, sort_keys=True).encode("utf-8"))
    append_jsonl(RECEIPT_PATH, receipt)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        "# M15 SDK / CLI Validation\n\n"
        f"Passed: `{str(passed).lower()}`\n\n"
        f"SDK decision: `{sdk_report.get('decision')}`\n\n"
        f"CLI returncode: `{cli_proc.returncode}`\n\n"
        f"Probe exists: `{probe_exists}`\n",
        encoding="utf-8",
    )
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARTIFACT_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [REPORT_PATH, RECEIPT_PATH, OUTPUT_PATH, Path("reports/current/bundle_ingest_report.json")]:
            if path.exists():
                archive.write(path, path.as_posix())
    print(json.dumps({"passed": passed, "decision": validation["decision"], "report": str(REPORT_PATH)}, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
