import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = ROOT / "examples" / "stegguardian_mock_resolution_table.json"
CASES = [
    {
        "label": "allow",
        "input": ROOT / "examples" / "stegguardian_adapter_input.json",
        "expected": "ALLOW",
    },
    {
        "label": "unresolved",
        "input": ROOT / "examples" / "stegguardian_adapter_unresolved_input.json",
        "expected": "FAIL_CLOSED",
    },
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def collect_refs(payload):
    refs = []
    for key in ["capability_state_ref", "provider_declaration_ref", "policy_ref"]:
        value = payload.get(key)
        if value:
            refs.append(value)
    refs.extend(payload.get("evidence_refs", []))
    refs.extend(payload.get("context_refs", []))
    return refs


def decide(payload, table):
    entries = table.get("entries", {})
    for ref in collect_refs(payload):
        if entries.get(ref) != "resolved":
            return "FAIL_CLOSED"
    if payload.get("cell_id") == "INT_CHILD_APPROVED_AI_TUTOR":
        return "ALLOW"
    return "CONDITIONAL"


def main():
    table = load_json(TABLE_PATH)
    failures = []

    for case in CASES:
        payload = load_json(case["input"])
        actual = decide(payload, table)
        expected = case["expected"]
        if actual != expected:
            failures.append(f"{case['label']}: expected {expected}, got {actual}")

    if failures:
        print("StegGuardian mock resolution validation failed:")
        for failure in failures:
            print("- " + failure)
        return 1

    print(f"StegGuardian mock resolution validation passed: {len(CASES)} cases")
    return 0


main()
