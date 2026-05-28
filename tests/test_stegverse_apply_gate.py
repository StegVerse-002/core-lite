"""
test_stegverse_apply_gate.py

Unit tests for StegVerse-002 M11 stegverse_apply_gate.py
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import stegverse_apply_gate as gate


def make_request(extra: dict = None) -> dict:
    req = {
        "schema": gate.REQUEST_SCHEMA,
        "request_id": "test.request.v1",
        "entity": "StegVerse-002",
        "stage": "SV002-M11",
        "capability": "governed_apply_review_boundary",
        "requester": "Rigel",
        "transition_class": "tooling",
        "authority_ref": "SV002-M11/apply-review-gate-only",
        "policy_ref": "triad/default-deny/no-broad-authority",
        "dry_run": True,  # dry_run=True so Triad unresolved -> ALLOW not DEFER
        "target_files": [
            {"path": "scripts/stegverse_apply_gate.py", "operation": "create"}
        ],
    }
    if extra:
        req.update(extra)
    return req


def run_gate(req: dict, tmpdir: str) -> dict:
    req_path = os.path.join(tmpdir, "request.json")
    with open(req_path, "w") as f:
        json.dump(req, f)
    report_path = os.path.join(tmpdir, "report.json")
    receipt_path = os.path.join(tmpdir, "receipt.jsonl")
    output_path = os.path.join(tmpdir, "output.md")
    gate.gate(
        request_path=req_path,
        entity="StegVerse-002",
        stage="SV002-M11",
        report_path=report_path,
        receipt_path=receipt_path,
        output_path=output_path,
    )
    with open(report_path) as f:
        return json.load(f)


class TestSchemaChecks(unittest.TestCase):

    def test_valid_schema(self):
        self.assertTrue(gate.check_request_schema({"schema": gate.REQUEST_SCHEMA}))

    def test_invalid_schema(self):
        self.assertFalse(gate.check_request_schema({"schema": "wrong"}))

    def test_entity_declared(self):
        self.assertTrue(gate.check_entity_declared({"entity": "StegVerse-002"}))
        self.assertFalse(gate.check_entity_declared({"entity": ""}))
        self.assertFalse(gate.check_entity_declared({}))

    def test_stage_valid(self):
        self.assertTrue(gate.check_stage_valid({"stage": "SV002-M11"}))
        self.assertTrue(gate.check_stage_valid({"stage": "SV002-M10.5"}))
        self.assertFalse(gate.check_stage_valid({"stage": "SV001-M11"}))
        self.assertFalse(gate.check_stage_valid({"stage": ""}))

    def test_capability_declared(self):
        self.assertTrue(gate.check_capability_declared({"capability": "something"}))
        self.assertFalse(gate.check_capability_declared({"capability": ""}))


class TestAuthorityChecks(unittest.TestCase):

    def test_scoped_authority_ref(self):
        req = {"authority_ref": "SV002-M11/apply-review-gate-only"}
        self.assertTrue(gate.check_authority_ref_scoped(req))

    def test_broad_authority_star(self):
        req = {"authority_ref": "SV002-M11/*"}
        self.assertFalse(gate.check_authority_ref_scoped(req))

    def test_broad_authority_all(self):
        req = {"authority_ref": "all"}
        self.assertFalse(gate.check_authority_ref_scoped(req))

    def test_broad_authority_admin(self):
        req = {"authority_ref": "admin"}
        self.assertFalse(gate.check_authority_ref_scoped(req))

    def test_missing_authority_ref(self):
        req = {"authority_ref": ""}
        self.assertFalse(gate.check_authority_ref_scoped(req))

    def test_policy_ref_present(self):
        self.assertTrue(gate.check_policy_ref_present({"policy_ref": "triad/default-deny"}))
        self.assertFalse(gate.check_policy_ref_present({"policy_ref": ""}))


class TestTransitionClass(unittest.TestCase):

    def test_allowed_classes(self):
        for tc in gate.ALLOWED_TRANSITION_CLASSES:
            self.assertTrue(gate.check_transition_class({"transition_class": tc}))

    def test_denied_class(self):
        self.assertFalse(gate.check_transition_class({"transition_class": "arbitrary"}))


class TestTargetPaths(unittest.TestCase):

    def test_clean_paths(self):
        req = {"target_files": [
            {"path": "scripts/foo.py", "operation": "create"},
            {"path": "docs/bar.md", "operation": "update"},
        ]}
        ok, denied = gate.check_target_paths_allowed(req)
        self.assertTrue(ok)
        self.assertEqual(denied, [])

    def test_denied_readme(self):
        req = {"target_files": [{"path": "README.md", "operation": "update"}]}
        ok, denied = gate.check_target_paths_allowed(req)
        self.assertFalse(ok)
        self.assertIn("denied_path:README.md", denied)

    def test_denied_workflow(self):
        req = {"target_files": [
            {"path": ".github/workflows/bad.yml", "operation": "create"}
        ]}
        ok, denied = gate.check_target_paths_allowed(req)
        self.assertFalse(ok)
        self.assertTrue(any("denied_prefix" in d for d in denied))

    def test_no_target_files(self):
        req = {}
        ok, denied = gate.check_target_paths_allowed(req)
        self.assertTrue(ok)


class TestTriadStubs(unittest.TestCase):

    def test_gcat_bcat_none_for_clean(self):
        req = make_request()
        self.assertIsNone(gate.check_gcat_bcat(req))

    def test_gcat_bcat_false_for_broad_authority(self):
        req = make_request({"authority_ref": "admin"})
        self.assertFalse(gate.check_gcat_bcat(req))

    def test_ecat_icat_none(self):
        req = make_request()
        self.assertIsNone(gate.check_ecat_icat(req))

    def test_ecat_icat_false_missing_entity(self):
        req = make_request({"entity": "", "requester": ""})
        self.assertFalse(gate.check_ecat_icat(req))

    def test_existence_none_for_create(self):
        req = make_request()
        self.assertIsNone(gate.check_existence(req))

    def test_existence_none_for_delete(self):
        req = make_request({"target_files": [
            {"path": "scripts/old.py", "operation": "delete"}
        ]})
        self.assertIsNone(gate.check_existence(req))


class TestDecision(unittest.TestCase):

    def test_allow_on_dry_run_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req = make_request({"dry_run": True})
            report = run_gate(req, tmpdir)
            self.assertEqual(report["decision"], "ALLOW")
            self.assertEqual(report["errors"], [])

    def test_defer_on_binding_transition(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req = make_request({"dry_run": False})
            report = run_gate(req, tmpdir)
            self.assertEqual(report["decision"], "DEFER")

    def test_deny_on_bad_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req = make_request({"schema": "wrong.schema"})
            report = run_gate(req, tmpdir)
            self.assertEqual(report["decision"], "DENY")

    def test_deny_on_broad_authority(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req = make_request({"authority_ref": "admin", "dry_run": True})
            report = run_gate(req, tmpdir)
            self.assertEqual(report["decision"], "DENY")

    def test_deny_on_workflow_target(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req = make_request({
                "dry_run": True,
                "target_files": [
                    {"path": ".github/workflows/bad.yml", "operation": "create"}
                ]
            })
            report = run_gate(req, tmpdir)
            self.assertEqual(report["decision"], "DENY")

    def test_deny_on_readme_target(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req = make_request({
                "dry_run": True,
                "target_files": [{"path": "README.md", "operation": "update"}]
            })
            report = run_gate(req, tmpdir)
            self.assertEqual(report["decision"], "DENY")

    def test_receipt_emitted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req = make_request({"dry_run": True})
            req_path = os.path.join(tmpdir, "request.json")
            with open(req_path, "w") as f:
                json.dump(req, f)
            receipt_path = os.path.join(tmpdir, "receipt.jsonl")
            gate.gate(
                request_path=req_path,
                entity="StegVerse-002",
                stage="SV002-M11",
                report_path=os.path.join(tmpdir, "report.json"),
                receipt_path=receipt_path,
                output_path=os.path.join(tmpdir, "output.md"),
            )
            self.assertTrue(os.path.exists(receipt_path))
            with open(receipt_path) as f:
                data = json.loads(f.readline())
            self.assertEqual(data["task"], "stegverse.apply.gate")
            self.assertIn("decision", data)
            self.assertIn("entity", data)

    def test_deny_on_invalid_transition_class(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req = make_request({"transition_class": "arbitrary", "dry_run": True})
            report = run_gate(req, tmpdir)
            self.assertEqual(report["decision"], "DENY")

    def test_deny_on_missing_policy_ref(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req = make_request({"policy_ref": "", "dry_run": True})
            report = run_gate(req, tmpdir)
            self.assertEqual(report["decision"], "DENY")


if __name__ == "__main__":
    unittest.main()
