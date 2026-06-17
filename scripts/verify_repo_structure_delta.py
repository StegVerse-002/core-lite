#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_STRUCTURE = {
    "core_m11_bundle_ingestion": [
        "core_lite/bundles/ingest.py",
        "scripts/run_bundle_ingestion_smoke_test.py",
        "reports/current/bundle_ingestion_smoke_test_report.json",
    ],
    "core_m12_incoming_mailbox": [
        "core_lite/incoming/__init__.py",
        "core_lite/incoming/mailbox.py",
        "scripts/run_incoming_mailbox.py",
        "scripts/run_m12_incoming_mailbox_tests.py",
        "tests/test_incoming_mailbox.py",
    ],
    "core_m13_candidate_review_apply": [
        "core_lite/candidates/__init__.py",
        "core_lite/candidates/review.py",
        "core_lite/candidates/apply.py",
        "scripts/candidate_bundle_apply.py",
        "scripts/run_m13_candidate_review_apply_tests.py",
        "tests/test_candidate_review_apply.py",
    ],
    "core_m14_formalism_linkage": [
        "core_lite/transition_table/formalism_refs.py",
        "scripts/run_m14_formalism_linkage_check.py",
        "tests/test_formalism_linkage.py",
    ],
    "core_m15_sdk_cli": [
        "core_lite/sdk/__init__.py",
        "core_lite/sdk/client.py",
        "scripts/core_lite_cli.py",
        "scripts/run_m15_sdk_cli_tests.py",
        "tests/test_sdk_cli_surface.py",
    ],
    "core_m16_activation_evidence": [
        "scripts/run_activation_evidence_export.py",
        "docs/M16_ACTIVATION_EVIDENCE_EXPORT.md",
    ],
    "stable_dispatcher_catalog": [
        "tools/tasks/task_catalog.json",
        "tools/scripts/register_task_additions.py",
    ],
}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compute_structure_score(repo_root: Path) -> dict:
    groups = []
    total = 0
    present = 0
    missing_all: list[str] = []
    for name, paths in REQUIRED_STRUCTURE.items():
        group_present = []
        group_missing = []
        for rel in paths:
            total += 1
            if (repo_root / rel).exists():
                present += 1
                group_present.append(rel)
            else:
                group_missing.append(rel)
                missing_all.append(rel)
        groups.append({
            "group": name,
            "present_count": len(group_present),
            "missing_count": len(group_missing),
            "present": group_present,
            "missing": group_missing,
        })
    score = round((present / total) * 100, 2) if total else 0.0
    return {"score_percent": score, "present_count": present, "total_count": total, "missing": missing_all, "groups": groups}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify repo structure delta against reported repo completion line.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--reported-repo-complete", type=float, default=83.0)
    parser.add_argument("--report", default="reports/current/repo_structure_delta_report.json")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    result = compute_structure_score(repo_root)
    delta = round(result["score_percent"] - args.reported_repo_complete, 2)
    report = {
        "schema": "stegverse.repo_structure_delta_report.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "reported_repo_complete_percent": args.reported_repo_complete,
        "verified_structure_percent": result["score_percent"],
        "delta_percent": delta,
        "present_count": result["present_count"],
        "total_count": result["total_count"],
        "missing": result["missing"],
        "groups": result["groups"],
        "basis": "Compares progress line 2 against required file-structure presence for M11-M16 activation surface.",
    }
    write_json(Path(args.report), report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not result["missing"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
