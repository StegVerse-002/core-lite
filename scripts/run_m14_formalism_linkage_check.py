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

from core_lite.transition_table.formalism_refs import validate_policy_formalism_linkage

POLICY_PATH = Path("core_lite/transition_table/policy.json")
REPORT_PATH = Path("reports/current/m14_formalism_linkage_report.json")
RECEIPT_PATH = Path("receipts/current/m14_formalism_linkage_receipt.jsonl")
OUTPUT_PATH = Path("outputs/m14_formalism_linkage.md")
ARTIFACT_PATH = Path("dist/run_artifacts/m14-formalism-linkage.zip")


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def main() -> int:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    status = validate_policy_formalism_linkage(policy)
    report = {
        "schema": "stegverse.m14_formalism_linkage_report.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "ALLOW" if status.ok else "FAIL_CLOSED",
        "passed": status.ok,
        "errors": status.errors,
        "warnings": status.warnings,
        "policy_path": str(POLICY_PATH),
        "formalism_refs": policy.get("formalism_refs", []),
        "boundary_metrics": policy.get("boundary_metrics", {}),
        "decision_regions": policy.get("decision_regions", {}),
    }
    write_json(REPORT_PATH, report)
    receipt = {
        "schema": "stegverse.m14_formalism_linkage_receipt.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "SV002-M14",
        "gate": "formalism-linkage-check",
        "decision": report["decision"],
        "passed": report["passed"],
        "report_path": str(REPORT_PATH),
        "report_hash": sha256_bytes(json.dumps(report, sort_keys=True).encode("utf-8")),
    }
    receipt["receipt_hash"] = sha256_bytes(json.dumps(receipt, sort_keys=True).encode("utf-8"))
    append_jsonl(RECEIPT_PATH, receipt)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        "# M14 Formalism Linkage Check\n\n"
        f"Passed: `{str(report['passed']).lower()}`\n\n"
        f"Decision: `{report['decision']}`\n\n"
        f"Errors: `{report['errors']}`\n\n"
        f"Warnings: `{report['warnings']}`\n",
        encoding="utf-8",
    )
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARTIFACT_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [REPORT_PATH, RECEIPT_PATH, OUTPUT_PATH, POLICY_PATH]:
            if path.exists():
                archive.write(path, path.as_posix())
    print(json.dumps({"passed": report["passed"], "decision": report["decision"], "errors": report["errors"], "report": str(REPORT_PATH)}, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
