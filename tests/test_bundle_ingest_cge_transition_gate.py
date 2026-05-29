#!/usr/bin/env python3
"""
tests/test_bundle_ingest_cge_transition_gate.py — StegVerse-002
Integration tests for the ingest_with_transition_gate function.

Tests:
  1. Bundle with valid candidate manifest → ALLOW_CANDIDATE_ONLY
  2. Bundle with missing manifest → FAIL_CLOSED
  3. Bundle with install manifest → ALLOW
  4. Transition table receipt written
  5. CGE receipt written
  6. Report written
  7. No code installed for candidate
  8. dry_run respected
"""
import json
import os
import sys
import tempfile
import zipfile
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core_lite.transition_table.ingest_gate import ingest_with_transition_gate


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _make_bundle(tmpdir, manifest: dict, name="test_bundle.zip") -> str:
    path = os.path.join(tmpdir, name)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("bundle_manifest.json", json.dumps(manifest, indent=2))
    return path


def _valid_candidate_manifest():
    return {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "test_candidate_gate_001",
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
            "task_hash": "sha256:def456",
            "candidate_provider": "openai",
            "candidate_round": 1,
        }
    }


def _valid_install_manifest():
    return {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "test_install_gate_001",
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
            "task_hash": "sha256:def456",
            "allowed_paths": ["core_lite/transition_table/"],
            "forbidden_paths": ["secrets/"],
            "rollback_policy": "git_revert",
        }
    }


def run_tests():
    results = []

    def record(name, passed, detail=""):
        results.append({"test": name, "passed": passed, "detail": detail})

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = tmpdir

        # Test 1: Valid candidate bundle
        bundle = _make_bundle(tmpdir, _valid_candidate_manifest(), "candidate.zip")
        result = ingest_with_transition_gate(
            bundle_path=bundle,
            entity="StegVerse-002",
            stage="SV002-M11",
            repo_root=repo_root,
            dry_run=False,
        )
        record("candidate_decision_allow_candidate_only",
               result["decision"] == "ALLOW_CANDIDATE_ONLY",
               f"decision={result['decision']}")
        record("candidate_disposition_accepted",
               result["candidate_disposition"] == "CANDIDATE_ACCEPTED_FOR_COMPARISON",
               f"disposition={result['candidate_disposition']}")
        record("candidate_no_code_install",
               not result["installs_code"],
               f"installs_code={result['installs_code']}")
        record("candidate_receipt_hash_present",
               bool(result.get("receipt_hash")),
               f"receipt_hash={result.get('receipt_hash', '')[:20]}...")

        # Test 2: Bundle with no manifest
        empty_path = os.path.join(tmpdir, "empty.zip")
        with zipfile.ZipFile(empty_path, "w") as z:
            z.writestr("README.md", "nothing here")
        result2 = ingest_with_transition_gate(
            bundle_path=empty_path,
            entity="StegVerse-002",
            stage="SV002-M11",
            repo_root=repo_root,
        )
        record("no_manifest_fail_closed",
               result2["decision"] == "FAIL_CLOSED",
               f"decision={result2['decision']}")

        # Test 3: Valid install bundle
        bundle3 = _make_bundle(tmpdir, _valid_install_manifest(), "install.zip")
        result3 = ingest_with_transition_gate(
            bundle_path=bundle3,
            entity="StegVerse-002",
            stage="SV002-M11",
            repo_root=repo_root,
        )
        record("install_decision_allow",
               result3["decision"] == "ALLOW",
               f"decision={result3['decision']}")
        record("install_installs_code",
               result3["installs_code"],
               f"installs_code={result3['installs_code']}")

        # Test 4: Transition table receipt written
        tt_receipt = os.path.join(repo_root, "receipts", "current", "transition_table_receipt.jsonl")
        record("transition_table_receipt_written",
               os.path.exists(tt_receipt),
               f"path={tt_receipt}")

        # Test 5: CGE receipt written
        cge_receipt = os.path.join(repo_root, "receipts", "current", "cge_admissibility_receipt.jsonl")
        record("cge_receipt_written",
               os.path.exists(cge_receipt),
               f"path={cge_receipt}")

        # Test 6: Report written
        report_path = os.path.join(repo_root, "reports", "current", "transition_table_report.json")
        record("report_written",
               os.path.exists(report_path),
               f"path={report_path}")

        # Test 7: dry_run flag preserved
        bundle4 = _make_bundle(tmpdir, _valid_candidate_manifest(), "dry.zip")
        result4 = ingest_with_transition_gate(
            bundle_path=bundle4,
            entity="StegVerse-002",
            stage="SV002-M11",
            repo_root=repo_root,
            dry_run=True,
        )
        record("dry_run_preserved",
               result4.get("dry_run") is True,
               f"dry_run={result4.get('dry_run')}")

        # Test 8: Coordinates present
        record("coordinates_present",
               len(result.get("coordinates", {})) >= 5,
               f"keys={list(result.get('coordinates', {}).keys())}")

    # Summary
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    verdict = "PASS" if failed == 0 else "FAIL"

    report = {
        "schema": "stegverse.test_report.v1",
        "timestamp_utc": _now_utc(),
        "test_suite": "test_bundle_ingest_cge_transition_gate",
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

    os.makedirs("reports/current", exist_ok=True)
    with open("reports/current/bundle_ingest_cge_transition_gate_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return verdict == "PASS"


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
