"""
core_lite/batch_ingestion/discovery.py — StegVerse-002

Discovery operates over the graph after ingestion.
Stage 33: discovery is constrained shortest-path computation
over a directed, receipt-bound graph.

Discovery steps:
  1. Find all candidates for task_hash
  2. Compare candidate group (score, diff, rank)
  3. Identify previous bundle lineage
  4. Detect supersession
  5. Route valid candidates to synthesis
  6. Route install candidates to CGE + Transition Table
  7. Route bad candidates to quarantine
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .graph import BatchIngestionGraph, GraphNode, GraphEdge
from .mailbox import MailboxRouter


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_str(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Candidate scoring (Stage 32 boundary distance metrics)
# ---------------------------------------------------------------------------

def score_candidate(bundle_path: str, manifest: dict) -> dict:
    """
    Score a candidate bundle for synthesis preference.
    Returns a score dict with boundary distances and a total score.
    Lower boundary distances = better candidate.
    """
    transition = manifest.get("transition", {})
    tc = transition.get("transition_class", "")
    authority = transition.get("authority_class", "")
    binding = transition.get("binding_level", "")
    task_hash = transition.get("task_hash", "")
    provider = transition.get("candidate_provider", "")
    files = manifest.get("files", [])

    score = {
        "has_task_hash": bool(task_hash),
        "has_provider": bool(provider),
        "has_files": len(files) > 0,
        "file_count": len(files),
        "authority_valid": authority in ("candidate_evidence_only",
                                         "scoped_repo_write"),
        "binding_safe": binding in ("non_binding", "commit_candidate"),
        "d_A": 0.0,  # distance to admissible region
        "total": 0,
    }

    # Compute rough d_A from manifest evidence
    penalties = 0
    if not score["has_task_hash"]: penalties += 2
    if not score["has_provider"]: penalties += 1
    if not score["has_files"]: penalties += 3
    if not score["authority_valid"]: penalties += 2
    if not score["binding_safe"]: penalties += 2

    score["d_A"] = min(1.0, penalties * 0.1)
    score["total"] = 100 - int(score["d_A"] * 100)
    return score


# ---------------------------------------------------------------------------
# Discovery result
# ---------------------------------------------------------------------------

@dataclass
class DiscoveryResult:
    task_hash: str
    timestamp_utc: str = field(default_factory=now_utc)
    candidates_found: List[dict] = field(default_factory=list)
    lineage_chain: List[str] = field(default_factory=list)
    superseded: List[str] = field(default_factory=list)
    route_synthesis: List[str] = field(default_factory=list)
    route_install: List[str] = field(default_factory=list)
    route_sandbox: List[str] = field(default_factory=list)
    route_quarantine: List[str] = field(default_factory=list)
    route_review: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "schema": "stegverse.discovery_result.v1",
            "task_hash": self.task_hash,
            "timestamp_utc": self.timestamp_utc,
            "candidates_found": self.candidates_found,
            "lineage_chain": self.lineage_chain,
            "superseded": self.superseded,
            "route_synthesis": self.route_synthesis,
            "route_install": self.route_install,
            "route_sandbox": self.route_sandbox,
            "route_quarantine": self.route_quarantine,
            "route_review": self.route_review,
            "errors": self.errors,
            "warnings": self.warnings,
            "total_candidates": len(self.candidates_found),
            "total_routed": (len(self.route_synthesis) + len(self.route_install) +
                             len(self.route_sandbox) + len(self.route_quarantine) +
                             len(self.route_review)),
        }


# ---------------------------------------------------------------------------
# Discovery engine
# ---------------------------------------------------------------------------

class DiscoveryEngine:
    """
    Operates over the graph to classify and route candidates.
    Implements Stage 33: constrained shortest-path discovery.
    """

    def __init__(
        self,
        graph: BatchIngestionGraph,
        mailbox: MailboxRouter,
        report_dir: str = "reports/current",
        receipt_dir: str = "receipts/current",
    ):
        self.graph = graph
        self.mailbox = mailbox
        self.report_dir = report_dir
        self.receipt_dir = receipt_dir

    def _load_manifest(self, bundle_path: str) -> Optional[dict]:
        try:
            with zipfile.ZipFile(bundle_path) as z:
                if "bundle_manifest.json" in z.namelist():
                    return json.loads(z.read("bundle_manifest.json"))
        except Exception:
            pass
        return None

    def _build_lineage_chain(self, task_hash: str) -> List[str]:
        """
        Walk bundle_graph to reconstruct the lineage chain for a task.
        Returns ordered list of bundle_ids from oldest to newest.
        """
        # Find all bundle nodes for this task_hash
        bundles = self.graph.find_nodes(
            node_type="bundle",
            task_hash=task_hash
        )
        if not bundles:
            bundles = self.graph.find_nodes(
                node_type="candidate",
                task_hash=task_hash
            )

        # Build chain via supersedes edges
        chain_map: Dict[str, str] = {}  # newer -> older
        for edge in self.graph.find_edges(relation="supersedes"):
            chain_map[edge.from_node] = edge.to_node

        # Find roots (not superseded by anything)
        all_ids = {b.node_id for b in bundles}
        superseded_ids = set(chain_map.values())
        roots = all_ids - superseded_ids

        # Build ordered chain from root
        chain = []
        for root in roots:
            current = root
            while current:
                chain.append(current)
                # Find what supersedes current
                next_node = None
                for newer, older in chain_map.items():
                    if older == current:
                        next_node = newer
                        break
                current = next_node

        return chain

    def _detect_supersession(
        self, candidates: List[dict], task_hash: str
    ) -> Tuple[List[str], List[str]]:
        """
        Detect which candidates supersede previous ones.
        Returns (active_ids, superseded_ids).
        """
        # A candidate with candidate_round > 1 and previous_bundle_ref
        # supersedes the referenced bundle
        superseded = set()
        for c in candidates:
            manifest = c.get("manifest", {})
            t = manifest.get("transition", {})
            prev_ref = t.get("previous_bundle_ref", "")
            prev_hash = t.get("previous_bundle_hash", "")
            if prev_ref or prev_hash:
                # Mark the referenced bundle as superseded
                ref_id = sha256_str(prev_ref or prev_hash)[:32]
                superseded.add(ref_id)
                # Also check graph
                for node in self.graph.find_nodes():
                    node_hash = node.attributes.get("bundle_hash", "")
                    if (prev_hash and node_hash == prev_hash) or \
                       (prev_ref and node.attributes.get("bundle_name", "") == prev_ref):
                        superseded.add(node.node_id)

        active = [c["bundle_id"] for c in candidates
                  if c["bundle_id"] not in superseded]
        return active, list(superseded)

    def _route_candidate(self, candidate: dict) -> str:
        """
        Route a single candidate to: synthesis / install / sandbox / review / quarantine
        """
        disposition = candidate.get("disposition", "")
        transition_class = candidate.get("transition_class", "")
        score = candidate.get("score", {})

        # Fail-closed → quarantine
        if disposition == "CANDIDATE_FAIL_CLOSED":
            return "quarantine"

        # Install class → install route (goes to CGE+TT again)
        if transition_class == "install":
            return "install"

        # Repair class → sandbox
        if transition_class == "repair":
            return "sandbox"

        # High boundary distance → sandbox for repair
        d_A = score.get("d_A", 0.0)
        if d_A > 0.5:
            return "sandbox"

        # Review required
        if disposition == "CANDIDATE_REQUIRES_REVIEW":
            return "review"

        # Accepted for comparison → synthesis
        if disposition in ("CANDIDATE_ACCEPTED_FOR_COMPARISON",
                           "CANDIDATE_ACCEPTED_FOR_SYNTHESIS"):
            return "synthesis"

        # Supersedes previous → synthesis (it's the better version)
        if disposition == "CANDIDATE_SUPERSEDES_PREVIOUS":
            return "synthesis"

        # Default: quarantine unknown dispositions
        return "quarantine"

    def discover(self, task_hash: str, candidate_bundles: List[dict]) -> DiscoveryResult:
        """
        Main discovery entry point.
        candidate_bundles: list of {bundle_path, bundle_id, manifest,
                                    disposition, transition_class, score}
        """
        result = DiscoveryResult(task_hash=task_hash)
        result.candidates_found = candidate_bundles

        if not candidate_bundles:
            result.warnings.append("no candidates found for task_hash")
            return result

        # Step 3: Identify lineage
        result.lineage_chain = self._build_lineage_chain(task_hash)

        # Step 4: Detect supersession
        active_ids, superseded_ids = self._detect_supersession(
            candidate_bundles, task_hash
        )
        result.superseded = superseded_ids

        # Step 5-7: Route each candidate
        for candidate in candidate_bundles:
            bundle_id = candidate.get("bundle_id", "")
            route = self._route_candidate(candidate)

            if route == "synthesis":
                result.route_synthesis.append(bundle_id)
                # Add comparison edge in graph
                for other in candidate_bundles:
                    if other["bundle_id"] != bundle_id:
                        edge_id = self.graph.make_edge_id(
                            bundle_id, other["bundle_id"], "compared_with"
                        )
                        self.graph.add_edge(GraphEdge(
                            edge_id=edge_id,
                            from_node=bundle_id,
                            to_node=other["bundle_id"],
                            relation="compared_with",
                            coordinates=candidate.get("score", {}),
                        ))

            elif route == "install":
                result.route_install.append(bundle_id)

            elif route == "sandbox":
                result.route_sandbox.append(bundle_id)

            elif route == "review":
                result.route_review.append(bundle_id)

            else:
                result.route_quarantine.append(bundle_id)
                # Add quarantine edge
                qnode_id = self.graph.make_node_id("quarantine", bundle_id)
                self.graph.add_node(GraphNode(
                    node_id=qnode_id,
                    node_type="quarantine_state",
                    label=f"quarantine:{bundle_id[:12]}",
                    attributes={
                        "bundle_id": bundle_id,
                        "task_hash": task_hash,
                        "reason": candidate.get("disposition", "unknown"),
                    }
                ))
                edge_id = self.graph.make_edge_id(bundle_id, qnode_id, "quarantined_as")
                self.graph.add_edge(GraphEdge(
                    edge_id=edge_id,
                    from_node=bundle_id,
                    to_node=qnode_id,
                    relation="quarantined_as",
                ))

        return result

    def write_report(self, result: DiscoveryResult) -> str:
        """Write discovery report and receipt. Returns report path."""
        os.makedirs(self.report_dir, exist_ok=True)
        os.makedirs(self.receipt_dir, exist_ok=True)

        report = result.to_dict()
        report_path = os.path.join(self.report_dir, "route_discovery_report.json")

        existing = []
        if os.path.exists(report_path):
            try:
                with open(report_path) as f:
                    existing = json.load(f)
                if not isinstance(existing, list):
                    existing = [existing]
            except Exception:
                existing = []
        existing.append(report)
        with open(report_path, "w") as f:
            json.dump(existing, f, indent=2)

        receipt_path = os.path.join(self.receipt_dir, "route_discovery_receipt.jsonl")
        with open(receipt_path, "a") as f:
            f.write(json.dumps(report, sort_keys=True) + "\n")

        return report_path
