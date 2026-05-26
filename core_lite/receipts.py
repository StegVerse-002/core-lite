"""
core_lite.receipts — Receipt chain for StegVerse-002.

Every consequence-bearing transition emits a receipt.
Receipts are append-only JSONL.
Each receipt hashes the previous receipt for chain continuity.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("core_lite.receipts")

RECEIPT_SCHEMA = "stegverse_receipt.v1"


@dataclass
class Receipt:
    schema: str = RECEIPT_SCHEMA
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: str = ""
    stage: str = ""
    gate: str = ""
    task_id: str = ""
    target_repo: str = ""
    target_path: str = ""
    action: str = ""
    decision: str = ""
    basis: str = ""
    input_type: str = ""
    input_hash: str = ""
    privacy_class: str = "private"
    allowed_use: list = field(default_factory=list)
    forbidden_use: list = field(default_factory=list)
    stop_condition: str = ""
    mutation_to_target_performed: bool = False
    workflow_change_authority: bool = False
    incoming_submission_authority: bool = False
    outputs: list = field(default_factory=list)
    previous_receipt_hash: str = ""
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        payload = json.dumps({
            "timestamp": self.timestamp,
            "actor": self.actor,
            "stage": self.stage,
            "gate": self.gate,
            "decision": self.decision,
            "basis": self.basis,
            "previous_receipt_hash": self.previous_receipt_hash,
        }, sort_keys=True)
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ReceiptRecorder:
    """
    Append-only receipt recorder.

    Usage:
        recorder = ReceiptRecorder(output_path)
        receipt = recorder.record(
            actor="StegVerse-002",
            stage="SV002-M5",
            gate="core-lite-intake",
            decision="ALLOW",
            basis="Intake succeeded",
        )
    """

    def __init__(self, output_path: Path):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        if not self.output_path.exists():
            return ""
        last_hash = ""
        with open(self.output_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        last_hash = entry.get("receipt_hash", "")
                    except json.JSONDecodeError:
                        pass
        return last_hash

    def record(
        self,
        *,
        actor: str,
        stage: str,
        gate: str = "",
        task_id: str = "",
        target_repo: str = "",
        target_path: str = "",
        action: str = "intake",
        decision: str = "ALLOW",
        basis: str = "",
        input_type: str = "",
        input_hash: str = "",
        privacy_class: str = "private",
        allowed_use: list = None,
        forbidden_use: list = None,
        stop_condition: str = "",
        mutation_to_target_performed: bool = False,
        workflow_change_authority: bool = False,
        incoming_submission_authority: bool = False,
        outputs: list = None,
    ) -> Receipt:
        receipt = Receipt(
            actor=actor,
            stage=stage,
            gate=gate,
            task_id=task_id,
            target_repo=target_repo,
            target_path=target_path,
            action=action,
            decision=decision,
            basis=basis,
            input_type=input_type,
            input_hash=input_hash,
            privacy_class=privacy_class,
            allowed_use=allowed_use or [],
            forbidden_use=forbidden_use or [],
            stop_condition=stop_condition,
            mutation_to_target_performed=mutation_to_target_performed,
            workflow_change_authority=workflow_change_authority,
            incoming_submission_authority=incoming_submission_authority,
            outputs=outputs or [],
            previous_receipt_hash=self._last_hash,
        )
        receipt.receipt_hash = receipt.compute_hash()
        self._last_hash = receipt.receipt_hash
        self._append(receipt)
        log.info("Receipt emitted: stage=%s decision=%s hash=%s",
                 stage, decision, receipt.receipt_hash[:16])
        return receipt

    def _append(self, receipt: Receipt):
        with open(self.output_path, "a") as f:
            f.write(receipt.to_json() + "\n")


def append_receipt(
    output_path: str,
    *,
    actor: str,
    stage: str,
    gate: str = "",
    decision: str = "ALLOW",
    basis: str = "",
    **kwargs,
) -> Receipt:
    """
    Convenience function — create a recorder and append one receipt.
    Compatible with the SV001-M3 contract surface.
    """
    recorder = ReceiptRecorder(Path(output_path))
    return recorder.record(
        actor=actor,
        stage=stage,
        gate=gate,
        decision=decision,
        basis=basis,
        **kwargs,
    )
