#!/usr/bin/env python3
"""
package_candidate_bundle.py — StegVerse-002 SV002-M11
Packages the synthesized candidate + all evidence into a zip bundle
for ingestion through the governed disposition route.

The bundle_manifest.json declares all workflow_dispatch inputs for each
pass through ingestion. Consecutive passes append to manifest history[],
and next-pass inputs are derived from that history to prevent runaway loops.

Pass schedule:
  pass 1: agent_provider=both, input_type=bundle       — evaluate both LLMs
  pass 2: agent_provider=none, input_type=bundle       — sandbox only
  pass 3: agent_provider=none, dry_run=true            — final verify
  pass 4+: QUARANTINE — runaway loop, do not re-dispatch
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
MAX_PASSES = 3

# Ordered pass schedule — each entry is the NEXT dispatch inputs
PASS_SCHEDULE = [
    {
        "pass": 1,
        "label": "llm-evaluation",
        "description": "Both LLMs evaluate the candidate bundle",
        "agent_provider": "both",
        "input_type": "bundle",
        "input_path": f"incoming/{BUNDLE_NAME}",
        "stage_override": "SV002-M11",
        "dry_run": "false",
        "task_id": "",
        "skip_tasks": "true",
        "repair_target": "",
        "kv_packet": "",
    },
    {
        "pass": 2,
        "label": "sandbox-test",
        "description": "Sandbox testing only — candidates already evaluated",
        "agent_provider": "none",
        "input_type": "bundle",
        "input_path": f"incoming/{BUNDLE_NAME}",
        "stage_override": "SV002-M11",
        "dry_run": "false",
        "task_id": "",
        "skip_tasks": "true",
        "repair_target": "",
        "kv_packet": "",
    },
    {
        "pass": 3,
        "label": "final-verify",
        "description": "Dry-run final verification before install",
        "agent_provider": "none",
        "input_type": "bundle",
        "input_path": f"incoming/{BUNDLE_NAME}",
        "stage_override": "SV002-M11",
        "dry_run": "true",
        "task_id": "",
        "skip_tasks": "true",
        "repair_target": "",
        "kv_packet": "",
    },
]


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_existing_manifest(bundle_path):
    """If a prior bundle exists, extract its manifest to carry forward history."""
    if not os.path.exists(bundle_path):
        return None
    try:
        with zipfile.ZipFile(bundle_path) as zf:
            if "bundle_manifest.json" in zf.namelist():
                return json.loads(zf.read("bundle_manifest.json"))
    except Exception:
        pass
    return None


def derive_next_dispatch(history):
    """
    Given the existing pass history, return the next dispatch inputs.
    Returns (dispatch_dict, error_string).
    error_string is non-None if the loop should be stopped.
    """
    completed_passes = len(history)

    if completed_passes >= MAX_PASSES:
        return None, (
            f"RUNAWAY LOOP: {completed_passes} passes already completed "
            f"(max={MAX_PASSES}). Bundle must be quarantined."
        )

    return PASS_SCHEDULE[completed_passes], None


def collect_evidence(report_dir, receipt_dir, output_dir):
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
    parser.add_argument("--require-tests-pass", action="store_true")
    parser.add_argument("--record-pass", default=None,
                        help="Record a completed pass into history before deriving next dispatch. "
                             "Value: JSON string with pass result fields.")
    args = parser.parse_args()

    os.makedirs(args.dist_dir, exist_ok=True)
    os.makedirs(args.report_dir, exist_ok=True)

    if not os.path.exists(args.synthesized_candidate):
        print(f"FATAL: synthesized candidate not found: {args.synthesized_candidate}")
        sys.exit(1)

    if args.require_tests_pass and os.path.exists(args.test_report):
        with open(args.test_report) as f:
            test_data = json.load(f)
        if test_data.get("verdict") != "PASS":
            print(f"FATAL: test report verdict is '{test_data.get('verdict')}', not PASS. Packaging blocked.")
            sys.exit(1)

    bundle_path = os.path.join(args.dist_dir, BUNDLE_NAME)

    # Carry forward history from any prior bundle
    prior_manifest = read_existing_manifest(bundle_path)
    history = prior_manifest.get("history", []) if prior_manifest else []

    # Record a completed pass if requested
    if args.record_pass:
        try:
            pass_record = json.loads(args.record_pass)
        except json.JSONDecodeError as e:
            print(f"FATAL: --record-pass value is not valid JSON: {e}")
            sys.exit(1)
        pass_record["recorded_utc"] = now_utc()
        history.append(pass_record)

    # Derive next dispatch inputs
    next_dispatch, loop_error = derive_next_dispatch(history)
    if loop_error:
        print(f"FATAL: {loop_error}")
        # Write a quarantine marker
        quarantine_marker = os.path.join(args.report_dir, "bundle_loop_quarantine.json")
        with open(quarantine_marker, "w") as f:
            json.dump({
                "schema": "stegverse.bundle_loop_quarantine.v1",
                "timestamp_utc": now_utc(),
                "bundle": BUNDLE_NAME,
                "reason": loop_error,
                "history": history,
            }, f, indent=2)
        sys.exit(1)

    # Build file list
    evidence_files = collect_evidence(args.report_dir, args.receipt_dir, args.output_dir)
    manifest_file_entries = []

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:

        # Synthesized candidate at root
        zf.write(args.synthesized_candidate, "synthesized_candidate.json")
        manifest_file_entries.append({
            "arcname": "synthesized_candidate.json",
            "sha256": sha256_file(args.synthesized_candidate),
        })

        # Evidence files
        for path in evidence_files:
            arcname = os.path.join("evidence", os.path.basename(path))
            zf.write(path, arcname)
            manifest_file_entries.append({
                "arcname": arcname,
                "sha256": sha256_file(path),
            })

        # Manifest — declares all dispatch inputs + full pass history
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "candidate_id": "sv002-m11-synthesized-intake-repair",
            "bundle_name": BUNDLE_NAME,
            "created_utc": now_utc(),
            "dispatch": next_dispatch,
            "history": history,
            "pass_schedule": PASS_SCHEDULE,
            "max_passes": MAX_PASSES,
            "files": manifest_file_entries,
        }
        manifest_bytes = json.dumps(manifest, indent=2).encode()
        zf.writestr("bundle_manifest.json", manifest_bytes)
        manifest_file_entries.append({
            "arcname": "bundle_manifest.json",
            "sha256": sha256_bytes(manifest_bytes),
        })

    bundle_sha = sha256_file(bundle_path)

    # Write bundle path for routing step
    with open(os.path.join(args.report_dir, "winning_candidate_bundle_path.txt"), "w") as f:
        f.write(bundle_path + "\n")

    # Write next dispatch inputs as a flat env file for the workflow routing step
    dispatch_env_path = os.path.join(args.report_dir, "next_dispatch_inputs.json")
    with open(dispatch_env_path, "w") as f:
        json.dump(next_dispatch, f, indent=2)

    # Install instructions
    pass_num = next_dispatch["pass"]
    pass_label = next_dispatch["label"]
    install_md = f"""# SV002-M11 Synthesized Intake Repair — Upload Instructions

