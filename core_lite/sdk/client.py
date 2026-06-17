from __future__ import annotations

from pathlib import Path
from typing import Any

from core_lite.bundles.ingest import BundleIngestor
from core_lite.candidates import CandidateApplier, CandidateReviewer
from core_lite.incoming import IncomingMailbox
from core_lite.transition_table.resolver import TransitionTableResolver


class CoreLiteClient:
    """Small governed SDK wrapper for stable Core-Lite operations.

    This SDK exposes only existing governed boundaries. It does not provide raw
    mutation authority or bypass BundleIngestor, candidate review, receipts, or
    transition-table policy.
    """

    def __init__(self, repo_root: str | Path = ".", *, entity: str = "StegVerse-002") -> None:
        self.repo_root = Path(repo_root)
        self.entity = entity

    def resolve_transition(self, manifest: dict[str, Any]) -> dict[str, Any]:
        decision = TransitionTableResolver().resolve(manifest, entity=self.entity, stage="SV002-M15")
        return decision.to_dict()

    def ingest_bundle(self, bundle_path: str | Path, *, dry_run: bool = False) -> dict[str, Any]:
        return BundleIngestor(self.repo_root, entity=self.entity, stage="SV002-M15", dry_run=dry_run).ingest(bundle_path)

    def process_incoming(self, incoming_dir: str | Path = "incoming", *, dry_run: bool = False) -> dict[str, Any]:
        return IncomingMailbox(self.repo_root, incoming_dir, entity=self.entity, stage="SV002-M15", dry_run=dry_run).process()

    def review_candidate(self, candidate_ref: str | Path) -> dict[str, Any]:
        return CandidateReviewer(self.repo_root, entity=self.entity, stage="SV002-M15").review(candidate_ref)

    def apply_candidate(self, candidate_ref: str | Path, review_report: str | Path) -> dict[str, Any]:
        return CandidateApplier(self.repo_root, entity=self.entity, stage="SV002-M15").apply(candidate_ref, review_report)
