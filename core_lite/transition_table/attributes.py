"""
core_lite/transition_table/attributes.py — StegVerse-002
Dataclass for transition attributes declared in a bundle manifest.
Derived from CGE + Transition Table Ingestion Enforcement README and
Stage 32-34 admissibility-space formalism.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TransitionAttributes:
    """
    Structured representation of the manifest transition block.
    Every field maps directly to the manifest transition section.
    """
    # Core classification
    transition_class: str = ""
    transition_cell: str = ""
    authority_class: str = ""
    state_effect: str = ""
    binding_level: str = ""
    target_scope: str = ""
    execution_scope: str = ""
    admissibility_gate: str = ""
    disposition_policy: str = ""

    # Candidate-specific
    task_ref: str = ""
    task_hash: str = ""
    candidate_provider: str = ""
    candidate_round: int = 0
    previous_bundle_ref: str = ""
    previous_bundle_hash: str = ""

    # Merged/synthesized candidate
    source_candidate_refs: List[str] = field(default_factory=list)
    source_candidate_hashes: List[str] = field(default_factory=list)
    synthesis_method: str = ""

    # Install bundle
    install_scope: str = ""
    allowed_paths: List[str] = field(default_factory=list)
    forbidden_paths: List[str] = field(default_factory=list)
    rollback_policy: str = ""

    # Repair bundle
    repair_target: str = ""
    broken_behavior: str = ""

    # Execution bundle
    execution_request: str = ""
    runtime_scope: str = ""
    operator_authority_ref: str = ""
    approval_ref: str = ""

    # Formalism references (Stage 32-34 proof chain)
    formalism_refs: List[dict] = field(default_factory=list)

    @classmethod
    def from_manifest(cls, manifest: dict) -> "TransitionAttributes":
        """
        Parse a bundle manifest dict and return a TransitionAttributes instance.
        The manifest must have a 'transition' block.
        """
        t = manifest.get("transition", {})
        return cls(
            transition_class=t.get("transition_class", ""),
            transition_cell=t.get("transition_cell", ""),
            authority_class=t.get("authority_class", ""),
            state_effect=t.get("state_effect", ""),
            binding_level=t.get("binding_level", ""),
            target_scope=t.get("target_scope", ""),
            execution_scope=t.get("execution_scope", ""),
            admissibility_gate=t.get("admissibility_gate", ""),
            disposition_policy=t.get("disposition_policy", ""),
            task_ref=t.get("task_ref", ""),
            task_hash=t.get("task_hash", ""),
            candidate_provider=t.get("candidate_provider", ""),
            candidate_round=int(t.get("candidate_round", 0) or 0),
            previous_bundle_ref=t.get("previous_bundle_ref", ""),
            previous_bundle_hash=t.get("previous_bundle_hash", ""),
            source_candidate_refs=t.get("source_candidate_refs", []),
            source_candidate_hashes=t.get("source_candidate_hashes", []),
            synthesis_method=t.get("synthesis_method", ""),
            install_scope=t.get("install_scope", ""),
            allowed_paths=t.get("allowed_paths", []),
            forbidden_paths=t.get("forbidden_paths", []),
            rollback_policy=t.get("rollback_policy", ""),
            repair_target=t.get("repair_target", ""),
            broken_behavior=t.get("broken_behavior", ""),
            execution_request=t.get("execution_request", ""),
            runtime_scope=t.get("runtime_scope", ""),
            operator_authority_ref=t.get("operator_authority_ref", ""),
            approval_ref=t.get("approval_ref", ""),
            formalism_refs=t.get("formalism_refs", []),
        )

    def to_dict(self) -> dict:
        return {
            "transition_class": self.transition_class,
            "transition_cell": self.transition_cell,
            "authority_class": self.authority_class,
            "state_effect": self.state_effect,
            "binding_level": self.binding_level,
            "target_scope": self.target_scope,
            "execution_scope": self.execution_scope,
            "admissibility_gate": self.admissibility_gate,
            "disposition_policy": self.disposition_policy,
            "task_ref": self.task_ref,
            "task_hash": self.task_hash,
            "candidate_provider": self.candidate_provider,
            "candidate_round": self.candidate_round,
            "previous_bundle_ref": self.previous_bundle_ref,
            "previous_bundle_hash": self.previous_bundle_hash,
            "source_candidate_refs": self.source_candidate_refs,
            "source_candidate_hashes": self.source_candidate_hashes,
            "synthesis_method": self.synthesis_method,
            "install_scope": self.install_scope,
            "allowed_paths": self.allowed_paths,
            "forbidden_paths": self.forbidden_paths,
            "rollback_policy": self.rollback_policy,
            "repair_target": self.repair_target,
            "broken_behavior": self.broken_behavior,
            "execution_request": self.execution_request,
            "runtime_scope": self.runtime_scope,
            "operator_authority_ref": self.operator_authority_ref,
            "approval_ref": self.approval_ref,
            "formalism_refs": self.formalism_refs,
        }
