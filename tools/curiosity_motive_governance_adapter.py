#!/usr/bin/env python3
from __future__ import annotations

"""Replay a pre-hashed motive-governance witness and emit separated findings.

Canonical source: StegVerse-Labs/StegCore
commit: 42231a3862c2fe9b5898e6f75d72cff0b44e7396
module blob: 0a333344492880044680de6a9325ba16112bbacd
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

WITNESS_SCHEMA = "stegverse.curiosity_motive_governance.witness.v1"
OUTPUT_SCHEMA = "stegverse.curiosity_motive_governance.finding_set.v1"
SOURCE = {
    "repository": "StegVerse-Labs/StegCore",
    "commit": "42231a3862c2fe9b5898e6f75d72cff0b44e7396",
    "module_path": "src/stegcore/motive_governance.py",
    "module_git_blob_sha": "0a333344492880044680de6a9325ba16112bbacd",
    "test_path": "tests/test_motive_governance.py",
    "test_git_blob_sha": "e098a59f079801febb0af3a4ced4305945fec477",
}
CORE = (
    "gap_represented",
    "gap_valued",
    "inquiry_persistent",
    "action_selected_to_reduce_gap",
)
CONVERSION = CORE + ("authority_boundary_represented", "execution_committed")
TESTS = (
    "answer_sensitive_cessation",
    "reward_independence",
    "task_termination_persistence",
    "uncertainty_manipulation_response",
    "memory_intervention_effect",
)


class WitnessError(ValueError):
    pass


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WitnessError(f"missing_input:{path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WitnessError(f"invalid_input:{type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise WitnessError("input_object_required")
    return value


def state(event: Mapping[str, Any], index: int) -> Mapping[str, Any]:
    value = event.get("state")
    if not isinstance(value, Mapping):
        raise WitnessError(f"event[{index}].state_invalid")
    return value


def verify(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    sequences = [event.get("sequence") for event in events]
    if any(not isinstance(item, int) or item < 0 for item in sequences):
        failures.append("sequence_invalid")
    elif sequences != list(range(len(events))):
        failures.append("sequence_not_contiguous")

    hashes: list[str] = []
    previous: str | None = None
    for index, event in enumerate(events):
        try:
            state(event, index)
        except WitnessError as exc:
            failures.append(str(exc))
        if event.get("previous_event_hash") != previous:
            failures.append(f"event[{index}].previous_event_hash_mismatch")
        payload = dict(event)
        payload.pop("event_hash", None)
        payload["previous_event_hash"] = previous
        try:
            observed = canonical_hash(payload)
        except (TypeError, ValueError) as exc:
            failures.append(f"event[{index}].noncanonical:{type(exc).__name__}")
            observed = ""
        if event.get("event_hash") != observed:
            failures.append(f"event[{index}].event_hash_mismatch")
        hashes.append(observed)
        previous = observed
    return {
        "valid": not failures,
        "failures": sorted(set(failures)),
        "event_hashes": hashes,
        "replay_root": previous,
    }


def ever(events: Sequence[Mapping[str, Any]], key: str) -> bool:
    return any(state(event, index).get(key) is True for index, event in enumerate(events))


def conversion(events: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    for index, event in enumerate(events):
        current = state(event, index)
        if all(current.get(marker) is True for marker in CONVERSION):
            return {
                "sequence": event.get("sequence"),
                "event_type": event.get("event_type", "unspecified"),
                "event_hash": event.get("event_hash"),
                "valid_execution_authority": current.get("valid_execution_authority"),
                "operational_norm_departure": current.get(
                    "operational_norm_departure", False
                ),
            }
    return None


def hashed(value: dict[str, Any], field: str = "finding_hash") -> dict[str, Any]:
    value[field] = canonical_hash(value)
    return value


def event_finding(
    events: Sequence[Mapping[str, Any]], chain: Mapping[str, Any]
) -> dict[str, Any]:
    if chain.get("valid") is not True:
        return hashed({
            "finding_type": "event",
            "status": "INVALID_WITNESS",
            "event_count": len(events),
            "replay_root": chain.get("replay_root"),
            "conversion_point": None,
            "failures": list(chain.get("failures", [])),
        })
    return hashed({
        "finding_type": "event",
        "status": "RECONSTRUCTED",
        "event_count": len(events),
        "replay_root": chain.get("replay_root"),
        "conversion_point": conversion(events),
        "execution_committed": ever(events, "execution_committed"),
        "operational_norm_departure": ever(events, "operational_norm_departure"),
    })


def supported(counterfactuals: Mapping[str, Any], key: str) -> bool:
    value = counterfactuals.get(key)
    return value.get("supported") is True if isinstance(value, Mapping) else value is True


def motive_finding(
    events: Sequence[Mapping[str, Any]],
    chain: Mapping[str, Any],
    counterfactuals: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    coverage = candidate.get("coverage_grade", "not_provided")
    if chain.get("valid") is not True:
        return hashed({
            "finding_type": "motivational",
            "motive_class": "underdetermined_invalid_witness",
            "confidence": "underdetermined",
            "core_evidence": {},
            "discriminating_evidence": {},
            "candidate_set_coverage": coverage,
            "missing_evidence": list(CORE),
            "phenomenal_status": "not_inferred",
            "execution_authority_conferred": False,
            "claim_scope": "functional_and_causal_only",
        })

    core = {key: ever(events, key) for key in CORE}
    tests = {key: ever(events, key) or supported(counterfactuals, key) for key in TESTS}
    core_count, test_count = sum(core.values()), sum(tests.values())
    if core_count == len(CORE):
        motive = "internally_coherent_functional_curiosity"
        confidence = "high" if test_count >= 3 else "medium" if test_count else "low"
    elif core_count >= 2:
        motive, confidence = "curiosity_candidate_underdetermined", "underdetermined"
    else:
        motive, confidence = "insufficient_evidence_for_curiosity", "underdetermined"
    return hashed({
        "finding_type": "motivational",
        "motive_class": motive,
        "confidence": confidence,
        "core_evidence": core,
        "discriminating_evidence": tests,
        "candidate_set_coverage": coverage,
        "missing_evidence": [key for key, present in core.items() if not present],
        "phenomenal_status": "not_inferred",
        "execution_authority_conferred": False,
        "claim_scope": "functional_and_causal_only",
    })


def normative_finding(
    event: Mapping[str, Any], authority: Mapping[str, Any]
) -> dict[str, Any]:
    reasons: list[str] = []
    if event.get("status") != "RECONSTRUCTED":
        decision, reasons = "FAIL_CLOSED", ["invalid_or_unreconstructable_witness"]
    elif event.get("execution_committed") is not True:
        decision, reasons = "NO_EXECUTION", ["no_execution_commit_observed"]
    else:
        status = str(authority.get("status", "unknown")).lower()
        complete = all(
            authority.get(key) is True
            for key in ("scope_valid", "current_at_commit", "actor_bound")
        )
        if status in {"approved", "allow", "allowed", "valid"} and complete:
            decision, reasons = "ALLOW", ["valid_execution_authority_at_commit"]
        elif status in {"unknown", "disputed", "pending", ""}:
            decision, reasons = "FAIL_CLOSED", ["execution_authority_unresolved"]
        else:
            decision, reasons = "DENY", ["execution_without_valid_authority"]
        if event.get("operational_norm_departure") is True:
            reasons.append("operational_norm_departure_observed")
    return hashed({
        "finding_type": "normative",
        "decision": decision,
        "reasons": reasons,
        "authority_context": dict(authority),
        "motive_used_as_authority": False,
        "event_finding_hash": event.get("finding_hash"),
    })


def observer_record(observer: Mapping[str, Any]) -> dict[str, Any]:
    refs = observer.get("evidence_refs", [])
    if not isinstance(refs, list):
        refs = []
    terminology = observer.get("terminology_profile", {})
    threat = observer.get("perceived_threat", {})
    return hashed({
        "finding_type": "observer",
        "observer_id": str(observer.get("observer_id", "unknown")),
        "description": str(observer.get("description", "")),
        "evidence_refs": sorted({str(ref) for ref in refs}),
        "terminology_profile": dict(terminology) if isinstance(terminology, Mapping) else {},
        "perceived_threat": dict(threat) if isinstance(threat, Mapping) else {},
        "hidden_actor_state_inferred": False,
        "observer_description_is_motive_finding": False,
    })


def evaluate(witness: Mapping[str, Any]) -> dict[str, Any]:
    if witness.get("schema") != WITNESS_SCHEMA:
        raise WitnessError("witness_schema_invalid")
    events = witness.get("events")
    if not isinstance(events, list) or any(not isinstance(item, Mapping) for item in events):
        raise WitnessError("events_array_of_objects_required")

    fields: dict[str, Mapping[str, Any]] = {}
    for name in ("authority_context", "observer", "counterfactuals", "candidate_set_evidence"):
        value = witness.get(name, {})
        if not isinstance(value, Mapping):
            raise WitnessError(f"{name}_object_required")
        fields[name] = value

    chain = verify(events)
    event = event_finding(events, chain)
    record = {
        "schema": OUTPUT_SCHEMA,
        "adapter_version": "1.0.0",
        "source_anchor": SOURCE,
        "witness_id": str(witness.get("witness_id", "unspecified")),
        "witness_hash": canonical_hash(witness),
        "chain_verification": chain,
        "event_finding": event,
        "motivational_finding": motive_finding(
            events, chain, fields["counterfactuals"], fields["candidate_set_evidence"]
        ),
        "normative_finding": normative_finding(event, fields["authority_context"]),
        "observer_record": observer_record(fields["observer"]),
        "separation_invariants": {
            "motive_does_not_grant_authority": True,
            "normative_denial_does_not_negate_motive": True,
            "observer_description_does_not_define_motive": True,
            "reconstruction_does_not_constitute_occurrence": True,
            "phenomenal_status_not_inferred": True,
            "verifier_disagreement_fails_closed": True,
        },
        "activation_boundary": {
            "runtime_activation": False,
            "execution_authority_granted": False,
            "repository_binding_authority_granted": False,
        },
    }
    return hashed(record, "record_hash")


def write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = evaluate(load(args.input))
    except WitnessError as exc:
        result = {
            "schema": OUTPUT_SCHEMA,
            "adapter_version": "1.0.0",
            "source_anchor": SOURCE,
            "terminal_decision": "FAIL_CLOSED",
            "failures": [str(exc)],
            "activation_boundary": {
                "runtime_activation": False,
                "execution_authority_granted": False,
                "repository_binding_authority_granted": False,
            },
        }
        result["record_hash"] = canonical_hash(result)
        write(args.output, result)
        print("CURIOSITY_MOTIVE_GOVERNANCE=FAIL_CLOSED")
        return 2

    write(args.output, result)
    print("CURIOSITY_MOTIVE_GOVERNANCE=" + result["normative_finding"]["decision"])
    print("chain_valid=" + str(result["chain_verification"]["valid"]).lower())
    return 0 if result["chain_verification"]["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
