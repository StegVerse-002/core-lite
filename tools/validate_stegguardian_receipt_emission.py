import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "examples" / "stegguardian_adapter_expected_output.json"
RECEIPT_PATH = ROOT / "examples" / "stegguardian_receipt_emission_expected.json"
REQUIRED_FIELDS = [
    "receipt_id",
    "subject_class",
    "interaction_type",
    "provider_class",
    "capability_state_ref",
    "policy_ref",
    "standing_ref",
    "decision",
    "decision_reasons",
    "disclosure_minimized",
    "challenge_path",
    "created_at",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    output = load_json(OUTPUT_PATH)
    receipt = load_json(RECEIPT_PATH)
    material = output.get("receipt_material", {})
    failures = []

    for field in REQUIRED_FIELDS:
        if field not in receipt:
            failures.append(f"missing receipt field {field}")

    for field in ["subject_class", "interaction_type", "provider_class", "capability_state_ref", "policy_ref", "standing_ref", "decision", "challenge_path"]:
        if receipt.get(field) != material.get(field):
            failures.append(f"receipt field {field} does not match adapter output material")

    if receipt.get("decision") != output.get("decision"):
        failures.append("receipt decision does not match output decision")

    if receipt.get("disclosure_minimized") is not True:
        failures.append("receipt disclosure_minimized must be true")

    if not isinstance(receipt.get("decision_reasons"), list) or not receipt.get("decision_reasons"):
        failures.append("receipt decision_reasons must be non-empty")

    if failures:
        print("StegGuardian receipt emission validation failed:")
        for failure in failures:
            print("- " + failure)
        return 1

    print("StegGuardian receipt emission validation passed")
    return 0


main()
