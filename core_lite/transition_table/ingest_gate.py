"""
core_lite/transition_table/ingest_gate.py — StegVerse-002

Wraps the existing BundleIngestor.ingest() to enforce:
  1. Transition Table resolution (this module)
  2. CGE admissibility (existing CGEEngine)
  3. Transition Table receipt written
  4. CGE receipt written
  5. Class-specific disposition

This is an additive wrapper. It does not modify BundleIngestor directly.
Call ingest_with_transition_gate() instead of BundleIngestor.ingest()
to get full Transition Table + CGE enforcement.

Integration:
    from core_lite.transition_table.ingest_gate import ingest_with_transition_gate

    result = ingest_with_transition_gate(
        bundle_path="incoming/my_bundle.zip",
        entity="StegVerse-002",
        stage="SV002-M11",
        repo_root=".",
        dry_run=False,
    )
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import zipfile
from typing import Optional

from .resolver import TransitionTableResolver, TransitionDecision
from .attributes import TransitionAttributes


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
    with open(path, "a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def _write_report(path: str, record: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = []
    if os.path.exists(path):
        try:
            with open(path) as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            existing = []
    existing.append(record)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)


def _load_manifest_from_bundle(bundle_path: str) -> Optional[dict]:
    """Extract and parse bundle_manifest.json from a zip bundle."""
    try:
        with zipfile.ZipFile(bundle_path) as z:
            if "bundle_manifest.json" not in z.namelist():
                return None
            return json.loads(z.read("bundle_manifest.json"))
    except Exception:
        return None


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
    Full Transition Table + CGE enforcement gate for bundle ingestion.

    Returns a result dict with:
        decision         — ALLOW / ALLOW_CANDIDATE_ONLY / SANDBOX / REVIEW / DENY / FAIL_CLOSED
        transition_class — from manifest
        candidate_disposition — CANDIDATE_FAIL_CLOSED / CANDIDATE_ACCEPTED_FOR_COMPARISON / etc.
        coordinates      — Stage 32 boundary metrics
        receipt_hash     — hash of the transition table receipt
        errors           — list of errors
        warnings         — list of warnings
        installs_code    — bool
        dry_run          — bool
    """
    report_dir = os.path.join(repo_root, "reports", "current")
    receipt_dir = os.path.join(repo_root, "receipts", "current")
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(receipt_dir, exist_ok=True)

    bundle_hash = _sha256_file(bundle_path) if os.path.exists(bundle_path) else "sha256:unknown"

    # --- Step 1: load manifest ---
    manifest = _load_manifest_from_bundle(bundle_path)

    if manifest is None:
        result = {
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
        _write_report(
            os.path.join(report_dir, "transition_table_report.json"),
            {**result, "bundle_path": bundle_path, "bundle_hash": bundle_hash,
             "timestamp_utc": _now_utc(), "entity": entity, "stage": stage}
        )
        return result

    manifest_hash = _sha256_str(json.dumps(manifest, sort_keys=True))

    # --- Step 2: Transition Table resolution ---
    resolver = TransitionTableResolver(policy_path=policy_path)
    decision_obj: TransitionDecision = resolver.resolve(
        manifest, bundle_hash=bundle_hash, entity=entity, stage=stage
    )

    # --- Step 3: CGE admissibility ---
    # Wire into existing CGEEngine if available; otherwise record as pending.
    cge_decision = "PENDING"
    cge_fingerprint = ""
    cge_basis = "CGE not wired — transition table decision is primary"

    try:
        # Attempt to import and call CGEEngine if it exists in core_lite
        from core_lite.cge import CGEEngine  # type: ignore
        cge = CGEEngine()
        cge_result = cge.decide(
            actor=entity,
            stage=stage,
            action=decision_obj.transition_class,
            target_scope=decision_obj.attributes.target_scope,
            input_type="bundle",
            metadata={
                "transition_cell": decision_obj.transition_cell,
                "authority_class": decision_obj.authority_class,
                "state_effect": decision_obj.state_effect,
                "binding_level": decision_obj.binding_level,
                "task_hash": decision_obj.attributes.task_hash,
                "bundle_hash": bundle_hash,
                "manifest_hash": manifest_hash,
            }
        )
        cge_decision = cge_result.get("decision", "UNKNOWN")
        cge_fingerprint = cge_result.get("fingerprint", "")
        cge_basis = cge_result.get("basis", "")
    except ImportError:
        cge_basis = "CGEEngine not importable in this context"
    except Exception as e:
        cge_basis = f"CGEEngine call failed: {e}"
        cge_decision = "ERROR"

    # --- Step 4: Compose final decision ---
    # If Transition Table says FAIL_CLOSED, CGE cannot override.
    # If CGE says DENY or FAIL_CLOSED, that takes precedence over TT ALLOW.
    final_decision = decision_obj.decision
    if cge_decision in ("DENY", "FAIL_CLOSED") and not decision_obj.is_fail_closed():
        final_decision = cge_decision

    # --- Step 5: Write transition table receipt ---
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

    receipt_str = json.dumps(receipt, sort_keys=True)
    receipt_hash = _sha256_str(receipt_str)
    receipt["receipt_hash"] = receipt_hash

    _append_receipt(
        os.path.join(receipt_dir, "transition_table_receipt.jsonl"),
        receipt
    )

    # Write CGE receipt separately
    cge_receipt = {
        "schema": "stegverse.cge_receipt.v1",
        "timestamp_utc": _now_utc(),
        "entity": entity,
        "stage": stage,
        "bundle_path": bundle_path,
        "bundle_hash": bundle_hash,
        "transition_class": decision_obj.transition_class,
        "transition_cell": decision_obj.transition_cell,
        "authority_class": decision_obj.authority_class,
        "decision": cge_decision,
        "fingerprint": cge_fingerprint,
        "basis": cge_basis,
        "previous_receipt_hash": previous_receipt_hash,
    }
    _append_receipt(
        os.path.join(receipt_dir, "cge_admissibility_receipt.jsonl"),
        cge_receipt
    )

    # Write transition table report
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
    _write_report(
        os.path.join(report_dir, "transition_table_report.json"),
        report
    )

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
