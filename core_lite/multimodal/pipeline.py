"""
core_lite.multimodal.pipeline — StegVerse-002 multimodal input pipeline.

This replacement preserves the existing pipeline entry point and routes
input_type=bundle into the governed bundle ingestion engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core_lite.cge import CGEEngine, CGERequest
from core_lite.receipts import ReceiptRecorder

log = logging.getLogger("core_lite.multimodal.pipeline")

MANIFEST_SCHEMA = "stegverse_multimodal_input_manifest.v1"


MODALITY_RULES = {
    "text": {"sensitive_by_default": False, "review_required_if": [], "notes": "Declare scope and purpose. Check for private context."},
    "voice": {"sensitive_by_default": True, "review_required_if": ["background_capture", "speaker_unverified"], "notes": "Voice is identity-adjacent but not identity-proof."},
    "image": {"sensitive_by_default": False, "review_required_if": ["contains_people"], "notes": "Images may contain people, locations, private documents."},
    "screenshot": {"sensitive_by_default": True, "review_required_if": ["credentials", "tokens", "private_messages", "financial_data"], "notes": "Screenshots require review if they contain credentials, tokens, or private data."},
    "document": {"sensitive_by_default": False, "review_required_if": ["pii", "legal", "medical", "financial"], "notes": "Documents may contain PII, legal, medical, or financial content."},
    "structured_data": {"sensitive_by_default": False, "review_required_if": ["pii_columns", "financial_columns", "health_columns"], "notes": "Check for PII, financial, or health data in columns."},
    "bundle": {"sensitive_by_default": False, "review_required_if": ["missing_manifest", "hash_mismatch"], "notes": "Bundle requires manifest and path validation."},
    "llm_output": {"sensitive_by_default": False, "review_required_if": ["operator_not_reviewed"], "notes": "LLM output is reasoning evidence, not authority."},
    "unknown": {"sensitive_by_default": True, "review_required_if": ["always"], "notes": "Unknown input type always requires review."},
}


@dataclass
class MultimodalInputManifest:
    schema: str = MANIFEST_SCHEMA
    input_id: str = ""
    input_type: str = "unknown"
    source: str = ""
    storage_target: str = "KnowledgeVault"
    actor: str = ""
    submitted_by: str = ""
    identity_context: str = ""
    target_scope: str = ""
    declared_purpose: str = ""
    privacy_class: str = "private"
    allowed_use: list = field(default_factory=list)
    forbidden_use: list = field(default_factory=list)
    stop_condition: str = ""
    input_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    file_path: str = ""
    metadata: dict = field(default_factory=dict)
    speaker_declared: str = ""
    speaker_verified: bool = False
    contains_people: bool = False
    redaction_status: str = "not_reviewed"
    operator_reviewed: bool = False
    source_model: str = ""
    source_session: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PipelineResult:
    status: str = "unknown"
    cge_decision: str = ""
    state_action: str = ""
    receipt_hash: str = ""
    review_required: bool = False
    review_notes: list = field(default_factory=list)
    steps: list = field(default_factory=list)
    manifest: Optional[MultimodalInputManifest] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("manifest", None)
        return d


class MultimodalPipeline:
    def __init__(self, repo_root: Path = Path("."), entity: str = "StegVerse-002", stage: str = "SV002-M5"):
        self.repo_root = repo_root
        self.entity = entity
        self.stage = stage
        self.receipts_path = repo_root / ".stegverse" / "receipts" / "multimodal_receipts.jsonl"
        self.cge = CGEEngine(repo_root=repo_root)
        self.recorder = ReceiptRecorder(self.receipts_path)

    def run(self, manifest: MultimodalInputManifest) -> PipelineResult:
        result = PipelineResult(manifest=manifest)
        result.steps.append(self._step(1, "capture", "ok", input_id=manifest.input_id))

        kv_path = self._kv_path(manifest)
        self._write_kv_manifest(manifest, kv_path)
        result.steps.append(self._step(2, "knowledgevault_store", "ok", path=str(kv_path)))

        manifest = self._normalize(manifest)
        result.steps.append(self._step(3, "normalize", "ok", input_type=manifest.input_type))

        modality_rules = MODALITY_RULES.get(manifest.input_type, MODALITY_RULES["unknown"])
        result.steps.append(self._step(4, "classify", "ok", input_type=manifest.input_type, rules=modality_rules.get("notes", "")))

        identity_status = self._check_identity(manifest)
        result.steps.append(self._step(5, "identity_context", identity_status, identity_context=manifest.identity_context, speaker_verified=manifest.speaker_verified))

        if not manifest.target_scope:
            manifest.target_scope = "core-lite"
        result.steps.append(self._step(6, "scope_declaration", "ok", target_scope=manifest.target_scope))

        privacy_status, privacy_notes = self._classify_privacy(manifest, modality_rules)
        if privacy_notes:
            result.review_notes.extend(privacy_notes)
        result.steps.append(self._step(7, "privacy_consent", privacy_status, privacy_class=manifest.privacy_class, notes=privacy_notes))

        if not manifest.allowed_use:
            manifest.allowed_use = ["context"]
        result.steps.append(self._step(8, "intended_use", "ok", allowed_use=manifest.allowed_use, forbidden_use=manifest.forbidden_use))

        precheck_issues = self._precheck(manifest, modality_rules)
        if precheck_issues:
            receipt = self.recorder.record(
                actor=self.entity,
                stage=self.stage,
                gate="multimodal_pipeline",
                action="precheck",
                decision="FAIL_CLOSED",
                basis=f"Precheck failed: {precheck_issues}",
                input_type=manifest.input_type,
            )
            result.status = "fail_closed"
            result.receipt_hash = receipt.receipt_hash
            result.steps.append(self._step(9, "precheck", "fail", issues=precheck_issues))
            return result

        result.steps.append(self._step(9, "precheck", "ok"))

        cge_request = CGERequest(
            actor=self.entity,
            stage=self.stage,
            target_scope=manifest.target_scope,
            action=manifest.declared_purpose or "ingest",
            input_type=manifest.input_type,
            privacy_class=manifest.privacy_class,
            allowed_use=manifest.allowed_use,
            forbidden_use=manifest.forbidden_use,
            stop_condition=manifest.stop_condition,
            identity_authority=False,
        )
        cge_result = self.cge.decide(cge_request)
        result.cge_decision = cge_result.decision
        result.steps.append(self._step(10, "cge_admissibility", "ok", decision=cge_result.decision, basis=cge_result.basis))

        receipt = self.recorder.record(
            actor=self.entity,
            stage=self.stage,
            gate="multimodal_pipeline",
            action=manifest.declared_purpose or "ingest",
            decision=cge_result.decision,
            basis=cge_result.basis,
            input_type=manifest.input_type,
            input_hash=manifest.input_hash,
            privacy_class=manifest.privacy_class,
            allowed_use=manifest.allowed_use,
            forbidden_use=manifest.forbidden_use,
            stop_condition=manifest.stop_condition,
        )
        result.receipt_hash = receipt.receipt_hash
        result.steps.append(self._step(11, "receipt", "ok", receipt_hash=receipt.receipt_hash))

        state_action = self._state_action(cge_result.decision)
        result.state_action = state_action
        result.steps.append(self._step(12, "state_action", "ok", action=state_action))

        admitted = cge_result.decision.startswith("ALLOW")
        result.status = "success" if admitted else "review_required"
        result.review_required = not admitted
        result.steps.append(self._step(13, "stop_enforcement", "ok", admitted=admitted, stop_condition=manifest.stop_condition))
        return result

    def _step(self, num: int, name: str, status: str, **kwargs) -> dict:
        return {"step": num, "name": name, "status": status, **kwargs}

    def _kv_path(self, manifest: MultimodalInputManifest) -> Path:
        return self.repo_root / "vault_template" / "manifests" / f"{manifest.input_id or 'input'}_manifest.json"

    def _write_kv_manifest(self, manifest: MultimodalInputManifest, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")

    def _normalize(self, manifest: MultimodalInputManifest) -> MultimodalInputManifest:
        if not manifest.input_hash and manifest.file_path:
            p = self.repo_root / manifest.file_path
            if p.exists():
                manifest.input_hash = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
        if not manifest.input_id:
            manifest.input_id = "input_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        return manifest

    def _check_identity(self, manifest: MultimodalInputManifest) -> str:
        if manifest.input_type == "voice" and not manifest.speaker_verified:
            return "advisory"
        return "ok"

    def _classify_privacy(self, manifest: MultimodalInputManifest, rules: dict) -> tuple[str, list]:
        notes = []
        if rules.get("sensitive_by_default") and manifest.privacy_class == "unknown":
            manifest.privacy_class = "sensitive"
            notes.append(f"Privacy class upgraded to sensitive for {manifest.input_type}")
        if manifest.input_type == "llm_output" and not manifest.operator_reviewed:
            notes.append("LLM output not operator-reviewed — treat as reasoning evidence only")
        return "ok", notes

    def _precheck(self, manifest: MultimodalInputManifest, rules: dict) -> list:
        issues = []
        if not manifest.actor:
            issues.append("actor missing")
        if not manifest.stage:
            issues.append("stage missing")
        if manifest.input_type == "unknown":
            issues.append("input_type unknown — review required")
        if manifest.input_type == "bundle" and not manifest.input_hash:
            issues.append("bundle missing hash")
        return issues

    def _state_action(self, decision: str) -> str:
        return {
            "ALLOW": "store_in_knowledgevault",
            "ALLOW_CONTEXT_ONLY": "attach_to_context",
            "ALLOW_REPORT_ONLY": "write_report",
            "ALLOW_CANDIDATE_ONLY": "create_candidate",
            "SANDBOX": "submit_to_sandbox",
            "REVIEW_REQUIRED": "request_review",
            "DENY": "reject",
            "FAIL_CLOSED": "quarantine",
        }.get(decision, "request_review")


def main() -> None:
    parser = argparse.ArgumentParser(prog="core_lite.multimodal.pipeline")
    parser.add_argument("--input-type", required=True)
    parser.add_argument("--input-path", default="")
    parser.add_argument("--entity", default="StegVerse-002")
    parser.add_argument("--stage", default="SV002-M5")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    if args.input_type == "bundle":
        from core_lite.bundles.ingest import BundleIngestor

        result = BundleIngestor(
            Path(args.repo_root),
            entity=args.entity,
            stage=args.stage,
            dry_run=args.dry_run,
        ).ingest(args.input_path)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result.get("status") == "success" else 1)

    pipeline = MultimodalPipeline(repo_root=Path(args.repo_root), entity=args.entity, stage=args.stage)
    manifest = MultimodalInputManifest(
        input_type=args.input_type,
        file_path=args.input_path,
        actor=args.entity,
        stage=args.stage,
    )
    result = pipeline.run(manifest)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
