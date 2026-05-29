#!/usr/bin/env python3
"""
tests/test_batch_ingestion_v2.py — StegVerse-002

Tests for batch ingestion v2 with evidence plane integration.
Tests all modules including evidence plane contribution builder.
"""
import datetime
import json
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core_lite.batch_ingestion.graph import BatchIngestionGraph, GraphNode, GraphEdge
from core_lite.batch_ingestion.mailbox import MailboxRouter
from core_lite.batch_ingestion.discovery import DiscoveryEngine, score_candidate
from core_lite.batch_ingestion.sandbox import EphemeralSandbox
from core_lite.batch_ingestion.evidence_plane import EvidencePlaneBuilder
from core_lite.batch_ingestion.controller import BatchIngestionController


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def make_bundle(tmpdir, manifest, name="test.zip", extra_files=None):
    path = os.path.join(tmpdir, name)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("bundle_manifest.json", json.dumps(manifest, indent=2))
        if extra_files:
            for fname, content in extra_files.items():
                z.writestr(fname, content)
    return path


def candidate_manifest(
    task_hash="sha256:test-task-001",
    provider="claude", round_num=1,
    prev_ref="", prev_hash="",
):
    return {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": f"candidate_{provider}_r{round_num}",
        "transition": {
            "transition_class": "candidate",
            "authority_class": "candidate_evidence_only",
            "state_effect": "evidence_state",
            "binding_level": "non_binding",
            "task_ref": "task.md",
            "task_hash": task_hash,
            "candidate_provider": provider,
            "candidate_round": round_num,
            "previous_bundle_ref": prev_ref,
            "previous_bundle_hash": prev_hash,
        },
        "files": [{"path": "outputs/test.txt", "operation": "write",
                   "content": f"candidate from {provider}\n"}],
    }


def install_manifest(task_hash="sha256:test-task-001"):
    return {
        "schema": "stegverse.bundle_manifest.v1",
        "bundle_name": "install_test",
        "transition": {
            "transition_class": "install",
            "authority_class": "scoped_repo_write",
            "state_effect": "code_state",
            "binding_level": "commit_candidate",
            "task_ref": "task.md",
            "task_hash": task_hash,
            "allowed_paths": ["tests/fixtures/"],
            "forbidden_paths": ["secrets/"],
            "rollback_policy": "git_revert",
        },
        "files": [{"path": "tests/fixtures/install_test.txt",
                   "operation": "write", "content": "installed\n"}],
    }


