#!/usr/bin/env python3
"""
stegverse_apply_gate.py

StegVerse-002 M11 — Governed Apply Boundary Resolver

Evaluates an apply request against the Triad-enforced admissibility contract
before any candidate may bind into the repository.

Decision set:
  ALLOW  — all hard checks passed and Triad binding checks resolved
  DENY   — one or more hard checks failed, apply halted
  DEFER  — no hard failure, but the binding transition still lacks resolved authority
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUEST_SCHEMA = "stegverse.apply_request.v1"
REVIEW_SCHEMA = "stegverse.apply_review.v1"

ALLOWED_TRANSITION_CLASSES = {
    "tooling",
    "schema",
    "policy",
    "governance",
    "repair",
    "documentation",
}

DENIED_TARGET_PATHS = {
    "README.md",
    "bundle_manifest.json",
}

DENIED_PATH_PREFIXES = {
    ".github/",
    ".git/",
    "dist/",
    "receipts/",
    "reports/",
}

BROAD_AUTHORITY_PATTERNS = {
    "*",
    "all",
    "root",
    "admin",
    "superuser",
    "unrestricted",
}

SAFE_DOCUMENTATION_PREFIXES = {
    "docs/",
    "outputs/",
}

SAFE_POLICY_MARKERS = {
    "triad/default-deny/no-broad-authority",
    "sv002-m11/scoped-documentation",
    "sv002/m11/scoped-documentation",
}

SAFE_AUTHORITY_MARKERS = {
    "scoped",
    "candidate",
    "documentation",
    "review",
    "m10.5",
    "m11",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def emit_receipt(receipt_path: str, payload: dict[str, Any]) -> str:
    receipt_dir = os.path.dirname(receipt_path)
    if receipt_dir:
        os.makedirs(receipt_dir, exist_ok=True)
    line = canonical(payload) + "\n"
    with open(receipt_path, "a", encoding="utf-8") as f:
        f.write(line)
    return sha256_bytes(line.encode("utf-8"))


def load_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_request_schema(req: dict[str, Any]) -> bool:
    return req.get("schema") == REQUEST_SCHEMA


def check_entity_declared(req: dict[str, Any]) -> bool:
    return bool(str(req.get("entity", "")).strip())


def check_stage_valid(req: dict[str, Any]) -> bool:
    return str(req.get("stage", "")).startswith("SV002-M")


def check_capability_declared(req: dict[str, Any]) -> bool:
    return bool(str(req.get("capability", "")).strip())


def check_transition_class(req: dict[str, Any]) -> bool:
    return req.get("transition_class") in ALLOWED_TRANSITION_CLASSES


def has_broad_authority(value: str) -> bool:
    lowered = value.lower().strip()
    return any(pattern in lowered for pattern in BROAD_AUTHORITY_PATTERNS)


def check_authority_ref_scoped(req: dict[str, Any]) -> bool:
    ref = str(req.get("authority_ref", "")).lower().strip()
    if not ref or has_broad_authority(ref):
        return False
    return True


def check_policy_ref_present(req: dict[str, Any]) -> bool:
    return bool(str(req.get("policy_ref", "")).strip())


def target_files(req: dict[str, Any]) -> list[dict[str, Any]]:
    files = req.get("target_files", [])
    return files if isinstance(files, list) else []


def check_target_paths_allowed(req: dict[str, Any]) -> tuple[bool, list[str]]:
    denied: list[str] = []
    for f in target_files(req):
        p = str(f.get("path", "")).strip()
        if not p:
            denied.append("path_missing")
            continue
        if p.startswith("/") or ".." in Path(p).parts:
            denied.append(f"path_escape_denied:{p}")
            continue
        if p in DENIED_TARGET_PATHS:
            denied.append(f"denied_path:{p}")
            continue
        for prefix in DENIED_PATH_PREFIXES:
            if p.startswith(prefix):
                denied.append(f"denied_prefix:{p}")
    return (len(denied) == 0, denied)


def is_documentation_only(req: dict[str, Any]) -> bool:
    if req.get("transition_class") != "documentation":
        return False
    files = target_files(req)
    if not files:
        return False
    for f in files:
        p = str(f.get("path", "")).strip()
        op = str(f.get("operation", "review")).strip()
        if op == "delete":
            return False
        if not any(p.startswith(prefix) for prefix in SAFE_DOCUMENTATION_PREFIXES):
            return False
        if p.endswith((".py", ".sh", ".yml", ".yaml", ".json")) and not p.endswith(".md"):
            return False
    return True


def check_gcat_bcat(req: dict[str, Any]) -> bool | None:
    """Resolve GCAT/BCAT for scoped low-risk candidates."""
    if not check_authority_ref_scoped(req):
        return False

    authority = str(req.get("authority_ref", "")).lower()
    policy = str(req.get("policy_ref", "")).lower()

    if req.get("transition_class") in {"governance", "policy"}:
        return None

    if is_documentation_only(req):
        has_safe_authority_marker = any(marker in authority for marker in SAFE_AUTHORITY_MARKERS)
        has_safe_policy_marker = any(marker in policy for marker in SAFE_POLICY_MARKERS)
        if has_safe_authority_marker and has_safe_policy_marker:
            return True

    return None


def check_ecat_icat(req: dict[str, Any]) -> bool | None:
    """Resolve entity coherence for known adapter/sandbox requesters."""
    entity = str(req.get("entity", "")).strip()
    requester = str(req.get("requester", "")).strip().lower()

    if not entity or not requester:
        return False

    if entity != "StegVerse-002":
        return None

    allowed_requester_prefixes = (
        "adapter-candidate-sandbox/",
        "stegverse-002/",
        "core-lite-intake/",
    )
    if requester.startswith(allowed_requester_prefixes):
        return True

    return None


def check_existence(req: dict[str, Any]) -> bool | None:
    """Resolve recoverability for additive/review documentation changes."""
    files = target_files(req)
    if not files:
        return False

    for f in files:
        op = str(f.get("operation", "review")).strip()
        p = str(f.get("path", "")).strip()
        if op == "delete":
            return None
        if not p:
            return False

    if is_documentation_only(req):
        return True

    return None


def compute_decision(checks: dict[str, Any], errors: list[str], req: dict[str, Any]) -> tuple[str, str]:
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
    triad_checks = [
        "gcat_bcat_admissible",
        "ecat_icat_coherent",
        "existence_recoverable",
    ]

    failed_hard = [k for k in hard_checks if checks.get(k) is False]
    if failed_hard or errors:
        return "DENY", f"Failed checks: {', '.join(failed_hard + errors)}"

    if not req.get("dry_run", False):
        unresolved = [k for k in triad_checks if checks.get(k) is None]
        if unresolved:
            return (
                "DEFER",
                "Triad checks unresolved for binding transition: "
                + ", ".join(unresolved)
                + ". Resolve Triad or set dry_run=true for review-only evaluation.",
            )

    return "ALLOW", ""


def write_outputs(
    report: dict[str, Any],
    report_path: str,
    receipt_path: str,
    output_path: str,
) -> str:
    completed = report["completed"]
    payload = {
        "schema": "stegverse.apply_review_receipt.v1",
        "timestamp": completed,
        "entity": report["entity"],
        "stage": report["stage"],
        "request_id": report["request_id"],
        "capability": report["capability"],
        "decision": report["decision"],
        "checks_hash": sha256_bytes(canonical(report["checks"]).encode("utf-8")),
        "report_hash_pre_receipt": sha256_bytes(canonical({k: v for k, v in report.items() if k != "receipt"}).encode("utf-8")),
    }
    receipt_hash = emit_receipt(receipt_path, payload)

    report["receipt"] = {
        "receipt_hash": receipt_hash,
        "receipt_path": receipt_path,
    }

    report_dir = os.path.dirname(report_path)
    if report_dir:
        os.makedirs(report_dir, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# StegVerse Apply Review\n\n")
        f.write(f"**Decision:** `{report['decision']}`\n\n")
        f.write(f"**Request:** `{report['request_id']}`\n\n")
        f.write(f"**Capability:** `{report['capability']}`\n\n")
        f.write(f"**Requester:** `{report['requester']}`\n\n")
        f.write(f"**Transition class:** `{report['transition_class']}`\n\n")
        f.write(f"**Deny / defer reason:** {report['deny_reason'] or 'none'}\n\n")
        f.write("## Checks\n\n")
        for key, value in report["checks"].items():
            f.write(f"- `{key}`: `{value}`\n")
        if report["errors"]:
            f.write("\n## Errors\n\n")
            for err in report["errors"]:
                f.write(f"- `{err}`\n")
        if report["warnings"]:
            f.write("\n## Warnings\n\n")
            for warning in report["warnings"]:
                f.write(f"- `{warning}`\n")
        f.write("\n## Receipt\n\n")
        f.write(f"`{receipt_hash}`\n")

    return receipt_hash


def emit_failure(
    *,
    started: str,
    entity: str,
    stage: str,
    request_id: str,
    capability: str,
    requester: str,
    transition_class: str,
    dry_run: bool,
    checks: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    deny_reason: str,
    report_path: str,
    receipt_path: str,
    output_path: str,
) -> int:
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
        "decision": "DENY",
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "deny_reason": deny_reason,
        "receipt": {},
    }
    write_outputs(report, report_path, receipt_path, output_path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1


def gate(
    request_path: str,
    entity: str,
    stage: str,
    report_path: str,
    receipt_path: str,
    output_path: str,
) -> int:
    started = now_utc()
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {
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

    try:
        req = load_json(request_path)
    except Exception as exc:
        return emit_failure(
            started=started,
            entity=entity,
            stage=stage,
            request_id="unknown",
            capability="unknown",
            requester="unknown",
            transition_class="unknown",
            dry_run=False,
            checks=checks,
            errors=[f"request_load_failed:{exc}"],
            warnings=warnings,
            deny_reason="Request could not be loaded.",
            report_path=report_path,
            receipt_path=receipt_path,
            output_path=output_path,
        )

    request_id = str(req.get("request_id", "unknown"))
    capability = str(req.get("capability", "unknown"))
    requester = str(req.get("requester", "unknown"))
    transition_class = str(req.get("transition_class", "unknown"))
    dry_run = bool(req.get("dry_run", False))

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

    checks["gcat_bcat_admissible"] = check_gcat_bcat(req)
    checks["ecat_icat_coherent"] = check_ecat_icat(req)
    checks["existence_recoverable"] = check_existence(req)

    if checks["gcat_bcat_admissible"] is None:
        warnings.append("gcat_bcat_unresolved")
    if checks["ecat_icat_coherent"] is None:
        warnings.append("ecat_icat_unresolved")
    if checks["existence_recoverable"] is None:
        warnings.append("existence_unresolved")

    decision, reason = compute_decision(checks, errors, req)
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
        "deny_reason": reason,
        "receipt": {},
        "m11_resolver": {
            "safe_documentation_auto_allow_enabled": True,
            "safe_documentation_only": is_documentation_only(req),
            "binding_requires_all_triad_checks_true": True,
        },
    }

    write_outputs(report, report_path, receipt_path, output_path)
    print(json.dumps(report, indent=2, sort_keys=True))

    if decision == "ALLOW":
        return 0
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--entity", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return gate(
        request_path=args.request,
        entity=args.entity,
        stage=args.stage,
        report_path=args.report,
        receipt_path=args.receipt,
        output_path=args.output,
    )


if __name__ == "__main__":
    sys.exit(main())
