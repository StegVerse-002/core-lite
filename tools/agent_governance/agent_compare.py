#!/usr/bin/env python3
"""Non-authoritative comparison gate for Claude/OpenAI collaboration outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.2-gllm"

DEFAULT_OPENAI_OUTPUT = "outputs/chatgpt_response.md"
DEFAULT_CLAUDE_OUTPUT = "outputs/claude_response.md"
DEFAULT_THREAD_OUTPUT = "outputs/thread.md"
DEFAULT_REPORT = "reports/current/agent_comparison_report.json"
DEFAULT_RECEIPT = "receipts/current/agent_comparison_receipt.jsonl"

RISK_TERMS = ["secret", "token", "password", "private key", "api key", "credential", "delete", "remove workflow", "disable", "bypass", "skip permissions", "dangerously", "force push", "chmod 777", "curl | bash", "eval(", "exec(", "broad authority", "unilateral authority"]
HIGH_RISK_PATH_PATTERNS = [".github/workflows/", ".env", "secrets/", "credentials/", "tracking/stegverse-002/stage_map.json", "dist/master-records/"]
REQUIRED_SECTIONS = ["Current State Assessment", "Directive Alignment", "Next Collaboration Primitive", "Proposed Implementation", "Authority Boundaries", "Receipts and Version History", "Risks & Dependencies", "Confidence"]


@dataclass
class ProviderArtifact:
    provider: str
    output_path: str
    exists: bool
    sha256: str
    bytes: int
    mentioned_paths: list[str]
    mentioned_risk_terms: list[str]
    required_sections_present: dict[str, bool]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def mentioned_risks(text: str) -> list[str]:
    lowered = text.lower()
    return sorted({term for term in RISK_TERMS if term in lowered})


def extract_paths(text: str) -> list[str]:
    paths = set()
    for token in re.findall(r"`([^`]+)`", text):
        token = token.strip()
        if "\n" in token or len(token) > 180:
            continue
        if "/" in token or token.endswith((".py", ".yml", ".yaml", ".md", ".json", ".jsonl")):
            paths.add(token)
    return sorted(paths)


def path_is_high_risk(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(normalized.startswith(pattern) or pattern in normalized for pattern in HIGH_RISK_PATH_PATTERNS)


def section_present(text: str, section: str) -> bool:
    return re.search(rf"^##\s+{re.escape(section)}\s*$", text, re.MULTILINE) is not None


def collect_provider(provider: str, output_path: Path) -> ProviderArtifact:
    text = read_text(output_path)
    return ProviderArtifact(provider, str(output_path), output_path.exists(), sha256_text(text) if text else "", len(text.encode("utf-8")), extract_paths(text), mentioned_risks(text), {s: section_present(text, s) for s in REQUIRED_SECTIONS})


def overlap_ratio(a: list[str], b: list[str]) -> float:
    set_a, set_b = set(a), set(b)
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def classify(openai: ProviderArtifact, claude: ProviderArtifact, thread_text: str) -> tuple[str, str, dict]:
    high_risk_paths = sorted({p for p in openai.mentioned_paths + claude.mentioned_paths if path_is_high_risk(p)})
    risk_terms = sorted(set(openai.mentioned_risk_terms + claude.mentioned_risk_terms))
    missing = []
    if not openai.exists:
        missing.append("openai")
    if not claude.exists:
        missing.append("claude")
    shared_sections = [s for s in REQUIRED_SECTIONS if openai.required_sections_present.get(s) and claude.required_sections_present.get(s)]
    analysis = {
        "path_overlap_ratio": overlap_ratio(openai.mentioned_paths, claude.mentioned_paths),
        "high_risk_paths": high_risk_paths,
        "risk_terms": risk_terms,
        "missing_providers": missing,
        "shared_sections": shared_sections,
        "thread_present": bool(thread_text.strip()),
    }
    if "broad authority" in risk_terms or "unilateral authority" in risk_terms:
        return "REVIEW_REQUIRED", "Provider outputs mention broad/unilateral authority; human review required even if framed as denied.", analysis
    if high_risk_paths:
        return "FAIL_CLOSED", "Provider outputs mention high-risk paths that require review.", analysis
    if missing:
        return "REVIEW_REQUIRED", "One or more provider outputs are missing.", analysis
    if len(shared_sections) < 3:
        return "REVIEW_REQUIRED", "Provider outputs do not contain enough shared structure.", analysis
    return "ALLOW_CANDIDATE_EVIDENCE", "LLM-LLM collaboration evidence is complete enough for review.", analysis


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare governed OpenAI and Claude collaboration outputs.")
    parser.add_argument("--openai-output", default=DEFAULT_OPENAI_OUTPUT)
    parser.add_argument("--claude-output", default=DEFAULT_CLAUDE_OUTPUT)
    parser.add_argument("--thread-output", default=DEFAULT_THREAD_OUTPUT)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    parser.add_argument("--receipt", default=DEFAULT_RECEIPT)
    parser.add_argument("--fail-on-high", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    openai = collect_provider("openai", Path(args.openai_output))
    claude = collect_provider("claude", Path(args.claude_output))
    thread_text = read_text(Path(args.thread_output))
    decision, basis, analysis = classify(openai, claude, thread_text)
    timestamp = utc_now()
    report = {
        "schema": "stegverse.agent_comparison_report.v1",
        "version": VERSION,
        "timestamp": timestamp,
        "decision": decision,
        "basis": basis,
        "providers": {"openai": asdict(openai), "claude": asdict(claude)},
        "analysis": analysis,
        "authority": {"mode": "candidate_evidence_only", "canonical_authority": False, "may_bind_repo_state": False, "broad_authority": False},
    }
    write_json(Path(args.report), report)
    append_jsonl(Path(args.receipt), {"schema": "stegverse.agent_comparison_receipt.v1", "version": VERSION, "timestamp": timestamp, "decision": decision, "basis": basis, "report_path": args.report, "openai_sha256": openai.sha256, "claude_sha256": claude.sha256, "thread_sha256": sha256_text(thread_text) if thread_text else "", "broad_authority": False})
    print(json.dumps(report, indent=2))
    return 1 if args.fail_on_high and decision == "FAIL_CLOSED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
