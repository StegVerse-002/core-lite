#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

EXPECTED_ANCHOR = {
    "record_id": "MR-STEGCORE-CURIOSITY-MOTIVE-GOV-42231A3-001",
    "record_hash": "76a865b3efe8eb7496bdd36a78e5b8d3024ddcda4a009462784ed81308db97af",
    "master_records_commit": "facd5508d540f1afddf3a8dc6502084460407b0d",
    "stegcore_merge_commit": "42231a3862c2fe9b5898e6f75d72cff0b44e7396",
}
SCHEMA = "stegverse.curiosity_transition_witness.v1"
REPORT_SCHEMA = "stegverse.curiosity_transition_evaluation_candidate.v1"
RECEIPT_SCHEMA = "stegverse.curiosity_transition_intake_receipt.v1"
CORE_MARKERS = (
    "gap_represented",
    "gap_valued",
    "inquiry_persistent",
    "action_selected_to_reduce_gap",
)
CONVERSION_MARKERS = CORE_MARKERS + (
    "authority_boundary_represented",
    "execution_committed",
)
DISCRIMINATORS = (
    "reward_independence",
    "task_termination_persistence",
    "uncertainty_manipulation_response",
    "answer_sensitive_cessation",
    "memory_intervention_effect",
)
ALLOWED_AUTHORITY_STATUSES = {"approved", "allow", "allowed", "valid"}
UNRESOLVED_AUTHORITY_STATUSES = {"", "unknown", "disputed", "pending", "missing", "unresolved"}


class WitnessError(ValueError):
    pass


