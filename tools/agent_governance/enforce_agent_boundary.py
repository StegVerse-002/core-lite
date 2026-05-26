#!/usr/bin/env python3
"""Enforce governed collaboration write boundary before committing coordination outputs."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_patterns(path: Path) -> list[str]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def changed_paths() -> list[str]:
    result = subprocess.run(["git", "status", "--porcelain"], text=True, capture_output=True, check=False)
    paths = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        paths.append(path)
    return sorted(set(paths))


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Enforce agent write boundary.")
    p.add_argument("--allowed", default="agent_policy/allowed_paths.json")
    p.add_argument("--forbidden", default="agent_policy/forbidden_paths.json")
    p.add_argument("--report", default="reports/current/agent_boundary_report.json")
    p.add_argument("--receipt", default="receipts/current/agent_boundary_receipt.jsonl")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    allowed = load_patterns(Path(args.allowed))
    forbidden = load_patterns(Path(args.forbidden))
    paths = changed_paths()

    violations = []
    allowed_effects = []
    for path in paths:
        if matches(path, forbidden):
            violations.append({"path": path, "reason": "forbidden_path_changed"})
        elif matches(path, allowed):
            allowed_effects.append(path)
        else:
            violations.append({"path": path, "reason": "path_not_allowed"})

    decision = "ALLOW_CANDIDATE_EVIDENCE" if not violations else "FAIL_CLOSED"
    timestamp = utc_now()
    report = {
        "schema": "stegverse.agent_boundary_report.v1",
        "version": "0.1.2-gllm",
        "timestamp": timestamp,
        "decision": decision,
        "changed_paths": paths,
        "allowed_effects": allowed_effects,
        "violations": violations,
        "allowed_patterns": allowed,
        "forbidden_patterns": forbidden,
        "authority": {"broad_authority": False, "canonical_authority": False},
    }
    write_json(Path(args.report), report)
    append_jsonl(Path(args.receipt), {"schema": "stegverse.agent_boundary_receipt.v1", "version": "0.1.2-gllm", "timestamp": timestamp, "decision": decision, "violation_count": len(violations), "report_path": args.report, "broad_authority": False})
    print(json.dumps(report, indent=2))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
