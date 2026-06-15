#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

EXPECTED_SOURCE_BUNDLE = "tracking/recovery_corrected/sv002_recovery_30d45378723de692_CHANGELOG.md.zip"
EXPECTED_BUNDLE_HASH = "sha256:17f224bca33c1a1cff197b1f06f76058f9d61fb0e399c3b034070137bec52b3e"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text().splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--expected-source-bundle", default=EXPECTED_SOURCE_BUNDLE)
    ap.add_argument("--expected-bundle-hash", default=EXPECTED_BUNDLE_HASH)
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    reports = root / "reports" / "current"
    receipts = root / "receipts" / "current"
    reports.mkdir(parents=True, exist_ok=True)
    receipts.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(receipts / "transition_table_receipt.jsonl")
    matches = [
        r for r in rows
        if r.get("transition_class") == "evidence"
        and r.get("authority_class") == "evidence_only"
        and r.get("bundle_hash") == args.expected_bundle_hash
    ]
    latest = matches[-1] if matches else {}

    errors: list[str] = []
    if not latest:
        errors.append("no matching corrected recovery proof receipt found by bundle_hash")
    else:
        if latest.get("transition_table_decision") != "ALLOW":
            errors.append("transition_table_decision is not ALLOW")
        if latest.get("cge_decision") != "ALLOW":
            errors.append("cge_decision is not ALLOW")
        if latest.get("final_decision") != "ALLOW":
            errors.append("final_decision is not ALLOW")
        if latest.get("cge_fingerprint", "") == "":
            errors.append("cge_fingerprint missing")
        if "CGEEngine call failed" in str(latest.get("cge_basis", "")):
            errors.append("cge_basis indicates failed CGE call")

    report = {
        "schema": "stegverse.cge_recovery_proof_regression.v2",
        "generated_at": now(),
        "expected_source_bundle": args.expected_source_bundle,
        "expected_bundle_hash": args.expected_bundle_hash,
        "decision": "ALLOW" if not errors else "FAIL_CLOSED",
        "errors": errors,
        "latest_receipt": latest,
        "governance": {
            "matches_staged_payload_by_bundle_hash": True,
            "requires_transition_table_allow": True,
            "requires_cge_allow": True,
            "requires_final_allow": True,
            "forbids_cge_error_fallback": True,
        },
    }

    report_path = reports / "cge_recovery_proof_regression_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    receipt = {
        "schema": "stegverse.cge_recovery_proof_regression_receipt.v2",
        "timestamp_utc": now(),
        "decision": report["decision"],
        "report_path": report_path.relative_to(root).as_posix(),
        "report_sha256": sha(report_path),
        "errors": errors,
        "expected_bundle_hash": args.expected_bundle_hash,
    }
    with (receipts / "cge_recovery_proof_regression_receipt.jsonl").open("a") as f:
        f.write(json.dumps(receipt, sort_keys=True) + "\n")

    print(json.dumps({"status": report["decision"], "errors": errors, "report": receipt["report_path"]}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
