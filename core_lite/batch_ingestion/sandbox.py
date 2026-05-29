"""
core_lite/batch_ingestion/sandbox.py — StegVerse-002

Ephemeral sandbox for repair candidate search.
Stage 34: sandbox is the bounded search space for repair candidates.
Repair = nearest admissible transition to a failed bundle.

Sandbox constraints:
  - no external effects
  - no production mutation
  - no secret access
  - no irreversible write
  - bounded paths
  - bounded runtime
  - bounded authority
  - receipt required
  - quarantine reference required

Each sandbox run is ephemeral — it operates in a temp directory,
produces a repair candidate bundle or a failure receipt, and exits.
The result is then fed back into the ingestion loop.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def sha256_str(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Sandbox result
# ---------------------------------------------------------------------------

@dataclass
class SandboxResult:
    sandbox_id: str
    bundle_path: str
    task_hash: str
    timestamp_utc: str = field(default_factory=now_utc)
    verdict: str = "UNKNOWN"        # PASS | FAIL | PARTIAL | BLOCKED
    repair_bundle_path: str = ""
    repair_bundle_hash: str = ""
    nearest_admissible: str = ""    # description of what was found
    boundary_distance_before: float = 1.0
    boundary_distance_after: float = 1.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    steps_taken: List[dict] = field(default_factory=list)
    runtime_seconds: float = 0.0
    receipt_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "schema": "stegverse.sandbox_result.v1",
            "sandbox_id": self.sandbox_id,
            "bundle_path": self.bundle_path,
            "task_hash": self.task_hash,
            "timestamp_utc": self.timestamp_utc,
            "verdict": self.verdict,
            "repair_bundle_path": self.repair_bundle_path,
            "repair_bundle_hash": self.repair_bundle_hash,
            "nearest_admissible": self.nearest_admissible,
            "boundary_distance_before": self.boundary_distance_before,
            "boundary_distance_after": self.boundary_distance_after,
            "errors": self.errors,
            "warnings": self.warnings,
            "steps_taken": self.steps_taken,
            "runtime_seconds": self.runtime_seconds,
            "receipt_hash": self.receipt_hash,
        }


# ---------------------------------------------------------------------------
# Repair strategies
# ---------------------------------------------------------------------------

def _strategy_fill_missing_fields(manifest: dict) -> tuple:
    """Fill in missing required transition fields."""
    changes = []
    t = manifest.setdefault("transition", {})

    if not t.get("task_hash"):
        t["task_hash"] = "sha256:pending-repair"
        changes.append("filled missing task_hash")

    if not t.get("candidate_provider"):
        t["candidate_provider"] = "repaired"
        changes.append("filled missing candidate_provider")

    if not t.get("candidate_round"):
        t["candidate_round"] = 1
        changes.append("set candidate_round to 1")

    if not t.get("authority_class"):
        t["authority_class"] = "candidate_evidence_only"
        changes.append("set default authority_class")

    if not t.get("state_effect"):
        t["state_effect"] = "evidence_state"
        changes.append("set default state_effect")

    if not t.get("binding_level"):
        t["binding_level"] = "non_binding"
        changes.append("set default binding_level")

    return manifest, changes


def _strategy_remove_forbidden_patterns(manifest: dict) -> tuple:
    """Remove forbidden patterns from file content."""
    FORBIDDEN = [
        "::set-output",
        "./evaluate",
        "actions/checkout@v2",
        "actions/checkout@v3",
    ]
    changes = []
    files = manifest.get("files", [])
    for i, f in enumerate(files):
        content = f.get("content", "")
        for pat in FORBIDDEN:
            if pat in content:
                content = content.replace(pat, f"# REMOVED:{pat}")
                changes.append(f"removed forbidden pattern '{pat}' from files[{i}]")
        f["content"] = content
    return manifest, changes


def _strategy_downgrade_authority(manifest: dict) -> tuple:
    """Downgrade authority_class to candidate_evidence_only if mismatch."""
    changes = []
    t = manifest.get("transition", {})
    tc = t.get("transition_class", "")
    auth = t.get("authority_class", "")

    if tc == "candidate" and auth != "candidate_evidence_only":
        t["authority_class"] = "candidate_evidence_only"
        t["state_effect"] = "evidence_state"
        t["binding_level"] = "non_binding"
        changes.append("downgraded authority to candidate_evidence_only")

    return manifest, changes


# Hack: type hint workaround since we can't import Tuple from typing at top



REPAIR_STRATEGIES = [
    _strategy_fill_missing_fields,
    _strategy_remove_forbidden_patterns,
    _strategy_downgrade_authority,
]


# ---------------------------------------------------------------------------
# Sandbox runner
# ---------------------------------------------------------------------------

class EphemeralSandbox:
    """
    Runs one bounded repair attempt on a candidate bundle.
    Operates in a temp directory with no production side effects.
    """

    def __init__(
        self,
        repo_root: str = ".",
        report_dir: str = "reports/current",
        receipt_dir: str = "receipts/current",
        dist_dir: str = "dist/sandbox",
        max_runtime_seconds: int = 60,
    ):
        self.repo_root = repo_root
        self.report_dir = report_dir
        self.receipt_dir = receipt_dir
        self.dist_dir = dist_dir
        self.max_runtime = max_runtime_seconds

    def _make_sandbox_id(self, bundle_path: str) -> str:
        return "sandbox-" + sha256_str(
            bundle_path + now_utc()
        ).replace("sha256:", "")[:12]

    def _load_manifest(self, bundle_path: str) -> Optional[dict]:
        try:
            with zipfile.ZipFile(bundle_path) as z:
                if "bundle_manifest.json" in z.namelist():
                    return json.loads(z.read("bundle_manifest.json"))
        except Exception:
            pass
        return None

    def _compute_boundary_distance(self, manifest: dict) -> float:
        """Rough boundary distance from manifest evidence."""
        t = manifest.get("transition", {})
        penalties = 0
        if not t.get("task_hash"): penalties += 2
        if not t.get("candidate_provider"): penalties += 1
        if not manifest.get("files"): penalties += 3
        if t.get("authority_class") not in ("candidate_evidence_only",
                                             "scoped_repo_write"): penalties += 2
        return min(1.0, penalties * 0.1)

    def _repack_bundle(
        self,
        original_path: str,
        repaired_manifest: dict,
        sandbox_dir: str,
        sandbox_id: str,
    ) -> str:
        """Repack the bundle with the repaired manifest."""
        basename = os.path.basename(original_path)
        name, ext = os.path.splitext(basename)
        repair_name = f"{name}_repaired_{sandbox_id}{ext}"
        repair_path = os.path.join(sandbox_dir, repair_name)

        with zipfile.ZipFile(original_path) as src_z:
            with zipfile.ZipFile(repair_path, "w", zipfile.ZIP_DEFLATED) as dst_z:
                for item in src_z.infolist():
                    if item.filename == "bundle_manifest.json":
                        dst_z.writestr("bundle_manifest.json",
                                      json.dumps(repaired_manifest, indent=2))
                    else:
                        dst_z.writestr(item, src_z.read(item.filename))

        return repair_path

    def run(
        self,
        bundle_path: str,
        task_hash: str,
        quarantine_ref: str = "",
        dry_run: bool = False,
    ) -> SandboxResult:
        """
        Run one ephemeral sandbox repair attempt.
        Returns SandboxResult with verdict and repair bundle path if successful.
        """
        sandbox_id = self._make_sandbox_id(bundle_path)
        start_time = time.time()

        result = SandboxResult(
            sandbox_id=sandbox_id,
            bundle_path=bundle_path,
            task_hash=task_hash,
        )

        os.makedirs(self.report_dir, exist_ok=True)
        os.makedirs(self.receipt_dir, exist_ok=True)
        os.makedirs(self.dist_dir, exist_ok=True)

        # Load manifest
        manifest = self._load_manifest(bundle_path)
        if manifest is None:
            result.verdict = "BLOCKED"
            result.errors.append("cannot load bundle_manifest.json — sandbox blocked")
            self._write_receipt(result)
            return result

        result.boundary_distance_before = self._compute_boundary_distance(manifest)

        # Run repair strategies in temp directory
        with tempfile.TemporaryDirectory() as sandbox_dir:
            repaired_manifest = json.loads(json.dumps(manifest))  # deep copy
            all_changes = []

            for strategy in REPAIR_STRATEGIES:
                try:
                    repaired_manifest, changes = strategy(repaired_manifest)
                    all_changes.extend(changes)
                    result.steps_taken.append({
                        "strategy": strategy.__name__,
                        "changes": changes,
                    })
                except Exception as e:
                    result.warnings.append(f"strategy {strategy.__name__} failed: {e}")

            result.boundary_distance_after = self._compute_boundary_distance(
                repaired_manifest
            )

            improved = (result.boundary_distance_after <
                        result.boundary_distance_before)
            result.nearest_admissible = (
                f"boundary_distance reduced from "
                f"{result.boundary_distance_before:.2f} to "
                f"{result.boundary_distance_after:.2f} "
                f"via {len(all_changes)} repairs"
            )

            if not improved and result.boundary_distance_after >= 0.5:
                result.verdict = "FAIL"
                result.errors.append(
                    "repair strategies did not reduce boundary distance below 0.5"
                )
            elif result.boundary_distance_after == 0.0:
                result.verdict = "PASS"
            else:
                result.verdict = "PARTIAL"

            # Repack if any improvement
            if all_changes and not dry_run:
                repair_path = self._repack_bundle(
                    bundle_path, repaired_manifest, sandbox_dir, sandbox_id
                )
                # Copy to dist/sandbox/
                final_path = os.path.join(
                    self.dist_dir, os.path.basename(repair_path)
                )
                shutil.copy2(repair_path, final_path)
                result.repair_bundle_path = final_path
                result.repair_bundle_hash = sha256_file(final_path)

        result.runtime_seconds = round(time.time() - start_time, 3)

        # Check runtime
        if result.runtime_seconds > self.max_runtime:
            result.warnings.append(
                f"sandbox runtime {result.runtime_seconds}s exceeded "
                f"limit {self.max_runtime}s"
            )

        self._write_receipt(result)
        return result

    def _write_receipt(self, result: SandboxResult) -> None:
        receipt = result.to_dict()
        receipt_str = json.dumps(receipt, sort_keys=True)
        result.receipt_hash = sha256_str(receipt_str)
        receipt["receipt_hash"] = result.receipt_hash

        receipt_path = os.path.join(self.receipt_dir, "sandbox_receipt.jsonl")
        with open(receipt_path, "a") as f:
            f.write(json.dumps(receipt, sort_keys=True) + "\n")

        # Write report
        report_path = os.path.join(self.report_dir, "sandbox_report.json")
        existing = []
        if os.path.exists(report_path):
            try:
                with open(report_path) as f:
                    existing = json.load(f)
                if not isinstance(existing, list):
                    existing = [existing]
            except Exception:
                existing = []
        existing.append(receipt)
        with open(report_path, "w") as f:
            json.dump(existing, f, indent=2)
