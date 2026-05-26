"""Validation and path policy for governed bundle ingestion."""
from __future__ import annotations

import posixpath
from pathlib import PurePosixPath

from .manifest import BundleManifest, ManifestFile


def normalize_bundle_path(path: str) -> str:
    cleaned = path.replace("\\", "/").strip()
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def validate_target_path(path: str, manifest: BundleManifest) -> tuple[bool, str]:
    p = normalize_bundle_path(path)

    if not p:
        return False, "empty_path"

    if p.startswith("/"):
        return False, "absolute_path_denied"

    parts = PurePosixPath(p).parts
    if ".." in parts:
        return False, "parent_traversal_denied"

    if p in {"bundle_manifest.json", "manifest.json"}:
        return False, "root_manifest_denied"

    if p == "README.md" and not manifest.allow_root_readme:
        return False, "root_readme_denied_without_explicit_allow"

    if p.startswith(".github/workflows/") and not manifest.allow_workflows:
        return False, "workflow_denied_without_explicit_allow"

    if p.startswith("incoming/"):
        return False, "incoming_target_denied"

    if p.startswith("quarantine/"):
        return False, "quarantine_target_denied"

    return True, "allowed"


def validate_manifest(manifest: BundleManifest) -> tuple[bool, list[str]]:
    errors: list[str] = []

    if manifest.schema != "stegverse.bundle_manifest.v1":
        errors.append("schema_mismatch")

    if not manifest.bundle_name:
        errors.append("bundle_name_missing")

    if not manifest.files:
        errors.append("files_empty")

    seen: set[str] = set()
    for item in manifest.files:
        p = normalize_bundle_path(item.path)
        if p in seen:
            errors.append(f"duplicate_path:{p}")
        seen.add(p)

        ok, reason = validate_target_path(p, manifest)
        if not ok:
            errors.append(f"path_denied:{p}:{reason}")

        if not item.sha256:
            errors.append(f"sha256_missing:{p}")

    return not errors, errors
