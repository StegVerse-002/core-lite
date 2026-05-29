"""
core_lite/transition_table/ingest_gate.py — StegVerse-002

Additive Transition Table + CGE gate for bundle ingestion.

This module does not replace BundleIngestor yet. It classifies a bundle's
manifest transition block, records Transition Table and CGE receipts, and
returns a class-specific disposition result that callers can use before any
install, candidate comparison, synthesis, or quarantine step.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import zipfile
from typing import Optional

from .resolver import TransitionTableResolver, TransitionDecision


def _now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _sha256_str(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


def _append_receipt(path: str, record: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def _write_report(path: str, record: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = []
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            existing = []
    existing.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, sort_keys=True)
        f.write("\n")


def _load_manifest_from_bundle(bundle_path: str) -> Optional[dict]:
    """Extract and parse bundle_manifest.json from a zip bundle."""
    try:
        with zipfile.ZipFile(bundle_path) as z:
            if "bundle_manifest.json" not in z.namelist():
                return None
            return json.loads(z.read("bundle_manifest.json"))
    except Exception:
        return None


def _run_cge(
    *,
    repo_root: str,
    entity: str,
    stage: str,
    transition_decision: TransitionDecision,
    bundle_hash: str,
    manifest_hash: str,
) -> tuple[str, str, str]:
    """
    Run the existing core_lite.cge engine using its request-object API.

    The current CGE engine takes CGERequest, not keyword arguments. This adapter
    records CGE output but lets a DENY or FAIL_CLOSED decision override the
    Transition Table decision at final disposition time.
    """
    try:
        from pathlib import Path
        from core_lite.cge import CGEEngine, CGERequest  # type: ignore

        attrs = transition_decision.attributes
        request = CGERequest(
            actor=entity,
            stage=stage,
            target_scope=attrs.target_scope or "core-lite",
            action=transition_decision.transition_class or "bundle_ingest",
            input_type="bundle",
            privacy_class="private",
            allowed_use=[transition_decision.authority_class] if transition_decision.authority_class else [],
            forbidden_use=[],
            stop_condition=attrs.disposition_policy,
            identity_authority=False,
            dry_run=False,
            metadata={
                "transition_cell": transition_decision.transition_cell,
                "authority_class": transition_decision.authority_class,
                "state_effect": transition_decision.state_effect,
                "binding_level": transition_decision.binding_level,
                "task_hash": attrs.task_hash,
                "bundle_hash": bundle_hash,
                "manifest_hash": manifest_hash,
            },
        )
        cge = CGEEngine(repo_root=Path(repo_root))
        cge_result = cge.decide(request)
        return cge_result.decision, cge_result.fingerprint, cge_result.basis
    except ImportError:
        return "PENDING", "", "CGEEngine not importable in this context"
    except Exception as exc:
        return "ERROR", "", f"CGEEngine call failed: {exc}"


def ingest_with_transition_gate(
    bundle_path: str,
    entity: str,
    stage: str,
    repo_root: str = ".",
    dry_run: bool = False,
    previous_receipt_hash: str = "",
    policy_path: Optional[str] = None,
) -> dict:
    """
    Full Transition Table + CGE pre-install gate for bundle ingestion.

    This function classifies and records disposition. It does not copy bundle
    payload files into target paths. Bundle installation should be performed by
    the caller only after the returned decision is admissible for the declared
    transition class.
    """
    report_dir = os.path.join(repo_root, "reports", "current")
    receipt_dir = os.path.join(repo_root, "receipts", "current")
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(receipt_dir, exist_ok=True)

    bundle_hash = _sha256_file(bundle_path) if os.path.exists(bundle_path) else "sha256:unknown"

    manifest = _load_manifest_from_bundle(bundle_path)
    if manifest is None:
        timestamp = _now_utc()
        result = {
            "schema": "stegverse.transition_table_report.v1",
            "timestamp_utc": timestamp,
            "entity": entity,
            "stage": stage,
            "bundle_path": bundle_path,
            "bundle_hash": bundle_hash,
            "decision": "FAIL_CLOSED",
            "transition_class": "",
            "candidate_disposition": "CANDIDATE_FAIL_CLOSED",
            "coordinates": {"delta_C": 1.0, "d_A": 1.0},
            "errors": ["FAIL_CLOSED: bundle_manifest.json missing or unreadable"],
            "warnings": [],
            "installs_code": False,
            "dry_run": dry_run,
            "receipt_hash": "",
        }
        _write_report(os.path.join(report_dir, "transition_table_report.json"), result)
        return {
            "decision": result["decision"],
            "transition_class": result["transition_class"],
            "candidate_disposition": result["candidate_disposition"],
            "coordinates": result["coordinates"],
            "receipt_hash": result["receipt_hash"],
            "errors": result["errors"],
            "warnings": result["warnings"],
            "installs_code": result["installs_code"],
            "dry_run": dry_run,
        }

    manifest_hash = _sha256_str(json.dumps(manifest, sort_keys=True))

    resolver = TransitionTableResolver(policy_path=policy_path)
    decision_obj = resolver.resolve(manifest, bundle_hash=bundle_hash, entity=entity, stage=stage)

    cge_decision, cge_fingerprint, cge_basis = _run_cge(
        repo_root=repo_root,
        entity=entity,
        stage=stage,
        transition_decision=decision_obj,
        bundle_hash=bundle_hash,
        manifest_hash=manifest_hash,
    )

    final_decision = decision_obj.decision
    if cge_decision in ("DENY", "FAIL_CLOSED") and not decision_obj.is_fail_closed():
        final_decision = cge_decision

    receipt = {
        "schema": "stegverse.transition_table_receipt.v1",
        "timestamp_utc": _now_utc(),
        "entity": entity,
        "stage": stage,
        "bundle_path": bundle_path,
        "bundle_hash": bundle_hash,
        "manifest_hash": manifest_hash,
        "transition_class": decision_obj.transition_class,
        "transition_cell": decision_obj.transition_cell,
        "authority_class": decision_obj.authority_class,
        "state_effect": decision_obj.state_effect,
        "binding_level": decision_obj.binding_level,
        "transition_table_decision": decision_obj.decision,
        "cge_decision": cge_decision,
        "cge_fingerprint": cge_fingerprint,
        "cge_basis": cge_basis,
        "final_decision": final_decision,
        "candidate_disposition": decision_obj.candidate_disposition,
        "coordinates": decision_obj.coordinates,
        "errors": decision_obj.errors,
        "warnings": decision_obj.warnings,
        "installs_code": decision_obj.installs_code,
        "dry_run": dry_run,
        "previous_receipt_hash": previous_receipt_hash,
    }
    receipt_hash = _sha256_str(json.dumps(receipt, sort_keys=True))
    receipt["receipt_hash"] = receipt_hash

    _append_receipt(os.path.join(receipt_dir, "transition_table_receipt.jsonl"), receipt)

    cge_receipt = {
        "schema": "stegverse.cge_receipt.v1",
        "timestamp_utc": _now_utc(),
        "entity": entity,
        "stage": stage,
        "bundle_path": bundle_path,
        "bundle_hash": bundle_hash,
        "manifest_hash": manifest_hash,
        "transition_class": decision_obj.transition_class,
        "transition_cell": decision_obj.transition_cell,
        "authority_class": decision_obj.authority_class,
        "decision": cge_decision,
        "fingerprint": cge_fingerprint,
        "basis": cge_basis,
        "previous_receipt_hash": previous_receipt_hash,
    }
    cge_receipt["receipt_hash"] = _sha256_str(json.dumps(cge_receipt, sort_keys=True))
    _append_receipt(os.path.join(receipt_dir, "cge_admissibility_receipt.jsonl"), cge_receipt)

    report = {
        "schema": "stegverse.transition_table_report.v1",
        "timestamp_utc": _now_utc(),
        "entity": entity,
        "stage": stage,
        "bundle_path": bundle_path,
        "bundle_hash": bundle_hash,
        "manifest_hash": manifest_hash,
        "transition_class": decision_obj.transition_class,
        "authority_class": decision_obj.authority_class,
        "transition_table_decision": decision_obj.decision,
        "cge_decision": cge_decision,
        "final_decision": final_decision,
        "candidate_disposition": decision_obj.candidate_disposition,
        "coordinates": decision_obj.coordinates,
        "errors": decision_obj.errors,
        "warnings": decision_obj.warnings,
        "receipt_hash": receipt_hash,
        "dry_run": dry_run,
    }
    _write_report(os.path.join(report_dir, "transition_table_report.json"), report)

    return {
        "decision": final_decision,
        "transition_class": decision_obj.transition_class,
        "candidate_disposition": decision_obj.candidate_disposition,
        "coordinates": decision_obj.coordinates,
        "receipt_hash": receipt_hash,
        "errors": decision_obj.errors,
        "warnings": decision_obj.warnings,
        "installs_code": decision_obj.installs_code,
        "dry_run": dry_run,
    }
