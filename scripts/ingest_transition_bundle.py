#!/usr/bin/env python3
"""
Verify and admit a proposed-transition bundle into local ingestion custody.

This script does not grant canonical authority and does not bind state.
It verifies the manifest, hashes, authority flags, and transport rule, then
emits an ingestion receipt.

Admission decisions:
  ADMITTED_AS_CANDIDATE_EVIDENCE
  REPAIR_REQUIRED
  DENIED
  QUARANTINED
  FAIL_CLOSED
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile
from typing import Any, Dict, List, Optional


VERSION = "0.1.3-gllm"
EXCLUDED_MANIFEST_FIELDS = ["manifest_sha256", "chain_link.link_id"]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def manifest_hash_projection(manifest: Dict[str, Any]) -> Dict[str, Any]:
    projected = json.loads(json.dumps(manifest))
    projected["manifest_sha256"] = ""
    projected.setdefault("chain_link", {})["link_id"] = ""
    return projected


def compute_manifest_sha256(manifest: Dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(manifest_hash_projection(manifest)))


def append_receipt(path: Path, receipt: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")


def load_schema(repo_root: Path, schema_path: str) -> Optional[Dict[str, Any]]:
    path = repo_root / schema_path
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def lightweight_schema_check(manifest: Dict[str, Any]) -> List[str]:
    """
    Dependency-free structural check.

    If jsonschema is installed, callers may layer it externally, but this function
    keeps the ingestion gate usable in minimal bootstrap conditions.
    """
    errors: List[str] = []
    required = [
        "schema",
        "version",
        "bundle_id",
        "created_utc",
        "source",
        "transition",
        "authority",
        "contents",
        "hashing",
        "chain_link",
        "manifest_sha256",
    ]
    for key in required:
        if key not in manifest:
            errors.append(f"missing required field: {key}")

    if manifest.get("schema") != "stegverse.transition_bundle.v1":
        errors.append("schema must equal stegverse.transition_bundle.v1")

    if not isinstance(manifest.get("contents"), list) or not manifest.get("contents"):
        errors.append("contents must be a non-empty array")

    authority = manifest.get("authority", {})
    if authority.get("broad_authority") is not False:
        errors.append("authority.broad_authority must be false")
    if authority.get("canonical_authority") is not False:
        errors.append("authority.canonical_authority must be false")
    if authority.get("may_bind_repo_state") is not False:
        errors.append("authority.may_bind_repo_state must be false")
    if authority.get("candidate_evidence_only") is not True:
        errors.append("authority.candidate_evidence_only must be true")

    transition = manifest.get("transition", {})
    if transition.get("requires_ingestion") is not True:
        errors.append("transition.requires_ingestion must be true")
    if transition.get("transport_mechanism") != "ingestion":
        errors.append("transition.transport_mechanism must equal ingestion")

    hashing = manifest.get("hashing", {})
    if hashing.get("algorithm") != "sha256":
        errors.append("hashing.algorithm must equal sha256")

    chain_link = manifest.get("chain_link", {})
    if chain_link.get("ingestion_required") is not True:
        errors.append("chain_link.ingestion_required must be true")

    return errors


def safe_extract(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or ".." in Path(name).parts:
                raise RuntimeError(f"Unsafe zip path: {info.filename}")
        zf.extractall(dest)


def verify_contents(extract_dir: Path, manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for entry in manifest.get("contents", []):
        bundle_path = entry.get("bundle_path")
        if not bundle_path:
            errors.append(f"content entry missing bundle_path: {entry}")
            continue
        path = extract_dir / bundle_path
        if not path.exists() or not path.is_file():
            if entry.get("required", False):
                errors.append(f"required bundled file missing: {bundle_path}")
            continue
        observed = sha256_file(path)
        if observed != entry.get("sha256"):
            errors.append(f"sha256 mismatch for {bundle_path}: expected {entry.get('sha256')} observed {observed}")
        if path.stat().st_size != entry.get("bytes"):
            errors.append(f"byte size mismatch for {bundle_path}")
    return errors


def classify_destination(repo_root: Path, decision: str) -> Path:
    if decision == "ADMITTED_AS_CANDIDATE_EVIDENCE":
        return repo_root / "dist/master-records/pending_candidate_bundles"
    if decision == "REPAIR_REQUIRED":
        return repo_root / "repair/bundles/pending"
    if decision == "QUARANTINED":
        return repo_root / "quarantine/bundles"
    return repo_root / "failed_bundles"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_zip", help="Path to proposed_transition_bundle.zip")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--receipt", default="receipts/current/transition_bundle_ingest_receipt.jsonl")
    parser.add_argument("--schema", default="schemas/transition_bundle.v1.schema.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    bundle_zip = Path(args.bundle_zip).resolve()

    decision = "FAIL_CLOSED"
    basis: List[str] = []
    manifest: Dict[str, Any] = {}
    manifest_sha_observed: Optional[str] = None
    bundle_sha = sha256_file(bundle_zip) if bundle_zip.exists() else None

    try:
        if not bundle_zip.exists():
            raise FileNotFoundError(f"bundle not found: {bundle_zip}")

        with tempfile.TemporaryDirectory() as tmp:
            extract_dir = Path(tmp)
            safe_extract(bundle_zip, extract_dir)

            manifest_path = extract_dir / "bundle_manifest.json"
            if not manifest_path.exists():
                decision = "DENIED"
                basis.append("bundle_manifest.json missing")
            else:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

                schema_errors = lightweight_schema_check(manifest)
                if schema_errors:
                    decision = "DENIED"
                    basis.extend(schema_errors)
                else:
                    manifest_sha_observed = compute_manifest_sha256(manifest)
                    if manifest_sha_observed != manifest.get("manifest_sha256"):
                        decision = "DENIED"
                        basis.append(
                            f"manifest_sha256 mismatch: expected {manifest.get('manifest_sha256')} observed {manifest_sha_observed}"
                        )
                    elif manifest.get("chain_link", {}).get("link_id") != manifest.get("manifest_sha256"):
                        decision = "DENIED"
                        basis.append("chain_link.link_id must equal manifest_sha256")
                    else:
                        content_errors = verify_contents(extract_dir, manifest)
                        if content_errors:
                            decision = "REPAIR_REQUIRED"
                            basis.extend(content_errors)
                        else:
                            authority = manifest.get("authority", {})
                            if authority.get("broad_authority") is True:
                                decision = "DENIED"
                                basis.append("broad authority requested")
                            elif authority.get("canonical_authority") is True:
                                decision = "DENIED"
                                basis.append("canonical authority requested at intake")
                            elif manifest.get("transition", {}).get("transport_mechanism") != "ingestion":
                                decision = "DENIED"
                                basis.append("transport mechanism is not ingestion")
                            else:
                                decision = "ADMITTED_AS_CANDIDATE_EVIDENCE"
                                basis.append("manifest, content hashes, authority flags, and ingestion transport verified")

            if not args.dry_run:
                destination = classify_destination(repo_root, decision)
                destination.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bundle_zip, destination / bundle_zip.name)

    except Exception as exc:
        decision = "FAIL_CLOSED"
        basis.append(str(exc))

    receipt = {
        "schema": "stegverse.transition_bundle_ingest_receipt.v1",
        "timestamp": utc_now(),
        "version": VERSION,
        "decision": decision,
        "basis": basis,
        "bundle_path": str(bundle_zip),
        "bundle_sha256": bundle_sha,
        "manifest_sha256": manifest.get("manifest_sha256") if manifest else None,
        "observed_manifest_sha256": manifest_sha_observed,
        "bundle_id": manifest.get("bundle_id") if manifest else None,
        "authority": "candidate_evidence_only",
        "canonical_authority": False,
        "broad_authority": False,
        "may_bind_repo_state": False,
        "next_required_link": "destination_admissibility_receipt" if decision == "ADMITTED_AS_CANDIDATE_EVIDENCE" else "repair_or_review_receipt",
    }

    append_receipt(repo_root / args.receipt, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))

    return 0 if decision == "ADMITTED_AS_CANDIDATE_EVIDENCE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
