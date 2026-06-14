#!/usr/bin/env python3
"""
bundle_manifest_reader.py — StegVerse-002 SV002-M11 v4

Exits:
  0 — manifest valid with dispatch block, next_dispatch_inputs.json written
      (only when STEGVERSE_ALLOW_SELF_REDISPATCH=true)
  2 — not a re-dispatch bundle, no dispatch block, or self-dispatch disabled
      → batch ingestion controller / disposition gate handles it directly
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


def env_truthy(name, default="false"):
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def write_json(path, payload):
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def append_summary(title, lines):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if not summary_path:
        return
    with open(summary_path, "a") as f:
        f.write(f"## {title}\n\n")
        for line in lines:
            f.write(f"{line}\n")
        f.write("\n")


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

    # Read manifest
    try:
        with zipfile.ZipFile(args.bundle) as z:
            if "bundle_manifest.json" not in z.namelist():
                print("NOT_A_REDISPATCH_BUNDLE: no bundle_manifest.json")
                sys.exit(2)
            manifest = json.loads(z.read("bundle_manifest.json"))
    except Exception as e:
        print(f"ERROR reading bundle: {e}")
        sys.exit(1)

    # Schema check
    if manifest.get("schema") != "stegverse.bundle_manifest.v1":
        print(f"NOT_A_REDISPATCH_BUNDLE: schema={manifest.get('schema')}")
        sys.exit(2)

    dispatch = manifest.get("dispatch", {})
    history = manifest.get("history", [])
    max_passes = manifest.get("max_passes", 3)

    # No dispatch block — this is an install/evidence/candidate bundle,
    # not a pass-schedule bundle. Let batch ingestion controller handle it.
    if not dispatch:
        print(
            "NO_DISPATCH_BLOCK: install/evidence bundle — "
            "batch ingestion controller will handle directly"
        )
        sys.exit(2)

    # Runaway loop check
    if len(history) >= max_passes:
        msg = (
            f"RUNAWAY LOOP: {len(history)} passes completed, "
            f"max={max_passes}. Bundle must be quarantined."
        )
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
        write_json(os.path.join(args.report_dir, "bundle_loop_quarantine.json"), quarantine)
        sys.exit(3)

    # Stale manifest check
    input_path = dispatch.get("input_path", "")
    if input_path:
        abs_input_path = os.path.join(args.repo_root, input_path)
        if not os.path.exists(abs_input_path):
            stale_record = {
                "schema": "stegverse.stale_manifest_receipt.v1",
                "timestamp_utc": now_utc(),
                "bundle": args.bundle,
                "dispatch_input_path": input_path,
                "reason": (
                    f"input_path '{input_path}' no longer exists — "
                    f"already processed or cleaned up. Skipping re-dispatch."
                ),
            }
            write_json(os.path.join(args.report_dir, "stale_manifest_receipt.json"), stale_record)
            append_summary(
                "Bundle Manifest — Stale Dispatch Skipped",
                [f"`{input_path}` no longer exists. Re-dispatch skipped."],
            )
            print(f"STALE_MANIFEST: '{input_path}' not found — skipping re-dispatch cleanly")
            sys.exit(4)

    # Safety guard: the workflow's self-dispatch step is disabled. A manifest with
    # a dispatch block must not be allowed to stall the disposition gate by
    # returning exit 0. Treat it as a direct bundle for disposition purposes.
    if not env_truthy("STEGVERSE_ALLOW_SELF_REDISPATCH"):
        disabled_record = {
            "schema": "stegverse.redispatch_disabled_receipt.v1",
            "timestamp_utc": now_utc(),
            "bundle": args.bundle,
            "dispatch": dispatch,
            "history_count": len(history),
            "max_passes": max_passes,
            "reason": (
                "self-dispatch is disabled; redispatch-style bundle is being "
                "returned to the declared-input disposition gate"
            ),
        }
        write_json(
            os.path.join(args.report_dir, "redispatch_disabled_receipt.json"),
            disabled_record,
        )
        append_summary(
            "Bundle Manifest — Redispatch Disabled",
            [
                f"Bundle: `{args.bundle}`",
                "Dispatch block detected, but self-dispatch is disabled.",
                "Returning exit 2 so the declared-input disposition gate handles the payload.",
            ],
        )
        print(
            "REDISPATCH_DISABLED: dispatch bundle will be handled by "
            "declared-input disposition gate"
        )
        sys.exit(2)

    # Write next dispatch inputs only if self-redispatch is explicitly enabled.
    dispatch_path = os.path.join(args.report_dir, "next_dispatch_inputs.json")
    with open(dispatch_path, "w") as f:
        json.dump(dispatch, f, indent=2)

    append_summary(
        "Bundle Manifest — Dispatch Inputs",
        [
            f"Pass {dispatch.get('pass', '?')} — `{dispatch.get('label', '?')}`",
            "",
            dispatch.get("description", ""),
            "",
            "| Input | Value |",
            "|---|---|",
            *[
                f"| {k} | `{v or '[blank]'}` |"
                for k, v in dispatch.items()
                if k not in ("pass", "label", "description")
            ],
            f"",
            f"Passes completed: {len(history)} / {max_passes}",
        ],
    )

    print(
        f"REDISPATCH_BUNDLE: pass={dispatch.get('pass')}, "
        f"label={dispatch.get('label')}, "
        f"agent_provider={dispatch.get('agent_provider')}, "
        f"history={len(history)}/{max_passes}"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
