#!/usr/bin/env python3
"""Append machine-readable LLM changelog entries for governed collaboration work."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CHANGELOG = "agent_history/llm_changelog.jsonl"
DEFAULT_VERSION_STATE = "agent_history/version_state.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() and path.is_file() else ""


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True) + "\n")


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"schema": "stegverse.llm_version_state.v1", "capability": "governed_collaboration", "current_version": "", "versions": [], "providers": {}}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Record an LLM or human-mediated change event.")
    p.add_argument("--provider", required=True, choices=["openai", "claude", "coordinator", "human"])
    p.add_argument("--conversation", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--change-type", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--files", nargs="*", default=[])
    p.add_argument("--decision", default="RECORDED")
    p.add_argument("--authority", default="candidate_evidence_only")
    p.add_argument("--changelog", default=DEFAULT_CHANGELOG)
    p.add_argument("--version-state", default=DEFAULT_VERSION_STATE)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    timestamp = utc_now()
    files = [{"path": f, "sha256": sha256_file(Path(f)), "exists": Path(f).exists()} for f in args.files]
    entry = {
        "schema": "stegverse.llm_changelog_entry.v1",
        "timestamp": timestamp,
        "version": args.version,
        "provider": args.provider,
        "conversation": args.conversation,
        "change_type": args.change_type,
        "summary": args.summary,
        "files": files,
        "decision": args.decision,
        "authority": args.authority,
        "broad_authority": False,
    }
    append_jsonl(Path(args.changelog), entry)

    state_path = Path(args.version_state)
    state = load_state(state_path)
    state["current_version"] = args.version
    state["updated_utc"] = timestamp
    state["absolute_directive"] = "No broad authority is ever admissible under Transition Table, AE, or GCAT/BCAT enforcement."
    state.setdefault("providers", {}).setdefault(args.provider, {})["last_change"] = entry

    versions = state.setdefault("versions", [])
    if not any(v.get("version") == args.version for v in versions):
        versions.append({"version": args.version, "timestamp": timestamp, "summary": args.summary, "changelog": args.changelog})

    save_state(state_path, state)
    print(json.dumps(entry, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