def run_tests():
    results = []

    def record(name, passed, detail=""):
        results.append({"test": name, "passed": passed, "detail": detail})

    with tempfile.TemporaryDirectory() as tmpdir:
        tracking = os.path.join(tmpdir, "tracking")
        mailbox = os.path.join(tmpdir, "incoming", "mailbox")
        reports = os.path.join(tmpdir, "reports", "current")
        receipts = os.path.join(tmpdir, "receipts", "current")
        quarantine = os.path.join(tmpdir, "quarantine", "incoming")
        sandbox_dist = os.path.join(tmpdir, "dist", "sandbox")
        ep_root = os.path.join(tracking, "evidence_plane")

        # ===== EVIDENCE PLANE TESTS =====

        ep = EvidencePlaneBuilder(
            evidence_plane_root=ep_root,
            receipt_dir=receipts,
        )

        # Gate result contribution
        gate_result = {
            "decision": "ALLOW_CANDIDATE_ONLY",
            "coordinates": {"d_A": 0.1, "delta_C": 0.0, "delta_R": 0.0},
            "errors": [],
        }
        c1 = ep.from_gate_result(
            "sha256:bundle001", "sha256:task001",
            "candidate", gate_result,
            candidate_manifest()
        )
        record("ep_gate_contribution_created",
               c1.event_type == "admission" and c1.contribution_hash != "",
               f"event={c1.event_type}, hash={c1.contribution_hash[:12]}")
        record("ep_gate_written_to_disk",
               os.path.exists(os.path.join(ep_root, "evidence_plane.jsonl")),
               "evidence_plane.jsonl")

        # Quarantine contribution
        c2 = ep.from_quarantine(
            "sha256:bundle002", "sha256:task001",
            "fail_closed:missing_manifest",
            {"d_A": 1.0, "delta_C": 1.0}
        )
        record("ep_quarantine_confirms_boundary",
               c2.confirms_boundary and c2.region == "coherence_collapse",
               f"boundary={c2.confirms_boundary}, region={c2.region}")

        # Discovery route contribution
        c3 = ep.from_discovery_route(
            "sha256:bundle003", "sha256:task001",
            "synthesis", {"d_A": 0.05},
            related_bundles=["sha256:bundle001"],
            lineage_depth=1,
        )
        record("ep_discovery_route_recorded",
               c3.event_type == "synthesis" and len(c3.related_bundles) == 1,
               f"event={c3.event_type}, related={c3.related_bundles}")

        # Summary
        summary = ep.summarize()
        record("ep_summary_counts",
               summary["total_contributions"] >= 3,
               f"total={summary['total_contributions']}")
        record("ep_summary_has_boundary_data",
               summary["boundary_data_points"] >= 1,
               f"boundary_points={summary['boundary_data_points']}")
        record("ep_regions_tracked",
               len(summary["by_region"]) >= 2,
               f"regions={list(summary['by_region'].keys())}")

        # Evidence plane receipt written
        ep_receipt = os.path.join(receipts, "evidence_plane_receipt.jsonl")
        record("ep_receipt_written",
               os.path.exists(ep_receipt),
               "evidence_plane_receipt.jsonl")

        # ===== GRAPH WITH EVIDENCE PLANE TESTS =====

        graph = BatchIngestionGraph(tracking_root=tracking)
        graph.load_all()

        n = graph.add_node(GraphNode(
            node_id="ep_node001",
            node_type="candidate",
            label="test",
            attributes={"task_hash": "sha256:test"},
            evidence_plane=c1.to_dict(),
        ))
        record("graph_node_carries_evidence_plane",
               bool(graph.get_node("ep_node001").evidence_plane),
               f"ep_keys={list(graph.get_node('ep_node001').evidence_plane.keys())[:3]}")

        e = graph.add_edge(GraphEdge(
            edge_id="ep_edge001",
            from_node="ep_node001",
            to_node="ep_node001",
            relation="validated_by",
            evidence_plane=c1.to_dict(),
        ))
        record("graph_edge_carries_evidence_plane",
               bool(e.evidence_plane),
               f"ep_present={bool(e.evidence_plane)}")

        # ===== CONTROLLER WITH EVIDENCE PLANE TESTS =====

        controller = BatchIngestionController(
            repo_root=tmpdir,
            mailbox_root=mailbox,
            tracking_root=tracking,
            report_dir=reports,
            receipt_dir=receipts,
            quarantine_dir=quarantine,
            dist_dir=os.path.join(tmpdir, "dist", "bundles"),
            sandbox_dist_dir=sandbox_dist,
            entity="StegVerse-002",
            stage="SV002-M11",
            dry_run=True,
        )

        b1 = make_bundle(tmpdir, candidate_manifest(provider="claude"), "c1.zip")
        b2 = make_bundle(tmpdir, candidate_manifest(provider="openai"), "c2.zip")

        proc1 = controller.process_bundle(b1)
        record("controller_produces_ep_contributions",
               len(proc1.get("evidence_plane_contributions", [])) >= 1,
               f"contributions={len(proc1.get('evidence_plane_contributions', []))}")

        ep_contrib = proc1["evidence_plane_contributions"][0]
        record("ep_contribution_has_boundary_contribution",
               "boundary_contribution" in ep_contrib,
               f"keys={list(ep_contrib.keys())[:5]}")
        record("ep_contribution_has_relationship_signal",
               "relationship_signal" in ep_contrib,
               "relationship_signal present")
        record("ep_contribution_has_repair_signal",
               "repair_signal" in ep_contrib,
               "repair_signal present")
        record("ep_contribution_has_provider_signal",
               "provider_signal" in ep_contrib,
               f"provider={ep_contrib.get('provider_signal', {}).get('candidate_provider')}")
        record("ep_contribution_hash_set",
               bool(ep_contrib.get("contribution_hash")),
               f"hash={ep_contrib.get('contribution_hash', '')[:12]}")

        # Batch with evidence plane summary
        batch = controller.process_batch([b1, b2])
        record("batch_result_has_ep_contributions",
               len(batch.evidence_plane_contributions) >= 2,
               f"contributions={len(batch.evidence_plane_contributions)}")

        report_path = os.path.join(reports, "batch_ingestion_report.json")
        if os.path.exists(report_path):
            with open(report_path) as f:
                rpt = json.load(f)
            # It's a list now
            if isinstance(rpt, list):
                rpt = rpt[-1]
            record("batch_report_has_ep_summary",
                   "evidence_plane_summary" in rpt,
                   f"keys={list(rpt.keys())[-3:]}")
        else:
            record("batch_report_has_ep_summary", False, "report not found")

        # No-manifest → quarantine with evidence plane
        no_mf = os.path.join(tmpdir, "no_mf.zip")
        with zipfile.ZipFile(no_mf, "w") as z:
            z.writestr("README.md", "no manifest")
        proc_nm = controller.process_bundle(no_mf)
        record("no_manifest_has_ep_contribution",
               len(proc_nm.get("evidence_plane_contributions", [])) >= 1,
               f"contributions={len(proc_nm.get('evidence_plane_contributions', []))}")
        q_ep = proc_nm["evidence_plane_contributions"][0]
        record("no_manifest_ep_confirms_boundary",
               q_ep.get("boundary_contribution", {}).get("confirms_boundary") is True,
               f"confirms_boundary={q_ep.get('boundary_contribution', {}).get('confirms_boundary')}")

        # Schema version check
        record("batch_report_schema_v2",
               rpt.get("schema") == "stegverse.batch_ingestion_report.v2",
               f"schema={rpt.get('schema')}")

    # Summary
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    verdict = "PASS" if failed == 0 else "FAIL"

    print(f"Tests: {passed}/{len(results)} passed — {verdict}")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['test']}: {r['detail']}")

    os.makedirs("reports/current", exist_ok=True)
    report = {
        "schema": "stegverse.test_report.v1",
        "timestamp_utc": now_utc(),
        "test_suite": "test_batch_ingestion_v2",
        "verdict": verdict,
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "results": results,
    }
    with open("reports/current/batch_ingestion_v2_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return verdict == "PASS"


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
