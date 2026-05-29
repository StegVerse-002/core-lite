#!/usr/bin/env python3
"""
package_candidate_bundle.py — StegVerse-002 SV002-M11
Packages the synthesized candidate + all evidence into a zip bundle
for ingestion through the governed disposition route.
Writes: dist/bundles/sv002_m11_synthesized_intake_repair_bundle.zip
        SV002_M11_SYNTHESIZED_INTAKE_REPAIR_UPLOAD.md (install instructions)
        reports/current/winning_candidate_bundle_path.txt (path for routing step)
"""
import argparse
import datetime
import hashlib
import json
import os
import sys
import zipfile

BUNDLE_NAME = "sv002_m11_synthesized_intake_repair_bundle.zip"
MANIFEST_SCHEMA = "stegverse.bundle_manifest.v1"


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_evidence(report_dir, receipt_dir, output_dir):
    """Collect all evidence files that exist."""
    candidates = [
        os.path.join(output_dir, "claude_candidate.json"),
        os.path.join(output_dir, "openai_candidate.json"),
        os.path.join(output_dir, "synthesized_candidate.json"),
        os.path.join(report_dir, "candidate_validation_report.json"),
        os.path.join(report_dir, "candidate_merge_report.json"),
        os.path.join(report_dir, "synthesized_candidate_test_report.json"),
        os.path.join(receipt_dir, "candidate_validation_receipt.jsonl"),
        os.path.join(receipt_dir, "candidate_merge_receipt.jsonl"),
    ]
    return [p for p in candidates if os.path.exists(p)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthesized-candidate", default="outputs/synthesized_candidate.json")
    parser.add_argument("--test-report", default="reports/current/synthesized_candidate_test_report.json")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--report-dir", default="reports/current")
    parser.add_argument("--receipt-dir", default="receipts/current")
    parser.add_argument("--dist-dir", default="dist/bundles")
    parser.add_argument("--require-tests-pass", action="store_true",
                        help="Abort packaging if test report shows failures")
    args = parser.parse_args()

    os.makedirs(args.dist_dir, exist_ok=True)
    os.makedirs(args.report_dir, exist_ok=True)

    # Check synthesized candidate exists
    if not os.path.exists(args.synthesized_candidate):
        print(f"FATAL: synthesized candidate not found: {args.synthesized_candidate}")
        sys.exit(1)

    # Optionally gate on test results
    if args.require_tests_pass and os.path.exists(args.test_report):
        with open(args.test_report) as f:
            test_data = json.load(f)
        if test_data.get("verdict") != "PASS":
            print(f"FATAL: test report verdict is '{test_data.get('verdict')}', not PASS. Packaging blocked.")
            sys.exit(1)

    bundle_path = os.path.join(args.dist_dir, BUNDLE_NAME)
    evidence_files = collect_evidence(args.report_dir, args.receipt_dir, args.output_dir)
    manifest_entries = []

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Always include synthesized candidate at root
        zf.write(args.synthesized_candidate, "synthesized_candidate.json")
        manifest_entries.append({
            "arcname": "synthesized_candidate.json",
            "source": args.synthesized_candidate,
            "sha256": sha256_file(args.synthesized_candidate),
        })

        # Include all evidence
        for path in evidence_files:
            arcname = os.path.join("evidence", os.path.basename(path))
            zf.write(path, arcname)
            manifest_entries.append({
                "arcname": arcname,
                "source": path,
                "sha256": sha256_file(path),
            })

        # Write manifest inside bundle
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "candidate_id": "sv002-m11-synthesized-intake-repair",
            "bundle_name": BUNDLE_NAME,
            "created_utc": now_utc(),
            "files": manifest_entries,
        }
        zf.writestr("bundle_manifest.json", json.dumps(manifest, indent=2))

    bundle_sha = sha256_file(bundle_path)

    # Write bundle path for routing step
    bundle_path_file = os.path.join(args.report_dir, "winning_candidate_bundle_path.txt")
    with open(bundle_path_file, "w") as f:
        f.write(bundle_path + "\n")

    # Write install instruction file
    install_md = f"""# SV002-M11 Synthesized Intake Repair — Upload Instructions

## Bundle

`{BUNDLE_NAME}`

SHA-256: `{bundle_sha}`

Created: `{now_utc()}`

## What This Contains

- `synthesized_candidate.json` — merged candidate patch from Claude + OpenAI validation
- `evidence/` — validation report, merge report, test report, receipts

## Installation

This bundle must be ingested through the governed disposition route.

### Automatic (if self-ingestion is enabled)

The workflow will copy this bundle to `incoming/` and push,
triggering the `push: paths: incoming/**` workflow run automatically.

### Manual

1. Download `{BUNDLE_NAME}` from the workflow artifacts.
2. Copy to `incoming/{BUNDLE_NAME}` in the repository.
3. Commit and push to `main`.
4. The `core-lite-intake` workflow will fire and process it through the disposition gate.

## Authority

Candidate evidence only. No broad authority. Installation requires passing disposition gate.

Policy ref: `triad/default-deny/no-broad-authority`
"""
    install_path = "SV002_M11_SYNTHESIZED_INTAKE_REPAIR_UPLOAD.md"
    with open(install_path, "w") as f:
        f.write(install_md)

    print(f"Bundle created: {bundle_path}")
    print(f"SHA-256: {bundle_sha}")
    print(f"Install instructions: {install_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
