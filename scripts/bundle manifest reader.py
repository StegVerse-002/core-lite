#!/usr/bin/env python3
"""
bundle_manifest_reader.py — StegVerse-002 SV002-M11
Reads a candidate patch bundle, extracts manifest dispatch inputs,
checks for runaway loops, and writes next dispatch inputs to a JSON file.

Fix v2:
  - Validates input_path from dispatch block exists in repo before writing
  - Writes STALE_MANIFEST receipt and exits 0 if input_path is gone
  - Prevents bot re-dispatch loops from stale manifests

Exits:
  0 — manifest valid, next_dispatch_inputs.json written
  2 — not a candidate patch bundle (schema mismatch or no manifest)
  3 — runaway loop detected, quarantine flag written
  4 — stale manifest (input_path no longer exists) — exits cleanly
  1 — other error
"""
import argparse
import datetime
import json
import os
import sys
import zipfile


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--report-dir", default="reports/current")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    os.makedirs(args.report_dir, exist_ok=True)

    if not os.path.exists(args.bundle):
        print(f"ERROR: bundle not found: {args.bundle}")
        sys.exit(1)

    # Open and read manifest
    try:
        with zipfile.ZipFile(args.bundle) as z:
            if "bundle_manifest.json" not in z.namelist():
                print("NOT_A_CANDIDATE_BUNDLE: no bundle_manifest.json")
                sys.exit(2)
            manifest = json.loads(z.read("bundle_manifest.json"))
    except Exception as e:
        print(f"ERROR reading bundle: {e}")
        sys.exit(1)

    # Validate schema
    if manifest.get("schema") != "stegverse.bundle_manifest.v1":
        print(f"NOT_A_CANDIDATE_BUNDLE: schema={manifest.get('schema')}")
        sys.exit(2)

    dispatch = manifest.get("dispatch", {})
    history = manifest.get("history", [])
    max_passes = manifest.get("max_passes", 3)

    # Runaway loop check
    if len(history) >= max_passes:
        msg = (f"RUNAWAY LOOP: {len(history)} passes completed, "
               f"max={max_passes}. Bundle must be quarantined.")
        print(f"::error::{msg}")
        quarantine = {
            "schema": "stegverse.bundle_loop_quarantine.v1",
            "timestamp_utc": now_utc(),
            "bundle": args.bundle,
            "passes_completed": len(history),
            "max_passes": max_passes,
            "history": history,
        }
        with open(os.path.join(args.report_dir, "bundle_quarantine_flag.txt"), "w") as f:
            f.write("QUARANTINE\n")
        with open(os.path.join(args.report_dir, "bundle_loop_quarantine.json"), "w") as f:
            json.dump(quarantine, f, indent=2)
        sys.exit(3)

    # Stale manifest check — verify input_path still exists in repo
    # This prevents bot re-dispatch loops when the referenced bundle
    # has already been cleaned up from incoming/
    input_path = dispatch.get("input_path", "")
    if input_path:
        abs_input_path = os.path.join(args.repo_root, input_path)
        if not os.path.exists(abs_input_path):
            stale_record = {
                "schema": "stegverse.stale_manifest_receipt.v1",
                "timestamp_utc": now_utc(),
                "bundle": args.bundle,
                "dispatch_input_path": input_path,
                "resolved_path": abs_input_path,
                "reason": (
                    f"input_path '{input_path}' declared in manifest dispatch "
                    f"no longer exists in repo — bundle already processed or "
                    f"cleaned up. Skipping re-dispatch to prevent loop."
                ),
                "history_passes": len(history),
            }
            stale_path = os.path.join(args.report_dir, "stale_manifest_receipt.json")
            with open(stale_path, "w") as f:
                json.dump(stale_record, f, indent=2)

            summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
            if summary_path:
                with open(summary_path, "a") as f:
                    f.write("## Bundle Manifest — Stale Dispatch Skipped\n\n")
                    f.write(f"input_path `{input_path}` no longer exists. ")
                    f.write("Re-dispatch skipped — bundle already processed.\n")

            print(f"STALE_MANIFEST: input_path '{input_path}' not found — "
                  f"skipping re-dispatch cleanly")
            sys.exit(4)

    # Write next dispatch inputs
    dispatch_path = os.path.join(args.report_dir, "next_dispatch_inputs.json")
    with open(dispatch_path, "w") as f:
        json.dump(dispatch, f, indent=2)

    # Write GitHub step summary
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write("## Bundle Manifest — Dispatch Inputs\n\n")
            f.write(f"Pass {dispatch.get('pass','?')} — `{dispatch.get('label','?')}`\n\n")
            f.write(f"{dispatch.get('description','')}\n\n")
            f.write("| Input | Value |\n|---|---|\n")
            for k, v in dispatch.items():
                if k not in ("pass", "label", "description"):
                    f.write(f"| {k} | `{v or '[blank]'}` |\n")
            f.write(f"\nPasses completed: {len(history)} / {max_passes}\n")

    print(f"CANDIDATE_BUNDLE: pass={dispatch.get('pass')}, "
          f"label={dispatch.get('label')}, "
          f"agent_provider={dispatch.get('agent_provider')}, "
          f"history={len(history)}/{max_passes}")
    sys.exit(0)


if __name__ == "__main__":
    main()
