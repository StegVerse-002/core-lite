#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import hashlib


REPORT_PATH = Path("reports/current/transition_table_gate_test_report.json")
RECEIPT_PATH = Path("receipts/current/transition_table_gate_test_receipt.jsonl")
OUTPUT_PATH = Path("outputs/transition_table_gate_tests.md")
ARTIFACT_PATH = Path("dist/run_artifacts/transition-table-gate-tests.zip")

TEST_FILES = [
    "tests/test_transition_table_resolver.py",
    "tests/test_bundle_ingest_cge_transition_gate.py",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def main() -> int:
    started_at = utc_now()

    missing = [path for path in TEST_FILES if not Path(path).exists()]
    if missing:
        report = {
            "schema": "stegverse.transition_table_gate_test_report.v1",
            "success": False,
            "decision": "FAIL_CLOSED",
            "started_at": started_at,
            "finished_at": utc_now(),
            "reason": "required test files are missing",
            "missing": missing,
            "test_files": TEST_FILES,
        }
        write_outputs(report, stdout="", stderr="")
        return 1

    command = [sys.executable, "-m", "pytest", *TEST_FILES]
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    finished_at = utc_now()

    success = proc.returncode == 0
    decision = "ALLOW" if success else "FAIL_CLOSED"

    report = {
        "schema": "stegverse.transition_table_gate_test_report.v1",
        "success": success,
        "decision": decision,
        "started_at": started_at,
        "finished_at": finished_at,
        "command": command,
        "returncode": proc.returncode,
        "test_files": TEST_FILES,
        "stdout_tail": proc.stdout[-6000:] if proc.stdout else "",
        "stderr_tail": proc.stderr[-4000:] if proc.stderr else "",
        "expected_outputs": {
            "reports/current/transition_table_gate_test_report.json": True,
            "receipts/current/transition_table_gate_test_receipt.jsonl": True,
            "outputs/transition_table_gate_tests.md": True,
            "dist/run_artifacts/transition-table-gate-tests.zip": True,
        },
    }

    write_outputs(report, proc.stdout, proc.stderr)
    return proc.returncode


def write_outputs(report: dict, stdout: str, stderr: str) -> None:
    write_json(REPORT_PATH, report)

    report_text = json.dumps(report, sort_keys=True)
    receipt = {
        "schema": "stegverse.transition_table_gate_test_receipt.v1",
        "timestamp_utc": utc_now(),
        "stage": "SV002-M11",
        "gate": "transition_table_gate_tests",
        "decision": report["decision"],
        "success": report["success"],
        "report_path": str(REPORT_PATH),
        "report_hash": sha256_text(report_text),
        "test_files": TEST_FILES,
    }
    receipt["receipt_hash"] = sha256_text(json.dumps(receipt, sort_keys=True))
    append_jsonl(RECEIPT_PATH, receipt)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        "\n".join([
            "# Transition Table Gate Tests",
            "",
            f"Decision: `{report['decision']}`",
            f"Success: `{str(report['success']).lower()}`",
            f"Report: `{REPORT_PATH}`",
            f"Receipt: `{RECEIPT_PATH}`",
            "",
            "## Test Files",
            "",
            *[f"- `{path}`" for path in TEST_FILES],
            "",
            "## Command",
            "",
            "```text",
            " ".join(report.get("command", [])) if report.get("command") else "[not executed]",
            "```",
            "",
            "## stdout tail",
            "",
            "```text",
            report.get("stdout_tail", stdout[-6000:] if stdout else ""),
            "```",
            "",
            "## stderr tail",
            "",
            "```text",
            report.get("stderr_tail", stderr[-4000:] if stderr else ""),
            "```",
            "",
        ]) + "\n",
        encoding="utf-8",
    )

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARTIFACT_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [REPORT_PATH, RECEIPT_PATH, OUTPUT_PATH]:
            if path.exists():
                archive.write(path, path.as_posix())


if __name__ == "__main__":
    raise SystemExit(main())
