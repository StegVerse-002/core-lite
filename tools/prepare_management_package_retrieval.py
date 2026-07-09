#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

POLICY_PATH = Path("config/management_package_retrieval_policy.json")
REPORT_JSON = Path("reports/current/management_package_retrieval_request.json")
REPORT_MD = Path("reports/current/management_package_retrieval_request.md")
RECEIPT_PATH = Path("receipts/current/management_package_retrieval_request_receipt.jsonl")


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def append_receipt(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    path = root / RECEIPT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = None
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            try:
                previous_hash = json.loads(lines[-1]).get("hash")
            except json.JSONDecodeError:
                previous_hash = None
    payload = {
        "schema": "stegverse.management_package_retrieval_request_receipt.v1",
        "version": report["version"],
        "repo": report["repo"],
        "source_repo": report["source_repo"],
        "result": report["result"],
        "candidate_evidence_only": report["authority"]["candidate_evidence_only"],
        "may_bind_repo_state": report["authority"].get("may_bind_repo_state", False),
        "previous_hash": previous_hash,
    }
    receipt = {**payload, "hash": stable_hash(payload)}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, sort_keys=True) + "\n")
    return receipt


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Management Package Retrieval Request",
        "",
        f"Generated: `{report['checked_utc']}`",
        f"Repo: `{report['repo']}`",
        f"Source repo: `{report['source_repo']}`",
        f"Source artifact: `{report['source_artifact']}`",
        f"Destination intake root: `{report['destination_intake_root']}`",
        "",
        "## Result",
        "",
        f"`{report['result']}`",
        "",
        "## Required Package Inputs",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report["required_package_inputs"])
    lines.extend([
        "",
        "## Boundary",
        "",
    ])
    for key, value in report["authority"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        "This request does not fetch artifacts, install files, grant authority, form quorum, or bind repository state.",
        "",
        "## Next Step",
        "",
        report["next_required_action"],
        "",
        "## Receipt",
        "",
        f"- Receipt hash: `{report['receipt']['hash']}`",
        f"- Receipt path: `{RECEIPT_PATH.as_posix()}`",
        "",
    ])
    return "\n".join(lines)


def build_report(root: Path) -> dict[str, Any]:
    policy = read_json(root / POLICY_PATH)
    report: dict[str, Any] = {
        "schema": "stegverse.management_package_retrieval_request.v1",
        "version": "0.1.22-gllm",
        "repo": policy["repo"],
        "checked_utc": now(),
        "authority": policy["authority"],
        "source_repo": policy["source_repo"],
        "source_artifact": policy["source_artifact"],
        "source_export_manifest": policy["source_export_manifest"],
        "destination_intake_root": policy["destination_intake_root"],
        "required_package_inputs": policy["required_package_inputs"],
        "retrieval_boundary": policy["retrieval_boundary"],
        "result": "MANAGEMENT_PACKAGE_RETRIEVAL_REQUEST_READY",
        "next_required_action": "Supply the Data-Continuation/core-lite workflow artifact outputs under incoming/data_continuation_core_lite/ and run sv002.management_package.intake.",
        "mutation_count": 0,
    }
    report["receipt"] = append_receipt(root, report)
    (root / REPORT_JSON).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (root / REPORT_MD).write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a non-authorizing 001 management package retrieval request.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = build_report(Path(args.repo_root).resolve())
    except Exception as exc:
        print(f"Management package retrieval request failed: {exc}")
        return 2
    print(f"Wrote {REPORT_MD.as_posix()}")
    print(f"Wrote {REPORT_JSON.as_posix()}")
    print(f"Wrote {RECEIPT_PATH.as_posix()}")
    print(f"Result: {report['result']}")
    print("Mutations performed: 0")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
