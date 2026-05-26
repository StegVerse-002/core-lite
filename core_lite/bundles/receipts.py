"""Receipt helpers for bundle ingestion."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from core_lite.receipts import append_receipt


def emit_ingestion_receipt(
    repo_root: Path,
    *,
    actor: str,
    stage: str,
    decision: str,
    basis: str,
    bundle_name: str,
    report_path: str,
) -> dict[str, Any]:
    receipt = append_receipt(
        repo_root / "receipts" / "current" / "ingestion_receipt.jsonl",
        actor=actor,
        stage=stage,
        gate="bundle-ingestion",
        task_id="bundle.ingest",
        decision=decision,
        basis=basis,
        target_path=report_path,
        action=f"ingest_bundle:{bundle_name}",
        stop_condition="Bundle validated, installed or quarantined, and receipted.",
    )
    return {
        "receipt_hash": receipt.receipt_hash,
        "receipt_path": "receipts/current/ingestion_receipt.jsonl",
    }
