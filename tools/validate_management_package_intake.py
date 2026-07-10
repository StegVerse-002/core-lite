#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

POLICY_PATH = Path("config/management_package_intake_policy.json")
PACKAGE_ROOT = Path("incoming/data_continuation_core_lite")
REFERENCE_MANIFEST = PACKAGE_ROOT / "source_reference_manifest.json"
REPORT_JSON = Path("reports/current/management_package_acceptance_report.json")
REPORT_MD = Path("reports/current/management_package_acceptance_report.md")
RECEIPT_PATH = Path("receipts/current/management_package_acceptance_receipt.jsonl")


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def append_receipt(report: dict[str, Any]) -> dict[str, Any]:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = None
    if RECEIPT_PATH.exists():
        lines = [line for line in RECEIPT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            try:
                previous_hash = json.loads(lines[-1]).get("hash")
            except json.JSONDecodeError:
                previous_hash = None

    payload = {
        "schema": "stegverse.management_package_acceptance_receipt.v1",
        "version": report["version"],
        "repo": report["repo"],
        "source_repo": report["source_repo"],
        "source_commit": report.get("source_commit"),
        "result": report["result"],
        "missing_input_count": len(report["missing_inputs"]),
        "reference_input_count": len(report["accepted_reference_inputs"]),
        "candidate_evidence_only": report["authority"]["candidate_evidence_only"],
        "may_bind_repo_state": report["authority"]["may_bind_repo_state"],
        "previous_hash": previous_hash,
    }
    receipt = {**payload, "hash": stable_hash(payload)}
    with RECEIPT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, sort_keys=True) + "\n")
    return receipt


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Management Package Intake Acceptance",
        "",
        f"Generated: `{report['checked_utc']}`",
        f"Repo: `{report['repo']}`",
        f"Source repo: `{report['source_repo']}`",
        f"Source commit: `{report.get('source_commit') or 'not supplied'}`",
        "",
        "## Result",
        "",
        f"`{report['result']}`",
        "",
        "## Authority Boundary",
        "",
    ]
    for key, value in report["authority"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Missing Inputs", ""])
    lines.extend(f"- `{value}`" for value in report["missing_inputs"]) if report["missing_inputs"] else lines.append("- None")
    lines.extend(["", "## Accepted Local Inputs", ""])
    lines.extend(f"- `{value}`" for value in report["accepted_local_inputs"]) if report["accepted_local_inputs"] else lines.append("- None")
    lines.extend(["", "## Accepted Immutable References", ""])
    if report["accepted_reference_inputs"]:
        for item in report["accepted_reference_inputs"]:
            lines.append(f"- `{item['path']}` @ `{item['blob_sha']}`")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Receipt",
        "",
        f"- Receipt hash: `{report['receipt']['hash']}`",
        f"- Receipt path: `{RECEIPT_PATH.as_posix()}`",
        "",
    ])
    return "\n".join(lines)


def resolve_required_inputs(policy: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for value in policy.get("required_inputs", []):
        text = str(value)
        if text.startswith("Data-Continuation/core-lite::"):
            out.append(text.split("::", 1)[1])
    return out


def load_reference_map(root: Path) -> tuple[dict[str, str], str | None]:
    path = root / REFERENCE_MANIFEST
    if not path.exists():
        return {}, None
    manifest = read_json(path)
    if manifest.get("source_repo") != "Data-Continuation/core-lite":
        raise ValueError("Reference manifest source_repo mismatch")
    if manifest.get("candidate_evidence_only") is not True:
        raise ValueError("Reference manifest must remain candidate evidence only")
    refs: dict[str, str] = {}
    for item in manifest.get("references", []):
        if not isinstance(item, dict):
            continue
        ref_path = str(item.get("path", "")).strip()
        blob_sha = str(item.get("blob_sha", "")).strip()
        if ref_path and len(blob_sha) == 40:
            refs[ref_path] = blob_sha
    return refs, str(manifest.get("source_commit") or "") or None


def build_report(root: Path) -> tuple[dict[str, Any], int]:
    policy = read_json(root / POLICY_PATH)
    required = resolve_required_inputs(policy)
    reference_map, source_commit = load_reference_map(root)

    accepted_local = [value for value in required if (root / PACKAGE_ROOT / value).exists()]
    accepted_reference = [
        {"path": value, "blob_sha": reference_map[value]}
        for value in required
        if value not in accepted_local and value in reference_map
    ]
    accepted_paths = set(accepted_local) | {item["path"] for item in accepted_reference}
    missing = [value for value in required if value not in accepted_paths]
    result = policy["intake_result_when_package_present"] if not missing else policy["intake_result_when_package_missing"]

    report: dict[str, Any] = {
        "schema": "stegverse.management_package_acceptance_report.v2",
        "version": "0.1.23-gllm",
        "repo": policy["repo"],
        "source_repo": "Data-Continuation/core-lite",
        "source_commit": source_commit,
        "checked_utc": now(),
        "authority": policy["authority"],
        "package_root": PACKAGE_ROOT.as_posix(),
        "reference_manifest": REFERENCE_MANIFEST.as_posix(),
        "required_inputs": required,
        "accepted_inputs": sorted(accepted_paths),
        "accepted_local_inputs": accepted_local,
        "accepted_reference_inputs": accepted_reference,
        "missing_inputs": missing,
        "intake_boundary": policy["intake_boundary"],
        "result": result,
        "next_candidate_goal": "management action candidate synthesis" if not missing else "produce, mirror, or reference remaining 001 management package inputs",
        "mutation_count": 0,
    }
    report["receipt"] = append_receipt(report)
    (root / REPORT_JSON).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (root / REPORT_MD).write_text(render_markdown(report), encoding="utf-8")
    return report, 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Data-Continuation/core-lite management package intake.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        report, code = build_report(Path(args.root).resolve())
    except Exception as exc:
        print(f"Management package intake validation failed: {exc}")
        return 2

    print(f"Wrote {REPORT_MD.as_posix()}")
    print(f"Wrote {REPORT_JSON.as_posix()}")
    print(f"Wrote {RECEIPT_PATH.as_posix()}")
    print(f"Result: {report['result']}")
    print("Mutations performed: 0")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
