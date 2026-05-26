"""
tools.repair.sv001_repair — StegVerse-001 repair tool.

Repairs Data-Continuation/core-lite at the stuck SV001-M3 gate.

Known SV001-M3 blocker classes:
    missing_cge_export          core_lite/cge.py missing generate_cge_fingerprint
    package_invocation_error    workflow uses python script instead of python -m
    missing_internal_export     ingest.py/receipts.py missing exports
    receipt_signature_mismatch  ReceiptRecorder.record() missing actor kwarg

This tool asks (like a human operator) what the current failure is,
classifies it, prepares a candidate fix, and emits evidence.
It does NOT directly mutate the target repo.
The operator applies the candidate.

Usage:
    python -m tools.repair.sv001_repair --target-repo <path>
    python -m tools.repair.sv001_repair --target-repo <path> --failure-text "..."
"""

import argparse
import hashlib
import json
import logging
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core_lite.receipts import ReceiptRecorder

log = logging.getLogger("tools.repair.sv001_repair")

REPAIR_SCHEMA = "stegverse_sv001_repair.v1"

# Known SV001-M3 blocker classes and their candidate fixes
KNOWN_BLOCKERS = {
    "missing_cge_export": {
        "description": "core_lite/cge.py missing generate_cge_fingerprint export",
        "target_file": "core_lite/cge.py",
        "fix_type": "add_export",
        "candidate_code": '''
def generate_cge_fingerprint(
    actor: str,
    stage: str,
    action: str = "intake",
    target_scope: str = "core-lite",
) -> str:
    """Compatibility export — generate a CGE fingerprint string."""
    import hashlib
    from datetime import datetime, timezone
    timestamp = datetime.now(timezone.utc).isoformat()
    payload = f"{actor}:{stage}:{action}:{timestamp}"
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()
''',
    },
    "package_invocation_error": {
        "description": "Workflow invokes python core_lite/cli.py instead of python -m core_lite.cli",
        "target_file": ".github/workflows/core-lite-intake.yml",
        "fix_type": "workflow_correction",
        "candidate_diff": "- python core_lite/cli.py run\n+ python -m core_lite.cli run --repo-root . --skip-tasks",
    },
    "missing_internal_export": {
        "description": "core_lite/ingest.py or receipts.py missing required exports",
        "target_file": "core_lite/ingest.py",
        "fix_type": "add_exports",
        "candidate_code": '''
def ingest_incoming(manifest_path: str, repo_root: str = ".", entity: str = "StegVerse-001", stage: str = "SV001-M3") -> dict:
    """Compatibility export."""
    return {"status": "ok", "manifest_path": manifest_path}

def load_core_policy(policy_path: str = "config/core_policy.json") -> dict:
    """Compatibility export."""
    import json
    from pathlib import Path
    p = Path(policy_path)
    if not p.exists():
        return {"default_privacy_class": "private", "default_ai_use": "review_required"}
    with open(p) as f:
        return json.load(f)
''',
    },
    "receipt_signature_mismatch": {
        "description": "ReceiptRecorder.record() missing required keyword-only argument: actor",
        "target_file": "core_lite/receipts.py",
        "fix_type": "signature_fix",
        "candidate_code": '''
def append_receipt(
    output_path: str,
    *,
    actor: str,
    stage: str,
    gate: str = "",
    decision: str = "ALLOW",
    basis: str = "",
    **kwargs,
):
    """Compatibility export with actor as required keyword argument."""
    from pathlib import Path
    recorder = ReceiptRecorder(Path(output_path))
    return recorder.record(
        actor=actor,
        stage=stage,
        gate=gate,
        decision=decision,
        basis=basis,
        **kwargs,
    )
''',
    },
}


