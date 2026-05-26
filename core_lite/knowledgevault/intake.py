"""
core_lite.knowledgevault.intake — KnowledgeVault context packet intake.

Receives a bounded context packet from KnowledgeVault,
validates it through CGE, and routes to the active stage.

KnowledgeVault is user-owned memory.
StegVerse-002 receives only bounded context packets.
It does not receive the full vault.
"""

import argparse
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from core_lite.cge import CGEEngine, CGERequest
from core_lite.receipts import ReceiptRecorder

log = logging.getLogger("core_lite.knowledgevault.intake")

CONTEXT_PACKET_SCHEMA = "stegverse_knowledgevault_context_packet.v1"
MEMORY_USE_RECEIPT_SCHEMA = "stegverse_memory_use_receipt.v1"


@dataclass
class ContextPacket:
    schema: str = CONTEXT_PACKET_SCHEMA
    packet_id: str = ""
    vault_id: str = ""
    created_at: str = ""
    created_by: str = ""
    target_entity: str = ""
    target_stage: str = ""
    purpose: str = ""
    identity_context: str = ""
    allowed_use: list = field(default_factory=list)
    forbidden_use: list = field(default_factory=list)
    privacy_class: str = "private"
    stop_condition: str = ""
    included_files: list = field(default_factory=list)
    packet_hash: str = ""

    @classmethod
    def from_file(cls, path: Path) -> "ContextPacket":
        with open(path) as f:
            d = json.load(f)
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def compute_hash(self) -> str:
        payload = json.dumps({
            "packet_id": self.packet_id,
            "vault_id": self.vault_id,
            "target_entity": self.target_entity,
            "target_stage": self.target_stage,
            "purpose": self.purpose,
            "allowed_use": sorted(self.allowed_use),
            "forbidden_use": sorted(self.forbidden_use),
        }, sort_keys=True)
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


class KnowledgeVaultIntake:
    """
    Context packet intake from KnowledgeVault.

    Invariants:
    - KnowledgeVault is user-owned memory
    - StegVerse-002 receives only bounded context packets
    - Context is not consent
    - Memory is not authority
    - Full vault is never ingested
    """

    def __init__(
        self,
        repo_root: Path = Path("."),
        entity: str = "StegVerse-002",
        stage: str = "SV002-M8",
    ):
        self.repo_root = repo_root
        self.entity = entity
        self.stage = stage
        self.receipts_path = repo_root / ".stegverse" / "receipts" / "kv_receipts.jsonl"
        self.cge = CGEEngine(repo_root=repo_root)
        self.recorder = ReceiptRecorder(self.receipts_path)

    def intake(self, packet_path: Path) -> dict:
        log.info("KnowledgeVault context packet intake: %s", packet_path)

        # Load packet
        try:
            packet = ContextPacket.from_file(packet_path)
        except Exception as e:
            return {"status": "fail_closed", "error": f"Cannot parse context packet: {e}"}

        # Validate target
        if packet.target_entity and packet.target_entity != self.entity:
            self.recorder.record(
                actor=self.entity, stage=self.stage, gate="kv_intake",
                action="context_packet_intake", decision="DENY",
                basis=f"Packet target_entity {packet.target_entity} != {self.entity}",
            )
            return {"status": "denied", "reason": "target_entity mismatch"}

        # Validate stage
        if packet.target_stage and not packet.target_stage.startswith("SV002"):
            log.warning("Context packet stage %s may not match current entity", packet.target_stage)

        # Verify hash
        computed = packet.compute_hash()
        if packet.packet_hash and packet.packet_hash != computed:
            self.recorder.record(
                actor=self.entity, stage=self.stage, gate="kv_intake",
                action="context_packet_intake", decision="FAIL_CLOSED",
                basis="Packet hash mismatch",
            )
            return {"status": "fail_closed", "reason": "packet_hash mismatch"}

        # CGE check
        cge_request = CGERequest(
            actor=self.entity,
            stage=self.stage,
            target_scope=packet.target_stage or self.stage,
            action="context_packet_intake",
            input_type="text",
            privacy_class=packet.privacy_class,
            allowed_use=packet.allowed_use,
            forbidden_use=packet.forbidden_use,
            stop_condition=packet.stop_condition,
            identity_authority=False,
        )
        cge_result = self.cge.decide(cge_request)

        # Memory-use receipt
        receipt = self.recorder.record(
            actor=self.entity,
            stage=self.stage,
            gate="kv_intake",
            action="context_packet_intake",
            decision=cge_result.decision,
            basis=cge_result.basis,
            privacy_class=packet.privacy_class,
            allowed_use=packet.allowed_use,
            forbidden_use=packet.forbidden_use,
            stop_condition=packet.stop_condition,
            outputs=packet.included_files,
        )

        # Write memory-use receipt to vault receipts
        self._write_memory_use_receipt(packet, cge_result, receipt)

        return {
            "status": "success" if cge_result.decision.startswith("ALLOW") else "review_required",
            "packet_id": packet.packet_id,
            "vault_id": packet.vault_id,
            "cge_decision": cge_result.decision,
            "receipt_hash": receipt.receipt_hash,
            "allowed_use": packet.allowed_use,
            "stop_condition": packet.stop_condition,
        }

    def _write_memory_use_receipt(self, packet: ContextPacket, cge_result, receipt) -> None:
        receipts_dir = self.repo_root / "vault_template" / "receipts"
        receipts_dir.mkdir(parents=True, exist_ok=True)
        memory_receipt = {
            "schema": MEMORY_USE_RECEIPT_SCHEMA,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "vault_id": packet.vault_id,
            "packet_id": packet.packet_id,
            "actor": self.entity,
            "target_entity": packet.target_entity,
            "target_stage": packet.target_stage,
            "purpose": packet.purpose,
            "decision": cge_result.decision,
            "basis": cge_result.basis,
            "files_used": packet.included_files,
            "allowed_use": packet.allowed_use,
            "forbidden_use": packet.forbidden_use,
            "stop_condition": packet.stop_condition,
            "receipt_hash": receipt.receipt_hash,
            "previous_receipt_hash": receipt.previous_receipt_hash,
        }
        receipt_path = receipts_dir / f"memory_use_{packet.packet_id or 'unknown'}.json"
        with open(receipt_path, "w") as f:
            json.dump(memory_receipt, f, indent=2)
        log.info("Memory-use receipt written: %s", receipt_path)


def main():
    parser = argparse.ArgumentParser(prog="core_lite.knowledgevault.intake")
    parser.add_argument("--packet-path", required=True)
    parser.add_argument("--entity", default="StegVerse-002")
    parser.add_argument("--stage", default="SV002-M8")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    intake = KnowledgeVaultIntake(
        repo_root=Path(args.repo_root),
        entity=args.entity,
        stage=args.stage,
    )
    result = intake.intake(Path(args.packet_path))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
