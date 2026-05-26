"""Quarantine helpers for invalid bundles."""
from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path


def quarantine_bundle(repo_root: Path, source: Path, reason: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = source.name.replace("/", "_").replace("\\", "_") or "bundle"
    target_dir = repo_root / "quarantine" / "bundles" / f"{stamp}_{safe_name}"
    target_dir.mkdir(parents=True, exist_ok=True)

    if source.exists():
        if source.is_file():
            shutil.copy2(source, target_dir / source.name)
        elif source.is_dir():
            shutil.copytree(source, target_dir / "source", dirs_exist_ok=True)

    (target_dir / "reason.txt").write_text(reason + "\n", encoding="utf-8")
    return target_dir
