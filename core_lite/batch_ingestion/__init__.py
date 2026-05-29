"""
core_lite/batch_ingestion — StegVerse-002 v2

Batch ingestion controller with evidence plane integration.

Every ingestion event is a measurement in the evidence plane —
the observable surface of admissibility geometry (Stage 32-34).

Usage:
    from core_lite.batch_ingestion import BatchIngestionController

    controller = BatchIngestionController(
        repo_root=".",
        entity="StegVerse-002",
        stage="SV002-M11",
        dry_run=False,
    )
    result = controller.process_batch(bundle_paths)
"""
from .controller import BatchIngestionController, BatchIngestionResult
from .graph import BatchIngestionGraph, GraphNode, GraphEdge
from .mailbox import MailboxRouter
from .discovery import DiscoveryEngine, DiscoveryResult
from .sandbox import EphemeralSandbox, SandboxResult
from .evidence_plane import (
    EvidencePlaneBuilder,
    EvidencePlaneContribution,
    EVENT_TYPES,
    TRANSITION_CLASS_TO_BLOCK,
    DECISION_TO_REGION,
)

__all__ = [
    "BatchIngestionController",
    "BatchIngestionResult",
    "BatchIngestionGraph",
    "GraphNode",
    "GraphEdge",
    "MailboxRouter",
    "DiscoveryEngine",
    "DiscoveryResult",
    "EphemeralSandbox",
    "SandboxResult",
    "EvidencePlaneBuilder",
    "EvidencePlaneContribution",
    "EVENT_TYPES",
    "TRANSITION_CLASS_TO_BLOCK",
    "DECISION_TO_REGION",
]
