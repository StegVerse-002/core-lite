"""
core_lite/batch_ingestion/graph.py — StegVerse-002

Four-graph node/edge store for the batch ingestion system.

Graphs:
  task_graph       — tasks and their bundles
  bundle_graph     — bundle lineage chain
  transition_graph — admissibility decisions as edges
  comparison_graph — candidate comparisons and synthesis

Each graph is persisted as a JSONL append-log under tracking/{graph_name}/.
Nodes and edges are hash-bound and receipt-linked.
Discovery operates over these graphs.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_str(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Node and Edge types
# ---------------------------------------------------------------------------

@dataclass
class GraphNode:
    node_id: str
    node_type: str          # task | bundle | candidate | merged_candidate
                            # test_result | install_bundle | receipt
                            # formalism_registry | quarantine_state
    label: str
    attributes: Dict = field(default_factory=dict)
    created_utc: str = field(default_factory=now_utc)
    receipt_hash: str = ""
    evidence_plane: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GraphEdge:
    edge_id: str
    from_node: str
    to_node: str
    relation: str           # produced_candidate | contained_in_bundle
                            # references_formalism | validated_by
                            # compared_with | synthesized_into
                            # tested_by | packaged_into | supersedes
                            # quarantined_as | installed_as
                            # repaired_by | sandbox_explored
    attributes: Dict = field(default_factory=dict)
    created_utc: str = field(default_factory=now_utc)
    receipt_hash: str = ""
    # Stage 32 coordinates on this edge
    coordinates: Dict = field(default_factory=dict)
    evidence_plane: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Graph store
# ---------------------------------------------------------------------------

GRAPH_NAMES = ["task_graph", "bundle_graph", "transition_graph", "comparison_graph"]


class BatchIngestionGraph:
    """
    Persistent four-graph store.
    Each graph is an append-only JSONL file under tracking/{graph_name}/graph.jsonl
    """

    def __init__(self, tracking_root: str = "tracking"):
        self.tracking_root = tracking_root
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, GraphEdge] = {}
        self._loaded = False

    def _graph_path(self, graph_name: str) -> str:
        return os.path.join(self.tracking_root, graph_name, "graph.jsonl")

    def _ensure_dirs(self) -> None:
        for name in GRAPH_NAMES:
            os.makedirs(os.path.join(self.tracking_root, name), exist_ok=True)

    def load_all(self) -> None:
        """Load all graph entries from disk into memory."""
        self._ensure_dirs()
        for graph_name in GRAPH_NAMES:
            path = self._graph_path(graph_name)
            if not os.path.exists(path):
                continue
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("record_type") == "node":
                            n = GraphNode(**{k: v for k, v in entry.items()
                                           if k != "record_type"})
                            self._nodes[n.node_id] = n
                        elif entry.get("record_type") == "edge":
                            e = GraphEdge(**{k: v for k, v in entry.items()
                                           if k != "record_type"})
                            self._edges[e.edge_id] = e
                    except Exception:
                        pass
        self._loaded = True

    def _append(self, graph_name: str, record: dict) -> None:
        self._ensure_dirs()
        path = self._graph_path(graph_name)
        with open(path, "a") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

    def _node_graph(self, node_type: str) -> str:
        """Route node to correct graph."""
        if node_type == "task":
            return "task_graph"
        elif node_type in ("bundle", "install_bundle"):
            return "bundle_graph"
        elif node_type in ("candidate", "merged_candidate", "test_result",
                           "quarantine_state"):
            return "comparison_graph"
        else:
            return "transition_graph"

    def _edge_graph(self, relation: str) -> str:
        """Route edge to correct graph."""
        if relation in ("produced_candidate", "contained_in_bundle"):
            return "task_graph"
        elif relation in ("supersedes", "installed_as", "references_formalism"):
            return "bundle_graph"
        elif relation in ("compared_with", "synthesized_into", "tested_by",
                          "quarantined_as", "repaired_by", "sandbox_explored"):
            return "comparison_graph"
        else:
            return "transition_graph"

    def add_node(self, node: GraphNode) -> GraphNode:
        """Add or update a node."""
        self._nodes[node.node_id] = node
        record = {"record_type": "node", **node.to_dict()}
        self._append(self._node_graph(node.node_type), record)
        return node

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        """Add an edge."""
        self._edges[edge.edge_id] = edge
        record = {"record_type": "edge", **edge.to_dict()}
        self._append(self._edge_graph(edge.relation), record)
        return edge

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def find_nodes(self, node_type: str = None, **attrs) -> List[GraphNode]:
        results = []
        for node in self._nodes.values():
            if node_type and node.node_type != node_type:
                continue
            match = all(node.attributes.get(k) == v for k, v in attrs.items())
            if match:
                results.append(node)
        return results

    def find_edges(self, from_node: str = None, to_node: str = None,
                   relation: str = None) -> List[GraphEdge]:
        results = []
        for edge in self._edges.values():
            if from_node and edge.from_node != from_node:
                continue
            if to_node and edge.to_node != to_node:
                continue
            if relation and edge.relation != relation:
                continue
            results.append(edge)
        return results

    def node_exists(self, node_id: str) -> bool:
        return node_id in self._nodes

    def make_node_id(self, prefix: str, *parts: str) -> str:
        combined = ":".join([prefix] + list(parts))
        return sha256_str(combined)[:32]

    def make_edge_id(self, from_node: str, to_node: str, relation: str) -> str:
        return sha256_str(f"{from_node}:{relation}:{to_node}")[:32]

    def summary(self) -> dict:
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "nodes_by_type": self._count_by("node_type", self._nodes.values()),
            "edges_by_relation": self._count_by("relation", self._edges.values()),
        }

    @staticmethod
    def _count_by(attr: str, items) -> dict:
        counts: Dict[str, int] = {}
        for item in items:
            key = getattr(item, attr, "unknown")
            counts[key] = counts.get(key, 0) + 1
        return counts
