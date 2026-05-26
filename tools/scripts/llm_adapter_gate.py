"""
tools.scripts.llm_adapter_gate — LLM Adapter Gate for StegVerse-002.

Converts external LLM reasoning into bounded transition instruction packets.
LLM output is reasoning evidence, not authority.
It cannot authorize mutation or execution by itself.
"""

import argparse
import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from core_lite.cge import CGEEngine, CGERequest
from core_lite.receipts import append_receipt

log = logging.getLogger("tools.llm_adapter_gate")

INSTRUCTION_PACKET_SCHEMA = "stegverse_llm_adapter_instruction_packet.v1"


@dataclass
class LLMAdapterInstructionPacket:
    schema: str = INSTRUCTION_PACKET_SCHEMA
    packet_id: str = ""
    source_provider: str = ""
    source_model: str = ""
    source_session: str = ""
    prompt_hash: str = ""
    response_hash: str = ""
    operator: str = ""
    target_entity: str = "StegVerse-002"
    target_stage: str = ""
    target_scope: str = ""
    transition_class: str = ""
    allowed_action: str = ""
    forbidden_actions: list = field(default_factory=list)
    risk_classification: str = "unknown"
    stop_condition: str = ""
    decision: str = ""
    basis: str = ""
    receipt_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class LLMAdapterGate:
    """
    LLM Adapter Gate.

    Ingests LLM response text and converts it into a bounded
    transition instruction packet. The packet may inform a transition
    but cannot authorize one directly.

    Core rule: LLM output is not authorization.
    """

    SAFE_TRANSITION_CLASSES = {
        "candidate_suggestion",
        "blocker_classification",
        "report_generation",
        "context_summary",
        "risk_note",
        "review_recommendation",
    }

    BLOCKED_TRANSITION_CLASSES = {
        "production_mutation",
        "deploy",
        "execute_workflow",
        "push_to_repo",
        "override_cge",
        "grant_authority",
    }

    def __init__(
        self,
        repo_root: Path = Path("."),
        entity: str = "StegVerse-002",
        stage: str = "SV002-M7",
    ):
        self.repo_root = repo_root
        self.entity = entity
        self.stage = stage
        self.cge = CGEEngine(repo_root=repo_root)
        self.receipts_path = repo_root / ".stegverse" / "receipts" / "llm_adapter_receipts.jsonl"

    def ingest(
        self,
        llm_response: str,
        source_provider: str = "unknown",
        source_model: str = "unknown",
        operator: str = "",
        target_scope: str = "core-lite",
        transition_class: str = "candidate_suggestion",
    ) -> LLMAdapterInstructionPacket:

        prompt_hash = "sha256:" + hashlib.sha256(b"").hexdigest()
        response_hash = "sha256:" + hashlib.sha256(llm_response.encode()).hexdigest()

        packet = LLMAdapterInstructionPacket(
            packet_id=f"llm_packet_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
            source_provider=source_provider,
            source_model=source_model,
            operator=operator or self.entity,
            target_entity=self.entity,
            target_stage=self.stage,
            target_scope=target_scope,
            prompt_hash=prompt_hash,
            response_hash=response_hash,
            transition_class=transition_class,
            forbidden_actions=[
                "production_mutation", "deploy", "bypass_cge",
                "grant_authority", "training_use", "publication",
            ],
            stop_condition="Instruction packet produced — operator review required before any action",
        )

        # Block forbidden transition classes
        if transition_class in self.BLOCKED_TRANSITION_CLASSES:
            packet.decision = "DENY"
            packet.basis = f"Transition class {transition_class} is forbidden for LLM adapter output"
            self._emit_receipt(packet)
            return packet

        # CGE check
        cge_request = CGERequest(
            actor=self.entity,
            stage=self.stage,
            target_scope=target_scope,
            action=transition_class,
            input_type="llm_output",
            privacy_class="private",
            allowed_use=["instruction_packet", "candidate_preparation"],
            forbidden_use=["production_mutation", "training", "publication"],
            stop_condition=packet.stop_condition,
        )
        cge_result = self.cge.decide(cge_request)

        packet.decision = cge_result.decision
        packet.basis = cge_result.basis
        packet.risk_classification = (
            "high" if transition_class not in self.SAFE_TRANSITION_CLASSES else "low"
        )

        # Extract allowed action from safe classes only
        if transition_class in self.SAFE_TRANSITION_CLASSES:
            packet.allowed_action = transition_class
        else:
            packet.allowed_action = "review_required"

        receipt = self._emit_receipt(packet)
        packet.receipt_hash = receipt.receipt_hash

        # Write packet
        self._write_packet(packet)
        return packet

    def _emit_receipt(self, packet: LLMAdapterInstructionPacket):
        return append_receipt(
            str(self.receipts_path),
            actor=self.entity,
            stage=self.stage,
            gate="llm_adapter_gate",
            action=packet.transition_class,
            decision=packet.decision,
            basis=packet.basis,
            input_type="llm_output",
            stop_condition=packet.stop_condition,
        )

    def _write_packet(self, packet: LLMAdapterInstructionPacket):
        out_dir = self.repo_root / "dist" / "current" / "llm_adapter"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{packet.packet_id}.json"
        with open(out_path, "w") as f:
            json.dump(packet.to_dict(), f, indent=2)
        log.info("LLM adapter packet written: %s", out_path)


def main():
    parser = argparse.ArgumentParser(prog="tools.scripts.llm_adapter_gate")
    parser.add_argument("--response-file", help="Path to LLM response text file")
    parser.add_argument("--response-text", help="LLM response as inline text")
    parser.add_argument("--source-provider", default="unknown")
    parser.add_argument("--source-model", default="unknown")
    parser.add_argument("--operator", default="")
    parser.add_argument("--target-scope", default="core-lite")
    parser.add_argument("--transition-class", default="candidate_suggestion")
    parser.add_argument("--entity", default="StegVerse-002")
    parser.add_argument("--stage", default="SV002-M7")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    if args.response_file:
        with open(args.response_file) as f:
            response = f.read()
    elif args.response_text:
        response = args.response_text
    else:
        response = ""

    gate = LLMAdapterGate(
        repo_root=Path(args.repo_root),
        entity=args.entity,
        stage=args.stage,
    )
    packet = gate.ingest(
        llm_response=response,
        source_provider=args.source_provider,
        source_model=args.source_model,
        operator=args.operator,
        target_scope=args.target_scope,
        transition_class=args.transition_class,
    )
    print(json.dumps(packet.to_dict(), indent=2))


if __name__ == "__main__":
    main()
