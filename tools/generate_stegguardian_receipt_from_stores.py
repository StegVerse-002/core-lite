import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "examples" / "stegguardian_adapter_input.json"
EXPECTED_RECEIPT_PATH = ROOT / "examples" / "stegguardian_receipt_emission_expected.json"
STORE_PATHS = [
    ROOT / "stores" / "capability-state" / "seed_records.json",
    ROOT / "stores" / "provider" / "seed_records.json",
    ROOT / "stores" / "rules" / "seed_records.json",
    ROOT / "stores" / "evidence" / "seed_records.json",
    ROOT / "stores" / "env" / "seed_records.json",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_records():
    records = {}
    for path in STORE_PATHS:
        records.update(load_json(path).get("records", {}))
    return records


def collect_refs(payload):
    refs = []
    for key in ["capability_state_ref", "provider_declaration_ref", "policy_ref"]:
        value = payload.get(key)
        if value:
            refs.append(value)
    refs.extend(payload.get("evidence_refs", []))
    refs.extend(payload.get("context_refs", []))
    return refs


def all_refs_resolved(payload, records):
    for ref in collect_refs(payload):
        record = records.get(ref)
        if not record:
            return False
        if record.get("status") != "active" or record.get("standing") != "resolved":
            return False
    return True


def generate_receipt(payload, records):
    resolved = all_refs_resolved(payload, records)
    decision = "ALLOW" if resolved and payload.get("cell_id") == "INT_CHILD_APPROVED_AI_TUTOR" else "FAIL_CLOSED"
    standing_ref = "standing:guardian_ai_tutor_allow_0001" if decision == "ALLOW" else "standing:unresolved"
    reasons = [
        "guardian education authority active",
        "provider educational declaration valid",
        "content class educational",
        "unrelated profiling absent",
    ] if decision == "ALLOW" else ["required standing could not be resolved or reconstructed"]

    return {
        "receipt_id": "core-lite-sg-rct-0001",
        "subject_class": payload["subject_class"],
        "interaction_type": payload["interaction_type"],
        "provider_class": payload["provider_class"],
        "capability_state_ref": payload["capability_state_ref"],
        "policy_ref": payload["policy_ref"],
        "standing_ref": standing_ref,
        "decision": decision,
        "decision_reasons": reasons,
        "disclosure_minimized": True,
        "challenge_path": "guardian.challenge.receipt" if decision == "ALLOW" else "subject.challenge.receipt",
        "created_at": "2026-06-20T00:00:00Z",
    }


def main():
    payload = load_json(INPUT_PATH)
    expected = load_json(EXPECTED_RECEIPT_PATH)
    actual = generate_receipt(payload, load_records())
    failures = []

    for key, expected_value in expected.items():
        if actual.get(key) != expected_value:
            failures.append(f"{key}: expected {expected_value}, got {actual.get(key)}")

    if failures:
        print("StegGuardian generated receipt validation failed:")
        for failure in failures:
            print("- " + failure)
        return 1

    print("StegGuardian generated receipt validation passed")
    return 0


main()
