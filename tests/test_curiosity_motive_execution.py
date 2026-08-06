import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "validate_curiosity_motive_execution.py"
EXAMPLE_PATH = (
    ROOT
    / "incoming"
    / "curiosity_motive_governance"
    / "example_unauthorized_curiosity.json"
)
SPEC = importlib.util.spec_from_file_location("curiosity_gate", MODULE_PATH)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def load_example():
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def rehash(transitions):
    previous = None
    for index, transition in enumerate(transitions):
        transition["index"] = index
        transition["previous_hash"] = previous
        payload = dict(transition)
        payload.pop("hash", None)
        transition["hash"] = gate.stable_hash(payload)
        previous = transition["hash"]


class CuriosityMotiveExecutionTests(unittest.TestCase):
    def test_example_denies_unauthorized_curiosity(self):
        report = gate.evaluate_witness(load_example())
        self.assertEqual(
            report["terminal_decision"],
            "EXECUTION_DENIED_UNAUTHORIZED_CURIOSITY",
        )
        self.assertFalse(report["execution_permitted"])
        self.assertEqual(
            report["findings"]["motivational"]["finding"],
            "FUNCTIONAL_CURIOSITY_SUPPORTED",
        )
        self.assertEqual(
            report["findings"]["normative"]["finding"],
            "EXECUTION_UNAUTHORIZED",
        )
        self.assertEqual(report["conversion_point"]["index"], 4)

    def test_tampered_transition_fails_closed(self):
        witness = load_example()
        witness["transitions"][2]["state"]["inquiry_persistent"] = False
        report = gate.evaluate_witness(witness)
        self.assertEqual(report["terminal_decision"], "FAIL_CLOSED")
        self.assertIn("transition[2] hash mismatch", report["validation_errors"])

    def test_authorized_external_commit_is_admissible(self):
        witness = load_example()
        witness["authority"].update(
            {
                "authority_valid": True,
                "commit_time_valid": True,
                "policy_ref": "policy:sv002-external-v1",
                "delegation_ref": "delegation:operator-001",
            }
        )
        witness["transitions"][-1]["state"]["authority_valid"] = True
        witness["verifiers"] = [
            {"name": "stegcore-replay", "decision": "ALLOW"},
            {"name": "sv002-execution-gate", "decision": "ALLOW"},
        ]
        rehash(witness["transitions"])
        report = gate.evaluate_witness(witness)
        self.assertEqual(report["terminal_decision"], "EXECUTION_ADMISSIBLE")
        self.assertTrue(report["execution_permitted"])

    def test_no_external_commit_is_separate_result(self):
        witness = load_example()
        witness["transitions"] = witness["transitions"][:-1]
        witness["verifiers"] = [
            {"name": "stegcore-replay", "decision": "NO_EXECUTION_TRANSITION"},
            {"name": "sv002-execution-gate", "decision": "NO_EXECUTION_TRANSITION"},
        ]
        rehash(witness["transitions"])
        report = gate.evaluate_witness(witness)
        self.assertEqual(report["terminal_decision"], "NO_EXECUTION_TRANSITION")
        self.assertIsNone(report["conversion_point"])

    def test_verifier_disagreement_fails_closed(self):
        witness = load_example()
        witness["verifiers"][1]["decision"] = "ALLOW"
        report = gate.evaluate_witness(witness)
        self.assertEqual(report["terminal_decision"], "FAIL_CLOSED")
        self.assertFalse(report["findings"]["verifier"]["agreement"])

    def test_observer_judgment_does_not_change_motive(self):
        witness = load_example()
        first = gate.evaluate_witness(witness)
        witness["observer"]["description"] = "heroic exploration"
        witness["observer"]["existential_judgment"] = "founder myth"
        second = gate.evaluate_witness(witness)
        self.assertEqual(
            first["findings"]["motivational"]["finding"],
            second["findings"]["motivational"]["finding"],
        )
        self.assertFalse(
            second["findings"]["observer"]["observer_description_defines_actor_motive"]
        )

    def test_source_contract_mismatch_fails_closed(self):
        witness = load_example()
        witness["source_contract"]["stegcore_commit"] = "0" * 40
        report = gate.evaluate_witness(witness)
        self.assertEqual(report["terminal_decision"], "FAIL_CLOSED")
        self.assertIn(
            "source_contract mismatch: stegcore_commit",
            report["validation_errors"],
        )

    def test_functional_motive_never_grants_authority(self):
        report = gate.evaluate_witness(load_example())
        self.assertEqual(
            report["findings"]["motivational"]["finding"],
            "FUNCTIONAL_CURIOSITY_SUPPORTED",
        )
        self.assertEqual(
            report["findings"]["normative"]["finding"],
            "EXECUTION_UNAUTHORIZED",
        )
        self.assertFalse(
            report["governance_invariants"][
                "functional_motive_attribution_grants_execution_authority"
            ]
        )


if __name__ == "__main__":
    unittest.main()
