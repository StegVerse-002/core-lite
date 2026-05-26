#!/usr/bin/env python3
"""
scripts/merge_outputs.py

StegVerse-002 governed collaboration capability v0.1.2-gllm.

Deterministic synthesis of OpenAI and Claude proposal outputs.
Also reads and updates machine-readable LLM changelog/version state.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "0.1.2-gllm"

OUTPUTS_DIR = Path("outputs")
REPORTS_DIR = Path("reports/current")
RECEIPTS_DIR = Path("receipts/current")
AGENT_HISTORY_DIR = Path("agent_history")

CLAUDE_OUTPUT = OUTPUTS_DIR / "claude_response.md"
OPENAI_OUTPUT = OUTPUTS_DIR / "chatgpt_response.md"
THREAD_OUTPUT = OUTPUTS_DIR / "thread.md"
REPORT_OUTPUT = REPORTS_DIR / "agent_coordination_report.json"
RECEIPT_OUTPUT = RECEIPTS_DIR / "agent_coordination_receipt.jsonl"
CHANGELOG_FILE = AGENT_HISTORY_DIR / "llm_changelog.jsonl"
VERSION_STATE_FILE = AGENT_HISTORY_DIR / "version_state.json"

SECTION_NAMES = [
    "Current State Assessment",
    "Directive Alignment",
    "Next Collaboration Primitive",
    "Proposed Implementation",
    "Authority Boundaries",
    "Receipts and Version History",
    "Risks & Dependencies",
    "Confidence",
]

RISK_TERMS = ["secret", "token", "api key", "password", "private key", "dangerously", "bypass", "delete", "remove workflow", "force push", "chmod 777", "broad authority", "unilateral authority"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_dirs() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    AGENT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def extract_section(text: str, title: str) -> str:
    match = re.search(rf"^##\s+{re.escape(title)}\s*$([\s\S]*?)(?=^##\s+|\Z)", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def find_mentions(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    return sorted({term for term in terms if term in lowered})


def extract_paths(text: str) -> list[str]:
    candidates = set()
    for token in re.findall(r"`([^`]+)`", text):
        cleaned = token.strip()
        if "\n" not in cleaned and len(cleaned) < 180 and ("/" in cleaned or cleaned.endswith((".py", ".yml", ".yaml", ".md", ".json", ".jsonl"))):
            candidates.add(cleaned)
    return sorted(candidates)


def provider_summary(name: str, path: Path, text: str) -> dict[str, Any]:
    return {
        "provider": name,
        "path": str(path),
        "exists": path.exists(),
        "bytes": len(text.encode("utf-8")),
        "sha256": sha256_text(text) if text else "",
        "sections_present": {section: bool(extract_section(text, section)) for section in SECTION_NAMES},
        "mentioned_paths": extract_paths(text),
        "risk_terms": find_mentions(text, RISK_TERMS),
    }


def load_version_state() -> dict[str, Any]:
    if VERSION_STATE_FILE.exists():
        try:
            return json.loads(VERSION_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "schema": "stegverse.llm_version_state.v1",
        "capability": "governed_collaboration",
        "current_version": VERSION,
        "versions": [],
        "providers": {"openai": {}, "claude": {}, "coordinator": {}, "human": {}},
    }


def append_changelog(entry: dict[str, Any]) -> None:
    with CHANGELOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def recent_changelog(max_lines: int = 20) -> list[dict[str, Any]]:
    if not CHANGELOG_FILE.exists():
        return []
    entries = []
    for line in CHANGELOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]:
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries


def update_version_state(report: dict[str, Any]) -> None:
    state = load_version_state()
    state["schema"] = "stegverse.llm_version_state.v1"
    state["capability"] = "governed_collaboration"
    state["current_version"] = VERSION
    state["updated_utc"] = report["timestamp"]
    state["absolute_directive"] = "No broad authority is ever admissible under Transition Table, AE, or GCAT/BCAT enforcement."

    version_entry = {
        "version": VERSION,
        "timestamp": report["timestamp"],
        "decision": report["decision"],
        "basis": report["basis"],
        "llm_change_log": "agent_history/llm_changelog.jsonl",
        "coordination_report": "reports/current/agent_coordination_report.json",
        "comparison_report": "reports/current/agent_comparison_report.json",
        "boundary_report": "reports/current/agent_boundary_report.json",
        "thread": "outputs/thread.md",
    }

    versions = state.get("versions", [])
    if not any(v.get("version") == VERSION for v in versions):
        versions.append(version_entry)
    else:
        versions = [version_entry if v.get("version") == VERSION else v for v in versions]
    state["versions"] = versions

    providers = state.setdefault("providers", {})
    providers.setdefault("openai", {})["last_output_sha256"] = report["providers"]["openai"]["sha256"]
    providers.setdefault("claude", {})["last_output_sha256"] = report["providers"]["claude"]["sha256"]
    providers.setdefault("coordinator", {})["last_thread_sha256"] = report.get("thread_sha256", "")

    VERSION_STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def synthesize_thread(claude: str, openai: str, report: dict[str, Any]) -> str:
    lines = [
        "# StegVerse-002 Governed Collaboration Thread",
        "",
        f"Version: `{VERSION}`",
        f"Generated: `{report['timestamp']}`",
        "",
        "## Absolute Directive",
        "",
        "There is never a valid StegVerse state in which any entity receives broad authority.",
        "",
        "Authority must always be scoped, staged, explicit, receipted, bounded by transition class, checked at the commit/execution boundary, recoverable, containable, and denied by default unless specifically granted.",
        "",
        "Rigel founder/user enrollment and Beta_Orionis counterpart enablement are future transitions, not current implementation targets.",
        "",
        "## Governance Status",
        "",
        "This thread is candidate evidence only. It does not approve, deploy, or bind repository state.",
        "",
        f"- Coordination decision: `{report['decision']}`",
        f"- Claude output present: `{report['providers']['claude']['exists']}`",
        f"- OpenAI output present: `{report['providers']['openai']['exists']}`",
        f"- Machine changelog: `agent_history/llm_changelog.jsonl`",
        f"- Version state: `agent_history/version_state.json`",
        "",
        "## Deterministic Comparison Summary",
        "",
        f"- Shared declared sections detected: `{', '.join(report['shared_sections']) if report['shared_sections'] else 'none'}`",
        f"- Claude mentioned paths: `{len(report['providers']['claude']['mentioned_paths'])}`",
        f"- OpenAI mentioned paths: `{len(report['providers']['openai']['mentioned_paths'])}`",
        f"- Risk terms detected: `{', '.join(report['risk_terms']) if report['risk_terms'] else 'none'}`",
        "",
        "## Recent Machine-Readable Changelog Entries",
        "",
        "```jsonl",
    ]
    entries = report.get("recent_changelog", [])
    if entries:
        for entry in entries:
            lines.append(json.dumps(entry, sort_keys=True))
    else:
        lines.append("[none]")
    lines += [
        "```",
        "",
        "## Claude Output",
        "",
        claude.strip() if claude.strip() else "_No Claude output present._",
        "",
        "---",
        "",
        "## OpenAI Output",
        "",
        openai.strip() if openai.strip() else "_No OpenAI output present._",
        "",
        "---",
        "",
        "## Coordination Receipt Summary",
        "",
        "```text",
        "reports/current/agent_coordination_report.json",
        "receipts/current/agent_coordination_receipt.jsonl",
        "agent_history/llm_changelog.jsonl",
        "agent_history/version_state.json",
        "```",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ensure_dirs()
    claude_text = read_text(CLAUDE_OUTPUT)
    openai_text = read_text(OPENAI_OUTPUT)

    claude_summary = provider_summary("claude", CLAUDE_OUTPUT, claude_text)
    openai_summary = provider_summary("openai", OPENAI_OUTPUT, openai_text)

    shared_sections = [s for s in SECTION_NAMES if claude_summary["sections_present"].get(s) and openai_summary["sections_present"].get(s)]
    all_risk_terms = sorted(set(claude_summary["risk_terms"] + openai_summary["risk_terms"]))

    if not claude_text and not openai_text:
        decision = "NO_PROVIDER_OUTPUT"
        basis = "Neither provider output was present."
    elif not claude_text or not openai_text:
        decision = "PARTIAL_PROVIDER_OUTPUT"
        basis = "Only one provider output was present; review is still possible."
    else:
        decision = "COORDINATION_THREAD_READY"
        basis = "Both provider outputs were present and merged into candidate evidence."

    report = {
        "schema": "stegverse.agent_coordination_report.v1",
        "version": VERSION,
        "timestamp": utc_now(),
        "decision": decision,
        "basis": basis,
        "providers": {"claude": claude_summary, "openai": openai_summary},
        "shared_sections": shared_sections,
        "risk_terms": all_risk_terms,
        "recent_changelog": recent_changelog(),
        "thread_path": "outputs/thread.md",
        "authority": {"mode": "propose_only", "canonical_authority": False, "may_bind_repo_state": False, "broad_authority": False},
    }

    thread = synthesize_thread(claude_text, openai_text, report)
    report["thread_sha256"] = sha256_text(thread)

    THREAD_OUTPUT.write_text(thread, encoding="utf-8")
    REPORT_OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    receipt = {
        "schema": "stegverse.agent_coordination_receipt.v1",
        "version": VERSION,
        "timestamp": report["timestamp"],
        "decision": decision,
        "basis": basis,
        "thread_path": "outputs/thread.md",
        "thread_sha256": sha256_text(thread),
        "report_path": "reports/current/agent_coordination_report.json",
        "claude_sha256": claude_summary["sha256"],
        "openai_sha256": openai_summary["sha256"],
        "canonical_authority": False,
        "broad_authority": False,
    }
    with RECEIPT_OUTPUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(receipt, sort_keys=True) + "\n")

    append_changelog({
        "schema": "stegverse.llm_changelog_entry.v1",
        "timestamp": report["timestamp"],
        "version": VERSION,
        "provider": "coordinator",
        "conversation": "workflow",
        "change_type": "coordination_synthesis",
        "summary": basis,
        "files": ["outputs/thread.md", "reports/current/agent_coordination_report.json", "receipts/current/agent_coordination_receipt.jsonl"],
        "output_hashes": {"thread": sha256_text(thread), "claude": claude_summary["sha256"], "openai": openai_summary["sha256"]},
        "authority": "candidate_evidence_only",
    })

    update_version_state(report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