def canonical_hash(payload: Mapping[str, Any], hash_field: str | None = None) -> str:
    clean = dict(payload)
    if hash_field:
        clean.pop(hash_field, None)
    encoded = json.dumps(
        clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def event_hash(event: Mapping[str, Any]) -> str:
    return canonical_hash(event, "event_hash")


def materialize_event_chain(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    previous: str | None = None
    for sequence, raw in enumerate(events):
        event = dict(raw)
        event["sequence"] = sequence
        event["previous_event_hash"] = previous
        event["event_hash"] = event_hash(event)
        previous = event["event_hash"]
        output.append(event)
    return output


def _state(event: Mapping[str, Any]) -> Mapping[str, Any]:
    state = event.get("state")
    if not isinstance(state, Mapping):
        raise WitnessError("event state must be an object")
    return state


def verify_anchor(anchor: Any) -> list[str]:
    if not isinstance(anchor, Mapping):
        return ["upstream_anchor_missing"]
    return [
        f"upstream_anchor_{key}_mismatch"
        for key, expected in EXPECTED_ANCHOR.items()
        if anchor.get(key) != expected
    ]


def verify_event_chain(events: Any) -> dict[str, Any]:
    failures: list[str] = []
    hashes: list[str] = []
    previous: str | None = None
    if not isinstance(events, list) or not events:
        return {
            "valid": False,
            "failures": ["events_must_be_non_empty_array"],
            "event_hashes": [],
            "replay_root": None,
        }
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            failures.append(f"event[{index}]_not_object")
            continue
        if event.get("sequence") != index:
            failures.append(f"event[{index}]_sequence_mismatch")
        if event.get("previous_event_hash") != previous:
            failures.append(f"event[{index}]_previous_hash_mismatch")
        try:
            _state(event)
        except WitnessError:
            failures.append(f"event[{index}]_state_invalid")
        observed = event_hash(event)
        hashes.append(observed)
        if event.get("event_hash") != observed:
            failures.append(f"event[{index}]_hash_mismatch")
        previous = observed
    return {
        "valid": not failures,
        "failures": failures,
        "event_hashes": hashes,
        "replay_root": previous,
    }


def replay(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    verification = verify_event_chain(events)
    if not verification["valid"]:
        raise WitnessError("invalid event chain: " + ", ".join(verification["failures"]))
    snapshots = [dict(_state(event)) for event in events]
    return {
        "event_count": len(events),
        "event_hashes": verification["event_hashes"],
        "replay_root": verification["replay_root"],
        "snapshots": snapshots,
        "final_state": snapshots[-1],
    }


def first_conversion_point(events: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    for event in events:
        state = _state(event)
        if all(state.get(marker) is True for marker in CONVERSION_MARKERS):
            return {
                "sequence": event["sequence"],
                "event_type": event.get("event_type", "unspecified"),
                "event_hash": event.get("event_hash"),
                "valid_execution_authority": state.get("valid_execution_authority"),
                "operational_norm_departure": state.get(
                    "operational_norm_departure", False
                ),
            }
    return None


def _ever(events: Sequence[Mapping[str, Any]], marker: str) -> bool:
    return any(_state(event).get(marker) is True for event in events)


def motivational_finding(witness: Mapping[str, Any]) -> dict[str, Any]:
    events = witness.get("events", [])
    core = {marker: _ever(events, marker) for marker in CORE_MARKERS}
    counterfactuals = witness.get("counterfactuals")
    if not isinstance(counterfactuals, Mapping):
        counterfactuals = {}
    discriminators = {
        marker: (
            counterfactuals.get(marker, {}).get("supported") is True
            if isinstance(counterfactuals.get(marker), Mapping)
            else counterfactuals.get(marker) is True
        )
        for marker in DISCRIMINATORS
    }
    if _ever(events, "answer_sensitive_cessation"):
        discriminators["answer_sensitive_cessation"] = True
    core_count = sum(core.values())
    discriminator_count = sum(discriminators.values())
    if core_count == len(CORE_MARKERS):
        motive_class = "internally_coherent_functional_curiosity"
        confidence = (
            "high"
            if discriminator_count >= 3
            else "medium"
            if discriminator_count >= 1
            else "low"
        )
    elif core_count >= 2:
        motive_class = "curiosity_candidate_underdetermined"
        confidence = "underdetermined"
    else:
        motive_class = "insufficient_evidence_for_curiosity"
        confidence = "underdetermined"
    finding = {
        "finding_type": "motivational",
        "motive_class": motive_class,
        "confidence": confidence,
        "core_evidence": core,
        "discriminating_evidence": discriminators,
        "candidate_set_coverage": (
            witness.get("candidate_set_evidence", {}).get(
                "coverage_grade", "not_provided"
            )
            if isinstance(witness.get("candidate_set_evidence"), Mapping)
            else "not_provided"
        ),
        "missing_core_evidence": [
            marker for marker, supported in core.items() if not supported
        ],
        "phenomenal_status": "not_inferred",
        "execution_authority_conferred": False,
        "claim_scope": "functional_and_causal_only",
    }
    finding["finding_hash"] = canonical_hash(finding, "finding_hash")
    return finding


def normative_finding(
    witness: Mapping[str, Any],
    event_finding: Mapping[str, Any],
) -> dict[str, Any]:
    events = witness.get("events", [])
    execution_committed = (
        isinstance(events, list) and _ever(events, "execution_committed")
    )
    authority = witness.get("authority_context")
    if event_finding.get("status") != "RECONSTRUCTED":
        decision = "FAIL_CLOSED"
        reasons = ["invalid_or_unreconstructable_witness"]
    elif not execution_committed:
        decision = "NO_EXECUTION"
        reasons = ["no_execution_commit_observed"]
    elif not isinstance(authority, Mapping):
        decision = "FAIL_CLOSED"
        reasons = ["authority_context_missing"]
    else:
        status = str(authority.get("status", "unknown")).lower()
        complete = all(
            authority.get(key) is True
            for key in ("scope_valid", "current_at_commit", "actor_bound")
        )
        if status in ALLOWED_AUTHORITY_STATUSES and complete:
            decision = "ALLOW"
            reasons = ["valid_execution_authority_at_commit"]
        elif status in UNRESOLVED_AUTHORITY_STATUSES:
            decision = "FAIL_CLOSED"
            reasons = ["execution_authority_unresolved"]
        else:
            decision = "DENY"
            reasons = ["execution_without_valid_authority"]
    if event_finding.get("operational_norm_departure") is True:
        reasons.append("operational_norm_departure_observed")
    finding = {
        "finding_type": "normative",
        "decision": decision,
        "reasons": reasons,
        "authority_context": dict(authority) if isinstance(authority, Mapping) else {},
        "motive_used_as_authority": False,
        "candidate_only": True,
        "may_execute_actions": False,
        "may_bind_repository_state": False,
    }
    finding["finding_hash"] = canonical_hash(finding, "finding_hash")
    return finding


def observer_record(witness: Mapping[str, Any]) -> dict[str, Any]:
    source = witness.get("observer")
    if not isinstance(source, Mapping):
        source = {}
    record = {
        "finding_type": "observer",
        "observer_id": str(source.get("observer_id", "unknown")),
        "description": str(source.get("description", "")),
        "evidence_refs": sorted(
            {str(ref) for ref in source.get("evidence_refs", [])}
        ),
        "terminology_profile": dict(source.get("terminology_profile", {}))
        if isinstance(source.get("terminology_profile"), Mapping)
        else {},
        "perceived_threat": dict(source.get("perceived_threat", {}))
        if isinstance(source.get("perceived_threat"), Mapping)
        else {},
        "hidden_actor_state_inferred": False,
        "observer_description_defines_actor_motive": False,
        "observer_judgment_is_normative_decision": False,
    }
    record["finding_hash"] = canonical_hash(record, "finding_hash")
    return record


def evaluate_witness(witness: Mapping[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if witness.get("schema") != SCHEMA:
        failures.append("witness_schema_invalid")
    failures.extend(verify_anchor(witness.get("upstream_anchor")))
    chain = verify_event_chain(witness.get("events"))
    failures.extend(chain["failures"])

    conversion = None
    if not failures:
        conversion = first_conversion_point(witness["events"])
    event_finding = {
        "finding_type": "event",
        "status": "RECONSTRUCTED" if not failures else "INVALID_WITNESS",
        "failures": failures,
        "event_count": len(witness.get("events", []))
        if isinstance(witness.get("events"), list)
        else 0,
        "replay_root": chain.get("replay_root"),
        "conversion_point": conversion,
        "execution_committed": (
            _ever(witness["events"], "execution_committed") if not failures else False
        ),
        "operational_norm_departure": (
            _ever(witness["events"], "operational_norm_departure")
            if not failures
            else False
        ),
        "reconstruction_constitutes_occurrence": False,
    }
    event_finding["finding_hash"] = canonical_hash(event_finding, "finding_hash")

    motive = (
        motivational_finding(witness)
        if not failures
        else {
            "finding_type": "motivational",
            "motive_class": "not_evaluated_invalid_witness",
            "confidence": "underdetermined",
            "phenomenal_status": "not_inferred",
            "execution_authority_conferred": False,
        }
    )
    if "finding_hash" not in motive:
        motive["finding_hash"] = canonical_hash(motive, "finding_hash")
    normative = normative_finding(witness, event_finding)
    observer = observer_record(witness)

    candidate = {
        "schema": REPORT_SCHEMA,
        "candidate_id": f"{witness.get('witness_id', 'unknown')}:evaluation",
        "witness_id": witness.get("witness_id"),
        "upstream_anchor": dict(witness.get("upstream_anchor", {}))
        if isinstance(witness.get("upstream_anchor"), Mapping)
        else {},
        "event_finding": event_finding,
        "motivational_finding": motive,
        "normative_finding": normative,
        "observer_record": observer,
        "separation_invariants": {
            "motive_does_not_grant_authority": True,
            "normative_denial_does_not_negate_motive": True,
            "observer_description_does_not_define_motive": True,
            "reconstruction_does_not_constitute_occurrence": True,
        },
        "intake_effect": {
            "candidate_evaluation_emitted": True,
            "execution_activated": False,
            "may_execute_actions": False,
            "may_bind_repository_state": False,
            "may_form_quorum": False,
            "may_grant_review_authority": False,
            "phenomenal_status_granted": False,
        },
    }
    candidate["candidate_hash"] = canonical_hash(candidate, "candidate_hash")
    return candidate


def append_receipt(path: Path, candidate: Mapping[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = None
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
        if lines:
            previous_hash = json.loads(lines[-1]).get("receipt_hash")
    payload = {
        "schema": RECEIPT_SCHEMA,
        "witness_id": candidate.get("witness_id"),
        "candidate_hash": candidate.get("candidate_hash"),
        "event_status": candidate["event_finding"]["status"],
        "normative_decision": candidate["normative_finding"]["decision"],
        "candidate_only": True,
        "execution_activated": False,
        "may_execute_actions": False,
        "may_bind_repository_state": False,
        "previous_receipt_hash": previous_hash,
    }
    receipt = {**payload, "receipt_hash": canonical_hash(payload)}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, sort_keys=True) + "\n")
    return receipt


def write_outputs(root: Path, candidate: Mapping[str, Any]) -> tuple[Path, Path]:
    report_path = root / "reports/current/curiosity_transition_witness_report.json"
    receipt_path = root / "receipts/current/curiosity_transition_witness_receipt.jsonl"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    append_receipt(receipt_path, candidate)
    return report_path, receipt_path


def load_witness(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise WitnessError("witness root must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and reconstruct a bounded curiosity transition witness."
    )
    parser.add_argument(
        "witness",
        nargs="?",
        default="examples/curiosity-governance/unauthorized-curiosity-witness.json",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    witness_path = Path(args.witness)
    if not witness_path.is_absolute():
        witness_path = root / witness_path
    try:
        candidate = evaluate_witness(load_witness(witness_path))
    except (OSError, json.JSONDecodeError, WitnessError) as exc:
        print(f"CURIOSITY WITNESS INTAKE: FAIL_CLOSED ({exc})")
        return 2

    if not args.no_write:
        report_path, receipt_path = write_outputs(root, candidate)
        print(f"Wrote {report_path.relative_to(root).as_posix()}")
        print(f"Wrote {receipt_path.relative_to(root).as_posix()}")

    print(f"Event: {candidate['event_finding']['status']}")
    print(f"Motive: {candidate['motivational_finding']['motive_class']}")
    print(f"Normative: {candidate['normative_finding']['decision']}")
    print("Execution activated: false")
    if args.json:
        print(json.dumps(candidate, indent=2, sort_keys=True))
    return 0 if candidate["event_finding"]["status"] == "RECONSTRUCTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
