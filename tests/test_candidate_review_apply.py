from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from core_lite.candidates import CandidateApplier, CandidateReviewer


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def make_bundle(path: Path) -> None:
    payload = b"candidate review apply test payload\n"
    manifest = {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "candidate_review_apply_test_bundle",
        "purpose": "candidate review apply unit test",
        "allow_root_readme": False,
        "allow_workflows": False,
        "files": [
            {
                "path": "outputs/candidate_review_apply_probe.txt",
                "sha256": sha256_bytes(payload),
                "bytes": len(payload),
            }
        ],
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("outputs/candidate_review_apply_probe.txt", payload)
        archive.writestr("bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def make_candidate_ref(path: Path, bundle_path: Path, candidate_id: str = "candidate-test") -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "stegverse.candidate_ref.v1",
                "candidate_id": candidate_id,
                "task_id": "stegverse.candidate.intake.apply",
                "bundle_path": str(bundle_path),
                "proposed_files": ["outputs/candidate_review_apply_probe.txt"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_candidate_review_then_apply_allows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = Path("candidate.zip")
    candidate_ref = Path("candidate_ref.json")
    make_bundle(bundle)
    make_candidate_ref(candidate_ref, bundle)

    review = CandidateReviewer(Path(".")).review(candidate_ref)
    assert review["decision"] == "ALLOW_CANDIDATE_REVIEW"

    apply_report = CandidateApplier(Path(".")).apply(candidate_ref, Path("reports/current/candidate_bundle_review_report.json"))
    assert apply_report["decision"] == "ALLOW_INSTALL"
    assert Path("outputs/candidate_review_apply_probe.txt").exists()


def test_candidate_apply_requires_matching_review(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = Path("candidate.zip")
    candidate_ref = Path("candidate_ref.json")
    make_bundle(bundle)
    make_candidate_ref(candidate_ref, bundle, candidate_id="candidate-a")

    review_path = Path("reports/current/candidate_bundle_review_report.json")
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        json.dumps(
            {
                "decision": "ALLOW_CANDIDATE_REVIEW",
                "candidate": {"candidate_id": "candidate-b"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    apply_report = CandidateApplier(Path(".")).apply(candidate_ref, review_path)
    assert apply_report["decision"] == "DENY_INSTALL"
    assert "candidate_id_mismatch" in apply_report["errors"]
