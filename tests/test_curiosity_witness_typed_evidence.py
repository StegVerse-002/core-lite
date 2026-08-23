import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHAIN = ROOT / "records" / "curiosity-witness-runtime-evidence-chain.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class TypedEvidenceChainTests(unittest.TestCase):
    def test_digest_types_and_shapes(self):
        chain = json.loads(CHAIN.read_text(encoding="utf-8"))
        allowed = {"file_digest", "record_self_hash", "canonical_object_digest", "git_object_id", "external_artifact"}
        for entry in chain["entries"]:
            with self.subTest(evidence_id=entry["evidence_id"]):
                self.assertIn(entry["digest_type"], allowed)
                if entry["digest_type"] == "git_object_id":
                    self.assertRegex(entry["digest"], HEX40)
                    self.assertIn(entry["object_kind"], {"commit", "blob"})
                else:
                    self.assertRegex(entry["digest"], HEX64)
                self.assertRegex(entry["source_repository"], r"^[^/]+/[^/]+$")
                self.assertIn("required_for_decision", entry)
                self.assertIn("availability_state", entry)
                self.assertIn("verification_state", entry)

    def test_hosted_artifact_fallback_requires_verified_repository_mirror(self):
        chain = json.loads(CHAIN.read_text(encoding="utf-8"))
        external = next(e for e in chain["entries"] if e["digest_type"] == "external_artifact")
        self.assertTrue(external["required_for_decision"])
        self.assertEqual(external["unavailable_behavior"], "USE_VERIFIED_REPOSITORY_MIRROR")
        self.assertEqual(external["mirror_state"], "REPOSITORY_RESIDENT")
        self.assertTrue(external["mirror_verification_required"])
        self.assertEqual(external["verification_state"], "MIRROR_HASH_VERIFIED")
        self.assertEqual(external["mirror_unavailable_behavior"], "FAIL_CLOSED")
        self.assertTrue(external["mirror_path"])


if __name__ == "__main__":
    unittest.main()
