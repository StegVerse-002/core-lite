#!/usr/bin/env python3
"""
candidate_synthesizer.py — StegVerse-002 SV002-M11
Merges two validated candidate patches into one synthesized candidate.
Prefers deterministic, repo-real content. Never picks one model blindly.
Writes: outputs/synthesized_candidate.json,
        reports/current/candidate_merge_report.json,
        receipts/current/candidate_merge_receipt.jsonl
"""
import argparse
import datetime
import json
import os
import sys

SYNTHESIZED_METADATA = {
    "schema": "stegverse.candidate_patch.v1",
    "candidate_id": "sv002-m11-synthesized-intake-repair",
    "provider": "merged-openai-claude",
    "description": (
        "Synthesized repair of core-lite-intake.yml: fixes inline Python heredoc "
        "causing YAML parse failure, fixes pipe corruption of JSONL disposition records, "
        "quotes 'on:' key to prevent boolean coercion, and adds per-payload pipeline log "
        "redirection. Preserves all inputs, triggers, job structure, and governance layer."
    ),
    "transition_class": "workflow-repair",
    "authority_ref": "SV002-M11/scoped-merged-candidate",
    "policy_ref": "triad/default-deny/no-broad-authority",
}

# Rejection criteria for individual file entries during synthesis
REJECT_PATTERNS = [
    "::set-output",
    "set-output name=",
    "./evaluate",
    "actions/checkout@v2",
    "actions/checkout@v3",
]


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def load_candidate(path):
    with open(path) as f:
        return json.load(f)


def score_file_entry(entry, provider):
    """
    Score a file entry for synthesis preference.
    Higher = prefer this provider's version.
    """
    content = entry.get("content", "")
    score = 0

    # Penalize deprecated/fake patterns
    for pat in REJECT_PATTERNS:
        if pat in content:
            score -= 10

    # Reward quoting of 'on:' key (YAML boolean fix)
    if '"on":' in content or "'on':" in content:
        score += 5

    # Reward python3 -c over heredoc
    if "python3 -c" in content:
        score += 5

    # Reward per-payload log redirection
    if "pipeline.log" in content:
        score += 3

    # Reward explicit printf record writes (not tee)
    if 'printf' in content and 'RECORD' in content:
        score += 3

    # Reward STAGE_REF via env
    if "STAGE_REF" in content:
        score += 2

    # Reward preservation of all inputs
    for inp in ["skip_tasks", "repair_target", "kv_packet", "task_id"]:
        if inp in content:
            score += 1

    # Penalize collapsing multi-job into single job
    if "jobs:\n  intake:" in content or 'jobs:\n  intake:' in content:
        score -= 20

    return score


def synthesize(claude_candidate, openai_candidate):
    """
    Build a merged file list. For each path, pick the better entry or merge where possible.
    """
    # Index by path
    claude_files = {f["path"]: f for f in claude_candidate.get("files", [])}
    openai_files = {f["path"]: f for f in openai_candidate.get("files", [])}

    all_paths = sorted(set(list(claude_files.keys()) + list(openai_files.keys())))

    merged_files = []
    decisions = []

    for path in all_paths:
        c_entry = claude_files.get(path)
        o_entry = openai_files.get(path)

        if c_entry and not o_entry:
            c_score = score_file_entry(c_entry, "claude")
            if c_score >= 0:
                merged_files.append(c_entry)
                decisions.append({"path": path, "decision": "claude-only", "claude_score": c_score})
            else:
                decisions.append({"path": path, "decision": "rejected-claude-only",
                                   "claude_score": c_score, "reason": "negative score"})

        elif o_entry and not c_entry:
            o_score = score_file_entry(o_entry, "openai")
            if o_score >= 0:
                merged_files.append(o_entry)
                decisions.append({"path": path, "decision": "openai-only", "openai_score": o_score})
            else:
                decisions.append({"path": path, "decision": "rejected-openai-only",
                                   "openai_score": o_score, "reason": "negative score"})

        else:
            # Both have this path — score and pick the better one
            c_score = score_file_entry(c_entry, "claude")
            o_score = score_file_entry(o_entry, "openai")

            if c_score >= o_score and c_score >= 0:
                merged_files.append(c_entry)
                decisions.append({"path": path, "decision": "prefer-claude",
                                   "claude_score": c_score, "openai_score": o_score})
            elif o_score > c_score and o_score >= 0:
                merged_files.append(o_entry)
                decisions.append({"path": path, "decision": "prefer-openai",
                                   "claude_score": c_score, "openai_score": o_score})
            else:
                decisions.append({"path": path, "decision": "both-rejected",
                                   "claude_score": c_score, "openai_score": o_score,
                                   "reason": "both scored negative"})

    return merged_files, decisions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", required=True, help="Path to validated Claude candidate JSON")
    parser.add_argument("--openai", required=True, help="Path to validated OpenAI candidate JSON")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--report-dir", default="reports/current")
    parser.add_argument("--receipt-dir", default="receipts/current")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.report_dir, exist_ok=True)
    os.makedirs(args.receipt_dir, exist_ok=True)

    errors = []

    claude_ok = os.path.exists(args.claude)
    openai_ok = os.path.exists(args.openai)

    if not claude_ok:
        errors.append(f"Claude candidate not found: {args.claude}")
    if not openai_ok:
        errors.append(f"OpenAI candidate not found: {args.openai}")

    if not claude_ok and not openai_ok:
        print("FATAL: no valid candidates available for synthesis.")
        sys.exit(1)

    # Load whichever are available; substitute empty if one is missing
    if claude_ok:
        claude_candidate = load_candidate(args.claude)
    else:
        claude_candidate = {"files": []}
        errors.append("Claude candidate absent — synthesizing from OpenAI only")

    if openai_ok:
        openai_candidate = load_candidate(args.openai)
    else:
        openai_candidate = {"files": []}
        errors.append("OpenAI candidate absent — synthesizing from Claude only")

    merged_files, decisions = synthesize(claude_candidate, openai_candidate)

    if not merged_files:
        print("FATAL: synthesis produced no valid file entries.")
        sys.exit(1)

    synthesized = dict(SYNTHESIZED_METADATA)
    synthesized["files"] = merged_files

    out_path = os.path.join(args.output_dir, "synthesized_candidate.json")
    with open(out_path, "w") as f:
        json.dump(synthesized, f, indent=2)

    report = {
        "schema": "stegverse.candidate_merge_report.v1",
        "timestamp_utc": now_utc(),
        "claude_candidate": args.claude if claude_ok else None,
        "openai_candidate": args.openai if openai_ok else None,
        "errors": errors,
        "decisions": decisions,
        "merged_file_count": len(merged_files),
        "output_path": out_path,
    }

    report_path = os.path.join(args.report_dir, "candidate_merge_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    receipt_path = os.path.join(args.receipt_dir, "candidate_merge_receipt.jsonl")
    with open(receipt_path, "a") as f:
        f.write(json.dumps(report, sort_keys=True) + "\n")

    print(f"Synthesis complete: {len(merged_files)} file(s) merged.")
    for d in decisions:
        print(f"  {d['path']}: {d['decision']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
