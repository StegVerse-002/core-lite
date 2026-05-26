"""Governed bundle ingestion engine for StegVerse-002 core-lite."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .manifest import BundleManifest, find_manifest_in_directory, load_manifest_file
from .validate import normalize_bundle_path, validate_manifest, validate_target_path
from .quarantine import quarantine_bundle
from .receipts import emit_ingestion_receipt


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BundleIngestor:
    def __init__(
        self,
        repo_root: Path,
        *,
        entity: str = "StegVerse-002",
        stage: str = "SV002-M10",
        dry_run: bool = False,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.entity = entity
        self.stage = stage
        self.dry_run = dry_run

    def ingest(self, input_path: str | Path) -> dict[str, Any]:
        source = self.repo_root / Path(input_path)
        started = datetime.now(timezone.utc).isoformat()
        report: dict[str, Any] = {
            "schema": "stegverse.bundle_ingest_report.v1",
            "entity": self.entity,
            "stage": self.stage,
            "input_path": str(input_path),
            "started": started,
            "dry_run": self.dry_run,
            "status": "unknown",
            "decision": "FAIL_CLOSED",
            "installed": [],
            "rejected": [],
            "errors": [],
        }

        if not source.exists():
            report["status"] = "failure"
            report["errors"].append("input_path_not_found")
            return self._finish(report, "FAIL_CLOSED", "Input path not found.")

        try:
            if source.is_file() and zipfile.is_zipfile(source):
                with tempfile.TemporaryDirectory() as td:
                    work = Path(td) / "bundle"
                    work.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(source) as z:
                        z.extractall(work)
                    self._ingest_directory(work, report)
            elif source.is_dir():
                self._ingest_directory(source, report)
            else:
                report["status"] = "failure"
                report["errors"].append("unsupported_input_type")
                q = quarantine_bundle(self.repo_root, source, "unsupported_input_type")
                report["quarantine_path"] = str(q.relative_to(self.repo_root))
                return self._finish(report, "FAIL_CLOSED", "Unsupported input type.")

        except Exception as exc:
            report["status"] = "failure"
            report["errors"].append(f"exception:{exc}")
            q = quarantine_bundle(self.repo_root, source, f"exception:{exc}")
            report["quarantine_path"] = str(q.relative_to(self.repo_root))
            return self._finish(report, "FAIL_CLOSED", f"Ingestion exception: {exc}")

        if report["errors"]:
            report["status"] = "failure"
            report["decision"] = "FAIL_CLOSED"
            q = quarantine_bundle(self.repo_root, source, ";".join(report["errors"]))
            report["quarantine_path"] = str(q.relative_to(self.repo_root))
            return self._finish(report, "FAIL_CLOSED", "Bundle failed validation.")

        report["status"] = "success"
        report["decision"] = "ALLOW_DRY_RUN" if self.dry_run else "ALLOW"
        return self._finish(report, report["decision"], "Bundle validated and processed.")

    def _ingest_directory(self, bundle_dir: Path, report: dict[str, Any]) -> None:
        manifest_path = find_manifest_in_directory(bundle_dir)
        if not manifest_path:
            report["errors"].append("manifest_missing")
            return

        manifest = load_manifest_file(manifest_path)
        report["bundle_name"] = manifest.bundle_name
        report["manifest_path"] = str(manifest_path)
        report["manifest"] = manifest.raw

        ok, errors = validate_manifest(manifest)
        if not ok:
            report["errors"].extend(errors)
            return

        for item in manifest.files:
            rel = normalize_bundle_path(item.path)
            src = bundle_dir / rel
            if not src.exists() or not src.is_file():
                report["rejected"].append({"path": rel, "reason": "source_file_missing"})
                report["errors"].append(f"source_file_missing:{rel}")
                continue

            actual_hash = sha256_file(src)
            if item.sha256 and actual_hash.lower() != item.sha256.lower().replace("sha256:", ""):
                report["rejected"].append({
                    "path": rel,
                    "reason": "sha256_mismatch",
                    "expected": item.sha256,
                    "actual": actual_hash,
                })
                report["errors"].append(f"sha256_mismatch:{rel}")
                continue

            ok_path, reason = validate_target_path(rel, manifest)
            if not ok_path:
                report["rejected"].append({"path": rel, "reason": reason})
                report["errors"].append(f"path_denied:{rel}:{reason}")
                continue

            target = self.repo_root / rel
            if not self.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)

            report["installed"].append({
                "path": rel,
                "sha256": actual_hash,
                "bytes": src.stat().st_size,
                "dry_run": self.dry_run,
            })

    def _finish(self, report: dict[str, Any], decision: str, basis: str) -> dict[str, Any]:
        report["decision"] = decision
        report["basis"] = basis
        report["completed"] = datetime.now(timezone.utc).isoformat()

        reports_dir = self.repo_root / "reports" / "current"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / "bundle_ingest_report.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        events_dir = self.repo_root / "tracking" / "ingestion_events"
        events_dir.mkdir(parents=True, exist_ok=True)
        event_path = events_dir / "bundle_ingest_events.jsonl"
        with event_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "schema": "stegverse.bundle_ingest_event.v1",
                "timestamp": report["completed"],
                "entity": self.entity,
                "stage": self.stage,
                "input_path": report["input_path"],
                "decision": decision,
                "status": report["status"],
                "installed_count": len(report.get("installed", [])),
                "rejected_count": len(report.get("rejected", [])),
            }, sort_keys=True) + "\n")

        receipt = emit_ingestion_receipt(
            self.repo_root,
            actor=self.entity,
            stage=self.stage,
            decision=decision,
            basis=basis,
            bundle_name=report.get("bundle_name", ""),
            report_path="reports/current/bundle_ingest_report.json",
        )
        report["receipt"] = receipt
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
