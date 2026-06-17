#!/usr/bin/env python3
"""
Evaluate StegVerse-002/core-lite heartbeat mode from the current proof state.

Read-only evaluator. It does not dispatch workflows, mutate state, grant authority,
or bind installation. It writes a report/receipt so the heartbeat itself is auditable.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def evaluate(policy: Dict[str, Any], proof: Dict[str, Any]) -> Dict[str, Any]:
    status = proof.get("status", "UNKNOWN")
    missing = proof.get("missing", []) or []
    needs_proof = bool(proof.get("needs_proof", True))
    errors = proof.get("errors", []) or []
    warnings = proof.get("warnings", []) or []

    missing_ingest_receipt = "receipts/current/transition_bundle_ingest_receipt.jsonl" in missing

    if status == "PROOF_COMPLETE" and not needs_proof and not errors:
        mode = "resting"
        interval = policy["heartbeat_modes"]["resting"]["interval_minutes"]
        reason = "proof complete; drift watch only"
        should_attempt_repair = False
    elif status in ("PARTIAL_PROOF", "PROOF_INVALID") or missing_ingest_receipt or errors:
        mode = "fast"
        interval = policy["heartbeat_modes"]["fast"]["interval_minutes"]
        reason = "proof incomplete or invalid; fast bounded repair posture"
        should_attempt_repair = True
    else:
        mode = "normal"
        interval = policy["heartbeat_modes"]["normal"]["interval_minutes"]
        reason = "activation pending; normal repair posture"
        should_attempt_repair = True

    return {
        "schema": "stegverse.heartbeat_evaluation.v1",
        "timestamp": utc_now(),
        "version": policy.get("version", "0.1.3-gllm"),
        "entity": policy.get("entity", "StegVerse-002"),
        "repo": policy.get("repo", "StegVerse-002/core-lite"),
        "mode": mode,
        "recommended_interval_minutes": interval,
        "reason": reason,
        "proof_status": status,
        "needs_proof": needs_proof,
        "missing": missing,
        "warnings": warnings,
        "errors": errors,
        "should_attempt_repair": should_attempt_repair,
        "authority": policy.get("authority", {}),
        "health_rules": policy.get("health_rules", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--policy", default="config/heartbeat_policy.json")
    parser.add_argument("--proof", default="reports/current/transition_bundle_proof_check.json")
    parser.add_argument("--report", default="reports/current/heartbeat_evaluation.json")
    parser.add_argument("--receipt", default="receipts/current/heartbeat_evaluation_receipt.jsonl")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    policy = load_json(root / args.policy, {})
    proof = load_json(root / args.proof, {"status": "UNKNOWN", "needs_proof": True, "missing": []})
    report = evaluate(policy, proof)

    report_path = root / args.report
    receipt_path = root / args.receipt
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_jsonl(receipt_path, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
