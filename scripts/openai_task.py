#!/usr/bin/env python3
"""
scripts/openai_task.py

StegVerse-002 governed collaboration capability v0.1.2-gllm.

OpenAI proposal agent. Propose-only. No repo mutation outside outputs/reports/receipts.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "0.1.2-gllm"

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
OUTPUTS_DIR = REPO_ROOT / "outputs"
REPORTS_DIR = REPO_ROOT / "reports" / "current"
RECEIPTS_DIR = REPO_ROOT / "receipts" / "current"

OUTPUT_FILE = OUTPUTS_DIR / "chatgpt_response.md"
SUMMARY_FILE = REPORTS_DIR / "openai_task_summary.json"
RECEIPT_FILE = RECEIPTS_DIR / "openai_task_receipt.jsonl"

TASK_FILE = REPO_ROOT / "task.md"
README_FILE = REPO_ROOT / "README.md"
CLAUDE_CONTEXT_FILE = REPO_ROOT / "CLAUDE.md"
CHANGELOG_FILE = REPO_ROOT / "agent_history" / "llm_changelog.jsonl"
VERSION_STATE_FILE = REPO_ROOT / "agent_history" / "version_state.json"
DIRECTIVE_FILE = REPO_ROOT / "governance" / "directives" / "no_broad_authority.directive.json"

MAX_FILE_CHARS = 12000
MAX_TREE_LINES = 800
MAX_CHANGELOG_LINES = 60


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_file(path: Path, max_chars: int = MAX_FILE_CHARS) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"[Could not read {path}: {exc}]"
    return content[:max_chars] + "\n\n[...truncated...]" if len(content) > max_chars else content


def read_changelog() -> str:
    if not CHANGELOG_FILE.exists():
        return "[No LLM changelog present yet.]"
    return "\n".join(CHANGELOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()[-MAX_CHANGELOG_LINES:])


def scan_repo_structure(root: Path, max_depth: int = 4) -> str:
    skip_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", "dist"}
    lines: list[str] = []

    def walk(path: Path, depth: int) -> None:
        if depth > max_depth or len(lines) >= MAX_TREE_LINES:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception:
            return
        for entry in entries:
            if len(lines) >= MAX_TREE_LINES:
                return
            if entry.name in skip_dirs:
                continue
            if entry.name.startswith(".") and entry.name not in {".github"}:
                continue
            indent = "  " * depth
            if entry.is_dir():
                lines.append(f"{indent}{entry.name}/")
                walk(entry, depth + 1)
            else:
                lines.append(f"{indent}{entry.name}")

    walk(root, 0)
    if len(lines) >= MAX_TREE_LINES:
        lines.append("[...tree truncated...]")
    return "\n".join(lines)


def selected_provider() -> str:
    provider = os.environ.get("AGENT_PROVIDER", "both").strip().lower()
    return provider if provider in {"none", "openai", "claude", "both"} else "both"


def write_output(text: str, *, status: str, model: str = "", error: str = "") -> None:
    OUTPUT_FILE.write_text(text.rstrip() + "\n", encoding="utf-8")
    summary = {
        "schema": "stegverse.openai_task_summary.v1",
        "version": VERSION,
        "timestamp": utc_now(),
        "provider": "openai",
        "status": status,
        "mode": "propose_only",
        "model": model,
        "output_path": "outputs/chatgpt_response.md",
        "output_sha256": sha256_text(text),
        "error": error,
        "authority": "candidate_evidence_only",
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "schema": "stegverse.openai_task_receipt.v1",
        "version": VERSION,
        "timestamp": summary["timestamp"],
        "provider": "openai",
        "decision": "PROPOSED" if status == "completed" else "SKIPPED_OR_FAILED",
        "basis": "OpenAI proposal agent writes candidate analysis only; no broad authority is admissible.",
        "output_path": "outputs/chatgpt_response.md",
        "output_sha256": summary["output_sha256"],
        "status": status,
    }
    with RECEIPT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(receipt, sort_keys=True) + "\n")


def build_prompt(task: str, readme: str, claude_context: str, structure: str, changelog: str, version_state: str, directive: str) -> list[dict[str, str]]:
    system = """You are the OpenAI proposal agent inside StegVerse-002/core-lite.

