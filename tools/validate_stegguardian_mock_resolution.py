import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "state" / "stegguardian" / "seed_state_records.json"
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


def ref_is_resolved(ref, state):
    record = state.get("records", {}).get(ref)
    if not record:
        return False
    return record.get("status") == "active" and record.get("standing") == "resolved"


def decide(payload, state):
    for ref in collect_refs(payload):
        if not ref_is_resolved(ref, state):
            return "FAIL_CLOSED"
    if payload.get("cell_id") == "INT_CHILD_APPROVED_AI_TUTOR":
        return "ALLOW"
    return "CONDITIONAL"


def main():
    state = load_json(STATE_PATH)
    failures = []

    for case in CASES:
        payload = load_json(case["input"])
        actual = decide(payload, state)
        expected = case["expected"]
        if actual != expected:
            failures.append(f"{case['label']}: expected {expected}, got {actual}")

    if failures:
        print("StegGuardian state resolution validation failed:")
        for failure in failures:
            print("- " + failure)
        return 1

    print(f"StegGuardian state resolution validation passed: {len(CASES)} cases")
    return 0


main()
