#!/usr/bin/env python3
"""
candidate_bundle_review.py

StegVerse-002 M10.5 — Candidate Bundle Review

Reviews a candidate transition bundle reference against the Triad-enforced
admissibility contract. Emits a structured review report and receipt.

Decision set:
  ALLOW_CANDIDATE_REVIEW  — all checks passed
  DENY_CANDIDATE          — one or more checks failed
  FAIL_CLOSED             — review could not complete

Usage:
  python scripts/candidate_bundle_review.py \\
    --ref incoming/candidate_bundle_ref.json \\
    --entity StegVerse-002 \\
    --stage SV002-M10 \\
    --report reports/current/candidate_bundle_review_report.json \\
    --receipt receipts/current/candidate_bundle_review_receipt.jsonl \\
    --output outputs/candidate_bundle_review.md
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Schema identifiers
# ---------------------------------------------------------------------------
REF_SCHEMA = "stegverse.candidate_bundle_ref.v1"
REVIEW_SCHEMA = "stegverse.candidate_transition_review.v1"
BUNDLE_MANIFEST_SCHEMA = "stegverse.bundle_manifest.v1"

# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------
ALLOWED_SOURCE_TYPES = {"url", "local_path", "release_asset"}
ALLOWED_TRANSITION_CLASSES = {
    "tooling", "schema", "policy", "governance", "repair", "documentation"
}
# Paths that a bundle is never permitted to install
DENIED_ROOT_FILES = {"README.md", "bundle_manifest.json"}
DENIED_PATH_PREFIXES = {".github/"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


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


def fetch_bundle(source_type: str, source: str, dest_path: str) -> bool:
    """Fetch the bundle zip to dest_path. Returns True on success."""
    try:
        if source_type == "local_path":
            if not os.path.exists(source):
                return False
            import shutil
            shutil.copy2(source, dest_path)
            return True
        elif source_type in ("url", "release_asset"):
            urllib.request.urlretrieve(source, dest_path)
            return True
    except Exception:
        return False
    return False


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_ref_schema(ref: dict) -> bool:
    return ref.get("schema") == REF_SCHEMA


def check_source_type(ref: dict) -> bool:
    return ref.get("source_type") in ALLOWED_SOURCE_TYPES


def check_no_broad_authority(manifest: dict) -> bool:
    """Manifest must not request allow_root_readme or allow_workflows."""
    if manifest.get("allow_root_readme", False):
        return False
    if manifest.get("allow_workflows", False):
        return False
    return True


def check_no_root_readme_overwrite(manifest: dict) -> bool:
    for f in manifest.get("files", []):
        if f.get("path") == "README.md":
            return False
    return True


def check_no_workflow_changes(manifest: dict) -> bool:
    for f in manifest.get("files", []):
        p = f.get("path", "")
        for prefix in DENIED_PATH_PREFIXES:
            if p.startswith(prefix):
                return False
    return True


def check_paths_allowed(manifest: dict, allowed_paths: list) -> tuple[bool, list]:
    """
    Each file in the manifest must have a path that starts with one of
    the allowed_paths entries, and must not be a denied root file.
    Returns (ok, list_of_denied_paths).
    """
    denied = []
    for f in manifest.get("files", []):
        p = f.get("path", "")
        if p in DENIED_ROOT_FILES:
            denied.append(f"denied_root_file:{p}")
            continue
        # Check against allowed_paths
        ok = any(
            p == ap or p.startswith(ap if ap.endswith("/") else ap + "/")
            for ap in allowed_paths
        )
        if not ok:
            denied.append(f"path_not_allowed:{p}")
    return (len(denied) == 0, denied)


def check_file_hashes(manifest: dict, extract_dir: str) -> tuple[bool, list]:
    mismatches = []
    for f in manifest.get("files", []):
        p = f.get("path", "")
        expected = f.get("sha256", "")
        full = os.path.join(extract_dir, p)
        if not os.path.exists(full):
            mismatches.append(f"missing:{p}")
            continue
        actual = sha256_file(full)
        if actual != expected:
            mismatches.append(f"hash_mismatch:{p}")
    return (len(mismatches) == 0, mismatches)


def check_transition_class(ref: dict) -> bool:
    return ref.get("declared_transition_class") in ALLOWED_TRANSITION_CLASSES


def check_stage(ref: dict) -> bool:
    stage = ref.get("declared_stage", "")
    return stage.startswith("SV002-M")


# ---------------------------------------------------------------------------
# Triad stubs (structured placeholders — must resolve for binding transitions)
# ---------------------------------------------------------------------------

def check_gcat_bcat(ref: dict, manifest: dict) -> bool | None:
    """
    GCAT/BCAT admissibility stub.
    Returns None = unresolved (review-only transitions may proceed with warning).
    Binding transitions must resolve this to True.
    """
    # Stub: deny if broad authority flags are set
    if manifest.get("allow_root_readme") or manifest.get("allow_workflows"):
        return False
    return None  # unresolved


def check_ecat_icat(ref: dict) -> bool | None:
    """
    ECAT/ICAT entity coherence stub.
    Returns None = unresolved.
    """
    return None  # unresolved


def check_existence(ref: dict) -> bool | None:
    """
    % Existence / recoverability stub.
    Returns None = unresolved (review-only is safe to proceed).
    """
    return None  # unresolved


# ---------------------------------------------------------------------------
# Main review logic
# ---------------------------------------------------------------------------

def review(
    ref_path: str,
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
        "ref_schema_valid": False,
        "source_type_allowed": False,
        "source_reachable": False,
        "hash_matches": False,
        "bundle_opens": False,
        "manifest_exists": False,
        "manifest_schema_valid": False,
        "no_broad_authority": False,
        "no_root_readme_overwrite": False,
        "no_workflow_changes": False,
        "paths_allowed": False,
        "file_hashes_match": False,
        "transition_class_allowed": False,
        "stage_allowed": False,
        "authority_ref_present": False,
        "policy_ref_present": False,
        "gcat_bcat_admissible": None,
        "ecat_icat_coherent": None,
        "existence_recoverable": None,
    }

    ref = {}
    manifest = {}
    candidate_id = "unknown"
    source = "unknown"

    # --- Load and validate ref ---
    try:
        ref = load_json(ref_path)
    except Exception as e:
        errors.append(f"ref_load_failed:{e}")
        return _fail_closed(
            started, entity, stage, candidate_id, source,
            checks, errors, warnings, report_path, receipt_path, output_path
        )

    candidate_id = ref.get("candidate_id", "unknown")
    source = ref.get("source", "unknown")

    checks["ref_schema_valid"] = check_ref_schema(ref)
    if not checks["ref_schema_valid"]:
        errors.append("ref_schema_invalid")

    checks["source_type_allowed"] = check_source_type(ref)
    if not checks["source_type_allowed"]:
        errors.append(f"source_type_denied:{ref.get('source_type')}")

    checks["authority_ref_present"] = bool(ref.get("authority_ref"))
    if not checks["authority_ref_present"]:
        errors.append("authority_ref_missing")

    checks["policy_ref_present"] = bool(ref.get("policy_ref"))
    if not checks["policy_ref_present"]:
        errors.append("policy_ref_missing")

    checks["transition_class_allowed"] = check_transition_class(ref)
    if not checks["transition_class_allowed"]:
        errors.append(f"transition_class_denied:{ref.get('declared_transition_class')}")

    checks["stage_allowed"] = check_stage(ref)
    if not checks["stage_allowed"]:
        errors.append(f"stage_denied:{ref.get('declared_stage')}")

    if errors:
        return _fail_closed(
            started, entity, stage, candidate_id, source,
            checks, errors, warnings, report_path, receipt_path, output_path
        )

    # --- Fetch bundle ---
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_zip = os.path.join(tmpdir, "bundle.zip")
        reachable = fetch_bundle(ref["source_type"], ref["source"], bundle_zip)
        checks["source_reachable"] = reachable
        if not reachable:
            errors.append(f"source_unreachable:{ref['source']}")
            return _fail_closed(
                started, entity, stage, candidate_id, source,
                checks, errors, warnings, report_path, receipt_path, output_path
            )

        # --- Hash check ---
        actual_hash = sha256_file(bundle_zip)
        expected_hash = ref.get("expected_sha256", "")
        checks["hash_matches"] = (actual_hash == expected_hash)
        if not checks["hash_matches"]:
            errors.append(
                f"hash_mismatch:expected={expected_hash}:actual={actual_hash}"
            )
            return _fail_closed(
                started, entity, stage, candidate_id, source,
                checks, errors, warnings, report_path, receipt_path, output_path
            )

        # --- Open bundle ---
        extract_dir = os.path.join(tmpdir, "bundle")
        try:
            with zipfile.ZipFile(bundle_zip) as zf:
                zf.extractall(extract_dir)
            checks["bundle_opens"] = True
        except Exception as e:
            errors.append(f"bundle_open_failed:{e}")
            checks["bundle_opens"] = False
            return _fail_closed(
                started, entity, stage, candidate_id, source,
                checks, errors, warnings, report_path, receipt_path, output_path
            )

        # --- Manifest ---
        manifest_path = os.path.join(extract_dir, "bundle_manifest.json")
        checks["manifest_exists"] = os.path.exists(manifest_path)
        if not checks["manifest_exists"]:
            errors.append("manifest_missing")
            return _fail_closed(
                started, entity, stage, candidate_id, source,
                checks, errors, warnings, report_path, receipt_path, output_path
            )

        try:
            manifest = load_json(manifest_path)
        except Exception as e:
            errors.append(f"manifest_load_failed:{e}")
            return _fail_closed(
                started, entity, stage, candidate_id, source,
                checks, errors, warnings, report_path, receipt_path, output_path
            )

        checks["manifest_schema_valid"] = (
            manifest.get("schema") == BUNDLE_MANIFEST_SCHEMA
        )
        if not checks["manifest_schema_valid"]:
            errors.append(f"manifest_schema_invalid:{manifest.get('schema')}")

        # --- Authority / safety checks ---
        checks["no_broad_authority"] = check_no_broad_authority(manifest)
        if not checks["no_broad_authority"]:
            errors.append("broad_authority_requested")

        checks["no_root_readme_overwrite"] = check_no_root_readme_overwrite(manifest)
        if not checks["no_root_readme_overwrite"]:
            errors.append("root_readme_overwrite_requested")

        checks["no_workflow_changes"] = check_no_workflow_changes(manifest)
        if not checks["no_workflow_changes"]:
            errors.append("workflow_changes_requested")

        # --- Path admissibility ---
        allowed_paths = manifest.get("allowed_paths", [])
        paths_ok, path_errors = check_paths_allowed(manifest, allowed_paths)
        checks["paths_allowed"] = paths_ok
        errors.extend(path_errors)

        # --- File hash verification ---
        hashes_ok, hash_errors = check_file_hashes(manifest, extract_dir)
        checks["file_hashes_match"] = hashes_ok
        errors.extend(hash_errors)

        # --- Triad stubs ---
        checks["gcat_bcat_admissible"] = check_gcat_bcat(ref, manifest)
        checks["ecat_icat_coherent"] = check_ecat_icat(ref)
        checks["existence_recoverable"] = check_existence(ref)

        if checks["gcat_bcat_admissible"] is None:
            warnings.append("gcat_bcat_unresolved:review_only_permitted")
        if checks["ecat_icat_coherent"] is None:
            warnings.append("ecat_icat_unresolved:review_only_permitted")
        if checks["existence_recoverable"] is None:
            warnings.append("existence_unresolved:review_only_permitted")

    # --- Decision ---
    hard_failures = [k for k, v in checks.items()
                     if v is False and k not in (
                         "gcat_bcat_admissible", "ecat_icat_coherent",
                         "existence_recoverable"
                     )]
    if hard_failures or errors:
        decision = "DENY_CANDIDATE"
    else:
        decision = "ALLOW_CANDIDATE_REVIEW"

    completed = now_utc()

    report = {
        "schema": REVIEW_SCHEMA,
        "entity": entity,
        "stage": stage,
        "candidate_id": candidate_id,
        "source": source,
        "started": started,
        "completed": completed,
        "decision": decision,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "bundle_name": manifest.get("bundle_name", ""),
        "declared_transition_class": ref.get("declared_transition_class", ""),
        "declared_stage": ref.get("declared_stage", ""),
        "receipt": {},
    }

    receipt_hash = _write_outputs(
        report, report_path, receipt_path, output_path,
        candidate_id, decision, entity, stage, started, completed
    )
    report["receipt"] = {
        "receipt_hash": receipt_hash,
        "receipt_path": receipt_path,
    }

    # Rewrite report with receipt
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))

    if decision == "ALLOW_CANDIDATE_REVIEW":
        return 0
    return 1


def _fail_closed(
    started, entity, stage, candidate_id, source,
    checks, errors, warnings, report_path, receipt_path, output_path
):
    completed = now_utc()
    decision = "FAIL_CLOSED"
    report = {
        "schema": REVIEW_SCHEMA,
        "entity": entity,
        "stage": stage,
        "candidate_id": candidate_id,
        "source": source,
        "started": started,
        "completed": completed,
        "decision": decision,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "bundle_name": "",
        "declared_transition_class": "",
        "declared_stage": "",
        "receipt": {},
    }
    receipt_hash = _write_outputs(
        report, report_path, receipt_path, output_path,
        candidate_id, decision, entity, stage, started, completed
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
    candidate_id, decision, entity, stage, started, completed
) -> str:
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    receipt_payload = {
        "schema": "stegverse.receipt.v1",
        "entity": entity,
        "stage": stage,
        "task": "stegverse.candidate.intake.review",
        "candidate_id": candidate_id,
        "decision": decision,
        "started": started,
        "completed": completed,
    }
    receipt_hash = emit_receipt(receipt_path, receipt_payload)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(f"# Candidate Bundle Review\n\n")
        f.write(f"**Entity:** {entity}\n")
        f.write(f"**Stage:** {stage}\n")
        f.write(f"**Candidate ID:** {candidate_id}\n")
        f.write(f"**Decision:** `{decision}`\n")
        f.write(f"**Completed:** {completed}\n")
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
        description="StegVerse-002 M10.5 Candidate Bundle Review"
    )
    parser.add_argument(
        "--ref", required=True,
        help="Path to candidate_bundle_ref.json"
    )
    parser.add_argument("--entity", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument(
        "--report",
        default="reports/current/candidate_bundle_review_report.json"
    )
    parser.add_argument(
        "--receipt",
        default="receipts/current/candidate_bundle_review_receipt.jsonl"
    )
    parser.add_argument(
        "--output",
        default="outputs/candidate_bundle_review.md"
    )
    args = parser.parse_args()

    sys.exit(review(
        ref_path=args.ref,
        entity=args.entity,
        stage=args.stage,
        report_path=args.report,
        receipt_path=args.receipt,
        output_path=args.output,
    ))


if __name__ == "__main__":
    main()
