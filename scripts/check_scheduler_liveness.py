#!/usr/bin/env python3
"""
Check whether the autonomous heartbeat scheduler has produced a recent beat.

This checker is read-only with respect to authority: it does not dispatch workflows,
repair proof, ingest bundles, bind state, or grant authority. It records whether
scheduler evidence exists so missing heartbeat activity is visible as a first-class
state instead of silent waiting.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_HEARTBEAT_RECEIPT = "receipts/current/heartbeat_evaluation_receipt.jsonl"
DEFAULT_PROOF_RECEIPT = "receipts/current/transition_bundle_proof_check_receipt.jsonl"


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(ts: dt.datetime) -> str:
    return ts.isoformat().replace("+00:00", "Z")


def parse_ts(value: Any) -> Optional[dt.datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def read_last_jsonl(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def evaluate(root: Path, max_age_minutes: int) -> Dict[str, Any]:
    now = utc_now()
    heartbeat_path = root / DEFAULT_HEARTBEAT_RECEIPT
    proof_path = root / DEFAULT_PROOF_RECEIPT

    heartbeat = read_last_jsonl(heartbeat_path)
    proof = read_last_jsonl(proof_path)

    heartbeat_ts = parse_ts((heartbeat or {}).get("timestamp"))
    proof_ts = parse_ts((proof or {}).get("checked_utc") or (proof or {}).get("timestamp"))

    observations: List[str] = []
    if heartbeat is None:
        observations.append("heartbeat_evaluation_receipt_missing")
    if proof is None:
        observations.append("transition_bundle_proof_check_receipt_missing")

    heartbeat_age_minutes: Optional[float] = None
    if heartbeat_ts is not None:
        heartbeat_age_minutes = round((now - heartbeat_ts).total_seconds() / 60.0, 2)
        if heartbeat_age_minutes > max_age_minutes:
            observations.append("heartbeat_evaluation_receipt_stale")

    proof_age_minutes: Optional[float] = None
    if proof_ts is not None:
        proof_age_minutes = round((now - proof_ts).total_seconds() / 60.0, 2)
        if proof_age_minutes > max_age_minutes:
            observations.append("transition_bundle_proof_check_receipt_stale")

    if not observations:
        status = "SCHEDULER_LIVE"
        needs_scheduler_attention = False
    elif "heartbeat_evaluation_receipt_missing" in observations:
        status = "SCHEDULER_NO_HEARTBEAT_EVIDENCE"
        needs_scheduler_attention = True
    elif any(obs.endswith("_stale") for obs in observations):
        status = "SCHEDULER_STALE"
        needs_scheduler_attention = True
    else:
        status = "SCHEDULER_PARTIAL_EVIDENCE"
        needs_scheduler_attention = True

    return {
        "schema": "stegverse.scheduler_liveness.v1",
        "timestamp": iso(now),
        "version": "0.1.3-gllm",
        "entity": "StegVerse-002",
        "repo": "StegVerse-002/core-lite",
        "status": status,
        "needs_scheduler_attention": needs_scheduler_attention,
        "max_age_minutes": max_age_minutes,
        "observations": observations,
        "heartbeat_receipt": DEFAULT_HEARTBEAT_RECEIPT,
        "proof_receipt": DEFAULT_PROOF_RECEIPT,
        "heartbeat_age_minutes": heartbeat_age_minutes,
        "proof_age_minutes": proof_age_minutes,
        "authority": {
            "candidate_evidence_only": True,
            "canonical_authority": False,
            "broad_authority": False,
            "may_bind_repo_state": False
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--max-age-minutes", type=int, default=15)
    parser.add_argument("--report", default="reports/current/scheduler_liveness_report.json")
    parser.add_argument("--receipt", default="receipts/current/scheduler_liveness_receipt.jsonl")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    report = evaluate(root, args.max_age_minutes)

    report_path = root / args.report
    receipt_path = root / args.receipt
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_jsonl(receipt_path, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
