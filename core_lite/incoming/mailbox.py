"""Guarded incoming mailbox for StegVerse-002 bundle submissions."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core_lite.bundles.ingest import BundleIngestor
from core_lite.receipts import append_receipt

RESERVED_NAMES = {".gitkeep", "README.md", "processed", "rejected"}


class IncomingMailbox:
    def __init__(self, repo_root: str | Path = ".", incoming_dir: str | Path = "incoming", *, entity: str = "StegVerse-002", stage: str = "SV002-M12", dry_run: bool = False) -> None:
        self.repo_root = Path(repo_root)
        self.incoming_dir = self.repo_root / Path(incoming_dir)
        self.processed_dir = self.incoming_dir / "processed"
        self.rejected_dir = self.incoming_dir / "rejected"
        self.entity = entity
        self.stage = stage
        self.dry_run = dry_run

    def process(self) -> dict[str, Any]:
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.rejected_dir.mkdir(parents=True, exist_ok=True)
        report: dict[str, Any] = {
            "schema": "stegverse.incoming_mailbox_report.v1",
            "entity": self.entity,
            "stage": self.stage,
            "started": datetime.now(timezone.utc).isoformat(),
            "incoming_dir": str(self.incoming_dir.relative_to(self.repo_root)),
            "dry_run": self.dry_run,
            "status": "success",
            "decision": "ALLOW",
            "basis": "Incoming mailbox processed with governed bundle ingestion.",
            "processed": [],
            "rejected": [],
            "ignored": [],
            "errors": [],
        }
        for item in sorted(self.incoming_dir.iterdir(), key=lambda p: p.name):
            if item.name in RESERVED_NAMES:
                report["ignored"].append({"path": self._rel(item), "reason": "reserved_mailbox_path"})
                continue
            if item.is_dir():
                report["rejected"].append({"path": self._rel(item), "reason": "directory_not_processed"})
                continue
            if item.suffix.lower() != ".zip":
                report["rejected"].append({"path": self._rel(item), "reason": "unsupported_file_type"})
                self._relocate(item, self.rejected_dir / item.name)
                continue
            ingestor = BundleIngestor(self.repo_root, entity=self.entity, stage=self.stage, dry_run=self.dry_run)
            ingest_report = ingestor.ingest(item.relative_to(self.repo_root))
            entry = {
                "path": self._rel(item),
                "decision": ingest_report.get("decision"),
                "status": ingest_report.get("status"),
                "errors": ingest_report.get("errors", []),
                "bundle_name": ingest_report.get("bundle_name", ""),
            }
            if ingest_report.get("decision") in {"ALLOW", "ALLOW_DRY_RUN"}:
                report["processed"].append(entry)
                if not self.dry_run and item.exists():
                    self._relocate(item, self.processed_dir / item.name)
            else:
                report["rejected"].append(entry)
                if not self.dry_run and item.exists():
                    self._relocate(item, self.rejected_dir / item.name)
        report["completed"] = datetime.now(timezone.utc).isoformat()
        self._write_outputs(report)
        return report

    def _write_outputs(self, report: dict[str, Any]) -> None:
        report_path = self.repo_root / "reports" / "current" / "incoming_mailbox_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        output_path = self.repo_root / "outputs" / "incoming_mailbox.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"# Incoming Mailbox Report\n\nDecision: `{report['decision']}`\n\nProcessed: `{len(report['processed'])}`\n\nRejected: `{len(report['rejected'])}`\n\nIgnored: `{len(report['ignored'])}`\n", encoding="utf-8")
        receipt = append_receipt(
            str(self.repo_root / "receipts" / "current" / "incoming_mailbox_receipt.jsonl"),
            actor=self.entity,
            stage=self.stage,
            gate="incoming-mailbox",
            task_id="sv002.incoming.mailbox.process",
            action="process-incoming-mailbox",
            decision=report["decision"],
            basis=report["basis"],
            target_path=report["incoming_dir"],
            mutation_to_target_performed=not self.dry_run,
            incoming_submission_authority=False,
            outputs=["reports/current/incoming_mailbox_report.json", "receipts/current/incoming_mailbox_receipt.jsonl", "outputs/incoming_mailbox.md"],
            stop_condition="Incoming mailbox scanned; bundle submissions delegated to BundleIngestor.",
        )
        report["receipt"] = receipt.to_dict()
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _relocate(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            target = target.with_name(f"{target.stem}.{stamp}{target.suffix}")
        shutil.move(str(source), str(target))

    def _rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)
