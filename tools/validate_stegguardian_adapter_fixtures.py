import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOW_INPUT = ROOT / "examples" / "stegguardian_adapter_input.json"
ALLOW_OUTPUT = ROOT / "examples" / "stegguardian_adapter_expected_output.json"
UNRESOLVED_INPUT = ROOT / "examples" / "stegguardian_adapter_unresolved_input.json"
UNRESOLVED_OUTPUT = ROOT / "examples" / "stegguardian_adapter_unresolved_expected_output.json"
REQUIRED_INPUT_FIELDS = [
    "cell_id",
    "subject_class",
    "interaction_type",
    "provider_class",
    "capability_state_ref",
    "provider_declaration_ref",
    "policy_ref",
    "evidence_refs",
    "context_refs",
]
REQUIRED_OUTPUT_FIELDS = [
    "decision",
    "standing_ref",
    "decision_reasons",
    "receipt_required",
    "receipt_material",
]
DECISIONS = {"ALLOW", "DENY", "CONDITIONAL", "FAIL_CLOSED"}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_input(payload, label):
    failures = []
    for field in REQUIRED_INPUT_FIELDS:
        if field not in payload:
            failures.append(f"{label}: missing input field {field}")
    if not isinstance(payload.get("evidence_refs"), list) or not payload.get("evidence_refs"):
        failures.append(f"{label}: evidence_refs must be a non-empty list")
    if not isinstance(payload.get("context_refs"), list) or not payload.get("context_refs"):
        failures.append(f"{label}: context_refs must be a non-empty list")
    return failures


def validate_output(payload, label, expected_decision):
    failures = []
    for field in REQUIRED_OUTPUT_FIELDS:
        if field not in payload:
            failures.append(f"{label}: missing output field {field}")
    if payload.get("decision") not in DECISIONS:
        failures.append(f"{label}: invalid decision {payload.get('decision')}")
    if payload.get("decision") != expected_decision:
        failures.append(f"{label}: expected {expected_decision}, got {payload.get('decision')}")
    if payload.get("receipt_required") is not True:
        failures.append(f"{label}: receipt_required must be true")
    receipt = payload.get("receipt_material", {})
    if receipt.get("decision") != payload.get("decision"):
        failures.append(f"{label}: receipt decision must match output decision")
    if receipt.get("disclosure_minimized") is not True:
        failures.append(f"{label}: receipt disclosure_minimized must be true")
    return failures


def main():
    checks = [
        (ALLOW_INPUT, ALLOW_OUTPUT, "ALLOW", "allow"),
        (UNRESOLVED_INPUT, UNRESOLVED_OUTPUT, "FAIL_CLOSED", "unresolved"),
    ]
    failures = []

    for input_path, output_path, expected_decision, label in checks:
        failures.extend(validate_input(load_json(input_path), label))
        failures.extend(validate_output(load_json(output_path), label, expected_decision))

    if failures:
        print("StegGuardian adapter fixture validation failed:")
        for failure in failures:
            print("- " + failure)
        return 1

    print(f"StegGuardian adapter fixture validation passed: {len(checks)} cases")
    return 0


main()
