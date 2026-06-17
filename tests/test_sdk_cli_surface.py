from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from core_lite.sdk import CoreLiteClient


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def make_bundle(path: Path) -> None:
    payload = b"sdk cli test payload\n"
    manifest = {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "sdk_cli_test_bundle",
        "purpose": "sdk cli unit test",
        "allow_root_readme": False,
        "allow_workflows": False,
        "files": [{"path": "outputs/sdk_cli_test_probe.txt", "sha256": sha256_bytes(payload), "bytes": len(payload)}],
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("outputs/sdk_cli_test_probe.txt", payload)
        archive.writestr("bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def test_sdk_ingest_bundle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = Path("bundle.zip")
    make_bundle(bundle)
    report = CoreLiteClient(Path(".")).ingest_bundle(bundle)
    assert report["decision"] == "ALLOW"
    assert Path("outputs/sdk_cli_test_probe.txt").exists()


def test_cli_ingest_bundle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = Path("bundle.zip")
    make_bundle(bundle)
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run([sys.executable, str(repo_root / "scripts/core_lite_cli.py"), "ingest-bundle", str(bundle)], text=True, capture_output=True)
    assert proc.returncode == 0, proc.stderr
