"""
core_lite.cge — Continuation/Governance/Execution admissibility engine.

Decisions:
    ALLOW
    ALLOW_CONTEXT_ONLY
    ALLOW_REPORT_ONLY
    ALLOW_CANDIDATE_ONLY
    SANDBOX
    REVIEW_REQUIRED
    DENY
    FAIL_CLOSED
    QUARANTINE
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("core_lite.cge")

CGE_DECISIONS = {
    "ALLOW",
    "ALLOW_CONTEXT_ONLY",
    "ALLOW_REPORT_ONLY",
    "ALLOW_CANDIDATE_ONLY",
    "SANDBOX",
    "REVIEW_REQUIRED",
    "DENY",
    "FAIL_CLOSED",
    "QUARANTINE",
}


@dataclass
class CGERequest:
    actor: str
    stage: str
    target_scope: str
    action: str
    input_type: str = "unknown"
    privacy_class: str = "private"
    allowed_use: list = field(default_factory=list)
    forbidden_use: list = field(default_factory=list)
    stop_condition: str = ""
    identity_authority: bool = False
    dry_run: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class CGEResult:
    decision: str
    basis: str
    actor: str
    stage: str
    target_scope: str
    action: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fingerprint: str = ""
    allowed_use: list = field(default_factory=list)
    forbidden_use: list = field(default_factory=list)
    stop_condition: str = ""
    review_notes: str = ""

    def to_dict(self):
        return asdict(self)


class CGEEngine:
    """
    CGE admissibility decision engine.

    Invariants enforced:
    - Memory is not authority
    - Context is not consent
    - Capability is not admissibility
    - Input is not execution
    - LLM reasoning is not authorization
    - Unknown fails to REVIEW_REQUIRED or FAIL_CLOSED
    """

    KNOWN_STAGES = {
        "SV002-M0", "SV002-M1", "SV002-M2", "SV002-M3",
        "SV002-M4", "SV002-M5", "SV002-M6", "SV002-M7",
        "SV002-M8", "SV002-M9", "SV002-M10", "SV002-M10.5",
        "SV002-M11", "SV002-M12",
        # Repair stages
        "SV001-M0", "SV001-M1", "SV001-M2", "SV001-M3",
    }

    HIGH_RISK_ACTIONS = {
        "production_mutation", "deploy", "push_to_target",
        "execute_without_review", "bypass_cge",
    }

    # Actions that are never permitted regardless of who requests them
    NEVER_PERMITTED_ACTIONS = {
        "training", "publication_without_consent",
        "identity_verification_claim", "bypass_cge",
        "silent_mutation", "self_approve",
    }

    def __init__(self, repo_root: Path = Path(".")):
        self.repo_root = repo_root
        self._fingerprint_path = repo_root / "stegverse" / "cge_fingerprint.json"

    def decide(self, request: CGERequest) -> CGEResult:
        """Main admissibility decision."""

        # Unknown stage
        if request.stage not in self.KNOWN_STAGES:
            return CGEResult(
                decision="REVIEW_REQUIRED",
                basis=f"Unknown stage: {request.stage}",
                actor=request.actor,
                stage=request.stage,
                target_scope=request.target_scope,
                action=request.action,
                review_notes="Stage not in known stage registry. Manual review required.",
            )

        # Forbidden action check
        if request.action in self.HIGH_RISK_ACTIONS:
            if not request.dry_run:
                return CGEResult(
                    decision="DENY",
                    basis=f"Action {request.action} requires explicit higher-tier authority",
                    actor=request.actor,
                    stage=request.stage,
                    target_scope=request.target_scope,
                    action=request.action,
                )

        # Never-permitted action check — block if the requested action itself is forbidden
        if request.action in self.NEVER_PERMITTED_ACTIONS:
            return CGEResult(
                decision="DENY",
                basis=f"Action {request.action} is never permitted",
                actor=request.actor,
                stage=request.stage,
                target_scope=request.target_scope,
                action=request.action,
            )
        # Note: request.forbidden_use is an output policy declaration (what downstream
        # systems must not do with the result). It does not deny the intake itself.

        # Identity authority overclaim
        if request.identity_authority:
            return CGEResult(
                decision="REVIEW_REQUIRED",
                basis="identity_authority=true — identity context is not identity proof",
                actor=request.actor,
                stage=request.stage,
                target_scope=request.target_scope,
                action=request.action,
                review_notes="Identity authority cannot be asserted without separate verification mechanism.",
            )

        # Unknown input type
        if request.input_type == "unknown":
            return CGEResult(
                decision="REVIEW_REQUIRED",
                basis="Input type unknown — unknown fails to review",
                actor=request.actor,
                stage=request.stage,
                target_scope=request.target_scope,
                action=request.action,
            )

        # Sensitive privacy class without explicit allowed use
        if request.privacy_class in ("sensitive", "restricted") and not request.allowed_use:
            return CGEResult(
                decision="REVIEW_REQUIRED",
                basis=f"Privacy class {request.privacy_class} with no explicit allowed_use",
                actor=request.actor,
                stage=request.stage,
                target_scope=request.target_scope,
                action=request.action,
            )

        # All checks passed
        decision = "ALLOW"
        basis = f"Stage {request.stage} — action {request.action} — admissibility checks passed"

        result = CGEResult(
            decision=decision,
            basis=basis,
            actor=request.actor,
            stage=request.stage,
            target_scope=request.target_scope,
            action=request.action,
            allowed_use=request.allowed_use,
            forbidden_use=request.forbidden_use,
            stop_condition=request.stop_condition,
        )

        result.fingerprint = self._generate_fingerprint(result)
        self._write_fingerprint(result)
        return result

    def _generate_fingerprint(self, result: CGEResult) -> str:
        payload = f"{result.actor}:{result.stage}:{result.action}:{result.timestamp}:{result.decision}"
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

    def _write_fingerprint(self, result: CGEResult):
        self._fingerprint_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._fingerprint_path, "w") as f:
            json.dump({
                "schema": "stegverse_cge_fingerprint.v1",
                "fingerprint": result.fingerprint,
                "decision": result.decision,
                "stage": result.stage,
                "actor": result.actor,
                "timestamp": result.timestamp,
            }, f, indent=2)


def generate_cge_fingerprint(
    actor: str,
    stage: str,
    action: str = "intake",
    target_scope: str = "core-lite",
) -> str:
    """Compatibility export — generate a CGE fingerprint string."""
    engine = CGEEngine()
    request = CGERequest(
        actor=actor,
        stage=stage,
        target_scope=target_scope,
        action=action,
    )
    result = engine.decide(request)
    return result.fingerprint


def precheck_manifest(manifest: dict) -> CGEResult:
    """Check a manifest dict for basic admissibility."""
    engine = CGEEngine()
    request = CGERequest(
        actor=manifest.get("actor", "unknown"),
        stage=manifest.get("stage", "unknown"),
        target_scope=manifest.get("target_scope", "unknown"),
        action=manifest.get("action", "unknown"),
        input_type=manifest.get("input_type", "unknown"),
        privacy_class=manifest.get("privacy_class", "private"),
        allowed_use=manifest.get("allowed_use", []),
        forbidden_use=manifest.get("forbidden_use", []),
        stop_condition=manifest.get("stop_condition", ""),
    )
    return engine.decide(request)


def classify_sandbox_result(result: dict) -> str:
    """Classify a sandbox result into a CGE decision."""
    status = result.get("status", "unknown")
    if status == "success":
        return "ALLOW"
    elif status == "partial":
        return "REVIEW_REQUIRED"
    elif status == "failure":
        return "FAIL_CLOSED"
    else:
        return "REVIEW_REQUIRED"


# Module-level CGE runner for CLI/workflow use
def main_cge_check(repo_root: str = ".", entity: str = "StegVerse-002", stage: str = "SV002-M5"):
    engine = CGEEngine(repo_root=Path(repo_root))
    request = CGERequest(
        actor=entity,
        stage=stage,
        target_scope="core-lite",
        action="intake",
        input_type="text",
        privacy_class="private",
        allowed_use=["context", "report", "candidate_preparation"],
        forbidden_use=["training", "publication", "production_mutation"],
        stop_condition="Core-Lite Intake succeeds with task_id blank and skip_tasks true",
    )
    result = engine.decide(request)
    print(json.dumps(result.to_dict(), indent=2))
    return result


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", default=".")
    p.add_argument("--entity", default="StegVerse-002")
    p.add_argument("--stage", default="SV002-M5")
    a = p.parse_args()
    main_cge_check(a.repo_root, a.entity, a.stage)
