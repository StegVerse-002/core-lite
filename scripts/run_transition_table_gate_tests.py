#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


REPORT_PATH = Path("reports/current/transition_table_gate_test_report.json")
RECEIPT_PATH = Path("receipts/current/transition_table_gate_test_receipt.jsonl")
OUTPUT_PATH = Path("outputs/transition_table_gate_tests.md")
ARTIFACT_PATH = Path("dist/run_artifacts/transition-table-gate-tests.zip")

# These files are executable script-style tests. They define run_tests()
# and call it from __main__. They are not pytest-collected test modules.
TEST_COMMANDS = [
    [sys.executable, "tests/test_transition_table_resolver.py"],
    [sys.executable, "tests/test_bundle_ingest_cge_transition_gate.py"],
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


def run_command(command: list[str]) -> dict:
    started_at = utc_now()
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    finished_at = utc_now()
    return {
        "command": command,
        "started_at": started_at,
        "finished_at": finished_at,
        "returncode": proc.returncode,
        "success": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_tail": proc.stdout[-6000:] if proc.stdout else "",
        "stderr_tail": proc.stderr[-4000:] if proc.stderr else "",
    }


def main() -> int:
    overall_started_at = utc_now()

    required_files = [cmd[1] for cmd in TEST_COMMANDS]
    missing = [path for path in required_files if not Path(path).exists()]
    if missing:
        report = {
            "schema": "stegverse.transition_table_gate_test_report.v1",
            "success": False,
            "decision": "FAIL_CLOSED",
            "started_at": overall_started_at,
            "finished_at": utc_now(),
            "reason": "required script-style test files are missing",
            "missing": missing,
            "test_commands": TEST_COMMANDS,
        }
        write_outputs(report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    results = [run_command(command) for command in TEST_COMMANDS]
    success = all(result["success"] for result in results)
    decision = "ALLOW" if success else "FAIL_CLOSED"

    report = {
        "schema": "stegverse.transition_table_gate_test_report.v1",
        "success": success,
        "decision": decision,
        "started_at": overall_started_at,
        "finished_at": utc_now(),
        "runner": "scripts/run_transition_table_gate_tests.py",
        "runner_mode": "script_style_tests_not_pytest_collection",
        "test_commands": TEST_COMMANDS,
        "results": results,
        "expected_outputs": {
            "reports/current/transition_table_gate_test_report.json": True,
            "receipts/current/transition_table_gate_test_receipt.jsonl": True,
            "outputs/transition_table_gate_tests.md": True,
            "dist/run_artifacts/transition-table-gate-tests.zip": True,
        },
    }

    write_outputs(report)

    # Print full compact result to dispatcher stdout so GitHub logs are useful.
    print(json.dumps({
        "success": success,
        "decision": decision,
        "runner_mode": report["runner_mode"],
        "results": [
            {
                "command": " ".join(r["command"]),
                "returncode": r["returncode"],
                "success": r["success"],
                "stdout_tail": r["stdout_tail"],
                "stderr_tail": r["stderr_tail"],
            }
            for r in results
        ],
        "report_path": str(REPORT_PATH),
        "receipt_path": str(RECEIPT_PATH),
        "artifact_path": str(ARTIFACT_PATH),
    }, indent=2, sort_keys=True))

    return 0 if success else 1


def write_outputs(report: dict) -> None:
    write_json(REPORT_PATH, report)

    report_text = json.dumps(report, sort_keys=True)
    receipt = {
        "schema": "stegverse.transition_table_gate_test_receipt.v1",
        "timestamp_utc": utc_now(),
        "stage": "SV002-M11",
        "gate": "transition_table_gate_tests",
        "decision": report["decision"],
        "success": report["success"],
        "runner_mode": report.get("runner_mode", ""),
        "report_path": str(REPORT_PATH),
        "report_hash": sha256_text(report_text),
        "test_commands": report.get("test_commands", []),
    }
    receipt["receipt_hash"] = sha256_text(json.dumps(receipt, sort_keys=True))
    append_jsonl(RECEIPT_PATH, receipt)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Transition Table Gate Tests",
        "",
        f"Decision: `{report['decision']}`",
        f"Success: `{str(report['success']).lower()}`",
        f"Runner mode: `{report.get('runner_mode', '[not executed]')}`",
        f"Report: `{REPORT_PATH}`",
        f"Receipt: `{RECEIPT_PATH}`",
        "",
        "## Commands",
        "",
    ]
    for result in report.get("results", []):
        lines.extend([
            f"### `{' '.join(result['command'])}`",
            "",
            f"Return code: `{result['returncode']}`",
            f"Success: `{str(result['success']).lower()}`",
            "",
            "stdout tail:",
            "",
            "```text",
            result.get("stdout_tail", ""),
            "```",
            "",
            "stderr tail:",
            "",
            "```text",
            result.get("stderr_tail", ""),
            "```",
            "",
        ])

    if not report.get("results"):
        lines.extend([
            "No test command results were produced.",
            "",
            "Reason:",
            "",
            "```text",
            report.get("reason", ""),
            "```",
            "",
        ])

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARTIFACT_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [REPORT_PATH, RECEIPT_PATH, OUTPUT_PATH]:
            if path.exists():
                archive.write(path, path.as_posix())


if __name__ == "__main__":
    raise SystemExit(main())
