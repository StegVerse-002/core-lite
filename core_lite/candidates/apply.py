from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core_lite.bundles.ingest import BundleIngestor
from core_lite.receipts import append_receipt


class CandidateApplier:
    """Apply candidate only after matching ALLOW_CANDIDATE_REVIEW report."""

    def __init__(self, repo_root: str | Path = ".", *, entity: str = "StegVerse-002", stage: str = "SV002-M13") -> None:
        self.repo_root = Path(repo_root)
        self.entity = entity
        self.stage = stage

    def apply(self, candidate_ref_path: str | Path, review_report_path: str | Path) -> dict[str, Any]:
        rel_ref = Path(candidate_ref_path)
        rel_review = Path(review_report_path)
        ref_path = self.repo_root / rel_ref
        review_path = self.repo_root / rel_review
        report: dict[str, Any] = {
            "schema": "stegverse.candidate_apply_report.v1",
            "entity": self.entity,
            "stage": self.stage,
            "candidate_ref_path": str(rel_ref),
            "review_report_path": str(rel_review),
            "started": datetime.now(timezone.utc).isoformat(),
            "decision": "FAIL_CLOSED",
            "basis": "",
            "candidate": {},
            "review": {},
            "ingest_report": {},
            "errors": [],
        }
        if not ref_path.exists():
            report["errors"].append("candidate_ref_missing")
        if not review_path.exists():
            report["errors"].append("review_report_missing")
        if report["errors"]:
            return self._finish(report, "FAIL_CLOSED", ";".join(report["errors"]))
        candidate = json.loads(ref_path.read_text(encoding="utf-8"))
        review = json.loads(review_path.read_text(encoding="utf-8"))
        report["candidate"] = candidate
        report["review"] = review
        if review.get("decision") != "ALLOW_CANDIDATE_REVIEW":
            report["errors"].append("review_not_allow_candidate_review")
            return self._finish(report, "DENY_INSTALL", "review_not_allow_candidate_review")
        if review.get("candidate", {}).get("candidate_id") != candidate.get("candidate_id"):
            report["errors"].append("candidate_id_mismatch")
            return self._finish(report, "DENY_INSTALL", "candidate_id_mismatch")
        bundle_path = candidate.get("bundle_path")
        if not bundle_path:
            report["errors"].append("bundle_path_missing")
            return self._finish(report, "DENY_INSTALL", "bundle_path_missing")
        ingest_report = BundleIngestor(self.repo_root, entity=self.entity, stage=self.stage, dry_run=False).ingest(bundle_path)
        report["ingest_report"] = ingest_report
        if ingest_report.get("decision") == "ALLOW":
            return self._finish(report, "ALLOW_INSTALL", "candidate_apply_ingestion_allowed")
        return self._finish(report, "DENY_INSTALL", f"candidate_apply_ingestion_not_allowed:{ingest_report.get('decision')}")

    def _finish(self, report: dict[str, Any], decision: str, basis: str) -> dict[str, Any]:
        report["decision"] = decision
        report["basis"] = basis
        report["completed"] = datetime.now(timezone.utc).isoformat()
        report_path = self.repo_root / "reports/current/candidate_bundle_apply_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt = append_receipt(
            str(self.repo_root / "receipts/current/candidate_bundle_apply_receipt.jsonl"),
            actor=self.entity,
            stage=self.stage,
            gate="candidate-apply",
            task_id="stegverse.candidate.intake.apply",
            action="apply-candidate",
            decision=decision,
            basis=basis,
            target_path=report["candidate_ref_path"],
            mutation_to_target_performed=(decision == "ALLOW_INSTALL"),
            workflow_change_authority=False,
            incoming_submission_authority=False,
            outputs=["reports/current/candidate_bundle_apply_report.json", "receipts/current/candidate_bundle_apply_receipt.jsonl"],
            stop_condition="Candidate apply decision emitted and receipt written.",
        )
        report["receipt"] = receipt.to_dict()
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report
