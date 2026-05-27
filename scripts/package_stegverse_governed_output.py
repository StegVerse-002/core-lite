#!/usr/bin/env python3
"""
package_stegverse_governed_output.py

Builds one StegVerse-authored governed output artifact from provider evidence.
LLM outputs remain evidence; StegVerse is the only official output authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "0.1.0-sv002-output-authority"

PRIMARY_MD = Path("outputs/stegverse_output.md")
PRIMARY_JSON = Path("outputs/stegverse_output.json")
REPORT_PATH = Path("reports/current/stegverse_output_report.json")
RECEIPT_PATH = Path("receipts/current/stegverse_output_receipt.jsonl")
ARTIFACT_PATH = Path("dist/run_artifacts/stegverse-governed-output.zip")

EVIDENCE_FILES = [
    Path("outputs/thread.md"),
    Path("outputs/chatgpt_response.md"),
    Path("outputs/claude_response.md"),
    Path("reports/current/agent_coordination_report.json"),
    Path("reports/current/agent_comparison_report.json"),
    Path("reports/current/agent_boundary_report.json"),
    Path("receipts/current/agent_coordination_receipt.jsonl"),
    Path("receipts/current/agent_comparison_receipt.jsonl"),
    Path("receipts/current/agent_boundary_receipt.jsonl"),
    Path("agent_history/llm_changelog.jsonl"),
    Path("agent_history/version_state.json"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def ensure_dirs() -> None:
    for path in [PRIMARY_MD, PRIMARY_JSON, REPORT_PATH, RECEIPT_PATH, ARTIFACT_PATH]:
        path.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(read_text(path)) if path.exists() else {}
    except Exception:
        return {}


def evidence_record(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": str(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
        "sha256": sha256_file(path) if exists else "",
        "authority": "candidate_evidence_only",
    }


def choose_basis(coordination_report: dict[str, Any]) -> str:
    decision = coordination_report.get("decision", "UNKNOWN")
    if decision == "COORDINATION_THREAD_READY":
        return "Provider evidence was merged by StegVerse into a governed candidate output."
    if decision == "PARTIAL_PROVIDER_OUTPUT":
        return "StegVerse produced a governed candidate from partial provider evidence; review remains required."
    if decision == "NO_PROVIDER_OUTPUT":
        return "No provider evidence was present; StegVerse produced a no-output governance record."
    return "StegVerse produced a governed output record from available evidence."


def build_markdown(report: dict[str, Any], thread_text: str) -> str:
    evidence_rows = []
    for item in report["evidence"]:
        status = "present" if item["exists"] else "missing"
        evidence_rows.append(f"- `{item['path']}` — {status} — `{item['sha256'] or 'no-hash'}`")

    primary_summary = report["summary"]
    lines = [
        "# StegVerse Governed Output",
        "",
        f"Version: `{report['version']}`",
        f"Generated: `{report['timestamp']}`",
        f"Decision: `{report['decision']}`",
        "",
        "## Output Authority",
        "",
        "This is the only official run-visible output for this governed coordination event.",
        "",
        "LLM provider responses are retained only as candidate evidence. They are not system voice, not approval, not publication, and not authority to bind repository state.",
        "",
        "## StegVerse Summary",
        "",
        primary_summary,
        "",
        "## Governing Boundary",
        "",
        "- No LLM publishes.",
        "- No LLM becomes the system voice.",
        "- No LLM output becomes consequence.",
        "- StegVerse synthesizes, receipts, and exposes one governed candidate output.",
        "- Human/operator approval is required before consequence-bearing execution.",
        "",
        "## Evidence Retained",
        "",
        *evidence_rows,
        "",
        "## StegVerse Synthesis Source",
        "",
    ]
    if thread_text.strip():
        lines.extend([thread_text.strip(), ""])
    else:
        lines.extend(["No coordination thread was present. The governed output is a record-only candidate.", ""])
    lines.extend([
        "## Receipts",
        "",
        "```text",
        "reports/current/stegverse_output_report.json",
        "receipts/current/stegverse_output_receipt.jsonl",
        "dist/run_artifacts/stegverse-governed-output.zip",
        "```",
        "",
    ])
    return "\n".join(lines)


def write_zip(report: dict[str, Any]) -> None:
    with zipfile.ZipFile(ARTIFACT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path, arcname in [
            (PRIMARY_MD, "STEGVERSE_OUTPUT.md"),
            (PRIMARY_JSON, "stegverse_output.json"),
            (REPORT_PATH, "reports/stegverse_output_report.json"),
            (RECEIPT_PATH, "receipts/stegverse_output_receipt.jsonl"),
        ]:
            if path.exists():
                z.write(path, arcname)
        for item in report["evidence"]:
            p = Path(item["path"])
            if p.exists():
                z.write(p, "evidence/" + str(p).replace("\\", "/"))


def append_receipt(report: dict[str, Any]) -> dict[str, Any]:
    previous_hash = ""
    if RECEIPT_PATH.exists():
        for line in RECEIPT_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                previous_hash = json.loads(line).get("receipt_hash", previous_hash)
            except Exception:
                continue

    receipt = {
        "schema": "stegverse.output_authority_receipt.v1",
        "version": VERSION,
        "timestamp": report["timestamp"],
        "actor": "StegVerse-002",
        "gate": "stegverse_output_authority",
        "decision": report["decision"],
        "basis": report["basis"],
        "primary_output": str(PRIMARY_MD),
        "primary_output_sha256": report["primary_output_sha256"],
        "artifact_path": str(ARTIFACT_PATH),
        "artifact_sha256": sha256_file(ARTIFACT_PATH) if ARTIFACT_PATH.exists() else "",
        "llm_outputs_authority": "candidate_evidence_only",
        "stegverse_output_authority": True,
        "human_required_for_consequence": True,
        "previous_receipt_hash": previous_hash,
    }
    receipt_payload = json.dumps(receipt, sort_keys=True)
    receipt["receipt_hash"] = sha256_text(receipt_payload)
    with RECEIPT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(receipt, sort_keys=True) + "\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(prog="package_stegverse_governed_output")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--decision", default="STEGVERSE_OUTPUT_READY")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    if repo_root != Path("."):
        import os
        os.chdir(repo_root)

    ensure_dirs()
    coordination_report = load_json(Path("reports/current/agent_coordination_report.json"))
    thread_text = read_text(Path("outputs/thread.md"))
    evidence = [evidence_record(path) for path in EVIDENCE_FILES]
    basis = choose_basis(coordination_report)

    report: dict[str, Any] = {
        "schema": "stegverse.output_authority_report.v1",
        "version": VERSION,
        "timestamp": utc_now(),
        "entity": "StegVerse-002",
        "decision": args.decision,
        "basis": basis,
        "summary": coordination_report.get("basis") or basis,
        "authority": {
            "official_output_authority": "StegVerse",
            "llm_provider_outputs": "candidate_evidence_only",
            "may_bind_repo_state": False,
            "may_publish_external_response": False,
            "human_required_for_consequence": True,
        },
        "evidence": evidence,
    }

    markdown = build_markdown(report, thread_text)
    report["primary_output_path"] = str(PRIMARY_MD)
    report["primary_output_sha256"] = sha256_text(markdown)

    PRIMARY_MD.write_text(markdown, encoding="utf-8")
    PRIMARY_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_zip(report)
    receipt = append_receipt(report)

    report["receipt"] = receipt
    report["artifact_path"] = str(ARTIFACT_PATH)
    report["artifact_sha256"] = sha256_file(ARTIFACT_PATH)
    PRIMARY_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
