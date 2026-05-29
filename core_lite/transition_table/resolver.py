"""
core_lite/transition_table/resolver.py — StegVerse-002
Transition Table resolver.

Reads manifest transition block → validates against policy →
computes admissibility-space coordinates (Stage 32) →
produces a TransitionDecision with receipt fields.

Enforcement order (from CGE + Transition Table Ingestion Enforcement README):
  1. Manifest transition block present
  2. transition_class declared and known
  3. Required fields present for class
  4. authority_class/state_effect/binding_level mapping valid
  5. Admissibility-space coordinates computed
  6. Decision: ALLOW / SANDBOX / REVIEW / DENY / FAIL_CLOSED

Does NOT install files. Does NOT call CGEEngine directly.
Callers (BundleIngestor) wire CGE after this resolver returns.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .attributes import TransitionAttributes

# Path to policy file relative to this module
_POLICY_PATH = os.path.join(os.path.dirname(__file__), "policy.json")


def _load_policy() -> dict:
    with open(_POLICY_PATH) as f:
        return json.load(f)


def _now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sha256(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Admissibility-space coordinate computation (Stage 32)
# ---------------------------------------------------------------------------

def _compute_coordinates(
    attrs: TransitionAttributes,
    policy_class: dict,
    errors: List[str],
    warnings: List[str],
) -> Dict[str, float]:
    """
    Compute boundary distance metrics from Stage 32 coordinate definitions.

    Metrics are in [0.0, 1.0] where 0.0 = no deficit, 1.0 = full collapse.
    These are heuristic approximations based on manifest evidence alone.
    Full numeric computation requires runtime state (future: CGE integration).
    """
    coords: Dict[str, float] = {}

    # delta_C — coherence deficit
    # Coherence collapses when transition_class is unknown or manifest is malformed
    fatal_errors = [e for e in errors if "FAIL_CLOSED" in e or "missing" in e.lower()
                    or "malformed" in e.lower() or "unknown" in e.lower()]
    coords["delta_C"] = min(1.0, len(fatal_errors) * 0.5)

    # delta_R — recoverability deficit
    # Non-binding transitions are fully recoverable; binding transitions have deficit
    binding = attrs.binding_level
    if binding == "non_binding":
        coords["delta_R"] = 0.0
    elif binding == "commit_candidate":
        coords["delta_R"] = 0.3
    elif binding == "potentially_binding":
        coords["delta_R"] = 0.6
    else:
        coords["delta_R"] = 0.2

    # delta_P — purpose convergence deficit
    # Candidate with task_hash: purpose is clear (low deficit)
    if attrs.task_hash:
        coords["delta_P"] = 0.0
    elif attrs.transition_class in ("candidate", "repair", "install"):
        coords["delta_P"] = 0.5  # task_hash missing but class requires it
    else:
        coords["delta_P"] = 0.1

    # delta_U — operator authority deficit
    # Candidate evidence: operator authority preserved (non_binding)
    # Install/execution: needs explicit authority fields
    if attrs.authority_class == "candidate_evidence_only":
        coords["delta_U"] = 0.0
    elif attrs.authority_class == "scoped_repo_write":
        coords["delta_U"] = 0.1 if attrs.allowed_paths else 0.4
    elif attrs.authority_class == "execution_request":
        has_auth = bool(attrs.operator_authority_ref and attrs.approval_ref)
        coords["delta_U"] = 0.0 if has_auth else 0.9
    else:
        coords["delta_U"] = 0.3

    # delta_O — observability deficit
    # Candidate with provider + round: fully observable
    if attrs.candidate_provider and attrs.candidate_round:
        coords["delta_O"] = 0.0
    elif attrs.transition_class == "candidate":
        coords["delta_O"] = 0.3
    else:
        coords["delta_O"] = 0.1

    # d_boundary_A — distance to boundary (combined recoverability + authority)
    coords["d_boundary_A"] = round(
        (coords["delta_R"] + coords["delta_U"]) / 2.0, 3
    )

    # d_A — distance to admissible region (all deficits, weighted)
    coords["d_A"] = round(
        coords["delta_C"] * 0.4
        + coords["delta_R"] * 0.2
        + coords["delta_P"] * 0.15
        + coords["delta_U"] * 0.15
        + coords["delta_O"] * 0.1,
        3,
    )

    return coords


# ---------------------------------------------------------------------------
# Decision mapping (Stage 32 regions)
# ---------------------------------------------------------------------------

def _map_decision(
    coords: Dict[str, float],
    errors: List[str],
    transition_class: str,
) -> Tuple[str, str]:
    """
    Map coordinates to a decision class and basis string.
    Returns (decision, basis).
    """
    # FAIL_CLOSED: coherence collapse
    if coords["delta_C"] >= 0.5:
        return "FAIL_CLOSED", "coherence_deficit >= 0.5 — transition cannot safely continue"

    # DENY: outside admissible region, coherent
    if coords["d_A"] >= 0.7:
        return "DENY", f"distance_to_admissible_region={coords['d_A']} — transition exits admissible space"

    # REVIEW: observability insufficient
    if coords["delta_O"] >= 0.4:
        return "REVIEW", f"observability_deficit={coords['delta_O']} — insufficient observability to classify"

    # SANDBOX: near boundary, bounded uncertainty
    if 0.3 <= coords["d_boundary_A"] < 0.6:
        return "SANDBOX", f"boundary_distance={coords['d_boundary_A']} — near boundary, bounded exploration"

    # Candidate-specific: accepted for comparison or synthesis
    if transition_class == "candidate":
        if coords["d_A"] < 0.2:
            return "ALLOW_CANDIDATE_ONLY", "candidate inside admissible region — accepted for comparison/synthesis"
        return "ALLOW_CANDIDATE_ONLY", "candidate accepted for comparison with warnings"

    # General ALLOW
    return "ALLOW", f"transition inside admissible region (d_A={coords['d_A']})"


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class TransitionDecision:
    transition_class: str
    transition_cell: str
    authority_class: str
    state_effect: str
    binding_level: str
    decision: str
    basis: str
    errors: List[str]
    warnings: List[str]
    coordinates: Dict[str, float]
    candidate_disposition: str  # CANDIDATE_FAIL_CLOSED / CANDIDATE_ACCEPTED_FOR_COMPARISON / etc.
    installs_code: bool
    attributes: TransitionAttributes
    timestamp_utc: str = field(default_factory=_now_utc)

    def to_dict(self) -> dict:
        return {
            "schema": "stegverse.transition_table_decision.v1",
            "timestamp_utc": self.timestamp_utc,
            "transition_class": self.transition_class,
            "transition_cell": self.transition_cell,
            "authority_class": self.authority_class,
            "state_effect": self.state_effect,
            "binding_level": self.binding_level,
            "decision": self.decision,
            "basis": self.basis,
            "errors": self.errors,
            "warnings": self.warnings,
            "coordinates": self.coordinates,
            "candidate_disposition": self.candidate_disposition,
            "installs_code": self.installs_code,
            "attributes": self.attributes.to_dict(),
        }

    def is_fail_closed(self) -> bool:
        return self.decision == "FAIL_CLOSED"

    def allows_code_install(self) -> bool:
        return self.decision == "ALLOW" and self.installs_code

    def allows_candidate_processing(self) -> bool:
        return self.decision in ("ALLOW_CANDIDATE_ONLY", "ALLOW") and not self.installs_code


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

class TransitionTableResolver:
    """
    Resolves a bundle manifest's transition block against the Transition Table policy.
    Computes admissibility-space coordinates and returns a TransitionDecision.
    """

    def __init__(self, policy_path: Optional[str] = None):
        self._policy = _load_policy() if policy_path is None else self._load(policy_path)

    @staticmethod
    def _load(path: str) -> dict:
        with open(path) as f:
            return json.load(f)

    def resolve(
        self,
        manifest: dict,
        bundle_hash: str = "",
        entity: str = "",
        stage: str = "",
    ) -> TransitionDecision:
        """
        Main entry point. Takes a parsed manifest dict.
        Returns a TransitionDecision.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # --- Step 1: transition block present ---
        if "transition" not in manifest:
            errors.append("FAIL_CLOSED: manifest missing 'transition' block")
            attrs = TransitionAttributes()
            coords = {"delta_C": 1.0, "delta_R": 0.0, "delta_P": 0.0,
                      "delta_U": 0.0, "delta_O": 0.0, "d_boundary_A": 0.0, "d_A": 1.0}
            return self._make_decision(attrs, coords, errors, warnings, "")

        attrs = TransitionAttributes.from_manifest(manifest)

        # --- Step 2: transition_class declared and known ---
        tc = attrs.transition_class
        known_classes = set(self._policy.get("classes", {}).keys())
        if not tc:
            errors.append("FAIL_CLOSED: transition_class is empty")
        elif tc not in known_classes:
            errors.append(f"FAIL_CLOSED: transition_class '{tc}' is unknown (known: {sorted(known_classes)})")

        # --- Step 3: required fields for class ---
        if tc in self._policy.get("classes", {}):
            policy_class = self._policy["classes"][tc]
            for req in policy_class.get("required_fields", []):
                val = getattr(attrs, req, None)
                if not val:
                    errors.append(f"missing required field '{req}' for transition_class '{tc}'")
        else:
            policy_class = {}

        # --- Step 4: authority/state/binding mapping ---
        if tc in self._policy.get("classes", {}) and not errors:
            pc = self._policy["classes"][tc]
            if attrs.authority_class not in pc.get("allowed_authority_classes", []):
                errors.append(
                    f"authority_class '{attrs.authority_class}' not allowed for '{tc}' "
                    f"(allowed: {pc.get('allowed_authority_classes')})"
                )
            if attrs.state_effect not in pc.get("allowed_state_effects", []):
                errors.append(
                    f"state_effect '{attrs.state_effect}' not allowed for '{tc}' "
                    f"(allowed: {pc.get('allowed_state_effects')})"
                )
            if attrs.binding_level not in pc.get("allowed_binding_levels", []):
                errors.append(
                    f"binding_level '{attrs.binding_level}' not allowed for '{tc}' "
                    f"(allowed: {pc.get('allowed_binding_levels')})"
                )

        # --- Step 5: compute coordinates ---
        coords = _compute_coordinates(attrs, policy_class, errors, warnings)

        return self._make_decision(attrs, coords, errors, warnings, tc)

    def _make_decision(
        self,
        attrs: TransitionAttributes,
        coords: Dict[str, float],
        errors: List[str],
        warnings: List[str],
        tc: str,
    ) -> TransitionDecision:
        decision, basis = _map_decision(coords, errors, tc)

        # Map to candidate disposition
        candidate_disposition = ""
        if tc == "candidate":
            if decision == "FAIL_CLOSED":
                candidate_disposition = "CANDIDATE_FAIL_CLOSED"
            elif decision in ("ALLOW_CANDIDATE_ONLY", "ALLOW"):
                candidate_disposition = "CANDIDATE_ACCEPTED_FOR_COMPARISON"
            elif decision == "SANDBOX":
                candidate_disposition = "CANDIDATE_REQUIRES_REVIEW"
            elif decision == "REVIEW":
                candidate_disposition = "CANDIDATE_REQUIRES_REVIEW"
            else:
                candidate_disposition = "CANDIDATE_QUARANTINED"

        policy_class = self._policy.get("classes", {}).get(tc, {})
        installs_code = policy_class.get("installs_code", False) and decision == "ALLOW"

        return TransitionDecision(
            transition_class=attrs.transition_class,
            transition_cell=attrs.transition_cell,
            authority_class=attrs.authority_class,
            state_effect=attrs.state_effect,
            binding_level=attrs.binding_level,
            decision=decision,
            basis=basis,
            errors=errors,
            warnings=warnings,
            coordinates=coords,
            candidate_disposition=candidate_disposition,
            installs_code=installs_code,
            attributes=attrs,
        )
