"""
test_candidate_bundle_review.py

Unit tests for StegVerse-002 M10.5 candidate_bundle_review.py
"""

import json
import os
import sys
import zipfile
import hashlib
import tempfile
import unittest

# Add scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import candidate_bundle_review as cbr


def sha256_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def make_bundle_zip(dest_path: str, files: dict, manifest: dict) -> str:
    """
    Create a test bundle zip with given files and manifest.
    Returns sha256 of the zip.
    """
    with zipfile.ZipFile(dest_path, "w") as zf:
        zf.writestr("bundle_manifest.json", json.dumps(manifest))
        for path, content in files.items():
            zf.writestr(path, content)
    return cbr.sha256_file(dest_path)


def make_ref(source: str, sha256: str, extra: dict = None) -> dict:
    ref = {
        "schema": cbr.REF_SCHEMA,
        "candidate_id": "test.candidate.v1",
        "source_type": "local_path",
        "source": source,
        "expected_sha256": sha256,
        "declared_transition_class": "tooling",
        "declared_stage": "SV002-M10",
        "authority_ref": "SV002-M10.5/candidate-review-only",
        "policy_ref": "triad/default-deny/no-broad-authority",
    }
    if extra:
        ref.update(extra)
    return ref


def make_manifest(files: dict, extra: dict = None) -> dict:
    manifest = {
        "schema": cbr.BUNDLE_MANIFEST_SCHEMA,
        "bundle_id": "test.bundle.v1",
        "bundle_name": "Test Bundle",
        "capability": "test",
        "created_utc": "2026-05-28T00:00:00+00:00",
        "description": "Test bundle",
        "allow_root_readme": False,
        "allow_workflows": False,
        "allowed_paths": ["docs/", "scripts/", "schemas/", "tests/", "tools/"],
        "expected_outputs": [],
        "files": [
            {
                "path": p,
                "sha256": sha256_bytes(c.encode()),
                "bytes": len(c),
                "required": True,
                "mode": "100644",
            }
            for p, c in files.items()
        ],
    }
    if extra:
        manifest.update(extra)
    return manifest


class TestRefValidation(unittest.TestCase):

    def test_valid_schema(self):
        ref = {"schema": cbr.REF_SCHEMA}
        self.assertTrue(cbr.check_ref_schema(ref))

    def test_invalid_schema(self):
        ref = {"schema": "wrong.schema"}
        self.assertFalse(cbr.check_ref_schema(ref))

    def test_allowed_source_types(self):
        for st in ("url", "local_path", "release_asset"):
            self.assertTrue(cbr.check_source_type({"source_type": st}))

    def test_denied_source_type(self):
        self.assertFalse(cbr.check_source_type({"source_type": "ftp"}))

    def test_transition_class_allowed(self):
        for tc in cbr.ALLOWED_TRANSITION_CLASSES:
            self.assertTrue(cbr.check_transition_class({"declared_transition_class": tc}))

    def test_transition_class_denied(self):
        self.assertFalse(cbr.check_transition_class({"declared_transition_class": "arbitrary"}))

    def test_stage_valid(self):
        self.assertTrue(cbr.check_stage({"declared_stage": "SV002-M10"}))
        self.assertTrue(cbr.check_stage({"declared_stage": "SV002-M10.5"}))

    def test_stage_invalid(self):
        self.assertFalse(cbr.check_stage({"declared_stage": "SV001-M10"}))
        self.assertFalse(cbr.check_stage({"declared_stage": ""}))


class TestManifestChecks(unittest.TestCase):

    def test_no_broad_authority_clean(self):
        m = {"allow_root_readme": False, "allow_workflows": False}
        self.assertTrue(cbr.check_no_broad_authority(m))

    def test_broad_authority_root_readme(self):
        m = {"allow_root_readme": True, "allow_workflows": False}
        self.assertFalse(cbr.check_no_broad_authority(m))

    def test_broad_authority_workflows(self):
        m = {"allow_root_readme": False, "allow_workflows": True}
        self.assertFalse(cbr.check_no_broad_authority(m))

    def test_no_root_readme_overwrite_clean(self):
        m = {"files": [{"path": "docs/something.md"}]}
        self.assertTrue(cbr.check_no_root_readme_overwrite(m))

    def test_root_readme_overwrite_denied(self):
        m = {"files": [{"path": "README.md"}]}
        self.assertFalse(cbr.check_no_root_readme_overwrite(m))

    def test_no_workflow_changes_clean(self):
        m = {"files": [{"path": "scripts/foo.py"}]}
        self.assertTrue(cbr.check_no_workflow_changes(m))

    def test_workflow_changes_denied(self):
        m = {"files": [{"path": ".github/workflows/foo.yml"}]}
        self.assertFalse(cbr.check_no_workflow_changes(m))

    def test_paths_allowed(self):
        allowed = ["docs/", "scripts/"]
        m = {"files": [{"path": "docs/foo.md"}, {"path": "scripts/bar.py"}]}
        ok, denied = cbr.check_paths_allowed(m, allowed)
        self.assertTrue(ok)
        self.assertEqual(denied, [])

    def test_paths_denied_root_manifest(self):
        allowed = ["docs/", "scripts/"]
        m = {"files": [{"path": "bundle_manifest.json"}]}
        ok, denied = cbr.check_paths_allowed(m, allowed)
        self.assertFalse(ok)
        self.assertIn("denied_root_file:bundle_manifest.json", denied)

    def test_paths_denied_not_in_allowed(self):
        allowed = ["docs/"]
        m = {"files": [{"path": "arbitrary/file.txt"}]}
        ok, denied = cbr.check_paths_allowed(m, allowed)
        self.assertFalse(ok)


