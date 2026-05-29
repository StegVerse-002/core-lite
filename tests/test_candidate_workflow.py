#!/usr/bin/env python3
"""
test_candidate_workflow.py — StegVerse-002 SV002-M11
Deterministic tests for the synthesized candidate patch.
Writes: reports/current/synthesized_candidate_test_report.json

Tests:
  1. YAML parses successfully
  2. workflow has push trigger for incoming/** only
  3. incoming/README.md is excluded from payload processing
  4. changed incoming files are selected from event diff
  5. legacy incoming files are inventoried but not deleted
  6. pipeline stdout is not written into JSONL disposition files
  7. JSONL records are written by a deterministic JSON emitter (python3 -c)
  8. failed payloads are copied to quarantine before incoming cleanup
  9. only dispositioned changed payloads are removed from incoming
 10. manual dispatch supports all required inputs
"""
import datetime
import json
import os
import re
import sys

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

CANDIDATE_PATH = "outputs/synthesized_candidate.json"
REPORT_PATH = "reports/current/synthesized_candidate_test_report.json"
REQUIRED_DISPATCH_INPUTS = {
    "input_type", "input_path", "stage_override",
    "dry_run", "agent_provider", "task_id",
}


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_workflow_content(candidate):
    """Extract the workflow file content from the synthesized candidate."""
    for f in candidate.get("files", []):
        if f.get("path") == ".github/workflows/core-lite-intake.yml":
            return f.get("content", "")
    return None


def run_tests(candidate):
    results = []

    def record(name, passed, detail=""):
        results.append({"test": name, "passed": passed, "detail": detail})

    # --- Test 1: YAML parses successfully ---
    content = get_workflow_content(candidate)
    if content is None:
        record("yaml_parses", False, "core-lite-intake.yml not found in candidate files")
        return results  # Can't run further tests without content

    if YAML_AVAILABLE:
        try:
            parsed = yaml.safe_load(content)
            record("yaml_parses", True)
        except yaml.YAMLError as e:
            record("yaml_parses", False, str(e))
            parsed = None
    else:
        # Fallback: just check for obvious structural markers
        parsed = None
        record("yaml_parses", "on:" in content or '"on":' in content,
               "yaml not available; checked for 'on:' key presence")

    # --- Test 2: push trigger for incoming/** ---
    has_push_incoming = bool(
        re.search(r'push\s*:', content) and
        re.search(r'incoming/\*\*', content)
    )
    record("push_trigger_incoming", has_push_incoming,
           "push trigger with incoming/** path filter" if has_push_incoming
           else "missing push trigger or incoming/** path")

    # --- Test 3: incoming/README.md excluded ---
    has_readme_exclusion = "incoming/README.md" in content
    record("readme_excluded", has_readme_exclusion,
           "incoming/README.md exclusion found" if has_readme_exclusion
           else "no incoming/README.md exclusion found")

    # --- Test 4: changed files selected from event diff ---
    has_diff = bool(
        re.search(r'git diff --name-only', content) or
        re.search(r'git diff-tree', content)
    )
    record("changed_files_from_diff", has_diff,
           "git diff used to select changed files" if has_diff
           else "no git diff found for changed file selection")

    # --- Test 5: legacy files inventoried not deleted ---
    has_inventory = bool(re.search(r'incoming_legacy_inventory', content))
    has_legacy_delete = bool(re.search(r'git rm.*legacy|rm.*legacy_inventory', content))
    record("legacy_inventoried_not_deleted",
           has_inventory and not has_legacy_delete,
           "legacy inventory present, no mass delete" if (has_inventory and not has_legacy_delete)
           else f"inventory={has_inventory}, legacy_delete={has_legacy_delete}")

    # --- Test 6: pipeline stdout NOT piped into JSONL ---
    # Original bug: `done < file.txt | tee -a *.jsonl`
    # Fix: explicit printf writes, no tee of the whole loop
    bad_tee = bool(re.search(r'done\s*<.*\|\s*tee.*\.jsonl', content))
    record("pipeline_stdout_not_in_jsonl", not bad_tee,
           "no loop|tee pattern found" if not bad_tee
           else "FOUND bad pattern: loop output piped into JSONL via tee")

    # --- Test 7: JSONL records from deterministic emitter ---
    has_python_emitter = bool(
        re.search(r'python3\s+-c\s+["\']import.*json', content) or
        re.search(r'python3\s+-c\s+"import', content)
    )
    record("jsonl_deterministic_emitter", has_python_emitter,
           "python3 -c JSON emitter found" if has_python_emitter
           else "no python3 -c JSON emitter found")

    # --- Test 8: quarantine before removal ---
    # cp to quarantine must appear before git rm / rm -f in the same block
    quarantine_idx = content.find("quarantine/incoming")
    cleanup_idx = content.find("git rm -f")
    if cleanup_idx == -1:
        cleanup_idx = content.find("rm -f")
    record("quarantine_before_removal",
           quarantine_idx != -1 and quarantine_idx < cleanup_idx,
           f"quarantine at {quarantine_idx}, cleanup at {cleanup_idx}")

    # --- Test 9: only dispositioned payloads removed ---
    has_processed_gate = bool(
        re.search(r'incoming_disposition_processed_files', content) and
        re.search(r'incoming_cleanup_candidates', content)
    )
    record("only_dispositioned_removed", has_processed_gate,
           "processed-files gate found for cleanup" if has_processed_gate
           else "no processed-files gate for cleanup")

    # --- Test 10: all required dispatch inputs present ---
    missing_inputs = []
    for inp in REQUIRED_DISPATCH_INPUTS:
        if inp not in content:
            missing_inputs.append(inp)
    record("dispatch_inputs_complete", len(missing_inputs) == 0,
           "all required inputs present" if not missing_inputs
           else f"missing inputs: {missing_inputs}")

    return results


def main():
    os.makedirs("reports/current", exist_ok=True)

    if not os.path.exists(CANDIDATE_PATH):
        report = {
            "schema": "stegverse.test_report.v1",
            "timestamp_utc": now_utc(),
            "candidate": CANDIDATE_PATH,
            "verdict": "ERROR",
            "error": f"synthesized candidate not found: {CANDIDATE_PATH}",
            "results": [],
        }
        with open(REPORT_PATH, "w") as f:
            json.dump(report, f, indent=2)
        print(f"ERROR: {CANDIDATE_PATH} not found")
        sys.exit(1)

    with open(CANDIDATE_PATH) as f:
        candidate = json.load(f)

    results = run_tests(candidate)

    passed = sum(1 for r in results if r["passed"] is True)
    failed = sum(1 for r in results if r["passed"] is False)
    total = len(results)
    verdict = "PASS" if failed == 0 else "FAIL"

    report = {
        "schema": "stegverse.test_report.v1",
        "timestamp_utc": now_utc(),
        "candidate": CANDIDATE_PATH,
        "verdict": verdict,
        "passed": passed,
        "failed": failed,
        "total": total,
        "results": results,
    }

    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Tests: {passed}/{total} passed — {verdict}")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['test']}: {r['detail']}")

    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
