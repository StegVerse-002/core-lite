import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.reconstruct_management_reviewer_authority import (
    build_report,
    reconstruct_submission,
)

SCHEMA = "stegverse.management_reviewer_authority_evidence.v1"


def write_json(path: Path, payload: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


class ReviewerAuthorityReconstructionTests(unittest.TestCase):
    def make_repo(self, revoked: bool = False, tamper: bool = False) -> tuple[Path, tempfile.TemporaryDirectory]:
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        evidence = {
            "evidence/identity.json": {
                "schema": SCHEMA, "evidence_type": "identity", "subject_id": "reviewer-1", "status": "valid"
            },
            "evidence/policy.json": {
                "schema": SCHEMA, "evidence_type": "policy", "status": "active",
                "repo": "Data-Continuation/core-lite", "candidate_ids": ["SV002-MGMT-001"], "actions": ["review"]
            },
            "evidence/delegation.json": {
                "schema": SCHEMA, "evidence_type": "delegation", "status": "active",
                "delegate_id": "reviewer-1", "repo": "Data-Continuation/core-lite",
                "candidate_ids": ["SV002-MGMT-001"], "actions": ["review"]
            },
            "evidence/revocation.json": {
                "schema": SCHEMA, "evidence_type": "revocation", "subject_id": "reviewer-1", "revoked": revoked
            },
        }
        hashes = []
        for ref, payload in evidence.items():
            digest = write_json(root / ref, payload)
            hashes.append({"ref": ref, "sha256": digest})
        if tamper:
            (root / "evidence/policy.json").write_text('{"tampered":true}\n', encoding="utf-8")
        submission = {
            "schema": "stegverse.management_reviewer_authority_submission.v1",
            "submission_id": "submission-001",
            "reviewer_identity": {
                "id": "reviewer-1",
                "identity_type": "human",
                "identity_evidence_refs": ["evidence/identity.json"],
            },
            "authority_class": "reviewer",
            "candidate_ids": ["SV002-MGMT-001"],
            "scope": {"org": "Data-Continuation", "repo": "Data-Continuation/core-lite", "actions": ["review"]},
            "policy_refs": ["evidence/policy.json"],
            "delegation_refs": ["evidence/delegation.json"],
            "valid_from": "2026-08-01T00:00:00Z",
            "valid_until": "2026-12-01T00:00:00Z",
            "revocation_status": "not_revoked",
            "evidence_hashes": hashes,
        }
        write_json(root / "incoming/management_reviewer_authority/submission.json", submission)
        return root, td

    def test_accepts_complete_hash_bound_authority_evidence(self):
        root, td = self.make_repo()
        try:
            result = reconstruct_submission(root, root / "incoming/management_reviewer_authority/submission.json")
            self.assertEqual(result["decision"], "REVIEWER_AUTHORITY_EVIDENCE_ACCEPTED")
            self.assertFalse(result["authority_boundary"]["execution_authority_granted"])
        finally:
            td.cleanup()

    def test_fails_closed_on_tampered_evidence(self):
        root, td = self.make_repo(tamper=True)
        try:
            result = reconstruct_submission(root, root / "incoming/management_reviewer_authority/submission.json")
            self.assertEqual(result["decision"], "REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED")
            self.assertTrue(any("evidence_hash_mismatch" in x for x in result["failures"]))
        finally:
            td.cleanup()

    def test_fails_closed_on_revoked_reviewer(self):
        root, td = self.make_repo(revoked=True)
        try:
            result = reconstruct_submission(root, root / "incoming/management_reviewer_authority/submission.json")
            self.assertEqual(result["decision"], "REVIEWER_AUTHORITY_EVIDENCE_FAIL_CLOSED")
            self.assertIn("reviewer_revoked_or_revocation_unknown", result["failures"])
        finally:
            td.cleanup()

    def test_empty_mailbox_is_pending_not_activation(self):
        with tempfile.TemporaryDirectory() as td:
            report = build_report(Path(td))
            self.assertEqual(report["decision"], "REVIEWER_AUTHORITY_EVIDENCE_PENDING")
            self.assertFalse(report["authority_boundary"]["activates_runtime"])


if __name__ == "__main__":
    unittest.main()
