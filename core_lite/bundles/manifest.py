"""Manifest loading for governed bundle ingestion."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


MANIFEST_NAMES = ("bundle_manifest.json", "manifest.json")


@dataclass
class ManifestFile:
    path: str
    sha256: str = ""
    bytes: int | None = None


@dataclass
class BundleManifest:
    schema: str
    bundle_name: str
    purpose: str = ""
    allow_root_readme: bool = False
    allow_workflows: bool = False
    files: list[ManifestFile] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BundleManifest":
        files = [
            ManifestFile(
                path=str(item.get("path", "")),
                sha256=str(item.get("sha256", "")),
                bytes=item.get("bytes"),
            )
            for item in data.get("files", [])
        ]
        return cls(
            schema=str(data.get("schema", "")),
            bundle_name=str(data.get("bundle_name", "")),
            purpose=str(data.get("purpose", "")),
            allow_root_readme=bool(data.get("allow_root_readme", False)),
            allow_workflows=bool(data.get("allow_workflows", False)),
            files=files,
            raw=data,
        )


def find_manifest_in_directory(bundle_dir: Path) -> Path | None:
    for name in MANIFEST_NAMES:
        candidate = bundle_dir / name
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def load_manifest_file(path: Path) -> BundleManifest:
    return BundleManifest.from_dict(json.loads(path.read_text(encoding="utf-8")))