Authority boundary:
- PROPOSE ONLY.
- Do not claim that you changed files.
- Do not approve, deploy, or bind anything.
- Recommend exact files, code, commands, and test plan.
- Respect task.md constraints.
- Use the LLM changelog/version state as continuity context.
- Treat the no-broad-authority directive as absolute.
- Your output will be compared with Claude output by deterministic synthesis.

Core invariant:
There is never a valid StegVerse state in which any entity receives broad authority.
All authority must be scoped, staged, explicit, receipted, bounded by transition class,
checked at commit/execution boundary, recoverable, containable, and denied by default
unless specifically granted.
"""
    user = f"""# Governed Collaboration Task Packet

## no_broad_authority.directive.json

{directive}

## task.md

{task}

## LLM Version State

{version_state}

## Recent Machine-Readable LLM Changelog

{changelog}

## README.md

{readme}

## CLAUDE.md

{claude_context}

## Repository Structure

{structure}

## Required Output Format

# OpenAI — Governed Collaboration Proposal
## Current State Assessment
## Directive Alignment
## Next Collaboration Primitive
## Proposed Implementation
## Authority Boundaries
## Receipts and Version History
## Risks & Dependencies
## Confidence
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def extract_response_text(body: dict[str, Any]) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"].strip()
    parts: list[str] = []
    for item in body.get("output", []) or []:
        for content in item.get("content", []) or []:
            text = content.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n\n".join(parts).strip()


def call_openai_responses(messages: list[dict[str, str]], model: str, api_key: str) -> str:
    payload = {"model": model, "input": messages, "temperature": 0.2, "max_output_tokens": 3000}
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return extract_response_text(body) or "# OpenAI — Empty Response\n\nThe OpenAI API returned no extractable text."


def main() -> int:
    ensure_dirs()
    provider = selected_provider()
    if provider not in {"openai", "both"}:
        write_output(f"# OpenAI — Skipped\n\nAGENT_PROVIDER={provider}; OpenAI was not selected for this run.\n", status="skipped")
        return 0
    if not TASK_FILE.exists():
        write_output("# OpenAI — Skipped\n\nNo task.md was present. No OpenAI proposal was generated.\n", status="skipped")
        return 0
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        write_output("# OpenAI — Skipped\n\nOPENAI_API_KEY is not configured.\n", status="skipped")
        return 0

    model = os.environ.get("OPENAI_MODEL", "gpt-4o").strip() or "gpt-4o"
    messages = build_prompt(
        read_file(TASK_FILE),
        read_file(README_FILE) if README_FILE.exists() else "[README.md not found]",
        read_file(CLAUDE_CONTEXT_FILE) if CLAUDE_CONTEXT_FILE.exists() else "[CLAUDE.md not found]",
        scan_repo_structure(REPO_ROOT),
        read_changelog(),
        read_file(VERSION_STATE_FILE, 6000) if VERSION_STATE_FILE.exists() else "[No version_state.json present yet.]",
        read_file(DIRECTIVE_FILE, 6000) if DIRECTIVE_FILE.exists() else "[No no_broad_authority.directive.json present yet.]",
    )
    try:
        output = call_openai_responses(messages, model, api_key)
        write_output(output, status="completed", model=model)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        write_output(f"# OpenAI — API Error\n\nHTTP {exc.code}\n\n```text\n{error_body}\n```\n", status="api_error", model=model, error=error_body)
    except Exception as exc:
        write_output(f"# OpenAI — Error\n\n```text\n{exc}\n```\n", status="error", model=model, error=str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
