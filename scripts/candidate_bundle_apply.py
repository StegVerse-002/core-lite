#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core_lite.candidates import CandidateApplier


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a candidate bundle after matching approved review.")
    parser.add_argument("--candidate-ref", default="candidate_ref.json")
    parser.add_argument("--review-report", default="reports/current/candidate_bundle_review_report.json")
    args = parser.parse_args()
    report = CandidateApplier(REPO_ROOT).apply(args.candidate_ref, args.review_report)
    print(json.dumps({"decision": report["decision"], "basis": report["basis"], "report": "reports/current/candidate_bundle_apply_report.json"}, indent=2))
    return 0 if report["decision"] == "ALLOW_INSTALL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
