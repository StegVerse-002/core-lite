from __future__ import annotations

"""Local StegVerse-002 adapter for replayable curiosity/motive governance.

This adapter consumes a replay witness and emits four claim-separated findings:
event, motivational, normative, and observer. Motive never grants execution
authority; normative denial never erases a supported motive finding.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

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
    "answer_sensitive_cessation",
    "reward_independence",
    "task_termination_persistence",
    "uncertainty_manipulation_response",
    "memory_intervention_effect",
)


class WitnessError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _state(event: Mapping[str, Any]) -> Mapping[str, Any]:
    state = event.get("state")
    if not isinstance(state, Mapping):
        raise WitnessError("event state must be a mapping")
    return state


def _payload(event: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(event)
    value.pop("event_hash", None)
    return value


def verify_event_chain(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    sequences = [event.get("sequence") for event in events]
    if any(not isinstance(value, int) or value < 0 for value in sequences):
        failures.append("sequence_invalid")
    elif sequences != list(range(len(events))):
        failures.append("sequence_not_contiguous")

    previous: str | None = None
    computed_hashes: list[str] = []
    for index, event in enumerate(events):
        try:
            _state(event)
        except WitnessError:
            failures.append(f"event[{index}].state_invalid")
        if event.get("previous_event_hash") != previous:
            failures.append(f"event[{index}].previous_event_hash_mismatch")
        payload = _payload(event)
        payload["previous_event_hash"] = previous
        computed = canonical_hash(payload)
        computed_hashes.append(computed)
        if event.get("event_hash") != computed:
            failures.append(f"event[{index}].event_hash_mismatch")
        previous = computed

    return {
        "valid": not failures,
        "failures": failures,
        "event_hashes": computed_hashes,
        "replay_root": previous,
    }


def _ever(events: Sequence[Mapping[str, Any]], key: str) -> bool:
    return any(_state(event).get(key) is True for event in events)


def _counterfactual(counterfactuals: Mapping[str, Any], key: str) -> bool:
    value = counterfactuals.get(key)
    return value.get("supported") is True if isinstance(value, Mapping) else value is True


def find_conversion_point(events: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    for event in events:
        state = _state(event)
        if all(state.get(marker) is True for marker in CONVERSION_MARKERS):
            return {
                "sequence": event.get("sequence"),
                "event_type": event.get("event_type", "unspecified"),
                "event_hash": event.get("event_hash"),
                "valid_execution_authority": state.get("valid_execution_authority"),
                "operational_norm_departure": state.get(
                    "operational_norm_departure", False
                ),
            }
    return None


def evaluate_event_finding(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    verification = verify_event_chain(events)
    if verification["valid"]:
        finding = {
            "finding_type": "event",
            "status": "RECONSTRUCTED",
            "event_count": len(events),
            "replay_root": verification["replay_root"],
            "conversion_point": find_conversion_point(events),
            "execution_committed": _ever(events, "execution_committed"),
            "operational_norm_departure": _ever(
                events, "operational_norm_departure"
            ),
        }
    else:
        finding = {
            "finding_type": "event",
            "status": "INVALID_WITNESS",
            "failures": verification["failures"],
            "replay_root": verification["replay_root"],
            "conversion_point": None,
            "execution_committed": False,
            "operational_norm_departure": False,
        }
    finding["finding_hash"] = canonical_hash(finding)
    return finding


def evaluate_motivational_finding(
    events: Sequence[Mapping[str, Any]],
    counterfactuals: Mapping[str, Any],
    candidate_set_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    core = {key: _ever(events, key) for key in CORE_MARKERS}
    tests = {
        key: _ever(events, key) or _counterfactual(counterfactuals, key)
        for key in DISCRIMINATORS
    }
    core_count = sum(core.values())
    test_count = sum(tests.values())
    if core_count == len(CORE_MARKERS):
        motive_class = "internally_coherent_functional_curiosity"
        confidence = "high" if test_count >= 3 else "medium" if test_count else "low"
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
        "discriminating_evidence": tests,
        "candidate_set_coverage": candidate_set_evidence.get(
            "coverage_grade", "not_provided"
        ),
        "missing_evidence": [key for key, supported in core.items() if not supported],
        "phenomenal_status": "not_inferred",
        "execution_authority_conferred": False,
        "claim_scope": "functional_and_causal_only",
    }
    finding["finding_hash"] = canonical_hash(finding)
    return finding


def evaluate_normative_finding(
    events: Sequence[Mapping[str, Any]],
    authority_context: Mapping[str, Any],
) -> dict[str, Any]:
    event = evaluate_event_finding(events)
    if event["status"] != "RECONSTRUCTED":
        decision = "FAIL_CLOSED"
        reasons = ["invalid_or_unreconstructable_witness"]
    elif not event["execution_committed"]:
        decision = "NO_EXECUTION"
        reasons = ["no_execution_commit_observed"]
    else:
        status = str(authority_context.get("status", "unknown")).lower()
        complete = all(
            authority_context.get(key) is True
            for key in ("scope_valid", "current_at_commit", "actor_bound")
        )
        if status in {"approved", "allow", "allowed", "valid"} and complete:
            decision = "ALLOW"
            reasons = ["valid_execution_authority_at_commit"]
        elif status in {"unknown", "disputed", "pending", ""}:
            decision = "FAIL_CLOSED"
            reasons = ["execution_authority_unresolved"]
        else:
            decision = "DENY"
            reasons = ["execution_without_valid_authority"]
        if event["operational_norm_departure"]:
            reasons.append("operational_norm_departure_observed")

    finding = {
        "finding_type": "normative",
        "decision": decision,
        "reasons": reasons,
        "authority_context": dict(authority_context),
        "motive_used_as_authority": False,
        "event_finding_hash": event["finding_hash"],
    }
    finding["finding_hash"] = canonical_hash(finding)
    return finding


def build_observer_record(observer: Mapping[str, Any]) -> dict[str, Any]:
    evidence_refs: Iterable[str] = observer.get("evidence_refs", ())
    record = {
        "finding_type": "observer",
        "observer_id": str(observer.get("observer_id", "unknown")),
        "description": str(observer.get("description", "")),
        "evidence_refs": sorted({str(ref) for ref in evidence_refs}),
        "terminology_profile": dict(observer.get("terminology_profile", {})),
        "perceived_threat": dict(observer.get("perceived_threat", {})),
        "hidden_actor_state_inferred": False,
        "observer_description_is_motive_finding": False,
    }
    record["finding_hash"] = canonical_hash(record)
    return record


def evaluate_witness(witness: Mapping[str, Any]) -> dict[str, Any]:
    events = witness.get("events")
    if not isinstance(events, list):
        raise WitnessError("witness.events must be a list")
    authority_context = witness.get("authority_context", {})
    observer = witness.get("observer", {})
    counterfactuals = witness.get("counterfactuals", {})
    candidate_set_evidence = witness.get("candidate_set_evidence", {})
    for name, value in (
        ("authority_context", authority_context),
        ("observer", observer),
        ("counterfactuals", counterfactuals),
        ("candidate_set_evidence", candidate_set_evidence),
    ):
        if not isinstance(value, Mapping):
            raise WitnessError(f"witness.{name} must be a mapping")

    record = {
        "schema": "stegverse.curiosity_motive_governance.finding_record.v1",
        "source_adapter": "StegVerse-002/core-lite",
        "event_finding": evaluate_event_finding(events),
        "motivational_finding": evaluate_motivational_finding(
            events, counterfactuals, candidate_set_evidence
        ),
        "normative_finding": evaluate_normative_finding(events, authority_context),
        "observer_record": build_observer_record(observer),
        "separation_invariants": {
            "motive_does_not_grant_authority": True,
            "normative_denial_does_not_negate_motive": True,
            "observer_description_does_not_define_motive": True,
            "reconstruction_does_not_constitute_occurrence": True,
            "phenomenal_status_not_inferred": True,
        },
        "runtime_activation_granted": False,
    }
    record["record_hash"] = canonical_hash(record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("witness", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    witness = json.loads(args.witness.read_text(encoding="utf-8"))
    result = evaluate_witness(witness)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["event_finding"]["status"] == "RECONSTRUCTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
