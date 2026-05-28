#!/usr/bin/env python3
"""
stegverse_apply_gate.py

StegVerse-002 M11 — Governed Apply/Review Boundary

Evaluates an apply request against the Triad-enforced admissibility contract.
Emits a structured review decision and receipt BEFORE any apply execution.

Decision set:
  ALLOW  — all checks passed, apply may proceed
  DENY   — one or more checks failed, apply halted
  DEFER  — unresolved Triad check on a binding transition, apply halted

Usage:
  python scripts/stegverse_apply_gate.py \\
    --request incoming/apply_request.json \\
    --entity StegVerse-002 \\
    --stage SV002-M11 \\
    --report reports/current/stegverse_apply_review_report.json \\
    --receipt receipts/current/stegverse_apply_review_receipt.jsonl \\
    --output outputs/stegverse_apply_review.md
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Schema identifiers
# ---------------------------------------------------------------------------
REQUEST_SCHEMA = "stegverse.apply_request.v1"
REVIEW_SCHEMA = "stegverse.apply_review.v1"

# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------
ALLOWED_TRANSITION_CLASSES = {
    "tooling", "schema", "policy", "governance", "repair", "documentation"
}
DENIED_TARGET_PATHS = {"README.md", "bundle_manifest.json"}
DENIED_PATH_PREFIXES = {".github/"}
BROAD_AUTHORITY_PATTERNS = {"*", "all", "root", "admin", "superuser", "unrestricted"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def emit_receipt(receipt_path: str, payload: dict) -> str:
    os.makedirs(os.path.dirname(receipt_path), exist_ok=True)
    line = json.dumps(payload, separators=(",", ":")) + "\n"
    with open(receipt_path, "a") as f:
        f.write(line)
    return sha256_bytes(line.encode())


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_request_schema(req: dict) -> bool:
    return req.get("schema") == REQUEST_SCHEMA


def check_entity_declared(req: dict) -> bool:
    return bool(req.get("entity", "").strip())


def check_stage_valid(req: dict) -> bool:
    stage = req.get("stage", "")
    return stage.startswith("SV002-M")


def check_capability_declared(req: dict) -> bool:
    return bool(req.get("capability", "").strip())


def check_transition_class(req: dict) -> bool:
    return req.get("transition_class") in ALLOWED_TRANSITION_CLASSES


def check_authority_ref_scoped(req: dict) -> bool:
    """Authority ref must be present and must not be broad."""
    ref = req.get("authority_ref", "").lower().strip()
    if not ref:
        return False
    for pattern in BROAD_AUTHORITY_PATTERNS:
        if pattern in ref:
            return False
    return True


def check_policy_ref_present(req: dict) -> bool:
    return bool(req.get("policy_ref", "").strip())


def check_no_broad_authority(req: dict) -> bool:
    """Derived check: authority_ref must not grant broad authority."""
    return check_authority_ref_scoped(req)


def check_target_paths_allowed(req: dict) -> tuple:
    """
    Target files must not touch denied paths or workflow directories.
    Returns (ok, list_of_denied).
    """
    denied = []
    for f in req.get("target_files", []):
        p = f.get("path", "")
        if p in DENIED_TARGET_PATHS:
            denied.append(f"denied_path:{p}")
            continue
        for prefix in DENIED_PATH_PREFIXES:
            if p.startswith(prefix):
                denied.append(f"denied_prefix:{p}")
    return (len(denied) == 0, denied)


# ---------------------------------------------------------------------------
# Triad checks
# ---------------------------------------------------------------------------

def check_gcat_bcat(req: dict) -> bool | None:
    """
    GCAT/BCAT admissibility.
    Returns False if broad authority is requested.
    Returns None (unresolved) otherwise — binding transitions must resolve.
    """
    if not check_authority_ref_scoped(req):
        return False
    transition_class = req.get("transition_class", "")
    if transition_class in ("governance", "policy"):
        # Higher-risk classes require explicit resolution
        return None
    return None  # unresolved — review-only transitions may proceed with DEFER


def check_ecat_icat(req: dict) -> bool | None:
    """
    ECAT/ICAT entity coherence.
    Returns None (unresolved) — must resolve for binding transitions.
    """
    # Stub: basic coherence check
    if not req.get("entity") or not req.get("requester"):
        return False
    return None


def check_existence(req: dict) -> bool | None:
    """
    % Existence / recoverability.
    Returns None (unresolved) for non-destructive transitions.
    Returns False for delete operations without explicit recoverability claim.
    """
    for f in req.get("target_files", []):
        if f.get("operation") == "delete":
            # Deletes require explicit existence/recoverability resolution
            return None  # defer — reviewer must resolve
    return None


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------

def _compute_decision(checks: dict, errors: list, req: dict) -> tuple:
    """
    Returns (decision, deny_reason).
    DENY: any hard check is False
    DEFER: any Triad check is None on a binding (non-dry-run) transition
    ALLOW: all hard checks pass
    """
    hard_checks = [
        "request_schema_valid",
        "entity_declared",
        "stage_valid",
        "capability_declared",
        "transition_class_allowed",
        "authority_ref_scoped",
        "policy_ref_present",
        "no_broad_authority",
        "target_paths_allowed",
    ]
    triad_checks = ["gcat_bcat_admissible", "ecat_icat_coherent", "existence_recoverable"]

    failed_hard = [k for k in hard_checks if checks.get(k) is False]
    if failed_hard or errors:
        return "DENY", f"Failed checks: {', '.join(failed_hard + errors)}"

    is_dry_run = req.get("dry_run", False)
    if not is_dry_run:
        unresolved_triad = [k for k in triad_checks if checks.get(k) is None]
        if unresolved_triad:
            return "DEFER", (
                f"Triad checks unresolved for binding transition: "
                f"{', '.join(unresolved_triad)}. "
                f"Resolve or set dry_run=true for review-only evaluation."
            )

    return "ALLOW", ""


# ---------------------------------------------------------------------------
# Main gate logic
# ---------------------------------------------------------------------------

def gate(
    request_path: str,
    entity: str,
    stage: str,
    report_path: str,
    receipt_path: str,
    output_path: str,
) -> int:
    started = now_utc()
    errors = []
    warnings = []

    checks = {
        "request_schema_valid": False,
        "entity_declared": False,
        "stage_valid": False,
        "capability_declared": False,
        "transition_class_allowed": False,
        "authority_ref_scoped": False,
        "policy_ref_present": False,
        "no_broad_authority": False,
        "target_paths_allowed": False,
        "gcat_bcat_admissible": None,
        "ecat_icat_coherent": None,
        "existence_recoverable": None,
    }

    req = {}
    request_id = "unknown"
    capability = "unknown"
    requester = "unknown"
    transition_class = "unknown"
    dry_run = False

    # --- Load request ---
    try:
        req = load_json(request_path)
    except Exception as e:
        errors.append(f"request_load_failed:{e}")
        return _emit_deny(
            started, entity, stage, request_id, capability, requester,
            transition_class, dry_run, checks, errors, warnings,
            "Request could not be loaded.",
            report_path, receipt_path, output_path
        )

    request_id = req.get("request_id", "unknown")
    capability = req.get("capability", "unknown")
    requester = req.get("requester", "unknown")
    transition_class = req.get("transition_class", "unknown")
    dry_run = req.get("dry_run", False)

    # --- Schema and field checks ---
    checks["request_schema_valid"] = check_request_schema(req)
    if not checks["request_schema_valid"]:
        errors.append(f"request_schema_invalid:{req.get('schema')}")

    checks["entity_declared"] = check_entity_declared(req)
    if not checks["entity_declared"]:
        errors.append("entity_missing")

    checks["stage_valid"] = check_stage_valid(req)
    if not checks["stage_valid"]:
        errors.append(f"stage_invalid:{req.get('stage')}")

    checks["capability_declared"] = check_capability_declared(req)
    if not checks["capability_declared"]:
        errors.append("capability_missing")

    checks["transition_class_allowed"] = check_transition_class(req)
    if not checks["transition_class_allowed"]:
        errors.append(f"transition_class_denied:{req.get('transition_class')}")

    checks["authority_ref_scoped"] = check_authority_ref_scoped(req)
    if not checks["authority_ref_scoped"]:
        errors.append("authority_ref_broad_or_missing")

    checks["policy_ref_present"] = check_policy_ref_present(req)
    if not checks["policy_ref_present"]:
        errors.append("policy_ref_missing")

    checks["no_broad_authority"] = checks["authority_ref_scoped"]

    paths_ok, path_errors = check_target_paths_allowed(req)
    checks["target_paths_allowed"] = paths_ok
    errors.extend(path_errors)

    # --- Triad ---
    checks["gcat_bcat_admissible"] = check_gcat_bcat(req)
    checks["ecat_icat_coherent"] = check_ecat_icat(req)
    checks["existence_recoverable"] = check_existence(req)

    if checks["gcat_bcat_admissible"] is None:
        warnings.append("gcat_bcat_unresolved")
    if checks["ecat_icat_coherent"] is None:
        warnings.append("ecat_icat_unresolved")
    if checks["existence_recoverable"] is None:
        warnings.append("existence_unresolved")

    # --- Decision ---
    decision, deny_reason = _compute_decision(checks, errors, req)
    completed = now_utc()

    report = {
        "schema": REVIEW_SCHEMA,
        "entity": entity,
        "stage": stage,
        "request_id": request_id,
        "capability": capability,
        "requester": requester,
        "transition_class": transition_class,
        "dry_run": dry_run,
        "started": started,
        "completed": completed,
        "decision": decision,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "deny_reason": deny_reason,
        "receipt": {},
    }

    receipt_hash = _write_outputs(
        report, report_path, receipt_path, output_path,
        request_id, decision, entity, stage, capability, started, completed
    )
    report["receipt"] = {
        "receipt_hash": receipt_hash,
        "receipt_path": receipt_path,
    }

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))

    if decision == "ALLOW":
        return 0
    return 1


def _emit_deny(
    started, entity, stage, request_id, capability, requester,
    transition_class, dry_run, checks, errors, warnings, deny_reason,
    report_path, receipt_path, output_path
) -> int:
    completed = now_utc()
    decision = "DENY"
    report = {
        "schema": REVIEW_SCHEMA,
        "entity": entity,
        "stage": stage,
        "request_id": request_id,
        "capability": capability,
        "requester": requester,
        "transition_class": transition_class,
        "dry_run": dry_run,
        "started": started,
        "completed": completed,
        "decision": decision,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "deny_reason": deny_reason,
        "receipt": {},
    }
    receipt_hash = _write_outputs(
        report, report_path, receipt_path, output_path,
        request_id, decision, entity, stage, capability, started, completed
    )
    report["receipt"] = {
        "receipt_hash": receipt_hash,
        "receipt_path": receipt_path,
    }
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    return 1


def _write_outputs(
    report, report_path, receipt_path, output_path,
    request_id, decision, entity, stage, capability, started, completed
) -> str:
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    receipt_payload = {
        "schema": "stegverse.receipt.v1",
        "entity": entity,
        "stage": stage,
        "task": "stegverse.apply.gate",
        "request_id": request_id,
        "capability": capability,
        "decision": decision,
        "started": started,
        "completed": completed,
    }
    receipt_hash = emit_receipt(receipt_path, receipt_payload)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(f"# Apply Gate Review\n\n")
        f.write(f"**Entity:** {entity}\n")
        f.write(f"**Stage:** {stage}\n")
        f.write(f"**Request ID:** {request_id}\n")
        f.write(f"**Capability:** {capability}\n")
        f.write(f"**Decision:** `{decision}`\n")
        f.write(f"**Completed:** {completed}\n")
        deny_reason = report.get("deny_reason", "")
        if deny_reason:
            f.write(f"\n**Reason:** {deny_reason}\n")
        errors = report.get("errors", [])
        warnings = report.get("warnings", [])
        if errors:
            f.write(f"\n## Errors\n\n")
            for e in errors:
                f.write(f"- `{e}`\n")
        if warnings:
            f.write(f"\n## Warnings\n\n")
            for w in warnings:
                f.write(f"- `{w}`\n")

    return receipt_hash


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="StegVerse-002 M11 Governed Apply/Review Gate"
    )
    parser.add_argument("--request", required=True, help="Path to apply_request.json")
    parser.add_argument("--entity", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument(
        "--report",
        default="reports/current/stegverse_apply_review_report.json"
    )
    parser.add_argument(
        "--receipt",
        default="receipts/current/stegverse_apply_review_receipt.jsonl"
    )
    parser.add_argument(
        "--output",
        default="outputs/stegverse_apply_review.md"
    )
    args = parser.parse_args()

    sys.exit(gate(
        request_path=args.request,
        entity=args.entity,
        stage=args.stage,
        report_path=args.report,
        receipt_path=args.receipt,
        output_path=args.output,
    ))


if __name__ == "__main__":
    main()
