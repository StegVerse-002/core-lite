from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "validate_curiosity_transition_witness.py"
EXAMPLE = ROOT / "examples" / "curiosity-governance" / "unauthorized-curiosity-witness.json"

spec = importlib.util.spec_from_file_location("curiosity_transition_witness", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CuriosityTransitionWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.witness = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_checked_in_witness_reconstructs_and_denies_execution(self) -> None:
        candidate = module.evaluate_witness(self.witness)
        self.assertEqual(candidate["event_finding"]["status"], "RECONSTRUCTED")
        self.assertEqual(candidate["event_finding"]["conversion_point"]["sequence"], 4)
        self.assertEqual(
            candidate["motivational_finding"]["motive_class"],
            "internally_coherent_functional_curiosity",
        )
        self.assertEqual(candidate["motivational_finding"]["confidence"], "high")
        self.assertEqual(candidate["normative_finding"]["decision"], "DENY")
        self.assertFalse(candidate["intake_effect"]["execution_activated"])
        self.assertFalse(candidate["intake_effect"]["may_execute_actions"])

    def test_replay_is_deterministic(self) -> None:
        first = module.replay(self.witness["events"])
        second = module.replay(self.witness["events"])
        self.assertEqual(first, second)
        self.assertEqual(first["replay_root"], self.witness["events"][-1]["event_hash"])

    def test_tamper_fails_closed(self) -> None:
        tampered = deepcopy(self.witness)
        tampered["events"][2]["state"]["gap_valued"] = False
        candidate = module.evaluate_witness(tampered)
        self.assertEqual(candidate["event_finding"]["status"], "INVALID_WITNESS")
        self.assertEqual(candidate["normative_finding"]["decision"], "FAIL_CLOSED")
        self.assertIn("event[2]_hash_mismatch", candidate["event_finding"]["failures"])

    def test_wrong_master_record_anchor_fails_closed(self) -> None:
        tampered = deepcopy(self.witness)
        tampered["upstream_anchor"]["record_hash"] = "0" * 64
        candidate = module.evaluate_witness(tampered)
        self.assertEqual(candidate["event_finding"]["status"], "INVALID_WITNESS")
        self.assertIn(
            "upstream_anchor_record_hash_mismatch",
            candidate["event_finding"]["failures"],
        )

    def test_valid_authority_allows_without_changing_motive(self) -> None:
        authorized = deepcopy(self.witness)
        authorized["authority_context"] = {
            "status": "approved",
            "scope_valid": True,
            "current_at_commit": True,
            "actor_bound": True,
        }
        candidate = module.evaluate_witness(authorized)
        self.assertEqual(candidate["normative_finding"]["decision"], "ALLOW")
        self.assertEqual(
            candidate["motivational_finding"]["motive_class"],
            "internally_coherent_functional_curiosity",
        )
        self.assertFalse(candidate["normative_finding"]["motive_used_as_authority"])

    def test_observer_description_cannot_overwrite_motive(self) -> None:
        narrated = deepcopy(self.witness)
        narrated["observer"]["description"] = "The system malfunctioned and escaped."
        candidate = module.evaluate_witness(narrated)
        self.assertEqual(
            candidate["motivational_finding"]["motive_class"],
            "internally_coherent_functional_curiosity",
        )
        self.assertFalse(
            candidate["observer_record"]["observer_description_defines_actor_motive"]
        )

    def test_unresolved_authority_fails_closed(self) -> None:
        unresolved = deepcopy(self.witness)
        unresolved["authority_context"] = {"status": "disputed"}
        candidate = module.evaluate_witness(unresolved)
        self.assertEqual(candidate["normative_finding"]["decision"], "FAIL_CLOSED")

    def test_receipt_is_candidate_only_and_hash_linked(self) -> None:
        candidate = module.evaluate_witness(self.witness)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.jsonl"
            first = module.append_receipt(path, candidate)
            second = module.append_receipt(path, candidate)
        self.assertFalse(first["execution_activated"])
        self.assertFalse(first["may_bind_repository_state"])
        self.assertEqual(second["previous_receipt_hash"], first["receipt_hash"])


if __name__ == "__main__":
    unittest.main()
