#!/usr/bin/env python3
"""Fail-closed validation for StegVerse-002/core-lite VERSION.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATH = ROOT / "VERSION.json"


def fail(message: str) -> None:
    raise SystemExit(f"ECOSYSTEM_COMPONENT_VERSION=FAIL\n- {message}")


def main() -> None:
    data = json.loads(VERSION_PATH.read_text(encoding="utf-8"))

    exact = {
        "schema_version": "1.0.0",
        "component_id": "STEGVERSE-002-CORE-LITE",
        "repository": "StegVerse-002/core-lite",
        "component_version": "0.1.28",
        "version_stage": "DEVELOPMENT",
        "source_of_truth": "docs/CORE_LITE_MIRROR_HANDOFF.md",
        "authority_effect": "NONE",
    }
    for key, expected in exact.items():
        if data.get(key) != expected:
            fail(f"{key} mismatch: expected {expected!r}, got {data.get(key)!r}")

    release = data.get("release", {})
    if release.get("tag") is not None or release.get("commit") is not None:
        fail("DEVELOPMENT declaration may not claim an immutable release tag/commit")
    if release.get("release_evidence") != []:
        fail("DEVELOPMENT declaration may not claim release evidence")

    runtime = data.get("runtime", {})
    if runtime.get("state") != "PENDING":
        fail("runtime state must remain PENDING until repository runtime evidence closes")

    activation = data.get("activation", {})
    if activation.get("state") != "PENDING":
        fail("activation state must remain PENDING until repository activation evidence closes")

    workstream = data.get("workstream_identity", {})
    if workstream.get("handoff_capable_through") != "v0.1.28":
        fail("handoff lineage must remain bound to v0.1.27")
    if workstream.get("current_structural_result") != "EXECUTED_EXPERIMENT_READINESS_AND_RUNTIME_EVIDENCE_IMPLEMENTED_PENDING_EXECUTED_PROOF":
        fail("structural result drift")
    if workstream.get("next_required_capability") != "REVIEWER_AUTHORITY_EVIDENCE_RECONSTRUCTION":
        fail("next required capability drift")

    projection = str(activation.get("current_projection", ""))
    required_non_authority_terms = (
        "DO_NOT_GRANT_QUORUM",
        "EXECUTION",
        "REPOSITORY_BINDING",
        "RUNTIME_ACTIVATION",
    )
    for term in required_non_authority_terms:
        if term not in projection:
            fail(f"activation projection lost non-authority boundary: {term}")

    print("ECOSYSTEM_COMPONENT_VERSION=PASS")
    print("COMPONENT=STEGVERSE-002-CORE-LITE")
    print("COMPONENT_VERSION=0.1.28")
    print("VERSION_STAGE=DEVELOPMENT")
    print("RELEASE=NOT_CLAIMED")
    print("RUNTIME=PENDING")
    print("ACTIVATION=PENDING")
    print("AUTHORITY_EFFECT=NONE")


if __name__ == "__main__":
    main()
