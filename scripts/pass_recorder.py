#!/usr/bin/env python3
"""
pass_recorder.py — StegVerse-002 SV002-M11
Determines the current pass number from an existing bundle manifest,
and prints a JSON pass record for use with --record-pass in package_candidate_bundle.py.
"""
import argparse
import json
import os
import sys
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--verdict", required=True)
    parser.add_argument("--agent-provider", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--run-url", default="")
    args = parser.parse_args()

    pass_num = 1
    label = "llm-evaluation"

    if os.path.exists(args.bundle):
        try:
            with zipfile.ZipFile(args.bundle) as z:
                if "bundle_manifest.json" in z.namelist():
                    m = json.loads(z.read("bundle_manifest.json"))
                    history = m.get("history", [])
                    pass_num = len(history) + 1
                    schedule = m.get("pass_schedule", [])
                    # Find label for this pass number
                    for entry in schedule:
                        if entry.get("pass") == pass_num:
                            label = entry.get("label", label)
                            break
        except Exception:
            pass

    record = {
        "pass": pass_num,
        "label": label,
        "verdict": args.verdict,
        "agent_provider": args.agent_provider,
        "run_id": args.run_id,
        "run_url": args.run_url,
    }
    print(json.dumps(record))


if __name__ == "__main__":
    main()
