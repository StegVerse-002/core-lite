#!/usr/bin/env python3
"""
Package a governed LLM collaboration run into a proposed-transition bundle.

This script does not grant authority, install files, move data across repo/org
boundaries, or bind state. It packages candidate evidence for ingestion.

Output:
  dist/bundles/proposed_transition_bundle.json
  dist/bundles/proposed_transition_bundle.zip
  dist/bundles/proposed_transition_bundle.sha256
  receipts/current/proposed_transition_bundle_receipt.jsonl
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import uuid
import zipfile
from typing import Any, Dict, List, Optional


SCHEMA = "stegverse.transition_bundle.v1"
VERSION = "0.1.3-gllm"

DEFAULT_REQUIRED_CONTENTS = [
    "outputs/thread.md",
    "outputs/claude_response.md",
    "outputs/chatgpt_response.md",
    "reports/current/agent_coordination_report.json",
    "reports/current/agent_comparison_report.json",
    "reports/current/agent_boundary_report.json",
    "receipts/current/agent_coordination_receipt.jsonl",
    "receipts/current/agent_comparison_receipt.jsonl",
    "receipts/current/agent_boundary_receipt.jsonl",
    "agent_history/llm_changelog.jsonl",
    "agent_history/version_state.json",
]

OPTIONAL_CONTENTS = [
    "receipts/current/openai_task_receipt.jsonl",
    "receipts/current/claude_task_receipt.jsonl",
    "reports/current/openai_task_summary.json",
    "reports/current/claude_task_summary.json",
]

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
    """
    Return the exact projection used for manifest hashing.

    Both package and ingest must use this same projection:
    - manifest_sha256 is set to empty string
    - chain_link.link_id is set to empty string

    This prevents the v0.1.2 draft bug where link_id was populated during
    verification and caused manifest hash mismatch.
    """
    projected = json.loads(json.dumps(manifest))
    projected["manifest_sha256"] = ""
    projected.setdefault("chain_link", {})["link_id"] = ""
    return projected


def compute_manifest_sha256(manifest: Dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(manifest_hash_projection(manifest)))


def safe_bundle_path(repo_path: str) -> str:
    normalized = repo_path.strip().lstrip("/").replace("\\", "/")
    parts = [p for p in normalized.split("/") if p not in ("", ".", "..")]
    if not parts:
        raise ValueError(f"Invalid empty bundle path from {repo_path!r}")
    return "files/" + "/".join(parts)


def load_json_if_exists(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def previous_receipt_hash(repo_root: Path) -> Optional[str]:
    candidates = [
        repo_root / "receipts/current/agent_boundary_receipt.jsonl",
        repo_root / "receipts/current/agent_coordination_receipt.jsonl",
        repo_root / "receipts/current/openai_task_receipt.jsonl",
    ]
    for path in candidates:
        if not path.exists():
            continue
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            continue
        return sha256_bytes(lines[-1].encode("utf-8"))
    return None


def build_content_entries(repo_root: Path, required: List[str], optional: List[str]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []

    for rel in required:
        src = repo_root / rel
        exists = src.exists() and src.is_file()
        if not exists:
            raise FileNotFoundError(f"Required bundle content missing: {rel}")
        entries.append(
            {
                "path": rel,
                "bundle_path": safe_bundle_path(rel),
                "sha256": sha256_file(src),
                "bytes": src.stat().st_size,
                "required": True,
                "exists": True,
            }
        )

    for rel in optional:
        src = repo_root / rel
        exists = src.exists() and src.is_file()
        if not exists:
            continue
        entries.append(
            {
                "path": rel,
                "bundle_path": safe_bundle_path(rel),
                "sha256": sha256_file(src),
                "bytes": src.stat().st_size,
                "required": False,
                "exists": True,
            }
        )

    return entries


def write_bundle_zip(repo_root: Path, manifest: Dict[str, Any], out_zip: Path) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        for entry in manifest["contents"]:
            src = repo_root / entry["path"]
            zf.write(src, entry["bundle_path"])


def append_receipt(path: Path, receipt: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-dir", default="dist/bundles")
    parser.add_argument("--bundle-name", default="proposed_transition_bundle")
    parser.add_argument("--destination-repo", default=None)
    parser.add_argument("--destination-org", default=None)
    parser.add_argument("--stage", default=os.environ.get("STEGVERSE_STAGE", "SV002-M10"))
    parser.add_argument("--workflow", default=os.environ.get("GITHUB_WORKFLOW", "core-lite-intake"))
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    out_dir = repo_root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    coordination = load_json_if_exists(repo_root / "reports/current/agent_coordination_report.json") or {}
    boundary = load_json_if_exists(repo_root / "reports/current/agent_boundary_report.json") or {}
    version_state = load_json_if_exists(repo_root / "agent_history/version_state.json") or {}

    coordination_decision = coordination.get("decision", "UNKNOWN")
    boundary_decision = boundary.get("decision", "UNKNOWN")

    if coordination_decision not in ("COORDINATION_THREAD_READY", "PARTIAL_PROVIDER_OUTPUT", "REVIEW_REQUIRED"):
        raise RuntimeError(f"Cannot package transition bundle from coordination decision: {coordination_decision}")

    if boundary.get("authority", {}).get("broad_authority") is True:
        raise RuntimeError("Refusing to package bundle: boundary report indicates broad_authority=true")

    if boundary_decision not in ("ALLOW_CANDIDATE_EVIDENCE", "REVIEW_REQUIRED"):
        raise RuntimeError(f"Cannot package transition bundle from boundary decision: {boundary_decision}")

    bundle_id = f"ptb-{utc_now().replace(':', '').replace('-', '')}-{uuid.uuid4().hex[:12]}"
    contents = build_content_entries(repo_root, DEFAULT_REQUIRED_CONTENTS, OPTIONAL_CONTENTS)

    destination_repo = args.destination_repo
    destination_org = args.destination_org
    current_repo = os.environ.get("STEGVERSE_REPO", "StegVerse-002/core-lite")
    current_org = current_repo.split("/", 1)[0] if "/" in current_repo else None

    cross_boundary = bool(
        (destination_repo and destination_repo != current_repo)
        or (destination_org and destination_org != current_org)
    )

    manifest: Dict[str, Any] = {
        "schema": SCHEMA,
        "version": VERSION,
        "bundle_id": bundle_id,
        "created_utc": utc_now(),
        "source": {
            "entity": os.environ.get("STEGVERSE_ENTITY", "StegVerse-002"),
            "repo": current_repo,
            "stage": args.stage,
            "workflow": args.workflow,
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_number": os.environ.get("GITHUB_RUN_NUMBER"),
            "commit_sha": os.environ.get("GITHUB_SHA"),
        },
        "transition": {
            "class": "proposed_state_transition",
            "status": "candidate_evidence_packaged",
            "decision": coordination_decision,
            "destination_repo": destination_repo,
            "destination_org": destination_org,
            "transport_mechanism": "ingestion",
            "requires_ingestion": True,
            "cross_repo_or_org_boundary": cross_boundary,
            "next_required_link": "ingestion_intake_receipt",
        },
        "authority": {
            "mode": "candidate_evidence_only",
            "candidate_evidence_only": True,
            "canonical_authority": False,
            "broad_authority": False,
            "may_bind_repo_state": False,
            "source_boundary_decision": boundary_decision,
        },
        "contents": contents,
        "hashing": {
            "algorithm": "sha256",
            "canonicalization": "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False)",
            "excluded_manifest_fields": EXCLUDED_MANIFEST_FIELDS,
        },
        "chain_link": {
            "link_id": "",
            "previous_receipt_hash": previous_receipt_hash(repo_root),
            "source_receipt": "receipts/current/proposed_transition_bundle_receipt.jsonl",
            "next_required_link": "ingestion_intake_receipt",
            "ingestion_required": True,
        },
        "manifest_sha256": "",
    }

    manifest_sha = compute_manifest_sha256(manifest)
    manifest["manifest_sha256"] = manifest_sha
    manifest["chain_link"]["link_id"] = manifest_sha

    manifest_path = out_dir / f"{args.bundle_name}.json"
    zip_path = out_dir / f"{args.bundle_name}.zip"
    sha_path = out_dir / f"{args.bundle_name}.sha256"

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_bundle_zip(repo_root, manifest, zip_path)
    sha_path.write_text(f"{sha256_file(zip_path)}  {zip_path.name}\n", encoding="utf-8")

    receipt = {
        "schema": "stegverse.proposed_transition_bundle_receipt.v1",
        "timestamp": utc_now(),
        "version": VERSION,
        "bundle_id": bundle_id,
        "decision": "PACKAGED_AS_CANDIDATE_EVIDENCE",
        "authority": "candidate_evidence_only",
        "canonical_authority": False,
        "broad_authority": False,
        "may_bind_repo_state": False,
        "manifest_path": str(manifest_path.relative_to(repo_root)),
        "bundle_path": str(zip_path.relative_to(repo_root)),
        "bundle_sha256": sha256_file(zip_path),
        "manifest_sha256": manifest_sha,
        "next_required_link": "ingestion_intake_receipt",
    }
    append_receipt(repo_root / "receipts/current/proposed_transition_bundle_receipt.jsonl", receipt)

    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