## Bundle

`{BUNDLE_NAME}`

SHA-256: `{bundle_sha}`

Created: `{now_utc()}`

## Next Pass

Pass {pass_num} — `{pass_label}`

{next_dispatch['description']}

Dispatch inputs declared in `bundle_manifest.json`:

| Input | Value |
|---|---|
| agent_provider | `{next_dispatch['agent_provider']}` |
| input_type | `{next_dispatch['input_type']}` |
| input_path | `{next_dispatch['input_path']}` |
| stage_override | `{next_dispatch['stage_override']}` |
| dry_run | `{next_dispatch['dry_run']}` |
| task_id | `{next_dispatch['task_id'] or '[blank]'}` |
| skip_tasks | `{next_dispatch['skip_tasks']}` |
| repair_target | `{next_dispatch['repair_target'] or '[blank]'}` |
| kv_packet | `{next_dispatch['kv_packet'] or '[blank]'}` |

## Pass History

Passes completed: {len(history)} / {MAX_PASSES} maximum

{chr(10).join(f"- Pass {p.get('pass', '?')}: {p.get('label', '?')} — {p.get('verdict', '?')} ({p.get('recorded_utc', '?')})" for p in history) if history else "- None yet"}

## Installation

1. Download `{BUNDLE_NAME}` from the workflow artifacts.
2. Copy to `incoming/{BUNDLE_NAME}` in the repository.
3. Commit and push to `main`.
4. The `core-lite-intake` workflow fires, reads `bundle_manifest.json`,
   and dispatches with the declared inputs above.

## Authority

Candidate evidence only. No broad authority. Installation requires passing disposition gate.

Policy ref: `triad/default-deny/no-broad-authority`
"""
    with open("SV002_M11_SYNTHESIZED_INTAKE_REPAIR_UPLOAD.md", "w") as f:
        f.write(install_md)

    print(f"Bundle created: {bundle_path}")
    print(f"SHA-256: {bundle_sha}")
    print(f"Next dispatch: pass {pass_num} ({pass_label})")
    print(f"Pass history: {len(history)}/{MAX_PASSES} completed")
    sys.exit(0)


if __name__ == "__main__":
    main()
