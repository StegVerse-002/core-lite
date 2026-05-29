"""
core_lite/batch_ingestion/evidence_plane.py — StegVerse-002

Evidence plane contribution builder.

Every ingestion event — admission, quarantine, sandbox run, repair,
install, failure, discovery route, supersession — is a measurement
in the evidence plane. The evidence plane is the observable surface
of the admissibility geometry (Stage 32-34).

Over time the receipt chain becomes a training set for the geometry
of A. The more events accumulate, the more the shape of the admissible
region becomes observable from evidence, not just declared by policy.

Evidence plane fields appear on every receipt, graph node, and report.

Transition block classification (from Transition Periodic Table):
  B1 — Identity
  B2 — Authority
  B3 — Access
  B4 — Information
  B5 — Financial
  B6 — Legal
  B7 — Model/Internal  ← candidate bundles land here
  B8 — Artificial Agency
  B9 — Replay displaced
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_str(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

EVENT_TYPES = {
    "admission":        "bundle admitted through TT+CGE gate",
    "quarantine":       "bundle quarantined — marks boundary or collapse region",
    "fail_closed":      "coherence collapse — geometry undefined at this point",
    "sandbox_run":      "ephemeral sandbox explored repair path",
    "sandbox_pass":     "sandbox found admissible repair — confirms interior",
    "sandbox_fail":     "sandbox failed to find admissible repair",
    "sandbox_partial":  "sandbox partially reduced boundary distance",
    "install":          "files written — confirms deep interior of A",
    "install_failed":   "install failed — near-boundary state",
    "discovery_route":  "candidate routed by discovery engine",
    "synthesis":        "candidates synthesized — composite transition event",
    "supersession":     "bundle supersedes prior — temporal ordering evidence",
    "repair":           "repair candidate produced — nearest admissible found",
    "review":           "routed to review — observability deficit",
    "comparison":       "candidates compared — pairwise boundary evidence",
}

# Map transition classes to transition blocks
TRANSITION_CLASS_TO_BLOCK = {
    "candidate":  "B7",   # Model/Internal — affects model/AI state
    "install":    "B3",   # Access — changes what can be reached/written
    "repair":     "B7",   # Model/Internal
    "evidence":   "B4",   # Information — reveals/records state
    "execution":  "B8",   # Artificial Agency
}

# Map decision to region
DECISION_TO_REGION = {
    "ALLOW":               "interior_admissible_region",
    "ALLOW_CANDIDATE_ONLY": "interior_admissible_region",
    "SANDBOX":             "bounded_uncertain_boundary_shell",
    "REVIEW":              "observability_deficit_shell",
    "DENY":                "coherent_exterior_region",
    "FAIL_CLOSED":         "coherence_collapse",
    "QUARANTINE":          "isolated_preservation_state",
}


# ---------------------------------------------------------------------------
# Evidence plane contribution
# ---------------------------------------------------------------------------

@dataclass
class EvidencePlaneContribution:
    """
    One measurement in the evidence plane.
    Carried on every receipt, graph node, and report.
    """
    event_type: str
    bundle_hash: str
    task_hash: str
    timestamp_utc: str = field(default_factory=now_utc)

    # Boundary geometry (Stage 32)
    region: str = ""
    coordinates: Dict[str, float] = field(default_factory=dict)
    confirms_boundary: bool = False
    transition_block: str = ""
    formalism_stage: int = 32

    # Relationship signals (Stage 33)
    related_bundles: List[str] = field(default_factory=list)
    relation_type: str = ""
    lineage_depth: int = 0

    # Repair metrics (Stage 34)
    repair_cost: float = 0.0
    boundary_distance_before: float = 0.0
    boundary_distance_after: float = 0.0
    strategies_applied: List[str] = field(default_factory=list)

    # Provider evidence
    candidate_provider: str = ""
    candidate_round: int = 0

    # Receipt hash of this contribution
    contribution_hash: str = ""

    def to_dict(self) -> dict:
        d = {
            "schema": "stegverse.evidence_plane_contribution.v1",
            "event_type": self.event_type,
            "event_description": EVENT_TYPES.get(self.event_type, ""),
            "bundle_hash": self.bundle_hash,
            "task_hash": self.task_hash,
            "timestamp_utc": self.timestamp_utc,
            "boundary_contribution": {
                "region": self.region,
                "coordinates": self.coordinates,
                "confirms_boundary": self.confirms_boundary,
                "transition_block": self.transition_block,
                "formalism_stage": self.formalism_stage,
            },
            "relationship_signal": {
                "related_bundles": self.related_bundles,
                "relation_type": self.relation_type,
                "lineage_depth": self.lineage_depth,
            },
            "repair_signal": {
                "repair_cost": self.repair_cost,
                "boundary_distance_before": self.boundary_distance_before,
                "boundary_distance_after": self.boundary_distance_after,
                "strategies_applied": self.strategies_applied,
            },
            "provider_signal": {
                "candidate_provider": self.candidate_provider,
                "candidate_round": self.candidate_round,
            },
            "contribution_hash": self.contribution_hash,
        }
        return d

    def finalize(self) -> "EvidencePlaneContribution":
        """Compute and set contribution_hash."""
        raw = json.dumps(self.to_dict(), sort_keys=True)
        self.contribution_hash = sha256_str(raw)
        return self


# ---------------------------------------------------------------------------
# Evidence plane builder
# ---------------------------------------------------------------------------

class EvidencePlaneBuilder:
    """
    Builds evidence plane contributions from ingestion events.
    Writes to tracking/evidence_plane/evidence_plane.jsonl
    """

    def __init__(
        self,
        evidence_plane_root: str = "tracking/evidence_plane",
        receipt_dir: str = "receipts/current",
    ):
        self.evidence_plane_root = evidence_plane_root
        self.receipt_dir = receipt_dir

    def _append(self, contribution: EvidencePlaneContribution) -> None:
        os.makedirs(self.evidence_plane_root, exist_ok=True)
        path = os.path.join(self.evidence_plane_root, "evidence_plane.jsonl")
        with open(path, "a") as f:
            f.write(json.dumps(contribution.to_dict(), sort_keys=True) + "\n")

        # Also write to receipts
        os.makedirs(self.receipt_dir, exist_ok=True)
        receipt_path = os.path.join(self.receipt_dir, "evidence_plane_receipt.jsonl")
        with open(receipt_path, "a") as f:
            f.write(json.dumps(contribution.to_dict(), sort_keys=True) + "\n")

    def from_gate_result(
        self,
        bundle_hash: str,
        task_hash: str,
        transition_class: str,
        gate_result: dict,
        manifest: dict,
    ) -> EvidencePlaneContribution:
        """Build contribution from Transition Table gate result."""
        decision = gate_result.get("decision", "UNKNOWN")
        coordinates = gate_result.get("coordinates", {})
        t = manifest.get("transition", {}) if manifest else {}

        event_type = "admission" if "ALLOW" in decision else (
            "fail_closed" if decision == "FAIL_CLOSED" else
            "quarantine" if decision == "QUARANTINE" else
            "review"
        )

        c = EvidencePlaneContribution(
            event_type=event_type,
            bundle_hash=bundle_hash,
            task_hash=task_hash,
            region=DECISION_TO_REGION.get(decision, "unknown"),
            coordinates=coordinates,
            confirms_boundary=(decision in ("DENY", "FAIL_CLOSED", "SANDBOX")),
            transition_block=TRANSITION_CLASS_TO_BLOCK.get(transition_class, "B7"),
            candidate_provider=t.get("candidate_provider", ""),
            candidate_round=int(t.get("candidate_round", 0) or 0),
        )
        c.finalize()
        self._append(c)
        return c

    def from_sandbox_result(
        self,
        bundle_hash: str,
        task_hash: str,
        sandbox_result,  # SandboxResult
    ) -> EvidencePlaneContribution:
        """Build contribution from a sandbox run."""
        verdict = sandbox_result.verdict
        event_map = {
            "PASS": "sandbox_pass",
            "FAIL": "sandbox_fail",
            "PARTIAL": "sandbox_partial",
            "BLOCKED": "fail_closed",
        }
        event_type = event_map.get(verdict, "sandbox_run")

        boundary_before = sandbox_result.boundary_distance_before
        boundary_after = sandbox_result.boundary_distance_after
        repair_cost = max(0.0, boundary_before - boundary_after)

        strategies = [
            s.get("strategy", "") for s in sandbox_result.steps_taken
            if s.get("changes")
        ]

        c = EvidencePlaneContribution(
            event_type=event_type,
            bundle_hash=bundle_hash,
            task_hash=task_hash,
            region="bounded_uncertain_boundary_shell",
            coordinates={
                "d_A_before": boundary_before,
                "d_A_after": boundary_after,
                "delta_repair": repair_cost,
            },
            confirms_boundary=(verdict == "FAIL"),
            transition_block="B7",
            repair_cost=repair_cost,
            boundary_distance_before=boundary_before,
            boundary_distance_after=boundary_after,
            strategies_applied=strategies,
        )
        c.finalize()
        self._append(c)
        return c

    def from_install_result(
        self,
        bundle_hash: str,
        task_hash: str,
        install_result: dict,
    ) -> EvidencePlaneContribution:
        """Build contribution from an install result."""
        decision = install_result.get("decision", "")
        event_type = "install" if decision == "INSTALL_COMPLETE" else "install_failed"

        c = EvidencePlaneContribution(
            event_type=event_type,
            bundle_hash=bundle_hash,
            task_hash=task_hash,
            region="interior_admissible_region" if event_type == "install"
                   else "bounded_uncertain_boundary_shell",
            coordinates={"d_A": 0.0 if event_type == "install" else 0.4},
            confirms_boundary=False,
            transition_block="B3",  # Access — file write
        )
        c.finalize()
        self._append(c)
        return c

    def from_discovery_route(
        self,
        bundle_hash: str,
        task_hash: str,
        route: str,
        score: dict,
        related_bundles: List[str] = None,
        lineage_depth: int = 0,
    ) -> EvidencePlaneContribution:
        """Build contribution from a discovery routing decision."""
        event_map = {
            "synthesis": "synthesis",
            "install":   "admission",
            "sandbox":   "sandbox_run",
            "review":    "review",
            "quarantine": "quarantine",
        }
        event_type = event_map.get(route, "discovery_route")
        d_A = score.get("d_A", 0.0)

        c = EvidencePlaneContribution(
            event_type=event_type,
            bundle_hash=bundle_hash,
            task_hash=task_hash,
            region=DECISION_TO_REGION.get(
                "ALLOW" if route in ("synthesis", "install") else
                "SANDBOX" if route == "sandbox" else
                "REVIEW" if route == "review" else "QUARANTINE",
                "unknown"
            ),
            coordinates={"d_A": d_A},
            confirms_boundary=(route in ("quarantine", "sandbox")),
            transition_block="B7",
            related_bundles=related_bundles or [],
            relation_type=route,
            lineage_depth=lineage_depth,
        )
        c.finalize()
        self._append(c)
        return c

    def from_quarantine(
        self,
        bundle_hash: str,
        task_hash: str,
        reason: str,
        coordinates: dict = None,
    ) -> EvidencePlaneContribution:
        """Build contribution from a quarantine event."""
        is_collapse = "fail_closed" in reason.lower() or "coherence" in reason.lower()

        c = EvidencePlaneContribution(
            event_type="fail_closed" if is_collapse else "quarantine",
            bundle_hash=bundle_hash,
            task_hash=task_hash,
            region=(
                "coherence_collapse" if is_collapse
                else "isolated_preservation_state"
            ),
            coordinates=coordinates or {"d_A": 1.0},
            confirms_boundary=True,
        )
        c.finalize()
        self._append(c)
        return c

    def load_all(self) -> List[dict]:
        """Load all evidence plane contributions from disk."""
        path = os.path.join(self.evidence_plane_root, "evidence_plane.jsonl")
        if not os.path.exists(path):
            return []
        contributions = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        contributions.append(json.loads(line))
                    except Exception:
                        pass
        return contributions

    def summarize(self) -> dict:
        """Summarize the evidence plane for reporting."""
        contributions = self.load_all()
        by_event = {}
        by_region = {}
        by_block = {}

        for c in contributions:
            et = c.get("event_type", "unknown")
            by_event[et] = by_event.get(et, 0) + 1

            bc = c.get("boundary_contribution", {})
            region = bc.get("region", "unknown")
            by_region[region] = by_region.get(region, 0) + 1

            block = bc.get("transition_block", "unknown")
            by_block[block] = by_block.get(block, 0) + 1

        return {
            "schema": "stegverse.evidence_plane_summary.v1",
            "total_contributions": len(contributions),
            "by_event_type": by_event,
            "by_region": by_region,
            "by_transition_block": by_block,
            "geometry_observable": len(contributions) >= 10,
            "boundary_data_points": sum(
                1 for c in contributions
                if c.get("boundary_contribution", {}).get("confirms_boundary")
            ),
        }
