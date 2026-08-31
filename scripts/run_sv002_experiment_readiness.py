#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPORT = Path("reports/current/sv002_experiment_readiness_report.json")
RECEIPT = Path("receipts/current/sv002_experiment_readiness_receipt.jsonl")


def run(command: list[str]) -> dict:
    completed = subprocess.run(command, text=True, capture_output=True)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-8000:],
        "stderr": completed.stderr[-8000:],
        "passed": completed.returncode == 0,
    }


def main() -> int:
    checks = [
        run([sys.executable, "-m", "unittest", "tests.test_management_reviewer_authority_reconstruction"]),
        run([sys.executable, "tools/reconstruct_management_reviewer_authority.py", "--repo-root", "."]),
        run([sys.executable, "tools/check_ecosystem_component_version.py"]),
    ]
    reconstruction = {}
    reconstruction_path = Path("reports/current/management_reviewer_authority_reconstruction_report.json")
    if reconstruction_path.exists():
        try:
            reconstruction = json.loads(reconstruction_path.read_text(encoding="utf-8"))
        except Exception:
            reconstruction = {"decision": "UNREADABLE"}

    terminal = "ALLOW_EXPERIMENT_READINESS" if all(check["passed"] for check in checks) else "FAIL_CLOSED"
    report = {
        "schema": "stegverse.sv002_experiment_readiness_report.v1",
        "repository": "StegVerse-002/core-lite",
        "terminal_decision": terminal,
        "checks": checks,
        "reviewer_authority_reconstruction": {
            "decision": reconstruction.get("decision"),
            "authority_boundary": reconstruction.get("authority_boundary", {}),
        },
        "experiment_boundary": {
            "source_ready_does_not_mean_runtime_activated": True,
            "workflow_pass_does_not_mean_runtime_activated": True,
            "review_evidence_does_not_form_quorum": True,
            "llm_output_is_bounded_input_not_authority": True,
            "no_private_or_owner_authority_evidence_fabricated": True,
        },
        "remaining_external_gate": (
            "none_for_source_readiness"
            if terminal == "ALLOW_EXPERIMENT_READINESS"
            else "repair_failed_readiness_check"
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    with RECEIPT.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "schema": "stegverse.sv002_experiment_readiness_receipt.v1",
            "repository": report["repository"],
            "terminal_decision": terminal,
            "authority_effect": "NONE",
            "runtime_activation_claimed": False,
            "report": REPORT.as_posix(),
        }, sort_keys=True) + "\n")
    print(f"SV002_EXPERIMENT_READINESS={terminal}")
    print(f"Wrote {REPORT.as_posix()}")
    print(f"Wrote {RECEIPT.as_posix()}")
    return 0 if terminal == "ALLOW_EXPERIMENT_READINESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
