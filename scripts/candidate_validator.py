#!/usr/bin/env python3
"""
candidate_validator.py — StegVerse-002 SV002-M11
Validates provider candidate patches against machine rules.
Writes: outputs/{provider}_candidate.json, reports/current/candidate_validation_report.json,
        receipts/current/candidate_validation_receipt.jsonl
"""
import argparse
import datetime
import json
import os
import re
import sys

REQUIRED_TOP_KEYS = {"schema", "candidate_id", "provider", "description",
                     "transition_class", "authority_ref", "policy_ref", "files"}
REQUIRED_FILE_KEYS = {"path", "operation", "content"}
FORBIDDEN_PATTERNS = [
    (r"::set-output", "deprecated ::set-output syntax"),
    (r"\./evaluate\b", "fake command ./evaluate"),
    (r"\./run\b", "fake command ./run"),
    (r"set-output name=", "deprecated set-output name= syntax"),
]
FORBIDDEN_PATHS = {
    "README.md", "incoming/", "secrets/", ".env",
}
ALLOWED_PATHS = {
    ".github/workflows/core-lite-intake.yml",
    "scripts/candidate_validator.py",
    "scripts/candidate_synthesizer.py",
    "scripts/package_candidate_bundle.py",
    "tests/test_candidate_workflow.py",
    "docs/SV002_M11_CANDIDATE_MERGE_TEST_INGEST.md",
}


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def extract_candidate_json(text):
    """Extract the first fenced JSON block from markdown text."""
    matches = re.findall(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if not matches:
        return None, "no fenced JSON block found"
    if len(matches) > 1:
        return None, f"multiple fenced JSON blocks found ({len(matches)}); exactly one required"
    try:
        data = json.loads(matches[0])
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"


def validate_candidate(data, provider_label):
    errors = []
    warnings = []

    # Schema check
    if data.get("schema") != "stegverse.candidate_patch.v1":
        errors.append(f"schema must be 'stegverse.candidate_patch.v1', got '{data.get('schema')}'")

    # Required top-level keys
    missing = REQUIRED_TOP_KEYS - set(data.keys())
    if missing:
        errors.append(f"missing required keys: {sorted(missing)}")

    # Provider identity
    if data.get("provider") in ("openai-or-claude", "", None):
        errors.append(f"provider field is unresolved or blank: '{data.get('provider')}'")

    # Files
    files = data.get("files", [])
    if not isinstance(files, list) or len(files) == 0:
        errors.append("files must be a non-empty list")
    else:
        for i, f in enumerate(files):
            missing_fkeys = REQUIRED_FILE_KEYS - set(f.keys())
            if missing_fkeys:
                errors.append(f"files[{i}] missing keys: {sorted(missing_fkeys)}")
                continue

            path = f.get("path", "")
            content = f.get("content", "")
            operation = f.get("operation", "")

            # Forbidden paths
            for fp in FORBIDDEN_PATHS:
                if path == fp or path.startswith(fp):
                    errors.append(f"files[{i}] path '{path}' is forbidden")

            # Allowed paths
            if path not in ALLOWED_PATHS:
                warnings.append(f"files[{i}] path '{path}' is not in the explicit allowed list")

            # Operation must be write
            if operation != "write":
                errors.append(f"files[{i}] operation must be 'write', got '{operation}'")

            # Content must not be empty
            if not content or not content.strip():
                errors.append(f"files[{i}] content is empty or blank")

            # Forbidden patterns in content
            for pattern, label in FORBIDDEN_PATTERNS:
                if re.search(pattern, content):
                    errors.append(f"files[{i}] content contains forbidden pattern: {label}")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to provider response .md file")
    parser.add_argument("--provider", required=True, help="Provider label (claude|openai)")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--report-dir", default="reports/current")
    parser.add_argument("--receipt-dir", default="receipts/current")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.report_dir, exist_ok=True)
    os.makedirs(args.receipt_dir, exist_ok=True)

    with open(args.input) as f:
        text = f.read()

    candidate_data, parse_error = extract_candidate_json(text)

    result = {
        "schema": "stegverse.candidate_validation_result.v1",
        "timestamp_utc": now_utc(),
        "provider": args.provider,
        "input": args.input,
        "parse_error": parse_error,
        "errors": [],
        "warnings": [],
        "verdict": "REJECTED",
    }

    if parse_error:
        result["errors"].append(parse_error)
    else:
        errors, warnings = validate_candidate(candidate_data, args.provider)
        result["errors"] = errors
        result["warnings"] = warnings
        result["verdict"] = "VALID" if not errors else "REJECTED"

        if result["verdict"] == "VALID":
            out_path = os.path.join(args.output_dir, f"{args.provider}_candidate.json")
            with open(out_path, "w") as f:
                json.dump(candidate_data, f, indent=2)
            result["output_path"] = out_path

    # Write report (append to shared report file)
    report_path = os.path.join(args.report_dir, "candidate_validation_report.json")
    existing = []
    if os.path.exists(report_path):
        try:
            with open(report_path) as f:
                existing = json.load(f)
        except Exception:
            existing = []
    existing.append(result)
    with open(report_path, "w") as f:
        json.dump(existing, f, indent=2)

    # Write receipt
    receipt_path = os.path.join(args.receipt_dir, "candidate_validation_receipt.jsonl")
    with open(receipt_path, "a") as f:
        f.write(json.dumps(result, sort_keys=True) + "\n")

    if result["verdict"] == "VALID":
        print(f"VALID: {args.provider} candidate accepted.")
        sys.exit(0)
    else:
        print(f"REJECTED: {args.provider} candidate failed validation.")
        for e in result["errors"]:
            print(f"  ERROR: {e}")
        for w in result["warnings"]:
            print(f"  WARN:  {w}")
        sys.exit(1)


if __name__ == "__main__":
    main()