class TestTriadStubs(unittest.TestCase):

    def test_gcat_bcat_returns_none_for_clean(self):
        ref = {}
        m = {"allow_root_readme": False, "allow_workflows": False}
        result = cbr.check_gcat_bcat(ref, m)
        self.assertIsNone(result)

    def test_gcat_bcat_returns_false_for_broad_authority(self):
        ref = {}
        m = {"allow_root_readme": True, "allow_workflows": False}
        result = cbr.check_gcat_bcat(ref, m)
        self.assertFalse(result)

    def test_ecat_icat_returns_none(self):
        self.assertIsNone(cbr.check_ecat_icat({}))

    def test_existence_returns_none(self):
        self.assertIsNone(cbr.check_existence({}))


class TestFullReview(unittest.TestCase):

    def _run_review(self, ref_data: dict, tmpdir: str) -> dict:
        ref_path = os.path.join(tmpdir, "ref.json")
        with open(ref_path, "w") as f:
            json.dump(ref_data, f)
        report_path = os.path.join(tmpdir, "report.json")
        receipt_path = os.path.join(tmpdir, "receipt.jsonl")
        output_path = os.path.join(tmpdir, "output.md")
        cbr.review(
            ref_path=ref_path,
            entity="StegVerse-002",
            stage="SV002-M10",
            report_path=report_path,
            receipt_path=receipt_path,
            output_path=output_path,
        )
        with open(report_path) as f:
            return json.load(f)

    def test_allow_on_valid_bundle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = {"docs/readme.md": "hello", "scripts/foo.py": "print('hi')"}
            manifest = make_manifest(files)
            bundle_path = os.path.join(tmpdir, "bundle.zip")
            sha = make_bundle_zip(bundle_path, files, manifest)
            ref = make_ref(bundle_path, sha)
            report = self._run_review(ref, tmpdir)
            self.assertEqual(report["decision"], "ALLOW_CANDIDATE_REVIEW")
            self.assertEqual(report["errors"], [])

    def test_deny_on_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = {"docs/readme.md": "hello"}
            manifest = make_manifest(files)
            bundle_path = os.path.join(tmpdir, "bundle.zip")
            make_bundle_zip(bundle_path, files, manifest)
            ref = make_ref(bundle_path, "sha256:" + "a" * 64)
            report = self._run_review(ref, tmpdir)
            self.assertIn(report["decision"], ("DENY_CANDIDATE", "FAIL_CLOSED"))

    def test_deny_on_root_manifest_in_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = {"bundle_manifest.json": "{}"}
            manifest = make_manifest({})
            # Manually inject denied file into manifest files list
            manifest["files"].append({
                "path": "bundle_manifest.json",
                "sha256": cbr.sha256_bytes(b"{}"),
                "bytes": 2,
                "required": True,
                "mode": "100644",
            })
            bundle_path = os.path.join(tmpdir, "bundle.zip")
            sha = make_bundle_zip(bundle_path, files, manifest)
            ref = make_ref(bundle_path, sha)
            report = self._run_review(ref, tmpdir)
            self.assertIn(report["decision"], ("DENY_CANDIDATE", "FAIL_CLOSED"))

    def test_deny_on_workflow_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = {".github/workflows/bad.yml": "on: push"}
            manifest = make_manifest(files, extra={
                "allowed_paths": [".github/"]
            })
            bundle_path = os.path.join(tmpdir, "bundle.zip")
            sha = make_bundle_zip(bundle_path, files, manifest)
            ref = make_ref(bundle_path, sha)
            report = self._run_review(ref, tmpdir)
            self.assertIn(report["decision"], ("DENY_CANDIDATE", "FAIL_CLOSED"))

    def test_receipt_emitted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = {"docs/readme.md": "hello"}
            manifest = make_manifest(files)
            bundle_path = os.path.join(tmpdir, "bundle.zip")
            sha = make_bundle_zip(bundle_path, files, manifest)
            ref = make_ref(bundle_path, sha)
            ref_path = os.path.join(tmpdir, "ref.json")
            with open(ref_path, "w") as f:
                json.dump(ref, f)
            receipt_path = os.path.join(tmpdir, "receipt.jsonl")
            cbr.review(
                ref_path=ref_path,
                entity="StegVerse-002",
                stage="SV002-M10",
                report_path=os.path.join(tmpdir, "report.json"),
                receipt_path=receipt_path,
                output_path=os.path.join(tmpdir, "output.md"),
            )
            self.assertTrue(os.path.exists(receipt_path))
            with open(receipt_path) as f:
                line = f.readline()
            data = json.loads(line)
            self.assertEqual(data["task"], "stegverse.candidate.intake.review")


if __name__ == "__main__":
    unittest.main()
