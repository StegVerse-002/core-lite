#!/usr/bin/env python3
"""SV002 M10.5 Adapter Candidate Sandbox Executor.

This closes the existing adapter loop inside core-lite-intake:

task.md
→ OpenAI / Anthropic candidate artifacts
→ candidate extraction
→ sandbox test
→ M11 apply gate
→ apply only if the binding gate returns ALLOW
→ otherwise deny/defer with receipts

Provider outputs are never trusted. A provider output is only machine-actionable
when it contains this explicit fenced JSON packet:

```json
{
  "schema": "stegverse.candidate_patch.v1",
  "candidate_id": "short-id",
  "provider": "openai",
  "description": "Full-file replacement candidate",
  "transition_class": "documentation",
  "authority_ref": "SV002-M10.5/scoped-candidate",
  "policy_ref": "triad/default-deny/no-broad-authority",
  "files": [
    {
      "path": "docs/example.md",
      "operation": "write",
      "content": "# Full file contents\n"
    }
  ]
}
```
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

REPORT_PATH = Path("reports/current/adapter_candidate_sandbox_report.json")
RECEIPT_PATH = Path("receipts/current/adapter_candidate_sandbox_receipt.jsonl")
OUTPUT_PATH = Path("outputs/adapter_candidate_sandbox.md")
ARTIFACT_PATH = Path("dist/run_artifacts/adapter-candidate-sandbox.zip")

PATCH_SCHEMA = "stegverse.candidate_patch.v1"
ALLOWED_TRANSITION_CLASSES = {"tooling", "schema", "policy", "governance", "repair", "documentation"}
DENIED_TARGET_PATHS = {"README.md", "bundle_manifest.json"}
DENIED_PREFIXES = {".github/", ".git/"}
BROAD_AUTHORITY_PATTERNS = {"*", "all", "root", "admin", "superuser", "unrestricted"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def append_receipt(report: dict[str, Any]) -> str:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "stegverse.adapter_candidate_sandbox_receipt.v1",
        "timestamp": utc_now(),
        "decision": report["decision"],
        "selected_candidate_id": report.get("selected_candidate_id"),
        "candidate_count": len(report.get("candidates", [])),
        "applied_files": report.get("applied_files", []),
        "report_hash": sha256_bytes(canonical(report).encode("utf-8")),
    }
    line = canonical(payload) + "\n"
    with RECEIPT_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line)
    return sha256_bytes(line.encode("utf-8"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def extract_json_blocks(text: str) -> list[str]:
    return re.findall(r"```(?:json|JSON)\s*(\{.*?\})\s*```", text, flags=re.DOTALL)


def normalize_candidate(raw: dict[str, Any], provider_hint: str) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if raw.get("schema") != PATCH_SCHEMA:
        return None, [f"unsupported_schema:{raw.get('schema')}"]

    candidate = dict(raw)
    candidate.setdefault("provider", provider_hint)
    candidate.setdefault("candidate_id", f"{provider_hint}-candidate")
    candidate.setdefault("transition_class", "tooling")
    candidate.setdefault("files", [])

    if candidate.get("transition_class") not in ALLOWED_TRANSITION_CLASSES:
        errors.append(f"transition_class_denied:{candidate.get('transition_class')}")

    authority = str(candidate.get("authority_ref", "")).lower().strip()
    policy = str(candidate.get("policy_ref", "")).strip()
    if not authority:
        errors.append("authority_ref_missing")
    if not policy:
        errors.append("policy_ref_missing")
    if any(pattern in authority for pattern in BROAD_AUTHORITY_PATTERNS):
        errors.append("broad_authority_requested")

    files = candidate.get("files")
    if not isinstance(files, list) or not files:
        errors.append("files_missing")
        return candidate, errors

    for item in files:
        path = str(item.get("path", ""))
        operation = item.get("operation", "write")
        if not path:
            errors.append("file_path_missing")
            continue
        if path in DENIED_TARGET_PATHS:
            errors.append(f"target_path_denied:{path}")
        if any(path.startswith(prefix) for prefix in DENIED_PREFIXES):
            errors.append(f"target_prefix_denied:{path}")
        if operation not in {"write", "create", "update"}:
            errors.append(f"operation_denied:{path}:{operation}")
        if "content" not in item:
            errors.append(f"content_missing:{path}")

    return candidate, errors


def collect_candidates(provider_outputs: dict[str, Path]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for provider, path in provider_outputs.items():
        text = load_text(path)
        for index, block in enumerate(extract_json_blocks(text), start=1):
            try:
                raw = json.loads(block)
            except Exception as exc:
                candidates.append({
                    "provider": provider,
                    "candidate_id": f"{provider}-invalid-json-{index}",
                    "valid_packet": False,
                    "errors": [f"json_parse_failed:{exc}"],
                    "decision": "DENY_CANDIDATE",
                })
                continue

            normalized, errors = normalize_candidate(raw, provider)
            if normalized is None:
                candidates.append({
                    "provider": provider,
                    "candidate_id": f"{provider}-unsupported-{index}",
                    "valid_packet": False,
                    "errors": errors,
                    "decision": "DENY_CANDIDATE",
                })
            else:
                normalized["valid_packet"] = not errors
                normalized["errors"] = errors
                normalized["decision"] = "CANDIDATE_PACKET_ACCEPTED" if not errors else "DENY_CANDIDATE"
                candidates.append(normalized)
    return candidates


def copy_repo_to_sandbox(repo_root: Path, sandbox: Path) -> None:
    ignored_names = {".git", "node_modules", "__pycache__", ".pytest_cache"}
    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {name for name in names if name in ignored_names}
    shutil.copytree(repo_root, sandbox, ignore=ignore)


def apply_candidate_files(candidate: dict[str, Any], repo_root: Path) -> list[str]:
    applied: list[str] = []
    for item in candidate.get("files", []):
        rel = Path(str(item["path"]))
        target = (repo_root / rel).resolve()
        if not str(target).startswith(str(repo_root.resolve())):
            raise RuntimeError(f"path_escape_denied:{rel.as_posix()}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(item.get("content", "")), encoding="utf-8")
        applied.append(rel.as_posix())
    return applied


def run_cmd(args: list[str], cwd: Path, timeout: int = 180) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
        return {
            "args": args,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:] if proc.stdout else "",
            "stderr": proc.stderr[-4000:] if proc.stderr else "",
        }
    except subprocess.TimeoutExpired as exc:
        return {"args": args, "returncode": 124, "stdout": exc.stdout or "", "stderr": f"timeout:{timeout}s"}


def candidate_apply_request(candidate: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    return {
        "schema": "stegverse.apply_request.v1",
        "request_id": f"adapter-sandbox-{candidate.get('candidate_id')}-{'dry' if dry_run else 'binding'}",
        "entity": "StegVerse-002",
        "stage": "SV002-M11",
        "capability": candidate.get("candidate_id", "adapter-candidate"),
        "requester": f"adapter-candidate-sandbox/{candidate.get('provider', 'unknown')}",
        "transition_class": candidate.get("transition_class", "tooling"),
        "authority_ref": candidate.get("authority_ref", ""),
        "policy_ref": candidate.get("policy_ref", ""),
        "dry_run": dry_run,
        "target_files": [
            {"path": item.get("path", ""), "operation": "review"}
            for item in candidate.get("files", [])
        ],
    }


def load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidate(candidate: dict[str, Any], repo_root: Path, index: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "candidate_id": candidate.get("candidate_id"),
        "provider": candidate.get("provider"),
        "valid_packet": candidate.get("valid_packet", False),
        "errors": list(candidate.get("errors", [])),
        "sandbox": {},
        "m11_gate": {},
        "decision": "DENY_CANDIDATE",
    }

    if not candidate.get("valid_packet", False):
        return result

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        sandbox = tmp / "repo"
        copy_repo_to_sandbox(repo_root, sandbox)

        try:
            apply_candidate_files(candidate, sandbox)
        except Exception as exc:
            result["errors"].append(str(exc))
            return result

        py_files = [
            item["path"] for item in candidate.get("files", [])
            if str(item.get("path", "")).endswith(".py")
        ]
        compile_results = []
        for rel in py_files:
            compile_results.append(run_cmd([sys.executable, "-m", "py_compile", rel], sandbox))
        result["sandbox"]["py_compile"] = compile_results
        if any(r.get("returncode") != 0 for r in compile_results):
            result["errors"].append("py_compile_failed")
            return result

        if (sandbox / "tests").exists():
            result["sandbox"]["pytest"] = run_cmd([sys.executable, "-m", "pytest", "-q"], sandbox, timeout=240)
        else:
            result["sandbox"]["pytest"] = {"returncode": 0, "stdout": "tests directory missing; skipped", "stderr": ""}

        if result["sandbox"]["pytest"].get("returncode") != 0:
            result["errors"].append("pytest_failed")
            return result

        dry_req = tmp / "apply_request_dry.json"
        binding_req = tmp / "apply_request_binding.json"
        dry_req.write_text(json.dumps(candidate_apply_request(candidate, True), indent=2, sort_keys=True), encoding="utf-8")
        binding_req.write_text(json.dumps(candidate_apply_request(candidate, False), indent=2, sort_keys=True), encoding="utf-8")

        dry_report = f"reports/current/adapter_candidate_{index}_apply_dry_report.json"
        binding_report = f"reports/current/adapter_candidate_{index}_apply_binding_report.json"

        dry_cmd = run_cmd([
            sys.executable, "scripts/stegverse_apply_gate.py",
            "--request", str(dry_req),
            "--entity", "StegVerse-002",
            "--stage", "SV002-M11",
            "--report", dry_report,
            "--receipt", "receipts/current/adapter_candidate_apply_gate_receipt.jsonl",
            "--output", f"outputs/adapter_candidate_{index}_apply_dry.md",
        ], sandbox)

        binding_cmd = run_cmd([
            sys.executable, "scripts/stegverse_apply_gate.py",
            "--request", str(binding_req),
            "--entity", "StegVerse-002",
            "--stage", "SV002-M11",
            "--report", binding_report,
            "--receipt", "receipts/current/adapter_candidate_apply_gate_receipt.jsonl",
            "--output", f"outputs/adapter_candidate_{index}_apply_binding.md",
        ], sandbox)

        dry_decision = load_json_if_exists(sandbox / dry_report).get("decision")
        binding_decision = load_json_if_exists(sandbox / binding_report).get("decision")

        result["m11_gate"]["dry_run_command"] = dry_cmd
        result["m11_gate"]["binding_command"] = binding_cmd
        result["m11_gate"]["dry_run_decision"] = dry_decision
        result["m11_gate"]["binding_decision"] = binding_decision

        if dry_decision == "ALLOW" and binding_decision == "ALLOW":
            result["decision"] = "SANDBOX_PASS_GATE_ALLOW"
        elif dry_decision == "ALLOW" and binding_decision == "DEFER":
            result["decision"] = "SANDBOX_PASS_GATE_DEFER"
        else:
            result["decision"] = "DENY_CANDIDATE"
            result["errors"].append("m11_gate_unexpected_decision")

    return result


def write_outputs(report: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)

    receipt_hash = append_receipt(report)
    report["receipt_hash"] = receipt_hash
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Adapter Candidate Sandbox Executor",
        "",
        f"**Decision:** `{report['decision']}`",
        f"**Selected candidate:** `{report.get('selected_candidate_id') or 'none'}`",
        f"**Applied files:** `{', '.join(report.get('applied_files', [])) or 'none'}`",
        f"**Receipt hash:** `{receipt_hash}`",
        "",
        "## Candidate Results",
        "",
    ]
    if not report.get("candidates"):
        lines.append("- No machine-actionable candidates were found. Failed closed with diagnostics.")
    for candidate in report.get("candidates", []):
        lines.append(f"- `{candidate.get('candidate_id')}` from `{candidate.get('provider')}` → `{candidate.get('decision')}`")
        for err in candidate.get("errors", []):
            lines.append(f"  - error: `{err}`")
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with zipfile.ZipFile(ARTIFACT_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in [REPORT_PATH, RECEIPT_PATH, OUTPUT_PATH]:
            if path.exists():
                zf.write(path, path.as_posix())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--openai-output", default="outputs/chatgpt_response.md")
    parser.add_argument("--claude-output", default="outputs/claude_response.md")
    parser.add_argument("--apply-if-gate-allows", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    started = utc_now()

    provider_outputs = {
        "openai": repo_root / args.openai_output,
        "claude": repo_root / args.claude_output,
    }

    raw_candidates = collect_candidates(provider_outputs)
    tested = [test_candidate(candidate, repo_root, i) for i, candidate in enumerate(raw_candidates, start=1)]

    selected = None
    for item in tested:
        if item.get("decision") in {"SANDBOX_PASS_GATE_ALLOW", "SANDBOX_PASS_GATE_DEFER"}:
            selected = item
            break

    applied_files: list[str] = []
    decision = "FAIL_CLOSED_NO_ACTIONABLE_CANDIDATE"
    if raw_candidates and selected is None:
        decision = "FAIL_CLOSED_NO_PASSING_CANDIDATE"
    elif selected and selected.get("decision") == "SANDBOX_PASS_GATE_DEFER":
        decision = "CANDIDATE_SANDBOXED_GATE_DEFERRED"
    elif selected and selected.get("decision") == "SANDBOX_PASS_GATE_ALLOW":
        candidate_packet = next(
            c for c in raw_candidates
            if c.get("candidate_id") == selected.get("candidate_id") and c.get("provider") == selected.get("provider")
        )
        if args.apply_if_gate_allows:
            applied_files = apply_candidate_files(candidate_packet, repo_root)
            decision = "CANDIDATE_APPLIED_AFTER_SANDBOX_AND_GATE"
        else:
            decision = "CANDIDATE_SANDBOXED_GATE_ALLOWED_NOT_APPLIED"

    report = {
        "schema": "stegverse.adapter_candidate_sandbox_report.v1",
        "started": started,
        "completed": utc_now(),
        "decision": decision,
        "selected_candidate_id": selected.get("candidate_id") if selected else None,
        "applied_files": applied_files,
        "provider_outputs": {k: str(v) for k, v in provider_outputs.items()},
        "candidates": tested,
        "governance": {
            "provider_outputs_are_candidate_evidence_only": True,
            "sandbox_required_before_apply_gate": True,
            "m11_gate_required_before_binding": True,
            "no_manual_bundle_transport_required": True,
            "default_fail_closed": True,
        },
    }
    write_outputs(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
