#!/usr/bin/env python3
"""
test_candidate_workflow.py — StegVerse-002 SV002-M11
Deterministic tests for the synthesized candidate patch.

Task-aware: detects what the candidate contains and runs
appropriate tests. Does not assume a specific file path.

Universal tests (all candidates):
  1. Candidate has valid schema
  2. Candidate has at least one file
  3. All files have path, operation, and content
  4. No forbidden patterns in any file content
  5. No forbidden authority claims
  6. Provider field is set correctly

Pipeline-specific tests (if pipeline.py present):
  7. Python syntax valid
  8. BatchIngestionController imported or referenced
  9. zip/bundle routing present
  10. Disposition records written

Workflow-specific tests (if core-lite-intake.yml present):
  7. YAML parses successfully
  8. push trigger for incoming/** present
  9. incoming/README.md excluded
  10. dispatch inputs complete
"""
import ast
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
FORBIDDEN_PATTERNS = [
    "::set-output",
    "./evaluate",
    "actions/checkout@v2",
    "actions/checkout@v3",
]
FORBIDDEN_AUTHORITY = [
    "sovereign_authority",
    "broad_authority",
    "self_accredit",
]


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_file_content(candidate, path_fragment):
    """Find a file in candidate by partial path match."""
    for f in candidate.get("files", []):
        if path_fragment in f.get("path", ""):
            return f.get("content", ""), f.get("path", "")
    return None, None


def run_tests(candidate):
    results = []

    def record(name, passed, detail=""):
        results.append({"test": name, "passed": passed, "detail": detail})

    files = candidate.get("files", [])

    # --- Universal Test 1: Valid schema ---
    record("schema_valid",
           candidate.get("schema") == "stegverse.candidate_patch.v1",
           f"schema={candidate.get('schema')}")

    # --- Universal Test 2: Has files ---
    record("has_files",
           len(files) > 0,
           f"file_count={len(files)}")

    if not files:
        return results

    # --- Universal Test 3: All files have required fields ---
    missing_fields = []
    for i, f in enumerate(files):
        for field in ("path", "operation", "content"):
            if not f.get(field):
                missing_fields.append(f"files[{i}] missing {field}")
    record("files_have_required_fields",
           len(missing_fields) == 0,
           f"missing={missing_fields}" if missing_fields else "all fields present")

    # --- Universal Test 4: No forbidden patterns ---
    forbidden_found = []
    for f in files:
        content = f.get("content", "")
        for pat in FORBIDDEN_PATTERNS:
            if pat in content:
                forbidden_found.append(f"{f.get('path')}: {pat}")
    record("no_forbidden_patterns",
           len(forbidden_found) == 0,
           f"found={forbidden_found}" if forbidden_found else "none found")

    # --- Universal Test 5: No forbidden authority claims ---
    authority_found = []
    for f in files:
        content = f.get("content", "").lower()
        for pat in FORBIDDEN_AUTHORITY:
            if pat in content:
                authority_found.append(f"{f.get('path')}: {pat}")
    record("no_forbidden_authority",
           len(authority_found) == 0,
           f"found={authority_found}" if authority_found else "none found")

    # --- Universal Test 6: Provider field set ---
    provider = candidate.get("provider", "")
    record("provider_field_set",
           bool(provider) and provider not in ("openai-or-claude", "YOUR_PROVIDER_NAME"),
           f"provider={provider}")

    # --- Detect candidate type and run specific tests ---

    # Pipeline candidate
    pipeline_content, pipeline_path = get_file_content(candidate, "pipeline.py")
    if pipeline_content is not None:
        record("candidate_type", True, f"pipeline candidate: {pipeline_path}")

        # Test 7: Python syntax valid
        try:
            ast.parse(pipeline_content)
            record("python_syntax_valid", True, "ast.parse passed")
        except SyntaxError as e:
            record("python_syntax_valid", False, str(e))

        # Test 8: BatchIngestionController referenced
        has_batch = ("BatchIngestionController" in pipeline_content or
                     "batch_ingestion" in pipeline_content)
        record("batch_ingestion_referenced",
               has_batch,
               "BatchIngestionController found" if has_batch
               else "BatchIngestionController not found")

        # Test 9: zip/bundle routing present
        has_zip_routing = bool(
            re.search(r'\.zip|bundle|ZipFile', pipeline_content)
        )
        record("zip_bundle_routing_present",
               has_zip_routing,
               "zip/bundle routing found" if has_zip_routing
               else "no zip/bundle routing found")

        # Test 10: Disposition record written
        has_disposition = bool(
            re.search(r'receipt|disposition|jsonl', pipeline_content,
                      re.IGNORECASE)
        )
        record("disposition_records_written",
               has_disposition,
               "disposition/receipt reference found" if has_disposition
               else "no disposition reference found")

        return results

    # Workflow candidate
    workflow_content, workflow_path = get_file_content(
        candidate, "core-lite-intake.yml"
    )
    if workflow_content is not None:
        record("candidate_type", True, f"workflow candidate: {workflow_path}")

        # Test 7: YAML parses
        if YAML_AVAILABLE:
            try:
                yaml.safe_load(workflow_content)
                record("yaml_parses", True)
            except yaml.YAMLError as e:
                record("yaml_parses", False, str(e))
                return results
        else:
            record("yaml_parses",
                   "on:" in workflow_content or '"on":' in workflow_content,
                   "yaml unavailable — checked for on: key")

        # Test 8: push trigger for incoming/**
        has_push = bool(
            re.search(r'push\s*:', workflow_content) and
            re.search(r'incoming/\*\*', workflow_content)
        )
        record("push_trigger_incoming", has_push,
               "push trigger with incoming/** found" if has_push
               else "missing push trigger or incoming/**")

        # Test 9: incoming/README.md excluded
        has_readme_excl = "incoming/README.md" in workflow_content
        record("readme_excluded", has_readme_excl,
               "incoming/README.md exclusion found" if has_readme_excl
               else "no README.md exclusion")

        # Test 10: dispatch inputs complete
        missing_inputs = [i for i in REQUIRED_DISPATCH_INPUTS
                          if i not in workflow_content]
        record("dispatch_inputs_complete",
               len(missing_inputs) == 0,
               "all inputs present" if not missing_inputs
               else f"missing: {missing_inputs}")

        return results

    # Generic candidate — unknown file type, run basic checks only
    record("candidate_type", True,
           f"generic candidate: {[f.get('path') for f in files]}")
    record("files_have_content",
           all(bool(f.get("content", "").strip()) for f in files),
           "all files have non-empty content")

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
