"""
core_lite.ingest — StegVerse-002 ingestion layer.

Handles manifest validation, path validation, input classification,
and routing to CGE for admissibility decisions.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core_lite.cge import CGEEngine, CGERequest, CGEResult, precheck_manifest
from core_lite.receipts import ReceiptRecorder

log = logging.getLogger("core_lite.ingest")


INGEST_SCHEMA = "stegverse_ingest_manifest.v1"

KNOWN_INPUT_TYPES = {
    "text", "voice", "image", "screenshot", "document",
    "structured_data", "bundle", "workflow_artifact",
    "repo_state", "llm_output", "unknown",
}

PRIVACY_CLASSES = {"public", "shareable", "private", "sensitive", "restricted", "unknown"}


@dataclass
class IngestManifest:
    schema: str = INGEST_SCHEMA
    input_id: str = ""
    input_type: str = "unknown"
    source: str = ""
    actor: str = ""
    stage: str = ""
    target_scope: str = ""
    declared_purpose: str = ""
    privacy_class: str = "private"
    allowed_use: list = field(default_factory=list)
    forbidden_use: list = field(default_factory=list)
    stop_condition: str = ""
    input_hash: str = ""
    file_path: str = ""
    identity_context: str = ""
    identity_authority: bool = False
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "IngestManifest":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_file(cls, path: Path) -> "IngestManifest":
        with open(path) as f:
            return cls.from_dict(json.load(f))


class IngestPipeline:
    """
    Full 13-step ingestion pipeline matching the StegVerse multimodal input strategy.

    Steps:
    1  Capture
    2  Store/reference in KnowledgeVault
    3  Normalize
    4  Classify
    5  Attach identity context
    6  Declare scope
    7  Classify privacy and consent
    8  Determine intended use
    9  Precheck
    10 CGE / admissibility decision
    11 Receipt
    12 State action
    13 STOP enforcement
    """

    def __init__(
        self,
        repo_root: Path = Path("."),
        entity: str = "StegVerse-002",
        stage: str = "SV002-M5",
        receipt_path: Optional[Path] = None,
    ):
        self.repo_root = repo_root
        self.entity = entity
        self.stage = stage
        self.receipt_path = receipt_path or (
            repo_root / ".stegverse" / "receipts" / "core_lite_receipts.jsonl"
        )
        self.cge = CGEEngine(repo_root=repo_root)
        self.recorder = ReceiptRecorder(self.receipt_path)

    def run(self, manifest: IngestManifest) -> dict:
        steps = []

        # Step 1 — Capture
        steps.append({"step": 1, "name": "capture", "status": "ok", "input_id": manifest.input_id})

        # Step 2 — KnowledgeVault reference
        kv_path = self._resolve_kv_path(manifest)
        steps.append({"step": 2, "name": "knowledgevault_reference", "status": "ok", "path": str(kv_path)})

        # Step 3 — Normalize
        normalized = self._normalize(manifest)
        steps.append({"step": 3, "name": "normalize", "status": "ok", "input_type": normalized.input_type})

        # Step 4 — Classify
        if normalized.input_type not in KNOWN_INPUT_TYPES:
            normalized.input_type = "unknown"
        steps.append({"step": 4, "name": "classify", "status": "ok", "input_type": normalized.input_type})

        # Step 5 — Identity context
        identity_ok = self._check_identity(normalized)
        steps.append({"step": 5, "name": "identity_context", "status": "ok" if identity_ok else "advisory",
                      "identity_authority": normalized.identity_authority})

        # Step 6 — Scope
        if not normalized.target_scope:
            normalized.target_scope = "core-lite"
        steps.append({"step": 6, "name": "scope", "status": "ok", "target_scope": normalized.target_scope})

        # Step 7 — Privacy
        if normalized.privacy_class not in PRIVACY_CLASSES:
            normalized.privacy_class = "unknown"
        steps.append({"step": 7, "name": "privacy_consent", "status": "ok",
                      "privacy_class": normalized.privacy_class})

        # Step 8 — Intended use
        if not normalized.allowed_use:
            normalized.allowed_use = ["context"]
        steps.append({"step": 8, "name": "intended_use", "status": "ok",
                      "allowed_use": normalized.allowed_use})

        # Step 9 — Precheck
        precheck_issues = self._precheck(normalized)
        if precheck_issues:
            self.recorder.record(
                actor=self.entity, stage=self.stage, gate="ingest",
                action="precheck", decision="FAIL_CLOSED",
                basis=f"Precheck failed: {precheck_issues}",
                stop_condition=normalized.stop_condition,
            )
            return {"status": "fail_closed", "step": 9, "issues": precheck_issues, "steps": steps}
        steps.append({"step": 9, "name": "precheck", "status": "ok"})

        # Step 10 — CGE
        cge_request = CGERequest(
            actor=self.entity,
            stage=self.stage,
            target_scope=normalized.target_scope,
            action=normalized.declared_purpose or "intake",
            input_type=normalized.input_type,
            privacy_class=normalized.privacy_class,
            allowed_use=normalized.allowed_use,
            forbidden_use=normalized.forbidden_use,
            stop_condition=normalized.stop_condition,
            identity_authority=normalized.identity_authority,
        )
        cge_result = self.cge.decide(cge_request)
        steps.append({"step": 10, "name": "cge_admissibility", "status": "ok",
                      "decision": cge_result.decision, "basis": cge_result.basis})

        # Step 11 — Receipt
        receipt = self.recorder.record(
            actor=self.entity,
            stage=self.stage,
            gate="ingest",
            action=normalized.declared_purpose or "intake",
            decision=cge_result.decision,
            basis=cge_result.basis,
            input_type=normalized.input_type,
            input_hash=normalized.input_hash,
            privacy_class=normalized.privacy_class,
            allowed_use=normalized.allowed_use,
            forbidden_use=normalized.forbidden_use,
            stop_condition=normalized.stop_condition,
        )
        steps.append({"step": 11, "name": "receipt", "status": "ok",
                      "receipt_hash": receipt.receipt_hash})

        # Step 12 — State action
        state_action = self._determine_state_action(cge_result.decision)
        steps.append({"step": 12, "name": "state_action", "status": "ok",
                      "action": state_action})

        # Step 13 — STOP enforcement
        stop_met = cge_result.decision in ("ALLOW", "ALLOW_CONTEXT_ONLY",
                                            "ALLOW_REPORT_ONLY", "ALLOW_CANDIDATE_ONLY")
        steps.append({"step": 13, "name": "stop_enforcement", "status": "ok",
                      "stop_condition": normalized.stop_condition,
                      "stop_met": stop_met})

        return {
            "status": "success" if stop_met else "review_required",
            "cge_decision": cge_result.decision,
            "state_action": state_action,
            "receipt_hash": receipt.receipt_hash,
            "steps": steps,
        }

    def _resolve_kv_path(self, manifest: IngestManifest) -> Path:
        return self.repo_root / "vault_template" / "manifests" / f"{manifest.input_id}.json"

    def _normalize(self, manifest: IngestManifest) -> IngestManifest:
        if not manifest.input_hash and manifest.file_path:
            p = self.repo_root / manifest.file_path
            if p.exists():
                manifest.input_hash = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
        return manifest

    def _check_identity(self, manifest: IngestManifest) -> bool:
        # Identity authority must never be true by default
        if manifest.identity_authority:
            log.warning("identity_authority=true — treating as advisory only")
            manifest.identity_authority = False
            return False
        return True

    def _precheck(self, manifest: IngestManifest) -> list:
        issues = []
        if not manifest.actor:
            issues.append("actor missing")
        if not manifest.stage:
            issues.append("stage missing")
        if not manifest.target_scope:
            issues.append("target_scope missing")
        if manifest.privacy_class == "unknown":
            issues.append("privacy_class unknown — review required")
        return issues

    def _determine_state_action(self, decision: str) -> str:
        return {
            "ALLOW": "store_in_knowledgevault",
            "ALLOW_CONTEXT_ONLY": "attach_to_context",
            "ALLOW_REPORT_ONLY": "write_report",
            "ALLOW_CANDIDATE_ONLY": "create_candidate",
            "SANDBOX": "submit_to_sandbox",
            "REVIEW_REQUIRED": "request_review",
            "DENY": "reject",
            "FAIL_CLOSED": "quarantine",
            "QUARANTINE": "quarantine",
        }.get(decision, "request_review")


def ingest_incoming(
    manifest_path: str,
    repo_root: str = ".",
    entity: str = "StegVerse-002",
    stage: str = "SV002-M5",
) -> dict:
    """
    Compatibility export — ingest an incoming manifest file.
    """
    pipeline = IngestPipeline(
        repo_root=Path(repo_root),
        entity=entity,
        stage=stage,
    )
    manifest = IngestManifest.from_file(Path(manifest_path))
    return pipeline.run(manifest)


def load_core_policy(policy_path: str = "config/core_policy.json") -> dict:
    """
    Compatibility export — load the core policy file.
    """
    p = Path(policy_path)
    if not p.exists():
        return {"default_privacy_class": "private", "default_ai_use": "review_required"}
    with open(p) as f:
        return json.load(f)
