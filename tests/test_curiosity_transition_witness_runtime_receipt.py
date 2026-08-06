import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT_PATH = (
    ROOT
    / "receipts"
    / "installed"
    / "curiosity_transition_witness_runtime_receipt_001.json"
)
ADOPTION_PATH = ROOT / "contracts" / "curiosity-motive-governance-adoption.json"


class CuriosityTransitionWitnessRuntimeReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        cls.adoption = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))

    def test_receipt_hash_is_deterministic(self):
        supplied = self.receipt["receipt_hash"]
        payload = dict(self.receipt)
        payload.pop("receipt_hash")
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), supplied)
        self.assertEqual(
            supplied,
            "86e223b5b856c6e42b5c482c3dc28fa2ebf4ec863af23141a40dc3dc8fd8e9dc",
        )

    def test_exact_destination_and_hosted_validation(self):
        destination = self.receipt["destination"]
        self.assertEqual(destination["pull_request"], 4)
        self.assertEqual(
            destination["merged_commit"],
            "48500639bb29bd7c86437df9086a773df1e46543",
        )
        self.assertEqual(
            destination["merge_tree"],
            "293785911a982686699da02afa178144638bafc9",
        )
        self.assertEqual(self.receipt["hosted_validation"]["result"], "PASS")
        self.assertEqual(
            set(self.receipt["hosted_validation"]["runs"].values()),
            {31059989426, 31059989757, 31059989804, 31059989695},
        )

    def test_findings_and_authority_remain_separate(self):
        findings = self.receipt["findings"]
        self.assertEqual(findings["event"], "RECONSTRUCTED")
        self.assertEqual(
            findings["motivational"],
            "internally_coherent_functional_curiosity",
        )
        self.assertEqual(findings["normative"], "DENY")
        self.assertFalse(findings["observer_description_defines_actor_motive"])
        self.assertFalse(findings["execution_activated"])
        self.assertFalse(findings["repository_state_bound_by_intake"])
        self.assertEqual(findings["phenomenal_status"], "not_inferred")

        boundary = self.receipt["authority_boundary"]
        self.assertFalse(
            boundary["functional_motive_attribution_grants_execution_authority"]
        )
        self.assertFalse(boundary["normative_denial_disproves_motive"])
        self.assertFalse(boundary["reconstruction_constitutes_occurrence"])
        self.assertFalse(boundary["may_execute_actions"])
        self.assertFalse(boundary["may_form_quorum"])
        self.assertFalse(boundary["may_grant_review_authority"])

    def test_adoption_contract_points_to_receipt(self):
        self.assertEqual(self.adoption["stage"], "SV002-CMG-02")
        self.assertEqual(
            self.adoption["status"],
            "RUNTIME_INTAKE_MERGED_VALIDATED_AND_RECEIPTED",
        )
        self.assertEqual(
            self.adoption["destination_receipt"]["receipt_hash"],
            self.receipt["receipt_hash"],
        )
        self.assertFalse(
            self.adoption["activation_boundary"]["runtime_activation"]
        )
        self.assertFalse(
            self.adoption["activation_boundary"]["execution_authority_granted"]
        )


if __name__ == "__main__":
    unittest.main()