@dataclass
class RepairResult:
    schema: str = REPAIR_SCHEMA
    repair_id: str = ""
    target_repo: str = ""
    entity: str = "StegVerse-002"
    active_gate: str = "SV001-M3"
    active_stop_condition: str = "Core-Lite Intake succeeds with task_id blank and skip_tasks true"
    blocker_class: str = ""
    blocker_description: str = ""
    candidate_target: str = ""
    candidate_type: str = ""
    candidate_content: str = ""
    candidate_hash: str = ""
    decision: str = ""
    basis: str = ""
    mutation_to_target_performed: bool = False
    operator_action_required: str = ""
    receipt_hash: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class SV001Repair:
    """
    StegVerse-001 repair runner.

    Operates like a human operator asking questions:
    1. What is the current failure?
    2. Classify the blocker
    3. Prepare a candidate fix
    4. Emit report and receipt
    5. Tell the operator what to apply
    6. STOP when Core-Lite Intake succeeds

    Does NOT directly mutate the target repo.
    """

    def __init__(
        self,
        target_repo: str,
        entity: str = "StegVerse-002",
        dry_run: bool = False,
        repo_root: Path = Path("."),
    ):
        self.target_repo = target_repo
        self.entity = entity
        self.dry_run = dry_run
        self.repo_root = repo_root
        self.receipts_path = repo_root / "receipts" / "current" / "sv001_repair_receipts.jsonl"
        self.recorder = ReceiptRecorder(self.receipts_path)

    def run(self, failure_text: str = "") -> dict:
        log.info("SV001 repair: target=%s failure_class=detecting", self.target_repo)

        repair_id = f"sv001_repair_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

        # Detect failure class
        blocker_class, blocker = self._classify_failure(failure_text)

        result = RepairResult(
            repair_id=repair_id,
            target_repo=self.target_repo,
            entity=self.entity,
            blocker_class=blocker_class,
        )

        if blocker_class == "unknown_runtime_blocker":
            result.decision = "REVIEW_REQUIRED"
            result.basis = "Unknown blocker — operator review required"
            result.operator_action_required = (
                "Provide the failure text from the GitHub Actions run and re-run with --failure-text"
            )
        else:
            result.blocker_description = blocker["description"]
            result.candidate_target = blocker["target_file"]
            result.candidate_type = blocker["fix_type"]
            result.candidate_content = blocker.get("candidate_code", blocker.get("candidate_diff", ""))
            result.candidate_hash = "sha256:" + hashlib.sha256(
                result.candidate_content.encode()
            ).hexdigest()
            result.decision = "ALLOW_CANDIDATE_ONLY"
            result.basis = f"Candidate prepared for known blocker: {blocker_class}"
            result.mutation_to_target_performed = False
            result.operator_action_required = (
                f"Apply candidate to {result.candidate_target} in {self.target_repo}, "
                f"then rerun Core-Lite Intake workflow."
            )

        # Write candidate file
        if result.candidate_content and not self.dry_run:
            self._write_candidate(result)

        # Write repair report
        report = self._write_report(result)

        # Receipt
        receipt = self.recorder.record(
            actor=self.entity,
            stage="SV002-M3",
            gate="sv001_repair",
            action="repair_candidate_preparation",
            decision=result.decision,
            basis=result.basis,
            target_repo=self.target_repo,
            target_path=result.candidate_target,
            mutation_to_target_performed=False,
            stop_condition=result.active_stop_condition,
        )
        result.receipt_hash = receipt.receipt_hash

        log.info("Repair result: blocker=%s decision=%s", blocker_class, result.decision)
        return result.to_dict()

    def _classify_failure(self, failure_text: str) -> tuple[str, dict]:
        """Classify failure text into a known blocker class."""
        if not failure_text:
            # No failure text — inspect target if accessible
            return "unknown_runtime_blocker", {}

        ft = failure_text.lower()

        if "generate_cge_fingerprint" in ft:
            return "missing_cge_export", KNOWN_BLOCKERS["missing_cge_export"]

        if "python core_lite/cli.py" in ft or "module not found" in ft:
            return "package_invocation_error", KNOWN_BLOCKERS["package_invocation_error"]

        if "ingest_incoming" in ft or "load_core_policy" in ft or "append_receipt" in ft:
            if "receipt" in ft:
                return "receipt_signature_mismatch", KNOWN_BLOCKERS["receipt_signature_mismatch"]
            return "missing_internal_export", KNOWN_BLOCKERS["missing_internal_export"]

        if "receiptrecorder" in ft or "missing.*argument.*actor" in ft or "actor" in ft:
            return "receipt_signature_mismatch", KNOWN_BLOCKERS["receipt_signature_mismatch"]

        return "unknown_runtime_blocker", {}

    def _write_candidate(self, result: RepairResult):
        candidate_dir = self.repo_root / "dist" / "current" / "sv001_repair"
        candidate_dir.mkdir(parents=True, exist_ok=True)

        # Write candidate content
        fname = Path(result.candidate_target).name
        candidate_path = candidate_dir / f"candidate_{fname}"
        with open(candidate_path, "w") as f:
            f.write(result.candidate_content)

        # Write manifest
        manifest = {
            "schema": "stegverse_candidate_manifest.v1",
            "repair_id": result.repair_id,
            "blocker_class": result.blocker_class,
            "target_file": result.candidate_target,
            "candidate_path": str(candidate_path),
            "candidate_hash": result.candidate_hash,
            "mutation_to_target_performed": False,
            "operator_action_required": result.operator_action_required,
            "generated_at": result.generated_at,
        }
        manifest_path = candidate_dir / f"{result.repair_id}_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        log.info("Candidate written: %s", candidate_path)

    def _write_report(self, result: RepairResult) -> dict:
        report_dir = self.repo_root / "reports" / "current" / "sv001_repair"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{result.repair_id}_report.json"
        with open(report_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        return result.to_dict()


def main():
    parser = argparse.ArgumentParser(prog="tools.repair.sv001_repair")
    parser.add_argument("--target-repo", required=True,
                        help="Target repo path or GitHub URL (e.g. Data-Continuation/core-lite)")
    parser.add_argument("--failure-text", default="",
                        help="Paste the failure text from the GitHub Actions run")
    parser.add_argument("--failure-file", default="",
                        help="Path to file containing failure text")
    parser.add_argument("--entity", default="StegVerse-002")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    failure_text = args.failure_text
    if args.failure_file:
        with open(args.failure_file) as f:
            failure_text = f.read()

    repair = SV001Repair(
        target_repo=args.target_repo,
        entity=args.entity,
        dry_run=args.dry_run,
        repo_root=Path(args.repo_root),
    )
    result = repair.run(failure_text=failure_text)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
