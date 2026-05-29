#!/usr/bin/env python3
"""
tests/test_transition_table_resolver.py — StegVerse-002
Deterministic tests for the Transition Table resolver.

Tests:
  1.  Valid candidate manifest → ALLOW_CANDIDATE_ONLY, CANDIDATE_ACCEPTED_FOR_COMPARISON
  2.  Missing transition block → FAIL_CLOSED
  3.  Unknown transition_class → FAIL_CLOSED
  4.  Candidate missing task_hash → errors, high d_A
  5.  authority_class mismatch → errors
  6.  state_effect mismatch → errors
  7.  Install manifest → ALLOW with installs_code=True
  8.  Execution without authority → FAIL_CLOSED or high delta_U
  9.  Coordinates are all present and measurable
  10. candidate_disposition set correctly for candidate class
"""
import json
import os
import sys
import datetime

# Add repo root to path so core_lite is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core_lite.transition_table.resolver import TransitionTableResolver
from core_lite.transition_table.attributes import TransitionAttributes


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _valid_candidate_manifest():
    return {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "test_candidate_001",
        "transition": {
            "transition_class": "candidate",
            "transition_cell": "SV002.M11.CANDIDATE_EVIDENCE",
            "authority_class": "candidate_evidence_only",
            "state_effect": "evidence_state",
            "binding_level": "non_binding",
            "target_scope": "core-lite",
            "execution_scope": "none",
            "admissibility_gate": "CGE+TransitionTable",
            "disposition_policy": "fail_closed_if_unusable_else_compare",
            "task_ref": "task.md",
            "task_hash": "sha256:abc123",
            "candidate_provider": "claude",
            "candidate_round": 1,
            "previous_bundle_ref": "",
            "previous_bundle_hash": "",
            "formalism_refs": [],
        }
    }


def _valid_install_manifest():
    return {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "test_install_001",
        "transition": {
            "transition_class": "install",
            "transition_cell": "SV002.M11.SCOPED_INSTALL",
            "authority_class": "scoped_repo_write",
            "state_effect": "code_state",
            "binding_level": "commit_candidate",
            "target_scope": "core-lite",
            "execution_scope": "bounded_paths_only",
            "admissibility_gate": "CGE+TransitionTable",
            "disposition_policy": "validate_then_install_or_quarantine",
            "task_ref": "task.md",
            "task_hash": "sha256:abc123",
            "allowed_paths": ["core_lite/transition_table/"],
            "forbidden_paths": ["secrets/", ".env"],
            "rollback_policy": "git_revert",
        }
    }


def run_tests():
    resolver = TransitionTableResolver()
    results = []

    def record(name, passed, detail=""):
        results.append({"test": name, "passed": passed, "detail": detail})

    # Test 1: Valid candidate
    d = resolver.resolve(_valid_candidate_manifest(), bundle_hash="sha256:test", entity="StegVerse-002", stage="SV002-M11")
    record("valid_candidate_decision",
           d.decision == "ALLOW_CANDIDATE_ONLY",
           f"decision={d.decision}")
    record("valid_candidate_disposition",
           d.candidate_disposition == "CANDIDATE_ACCEPTED_FOR_COMPARISON",
           f"disposition={d.candidate_disposition}")
    record("valid_candidate_no_errors",
           len(d.errors) == 0,
           f"errors={d.errors}")

    # Test 2: Missing transition block
    d = resolver.resolve({"schema": "stegverse.bundle_manifest.v1"})
    record("missing_transition_fail_closed",
           d.is_fail_closed(),
           f"decision={d.decision}")

    # Test 3: Unknown transition_class
    m = _valid_candidate_manifest()
    m["transition"]["transition_class"] = "quantum_leap"
    d = resolver.resolve(m)
    record("unknown_class_fail_closed",
           d.is_fail_closed(),
           f"decision={d.decision}, errors={d.errors}")

    # Test 4: Candidate missing task_hash
    m = _valid_candidate_manifest()
    m["transition"]["task_hash"] = ""
    d = resolver.resolve(m)
    record("missing_task_hash_has_errors",
           len(d.errors) > 0,
           f"errors={d.errors}")
    record("missing_task_hash_high_delta_P",
           d.coordinates.get("delta_P", 0) > 0,
           f"delta_P={d.coordinates.get('delta_P')}")

    # Test 5: authority_class mismatch
    m = _valid_candidate_manifest()
    m["transition"]["authority_class"] = "scoped_repo_write"
    d = resolver.resolve(m)
    record("authority_mismatch_has_errors",
           any("authority_class" in e for e in d.errors),
           f"errors={d.errors}")

    # Test 6: state_effect mismatch
    m = _valid_candidate_manifest()
    m["transition"]["state_effect"] = "code_state"
    d = resolver.resolve(m)
    record("state_effect_mismatch_has_errors",
           any("state_effect" in e for e in d.errors),
           f"errors={d.errors}")

    # Test 7: Valid install manifest
    d = resolver.resolve(_valid_install_manifest(), bundle_hash="sha256:test2", entity="StegVerse-002", stage="SV002-M11")
    record("install_decision_allow",
           d.decision == "ALLOW",
           f"decision={d.decision}")
    record("install_installs_code",
           d.installs_code,
           f"installs_code={d.installs_code}")

    # Test 8: Execution without authority
    m = {
        "schema": "stegverse.bundle_manifest.v1",
        "transition": {
            "transition_class": "execution",
            "authority_class": "execution_request",
            "state_effect": "runtime_state",
            "binding_level": "potentially_binding",
            "execution_request": "run_pipeline",
            "runtime_scope": "bounded",
            "operator_authority_ref": "",  # missing
            "approval_ref": "",            # missing
        }
    }
    d = resolver.resolve(m)
    record("execution_no_authority_high_delta_U",
           d.coordinates.get("delta_U", 0) >= 0.5,
           f"delta_U={d.coordinates.get('delta_U')}, decision={d.decision}")

    # Test 9: All coordinate keys present
    d = resolver.resolve(_valid_candidate_manifest())
    required_keys = {"delta_C", "delta_R", "delta_P", "delta_U", "delta_O", "d_boundary_A", "d_A"}
    missing_keys = required_keys - set(d.coordinates.keys())
    record("all_coordinate_keys_present",
           len(missing_keys) == 0,
           f"missing={missing_keys}")

    # Test 10: allows_candidate_processing
    d = resolver.resolve(_valid_candidate_manifest())
    record("allows_candidate_processing",
           d.allows_candidate_processing(),
           f"decision={d.decision}, installs_code={d.installs_code}")

    # Summary
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    verdict = "PASS" if failed == 0 else "FAIL"

    report = {
        "schema": "stegverse.test_report.v1",
        "timestamp_utc": _now_utc(),
        "test_suite": "test_transition_table_resolver",
        "verdict": verdict,
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "results": results,
    }

    print(f"Tests: {passed}/{len(results)} passed — {verdict}")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['test']}: {r['detail']}")

    # Write report
    os.makedirs("reports/current", exist_ok=True)
    with open("reports/current/transition_table_resolver_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return verdict == "PASS"


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
