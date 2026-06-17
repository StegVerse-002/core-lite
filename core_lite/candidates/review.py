from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core_lite.receipts import append_receipt


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class CandidateReviewer:
    """Evidence-only candidate review. Does not install files."""

    def __init__(self, repo_root: str | Path = ".", *, entity: str = "StegVerse-002", stage: str = "SV002-M13") -> None:
        self.repo_root = Path(repo_root)
        self.entity = entity
        self.stage = stage

    def review(self, candidate_ref_path: str | Path) -> dict[str, Any]:
        rel_ref = Path(candidate_ref_path)
        ref_path = self.repo_root / rel_ref
        report: dict[str, Any] = {
            "schema": "stegverse.candidate_review_report.v1",
            "entity": self.entity,
            "stage": self.stage,
            "candidate_ref_path": str(rel_ref),
            "started": datetime.now(timezone.utc).isoformat(),
            "decision": "FAIL_CLOSED",
            "basis": "",
            "candidate": {},
            "errors": [],
        }
        if not ref_path.exists():
            report["errors"].append("candidate_ref_missing")
            return self._finish(report, "FAIL_CLOSED", "candidate_ref_missing")
        try:
            candidate = json.loads(ref_path.read_text(encoding="utf-8"))
        except Exception as exc:
            report["errors"].append(f"candidate_ref_parse_error:{exc}")
            return self._finish(report, "FAIL_CLOSED", "candidate_ref_parse_error")
        report["candidate"] = candidate
        for field in ["schema", "candidate_id", "bundle_path", "task_id", "proposed_files"]:
            if not candidate.get(field):
                report["errors"].append(f"missing_required_field:{field}")
        if candidate.get("schema") != "stegverse.candidate_ref.v1":
            report["errors"].append("schema_mismatch")
        if report["errors"]:
            return self._finish(report, "DENY_CANDIDATE", ";".join(report["errors"]))
        report["candidate_ref_hash"] = sha256_file(ref_path)
        return self._finish(report, "ALLOW_CANDIDATE_REVIEW", "candidate_reference_shape_valid")

    def _finish(self, report: dict[str, Any], decision: str, basis: str) -> dict[str, Any]:
        report["decision"] = decision
        report["basis"] = basis
        report["completed"] = datetime.now(timezone.utc).isoformat()
        report_path = self.repo_root / "reports/current/candidate_bundle_review_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt = append_receipt(
            str(self.repo_root / "receipts/current/candidate_bundle_review_receipt.jsonl"),
            actor=self.entity,
            stage=self.stage,
            gate="candidate-review",
            task_id="stegverse.candidate.intake.review",
            action="review-candidate",
            decision=decision,
            basis=basis,
            target_path=report["candidate_ref_path"],
            mutation_to_target_performed=False,
            workflow_change_authority=False,
            incoming_submission_authority=False,
            outputs=["reports/current/candidate_bundle_review_report.json", "receipts/current/candidate_bundle_review_receipt.jsonl"],
            stop_condition="Candidate review decision emitted and receipt written; no install performed.",
        )
        report["receipt"] = receipt.to_dict()
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report
