#!/usr/bin/env python3
"""
scripts/create_test_fixtures.py — StegVerse-002
Creates test fixture bundles needed by the declared task smoke tests.

Creates:
  tests/fixtures/bundles/minimal_ingestible_bundle.zip
  tests/fixtures/bundles/candidate_fixture_bundle.zip
  tests/fixtures/bundles/install_fixture_bundle.zip
"""
import hashlib
import json
import os
import zipfile
import datetime


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def make_bundle(path: str, manifest: dict, extra_files: dict = None) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    manifest_bytes = json.dumps(manifest, indent=2).encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bundle_manifest.json", manifest_bytes)
        if extra_files:
            for name, content in extra_files.items():
                zf.writestr(name, content if isinstance(content, str) else json.dumps(content))
    return "sha256:" + hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    fixtures_dir = "tests/fixtures/bundles"
    os.makedirs(fixtures_dir, exist_ok=True)

    # 1. Minimal ingestible bundle — simplest valid bundle for smoke test
    minimal_manifest = {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "minimal_ingestible_bundle",
        "version": "0.1.0",
        "created_utc": now_utc(),
        "transition": {
            "transition_class": "evidence",
            "transition_cell": "SV002.TEST.MINIMAL_EVIDENCE",
            "authority_class": "evidence_only",
            "state_effect": "evidence_state",
            "binding_level": "non_binding",
            "target_scope": "core-lite",
            "execution_scope": "none",
            "admissibility_gate": "CGE+TransitionTable",
            "disposition_policy": "store_evidence_only",
            "task_ref": "task.md",
            "task_hash": "sha256:test-fixture-task-hash",
        },
        "files": [],
        "description": "Minimal fixture bundle for ingestion smoke tests.",
    }
    sha = make_bundle(
        os.path.join(fixtures_dir, "minimal_ingestible_bundle.zip"),
        minimal_manifest,
        extra_files={"README.md": "# Minimal ingestible bundle fixture\n\nFor smoke tests only.\n"}
    )
    print(f"Created minimal_ingestible_bundle.zip: {sha}")

    # 2. Candidate fixture bundle
    candidate_manifest = {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "candidate_fixture_bundle",
        "version": "0.1.0",
        "created_utc": now_utc(),
        "transition": {
            "transition_class": "candidate",
            "transition_cell": "SV002.TEST.CANDIDATE_FIXTURE",
            "authority_class": "candidate_evidence_only",
            "state_effect": "evidence_state",
            "binding_level": "non_binding",
            "target_scope": "core-lite",
            "execution_scope": "none",
            "admissibility_gate": "CGE+TransitionTable",
            "disposition_policy": "fail_closed_if_unusable_else_compare",
            "task_ref": "task.md",
            "task_hash": "sha256:test-fixture-task-hash",
            "candidate_provider": "fixture",
            "candidate_round": 1,
            "previous_bundle_ref": "",
            "previous_bundle_hash": "",
        },
        "files": [
            {
                "path": "tests/fixtures/example_output.txt",
                "operation": "write",
                "content": "fixture candidate output\n",
            }
        ],
        "description": "Candidate fixture bundle for ingestion tests.",
    }
    sha2 = make_bundle(
        os.path.join(fixtures_dir, "candidate_fixture_bundle.zip"),
        candidate_manifest
    )
    print(f"Created candidate_fixture_bundle.zip: {sha2}")

    # 3. Install fixture bundle
    install_manifest = {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "install_fixture_bundle",
        "version": "0.1.0",
        "created_utc": now_utc(),
        "transition": {
            "transition_class": "install",
            "transition_cell": "SV002.TEST.SCOPED_INSTALL_FIXTURE",
            "authority_class": "scoped_repo_write",
            "state_effect": "code_state",
            "binding_level": "commit_candidate",
            "target_scope": "core-lite",
            "execution_scope": "bounded_paths_only",
            "admissibility_gate": "CGE+TransitionTable",
            "disposition_policy": "validate_then_install_or_quarantine",
            "task_ref": "task.md",
            "task_hash": "sha256:test-fixture-task-hash",
            "allowed_paths": ["tests/fixtures/"],
            "forbidden_paths": ["secrets/", ".env"],
            "rollback_policy": "git_revert",
        },
        "files": [
            {
                "path": "tests/fixtures/example_install.txt",
                "operation": "write",
                "content": "fixture install output\n",
            }
        ],
        "description": "Install fixture bundle for ingestion tests.",
    }
    sha3 = make_bundle(
        os.path.join(fixtures_dir, "install_fixture_bundle.zip"),
        install_manifest
    )
    print(f"Created install_fixture_bundle.zip: {sha3}")

    # Write fixture index
    index = {
        "schema": "stegverse.fixture_index.v1",
        "generated_utc": now_utc(),
        "fixtures": [
            {"name": "minimal_ingestible_bundle.zip",
             "transition_class": "evidence",
             "purpose": "smoke test — simplest valid ingestible bundle"},
            {"name": "candidate_fixture_bundle.zip",
             "transition_class": "candidate",
             "purpose": "candidate ingestion gate tests"},
            {"name": "install_fixture_bundle.zip",
             "transition_class": "install",
             "purpose": "install gate tests"},
        ]
    }
    with open(os.path.join(fixtures_dir, "fixture_index.json"), "w") as f:
        json.dump(index, f, indent=2)
    print(f"Created fixture_index.json")


if __name__ == "__main__":
    main()
