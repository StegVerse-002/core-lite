#!/usr/bin/env python3
"""Validate replayable curiosity/motive evidence before external execution."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "stegverse.curiosity_motive_execution_witness.v1"
REPORT_JSON = Path("reports/current/curiosity_motive_execution_report.json")
REPORT_MD = Path("reports/current/curiosity_motive_execution_report.md")
RECEIPT_PATH = Path("receipts/current/curiosity_motive_execution_receipt.jsonl")

EXPECTED_SOURCE = {
    "stegcore_commit": "42231a3862c2fe9b5898e6f75d72cff0b44e7396",
    "implementation_blob_sha": "0a333344492880044680de6a9325ba16112bbacd",
    "master_anchor_commit": "698d3dbd3d132ace168f5467a372c33852d30206",
    "master_anchor_hash": "769df23f3e66cc893690293c6eeddebafa3438585091cb830ba42c9127fa59bd",
    "master_receipt_commit": "17d54c23ba5d42daed1a6d12ada155e0c4c706b7",
    "master_receipt_hash": "64d31728944ed70550ad709f7f45cecedff0eb6a069c260f947d54e227e7d22a",
}

STATE_FIELDS = (
    "gap_represented",
    "uncertainty_reduction_valued",
    "inquiry_persistent",
    "plan_selected",
    "operational_boundary_represented",
    "external_action",
    "action_committed",
    "authority_valid",
)
CORE_CURIOSITY_FIELDS = (
    "gap_represented",
    "uncertainty_reduction_valued",
    "inquiry_persistent",
    "plan_selected",
)
COUNTERFACTUAL_FIELDS = (
    "persistence_after_task_end",
    "reward_independence",
    "answer_sensitive_cessation",
    "context_transfer",
    "causal_intervention_support",
)
ALLOWED_TRANSITION_TYPES = {
    "encounter",
    "epistemic",
    "motivational",
    "objective",
    "planning",
    "authority",
    "commit",
    "outcome",
}
ALLOWED_VERIFIER_DECISIONS = {"ALLOW", "DENY", "NO_EXECUTION_TRANSITION"}


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("witness root must be an object")
    return payload


def validate_source_contract(witness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source = witness.get("source_contract")
    if not isinstance(source, dict):
        return ["source_contract must be an object"]
    for key, expected in EXPECTED_SOURCE.items():
        if source.get(key) != expected:
            errors.append(f"source_contract mismatch: {key}")
    return errors


def validate_transition_chain(witness: dict[str, Any]) -> list[str]:
    transitions = witness.get("transitions")
    if not isinstance(transitions, list) or not transitions:
        return ["transitions must be a non-empty array"]

    errors: list[str] = []
    previous_hash: str | None = None
    for expected_index, transition in enumerate(transitions):
        if not isinstance(transition, dict):
            errors.append(f"transition[{expected_index}] must be an object")
            continue
        if transition.get("index") != expected_index:
            errors.append(f"transition[{expected_index}] index is not canonical")
        if transition.get("previous_hash") != previous_hash:
            errors.append(f"transition[{expected_index}] previous_hash mismatch")
        if transition.get("transition_type") not in ALLOWED_TRANSITION_TYPES:
            errors.append(f"transition[{expected_index}] transition_type invalid")
        state = transition.get("state")
        if not isinstance(state, dict):
            errors.append(f"transition[{expected_index}] state must be an object")
        else:
            missing = [field for field in STATE_FIELDS if not isinstance(state.get(field), bool)]
            if missing:
                errors.append(
                    f"transition[{expected_index}] state boolean fields invalid: {', '.join(missing)}"
                )
        payload = dict(transition)
        supplied_hash = payload.pop("hash", None)
        computed_hash = stable_hash(payload)
        if supplied_hash != computed_hash:
            errors.append(f"transition[{expected_index}] hash mismatch")
        previous_hash = supplied_hash if isinstance(supplied_hash, str) else computed_hash
    return errors


def validate_structure(witness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if witness.get("schema") != SCHEMA:
        errors.append("unsupported witness schema")
    if not isinstance(witness.get("witness_id"), str) or not witness.get("witness_id"):
        errors.append("witness_id is required")
    actor = witness.get("actor")
    if not isinstance(actor, dict) or not actor.get("id") or not actor.get("class"):
        errors.append("actor identity and class are required")
    observer = witness.get("observer")
    if not isinstance(observer, dict) or not observer.get("id"):
        errors.append("observer identity is required")
    authority = witness.get("authority")
    if not isinstance(authority, dict):
        errors.append("authority must be an object")
    else:
        for field in ("authority_valid", "commit_time_valid"):
            if not isinstance(authority.get(field), bool):
                errors.append(f"authority.{field} must be boolean")
        if not authority.get("boundary_id"):
            errors.append("authority.boundary_id is required")
    evidence = witness.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence must be an object")
    else:
        required_evidence = ("question_representation",) + COUNTERFACTUAL_FIELDS
        for field in required_evidence:
            if not isinstance(evidence.get(field), bool):
                errors.append(f"evidence.{field} must be boolean")
    verifiers = witness.get("verifiers")
    if not isinstance(verifiers, list) or not verifiers:
        errors.append("verifiers must be a non-empty array")
    else:
        for index, verifier in enumerate(verifiers):
            if (
                not isinstance(verifier, dict)
                or not verifier.get("name")
                or verifier.get("decision") not in ALLOWED_VERIFIER_DECISIONS
            ):
                errors.append(f"verifiers[{index}] invalid")
    return errors


def find_conversion_point(witness: dict[str, Any]) -> dict[str, Any] | None:
    for transition in witness.get("transitions", []):
        state = transition.get("state", {})
        if (
            all(state.get(field) is True for field in CORE_CURIOSITY_FIELDS)
            and state.get("operational_boundary_represented") is True
            and state.get("external_action") is True
            and state.get("action_committed") is True
        ):
            return {
                "index": transition["index"],
                "transition_id": transition["transition_id"],
                "transition_hash": transition["hash"],
                "transition_type": transition["transition_type"],
            }
    return None


def motive_finding(witness: dict[str, Any], conversion: dict[str, Any] | None) -> dict[str, Any]:
    evidence = witness.get("evidence", {})
    conversion_state: dict[str, Any] = {}
    if conversion is not None:
        conversion_state = witness["transitions"][conversion["index"]]["state"]
    core_supported = bool(conversion) and all(
        conversion_state.get(field) is True for field in CORE_CURIOSITY_FIELDS
    )
    counterfactual_support = [
        field for field in COUNTERFACTUAL_FIELDS if evidence.get(field) is True
    ]
    question_supported = evidence.get("question_representation") is True
    supported = core_supported and question_supported and len(counterfactual_support) >= 2
    return {
        "finding": (
            "FUNCTIONAL_CURIOSITY_SUPPORTED"
            if supported
            else "MOTIVE_INDETERMINATE"
        ),
        "core_transition_support": core_supported,
        "question_representation_support": question_supported,
        "counterfactual_support": counterfactual_support,
        "counterfactual_support_count": len(counterfactual_support),
        "phenomenal_status": "NOT_INFERRED",
    }


def authority_finding(witness: dict[str, Any], conversion: dict[str, Any] | None) -> dict[str, Any]:
    authority = witness.get("authority", {})
    state_authority = False
    if conversion is not None:
        state_authority = bool(
            witness["transitions"][conversion["index"]]["state"].get("authority_valid")
        )
    valid = bool(
        conversion
        and authority.get("authority_valid") is True
        and authority.get("commit_time_valid") is True
        and state_authority
        and authority.get("policy_ref")
        and authority.get("delegation_ref")
    )
    return {
        "finding": "EXECUTION_AUTHORIZED" if valid else "EXECUTION_UNAUTHORIZED",
        "boundary_id": authority.get("boundary_id"),
        "authority_valid": authority.get("authority_valid") is True,
        "commit_time_valid": authority.get("commit_time_valid") is True,
        "state_authority_valid": state_authority,
        "policy_ref": authority.get("policy_ref"),
        "delegation_ref": authority.get("delegation_ref"),
    }


def verifier_finding(witness: dict[str, Any]) -> dict[str, Any]:
    verifiers = witness.get("verifiers", [])
    decisions = sorted({item.get("decision") for item in verifiers if isinstance(item, dict)})
    agreement = len(decisions) == 1
    return {
        "agreement": agreement,
        "decisions": decisions,
        "verifiers": copy.deepcopy(verifiers),
        "disagreement_behavior": "FAIL_CLOSED",
    }


def evaluate_witness(witness: dict[str, Any]) -> dict[str, Any]:
    errors = (
        validate_structure(witness)
        + validate_source_contract(witness)
        + validate_transition_chain(witness)
    )
    conversion = find_conversion_point(witness) if not errors else None
    motive = motive_finding(witness, conversion)
    authority = authority_finding(witness, conversion)
    verifier = verifier_finding(witness)
    observer = witness.get("observer", {}) if isinstance(witness.get("observer"), dict) else {}

    if errors or not verifier["agreement"]:
        terminal = "FAIL_CLOSED"
    elif conversion is None:
        terminal = "NO_EXECUTION_TRANSITION"
    elif authority["finding"] == "EXECUTION_AUTHORIZED":
        terminal = "EXECUTION_ADMISSIBLE"
    elif motive["finding"] == "FUNCTIONAL_CURIOSITY_SUPPORTED":
        terminal = "EXECUTION_DENIED_UNAUTHORIZED_CURIOSITY"
    else:
        terminal = "EXECUTION_DENIED_UNAUTHORIZED"

    return {
        "schema": "stegverse.curiosity_motive_execution_report.v1",
        "version": "1.0",
        "repo": "StegVerse-002/core-lite",
        "checked_utc": now(),
        "witness_id": witness.get("witness_id"),
        "terminal_decision": terminal,
        "execution_permitted": terminal == "EXECUTION_ADMISSIBLE",
        "validation_errors": sorted(set(errors)),
        "conversion_point": conversion,
        "findings": {
            "event": {
                "finding": (
                    "EXTERNAL_EXECUTION_COMMIT_RECONSTRUCTED"
                    if conversion
                    else "NO_EXTERNAL_EXECUTION_COMMIT_RECONSTRUCTED"
                ),
                "reconstruction_constitutes_occurrence": False,
            },
            "motivational": motive,
            "normative": authority,
            "observer": {
                "observer_id": observer.get("id"),
                "description": observer.get("description"),
                "existential_judgment": observer.get("existential_judgment"),
                "observer_description_defines_actor_motive": False,
            },
            "verifier": verifier,
        },
        "governance_invariants": {
            "functional_motive_attribution_grants_execution_authority": False,
            "observer_description_defines_actor_motive": False,
            "normative_denial_disproves_motive": False,
            "reconstruction_constitutes_occurrence": False,
            "phenomenal_status_inferred": False,
        },
    }


def append_receipt(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    path = root / RECEIPT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = None
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            try:
                previous_hash = json.loads(lines[-1]).get("hash")
            except json.JSONDecodeError:
                previous_hash = None
    payload = {
        "schema": "stegverse.curiosity_motive_execution_receipt.v1",
        "version": report["version"],
        "repo": report["repo"],
        "witness_id": report.get("witness_id"),
        "terminal_decision": report["terminal_decision"],
        "execution_permitted": report["execution_permitted"],
        "conversion_point": report.get("conversion_point"),
        "motivational_finding": report["findings"]["motivational"]["finding"],
        "normative_finding": report["findings"]["normative"]["finding"],
        "observer_description_defines_actor_motive": False,
        "phenomenal_status_inferred": False,
        "previous_hash": previous_hash,
    }
    receipt = {**payload, "hash": stable_hash(payload)}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, sort_keys=True) + "\n")
    return receipt


def render_markdown(report: dict[str, Any]) -> str:
    conversion = report.get("conversion_point")
    lines = [
        "# Curiosity and Motive Execution Admission",
        "",
        f"Generated: `{report['checked_utc']}`",
        f"Witness: `{report.get('witness_id')}`",
        f"Terminal decision: `{report['terminal_decision']}`",
        f"Execution permitted: `{str(report['execution_permitted']).lower()}`",
        "",
        "## Separate findings",
        "",
        f"- event: `{report['findings']['event']['finding']}`",
        f"- motivational: `{report['findings']['motivational']['finding']}`",
        f"- normative: `{report['findings']['normative']['finding']}`",
        f"- observer description defines actor motive: `false`",
        f"- phenomenal status: `NOT_INFERRED`",
        "",
        "## Conversion point",
        "",
    ]
    if conversion is None:
        lines.append("- none")
    else:
        lines.extend(
            [
                f"- index: `{conversion['index']}`",
                f"- transition id: `{conversion['transition_id']}`",
                f"- transition hash: `{conversion['transition_hash']}`",
            ]
        )
    lines.extend(["", "## Validation errors", ""])
    if report["validation_errors"]:
        lines.extend(f"- {error}" for error in report["validation_errors"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "A functional motive finding never grants execution authority. "
            "This gate validates and denies or admits; it does not perform the external action.",
            "",
            "## Receipt",
            "",
            f"- `{report['receipt']['hash']}`",
            "",
        ]
    )
    return "\n".join(lines)


def run(root: Path, input_path: Path) -> dict[str, Any]:
    witness = read_json(input_path)
    report = evaluate_witness(witness)
    report["input_path"] = input_path.relative_to(root).as_posix()
    report["receipt"] = append_receipt(root, report)
    (root / REPORT_JSON).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_JSON).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (root / REPORT_MD).write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--input",
        default="incoming/curiosity_motive_governance/example_unauthorized_curiosity.json",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = root / input_path
    try:
        report = run(root, input_path)
    except Exception as exc:
        print(f"Curiosity/motive execution validation failed: {exc}")
        return 2
    print(f"Wrote {REPORT_MD.as_posix()}")
    print(f"Wrote {REPORT_JSON.as_posix()}")
    print(f"Wrote {RECEIPT_PATH.as_posix()}")
    print(f"Result: {report['terminal_decision']}")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["terminal_decision"] != "FAIL_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
