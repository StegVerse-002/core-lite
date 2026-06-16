from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from core_lite.incoming import IncomingMailbox


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def make_bundle(path: Path, *, schema: str = "stegverse.bundle_manifest.v1") -> None:
    payload = b"incoming mailbox test payload\n"
    manifest = {
        "schema": schema,
        "bundle_name": "incoming_mailbox_test_bundle",
        "purpose": "incoming mailbox unit test",
        "allow_root_readme": False,
        "allow_workflows": False,
        "files": [
            {
                "path": "outputs/incoming_mailbox_probe.txt",
                "sha256": sha256_bytes(payload),
                "bytes": len(payload),
            }
        ],
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("outputs/incoming_mailbox_probe.txt", payload)
        archive.writestr("bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def test_incoming_good_bundle_processes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    incoming = Path("incoming")
    incoming.mkdir()
    make_bundle(incoming / "good.zip")

    report = IncomingMailbox(Path("."), incoming).process()

    assert report["decision"] == "ALLOW"
    assert len(report["processed"]) == 1
    assert Path("outputs/incoming_mailbox_probe.txt").exists()
    assert Path("incoming/processed/good.zip").exists()
    assert Path("reports/current/incoming_mailbox_report.json").exists()
    assert Path("receipts/current/incoming_mailbox_receipt.jsonl").exists()


def test_incoming_bad_bundle_rejects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    incoming = Path("incoming")
    incoming.mkdir()
    make_bundle(incoming / "bad.zip", schema="bad.schema")

    report = IncomingMailbox(Path("."), incoming).process()

    assert report["decision"] == "ALLOW"
    assert len(report["rejected"]) == 1
    assert Path("incoming/rejected/bad.zip").exists()
