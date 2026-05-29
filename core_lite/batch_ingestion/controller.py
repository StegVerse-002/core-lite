"""
core_lite/batch_ingestion/controller.py — StegVerse-002 v2

Full batch ingestion controller with evidence plane integration.

Every event — admission, quarantine, sandbox, install, failure,
discovery route, supersession — writes an evidence plane contribution.
The evidence plane is the observable surface of admissibility geometry.

Enforced loop:
  incoming bundle
  → Transition Table gate + CGE
  → evidence plane: gate measurement
  → mailbox routing by task_hash
  → graph node registered (with evidence_plane field)
  → discovery: group, compare, lineage, supersession, route
  → evidence plane: discovery route measurement
  → synthesis / sandbox / install / quarantine
  → evidence plane: outcome measurement
  → batch reports + receipts (all carry evidence_plane)
  → tracking/evidence_plane/evidence_plane.jsonl updated
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .graph import BatchIngestionGraph, GraphNode, GraphEdge
from .mailbox import MailboxRouter
from .discovery import DiscoveryEngine, score_candidate
from .sandbox import EphemeralSandbox, SandboxResult
from .evidence_plane import EvidencePlaneBuilder, EvidencePlaneContribution


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def sha256_str(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


def append_receipt(path: str, record: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def write_report(path: str, record: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = []
    if os.path.exists(path):
        try:
            with open(path) as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            existing = []
    existing.append(record)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)


def load_manifest(bundle_path: str) -> Optional[dict]:
    try:
        with zipfile.ZipFile(bundle_path) as z:
            if "bundle_manifest.json" in z.namelist():
                return json.loads(z.read("bundle_manifest.json"))
    except Exception:
        pass
    return None


@dataclass
class BatchIngestionResult:
    batch_id: str
    timestamp_utc: str = field(default_factory=now_utc)
    bundles_processed: int = 0
    bundles_admitted: int = 0
    bundles_quarantined: int = 0
    bundles_sandboxed: int = 0
    bundles_installed: int = 0
    candidates_found: int = 0
    synthesis_attempted: bool = False
    sandbox_runs: List[dict] = field(default_factory=list)
    install_results: List[dict] = field(default_factory=list)
    quarantine_results: List[dict] = field(default_factory=list)
    evidence_plane_contributions: List[dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "schema": "stegverse.batch_ingestion_report.v2",
            "batch_id": self.batch_id,
            "timestamp_utc": self.timestamp_utc,
            "bundles_processed": self.bundles_processed,
            "bundles_admitted": self.bundles_admitted,
            "bundles_quarantined": self.bundles_quarantined,
            "bundles_sandboxed": self.bundles_sandboxed,
            "bundles_installed": self.bundles_installed,
            "candidates_found": self.candidates_found,
            "synthesis_attempted": self.synthesis_attempted,
            "sandbox_runs": self.sandbox_runs,
            "install_results": self.install_results,
            "quarantine_results": self.quarantine_results,
            "evidence_plane_contributions": self.evidence_plane_contributions,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class BatchIngestionController:
    """
    Orchestrates the full governed ingestion loop with evidence plane.
    """

    def __init__(
        self,
        repo_root: str = ".",
        mailbox_root: str = "incoming/mailbox",
        tracking_root: str = "tracking",
        report_dir: str = "reports/current",
        receipt_dir: str = "receipts/current",
        quarantine_dir: str = "quarantine/incoming",
        dist_dir: str = "dist/bundles",
        sandbox_dist_dir: str = "dist/sandbox",
        entity: str = "StegVerse-002",
        stage: str = "SV002-M11",
        dry_run: bool = False,
    ):
        self.repo_root = repo_root
        self.report_dir = report_dir
        self.receipt_dir = receipt_dir
        self.quarantine_dir = quarantine_dir
        self.dist_dir = dist_dir
        self.entity = entity
        self.stage = stage
        self.dry_run = dry_run

        self.graph = BatchIngestionGraph(tracking_root=tracking_root)
        self.mailbox = MailboxRouter(mailbox_root=mailbox_root)
        self.discovery = DiscoveryEngine(
            graph=self.graph,
            mailbox=self.mailbox,
            report_dir=report_dir,
            receipt_dir=receipt_dir,
        )
        self.sandbox = EphemeralSandbox(
            repo_root=repo_root,
            report_dir=report_dir,
            receipt_dir=receipt_dir,
            dist_dir=sandbox_dist_dir,
        )
        self.evidence = EvidencePlaneBuilder(
            evidence_plane_root=os.path.join(tracking_root, "evidence_plane"),
            receipt_dir=receipt_dir,
        )

        self.graph.load_all()

    def _try_transition_table_gate(self, bundle_path: str, manifest: dict) -> dict:
        try:
            from core_lite.transition_table.ingest_gate import (
                ingest_with_transition_gate
            )
            return ingest_with_transition_gate(
                bundle_path=bundle_path,
                entity=self.entity,
                stage=self.stage,
                repo_root=self.repo_root,
                dry_run=self.dry_run,
            )
        except ImportError:
            t = manifest.get("transition", {}) if manifest else {}
            tc = t.get("transition_class", "")
            return {
                "decision": "ALLOW_CANDIDATE_ONLY" if tc == "candidate" else "ALLOW",
                "transition_class": tc,
                "candidate_disposition": (
                    "CANDIDATE_ACCEPTED_FOR_COMPARISON" if tc == "candidate" else ""
                ),
                "coordinates": {"d_A": 0.1},
                "errors": [],
                "warnings": ["TransitionTable not installed — manifest fallback"],
                "installs_code": tc == "install",
            }
        except Exception as e:
            return {
                "decision": "FAIL_CLOSED",
                "transition_class": "",
                "candidate_disposition": "CANDIDATE_FAIL_CLOSED",
                "coordinates": {"d_A": 1.0, "delta_C": 1.0},
                "errors": [f"gate error: {e}"],
                "warnings": [],
                "installs_code": False,
            }

    def _quarantine_bundle(
        self, bundle_path: str, reason: str, task_hash: str,
        manifest: Optional[dict], bundle_hash: str,
        ep_contrib: dict = None,
    ) -> dict:
        qdir = os.path.join(self.quarantine_dir, "batch")
        os.makedirs(qdir, exist_ok=True)
        dest = os.path.join(qdir, os.path.basename(bundle_path))

        if not self.dry_run and os.path.exists(bundle_path):
            shutil.copy2(bundle_path, dest)

        record = {
            "schema": "stegverse.quarantine_receipt.v2",
            "timestamp_utc": now_utc(),
            "bundle_path": bundle_path,
            "bundle_hash": bundle_hash,
            "task_hash": task_hash,
            "reason": reason,
            "quarantine_dest": dest,
            "metric_preservation": {
                "bundle_hash": bundle_hash,
                "manifest_hash": sha256_str(
                    json.dumps(manifest, sort_keys=True)
                ) if manifest else "",
                "reason": reason,
            },
            "evidence_plane": ep_contrib or {},
            "dry_run": self.dry_run,
        }
        append_receipt(
            os.path.join(self.receipt_dir, "batch_ingestion_receipt.jsonl"),
            record
        )
        return record

    def _install_bundle(
        self, bundle_path: str, manifest: dict,
        bundle_hash: str, gate_result: dict,
    ) -> dict:
        result = {
            "schema": "stegverse.install_result.v2",
            "timestamp_utc": now_utc(),
            "bundle_path": bundle_path,
            "bundle_hash": bundle_hash,
            "decision": "INSTALL_ATTEMPTED",
            "files_written": [],
            "files_skipped": [],
            "errors": [],
            "evidence_plane": {},
            "dry_run": self.dry_run,
        }

        allowed_paths = manifest.get("transition", {}).get("allowed_paths", [])
        forbidden_paths = manifest.get("transition", {}).get("forbidden_paths", [])

        try:
            with zipfile.ZipFile(bundle_path) as z:
                for item in z.infolist():
                    if item.filename == "bundle_manifest.json":
                        continue
                    allowed = any(
                        item.filename.startswith(ap.rstrip("/"))
                        for ap in allowed_paths
                    ) if allowed_paths else True
                    forbidden = any(
                        item.filename.startswith(fp.rstrip("/"))
                        for fp in forbidden_paths
                    )
                    if forbidden:
                        result["files_skipped"].append(f"{item.filename} (forbidden)")
                        continue
                    if not allowed:
                        result["files_skipped"].append(
                            f"{item.filename} (not in allowed_paths)"
                        )
                        continue
                    if not self.dry_run:
                        dest = os.path.join(self.repo_root, item.filename)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with z.open(item) as src, open(dest, "wb") as dst:
                            dst.write(src.read())
                        result["files_written"].append(item.filename)
                    else:
                        result["files_written"].append(f"{item.filename} (dry_run)")
            result["decision"] = "INSTALL_COMPLETE"
        except Exception as e:
            result["errors"].append(str(e))
            result["decision"] = "INSTALL_FAILED"

        append_receipt(
            os.path.join(self.receipt_dir, "batch_ingestion_receipt.jsonl"),
            result
        )
        return result

    def process_bundle(self, bundle_path: str) -> dict:
        bundle_hash = sha256_file(bundle_path) if os.path.exists(bundle_path) else ""
        manifest = load_manifest(bundle_path)

        result = {
            "bundle_path": bundle_path,
            "bundle_hash": bundle_hash,
            "manifest": manifest,
            "gate_result": None,
            "mailbox_result": None,
            "sandbox_results": [],
            "install_result": None,
            "quarantine_result": None,
            "evidence_plane_contributions": [],
            "final_disposition": "UNKNOWN",
        }

        if manifest is None:
            ep = self.evidence.from_quarantine(
                bundle_hash, "", "no_manifest",
                {"d_A": 1.0, "delta_C": 1.0}
            )
            result["evidence_plane_contributions"].append(ep.to_dict())
            qr = self._quarantine_bundle(
                bundle_path, "no_manifest", "", None, bundle_hash,
                ep_contrib=ep.to_dict()
            )
            result["quarantine_result"] = qr
            result["final_disposition"] = "QUARANTINED_NO_MANIFEST"
            return result

        task_hash = manifest.get("transition", {}).get("task_hash", "")
        transition_class = manifest.get("transition", {}).get("transition_class", "")
        candidate_round = manifest.get("transition", {}).get("candidate_round", 0)
        candidate_provider = manifest.get("transition", {}).get("candidate_provider", "")

        # Register task node
        if task_hash:
            task_ref = manifest.get("transition", {}).get("task_ref", "")
            task_node_id = self.graph.make_node_id("task", task_hash)
            if not self.graph.node_exists(task_node_id):
                self.graph.add_node(GraphNode(
                    node_id=task_node_id,
                    node_type="task",
                    label=f"task:{task_ref or task_hash[:12]}",
                    attributes={"task_hash": task_hash, "task_ref": task_ref},
                ))

        # Register bundle node
        bundle_node_id = self.graph.make_node_id("bundle", bundle_hash)
        self.graph.add_node(GraphNode(
            node_id=bundle_node_id,
            node_type=transition_class if transition_class in (
                "candidate", "install", "repair", "evidence") else "bundle",
            label=f"{transition_class}:{os.path.basename(bundle_path)}",
            attributes={
                "bundle_hash": bundle_hash,
                "bundle_path": bundle_path,
                "task_hash": task_hash,
                "transition_class": transition_class,
                "candidate_round": candidate_round,
                "candidate_provider": candidate_provider,
            }
        ))

        if task_hash:
            self.graph.add_edge(GraphEdge(
                edge_id=self.graph.make_edge_id(
                    task_node_id, bundle_node_id, "produced_candidate"
                ),
                from_node=task_node_id,
                to_node=bundle_node_id,
                relation="produced_candidate",
            ))

        # Transition Table + CGE gate
        gate_result = self._try_transition_table_gate(bundle_path, manifest)
        result["gate_result"] = gate_result
        decision = gate_result.get("decision", "FAIL_CLOSED")

        # Evidence plane: gate measurement
        ep_gate = self.evidence.from_gate_result(
            bundle_hash, task_hash, transition_class, gate_result, manifest
        )
        result["evidence_plane_contributions"].append(ep_gate.to_dict())

        # Update bundle node with evidence plane
        self.graph.add_node(GraphNode(
            node_id=bundle_node_id,
            node_type=transition_class if transition_class in (
                "candidate", "install", "repair", "evidence") else "bundle",
            label=f"{transition_class}:{os.path.basename(bundle_path)}",
            attributes={
                "bundle_hash": bundle_hash,
                "task_hash": task_hash,
                "transition_class": transition_class,
                "candidate_round": candidate_round,
                "candidate_provider": candidate_provider,
                "decision": decision,
            },
            evidence_plane=ep_gate.to_dict(),
        ))

        # Transition decision node
        transition_node_id = self.graph.make_node_id("transition", bundle_hash, decision)
        self.graph.add_node(GraphNode(
            node_id=transition_node_id,
            node_type="receipt",
            label=f"tt_decision:{decision}",
            attributes={
                "decision": decision,
                "bundle_hash": bundle_hash,
                "coordinates": gate_result.get("coordinates", {}),
            },
            evidence_plane=ep_gate.to_dict(),
        ))
        self.graph.add_edge(GraphEdge(
            edge_id=self.graph.make_edge_id(
                bundle_node_id, transition_node_id, "validated_by"
            ),
            from_node=bundle_node_id,
            to_node=transition_node_id,
            relation="validated_by",
            coordinates=gate_result.get("coordinates", {}),
            evidence_plane=ep_gate.to_dict(),
        ))

        # Route by decision
        if decision == "FAIL_CLOSED":
            ep_q = self.evidence.from_quarantine(
                bundle_hash, task_hash,
                f"fail_closed:{(gate_result.get('errors') or ['unknown'])[0]}",
                gate_result.get("coordinates", {}),
            )
            result["evidence_plane_contributions"].append(ep_q.to_dict())
            qr = self._quarantine_bundle(
                bundle_path,
                f"fail_closed:{(gate_result.get('errors') or ['unknown'])[0]}",
                task_hash, manifest, bundle_hash,
                ep_contrib=ep_q.to_dict()
            )
            result["quarantine_result"] = qr
            result["final_disposition"] = "QUARANTINED_FAIL_CLOSED"
            mr = self.mailbox.route(
                bundle_path, task_hash, transition_class,
                "CANDIDATE_FAIL_CLOSED", self.dry_run
            )
            result["mailbox_result"] = mr
            return result

        candidate_disposition = gate_result.get("candidate_disposition", "")
        installs_code = gate_result.get("installs_code", False)

        # Mailbox routing
        mr = self.mailbox.route(
            bundle_path, task_hash, transition_class,
            candidate_disposition, self.dry_run
        )
        result["mailbox_result"] = mr

        score = score_candidate(bundle_path, manifest)

        # Sandbox if needed
        if (decision == "SANDBOX" or
            (transition_class == "candidate" and score.get("d_A", 0) > 0.3
             and not installs_code)):

            sandbox_result = self.sandbox.run(
                bundle_path, task_hash, dry_run=self.dry_run
            )
            result["sandbox_results"].append(sandbox_result.to_dict())

            # Evidence plane: sandbox measurement
            ep_sb = self.evidence.from_sandbox_result(
                bundle_hash, task_hash, sandbox_result
            )
            result["evidence_plane_contributions"].append(ep_sb.to_dict())

            # Recursive repair follow-up
            if sandbox_result.verdict in ("PASS", "PARTIAL") and \
               sandbox_result.repair_bundle_path and not self.dry_run:
                repair_result = self.process_bundle(
                    sandbox_result.repair_bundle_path
                )
                result["sandbox_results"].append({
                    "sandbox_id": sandbox_result.sandbox_id,
                    "repair_followup": repair_result,
                })

            # Graph: sandbox node
            sandbox_node_id = self.graph.make_node_id(
                "sandbox", sandbox_result.sandbox_id
            )
            self.graph.add_node(GraphNode(
                node_id=sandbox_node_id,
                node_type="test_result",
                label=f"sandbox:{sandbox_result.verdict}",
                attributes={
                    "verdict": sandbox_result.verdict,
                    "boundary_before": sandbox_result.boundary_distance_before,
                    "boundary_after": sandbox_result.boundary_distance_after,
                },
                evidence_plane=ep_sb.to_dict(),
            ))
            self.graph.add_edge(GraphEdge(
                edge_id=self.graph.make_edge_id(
                    bundle_node_id, sandbox_node_id, "sandbox_explored"
                ),
                from_node=bundle_node_id,
                to_node=sandbox_node_id,
                relation="sandbox_explored",
                evidence_plane=ep_sb.to_dict(),
            ))

        # Install if allowed
        if installs_code and decision == "ALLOW":
            install_result = self._install_bundle(
                bundle_path, manifest, bundle_hash, gate_result
            )
            ep_install = self.evidence.from_install_result(
                bundle_hash, task_hash, install_result
            )
            result["evidence_plane_contributions"].append(ep_install.to_dict())
            install_result["evidence_plane"] = ep_install.to_dict()
            result["install_result"] = install_result
            result["final_disposition"] = (
                "INSTALLED" if install_result["decision"] == "INSTALL_COMPLETE"
                else "INSTALL_FAILED"
            )

            install_node_id = self.graph.make_node_id("install", bundle_hash)
            self.graph.add_node(GraphNode(
                node_id=install_node_id,
                node_type="install_bundle",
                label=f"install:{install_result['decision']}",
                attributes={"decision": install_result["decision"]},
                evidence_plane=ep_install.to_dict(),
            ))
            self.graph.add_edge(GraphEdge(
                edge_id=self.graph.make_edge_id(
                    bundle_node_id, install_node_id, "installed_as"
                ),
                from_node=bundle_node_id,
                to_node=install_node_id,
                relation="installed_as",
                evidence_plane=ep_install.to_dict(),
            ))

        elif transition_class == "candidate":
            result["final_disposition"] = f"CANDIDATE_{candidate_disposition}"
        elif decision in ("ALLOW", "ALLOW_CANDIDATE_ONLY"):
            result["final_disposition"] = "ADMITTED"
        else:
            result["final_disposition"] = f"ROUTED_{decision}"

        return result

    def process_batch(self, bundle_paths: List[str]) -> BatchIngestionResult:
        batch_id = sha256_str(
            ":".join(bundle_paths) + now_utc()
        ).replace("sha256:", "")[:16]

        batch_result = BatchIngestionResult(batch_id=batch_id)
        task_groups: Dict[str, List[dict]] = {}

        for bundle_path in bundle_paths:
            batch_result.bundles_processed += 1
            proc = self.process_bundle(bundle_path)

            # Collect evidence plane contributions
            batch_result.evidence_plane_contributions.extend(
                proc.get("evidence_plane_contributions", [])
            )

            disposition = proc.get("final_disposition", "UNKNOWN")
            manifest = proc.get("manifest") or {}
            task_hash = manifest.get("transition", {}).get("task_hash", "unknown")

            if "QUARANTINE" in disposition or "FAIL" in disposition:
                batch_result.bundles_quarantined += 1
                if proc.get("quarantine_result"):
                    batch_result.quarantine_results.append(
                        proc["quarantine_result"]
                    )
            elif "INSTALLED" in disposition:
                batch_result.bundles_installed += 1
                if proc.get("install_result"):
                    batch_result.install_results.append(proc["install_result"])
            else:
                batch_result.bundles_admitted += 1

            if proc.get("sandbox_results"):
                batch_result.bundles_sandboxed += 1
                batch_result.sandbox_runs.extend(proc["sandbox_results"])

            gate = proc.get("gate_result") or {}
            score_result = score_candidate(bundle_path, manifest)
            task_groups.setdefault(task_hash, []).append({
                "bundle_path": bundle_path,
                "bundle_id": self.graph.make_node_id(
                    "bundle", proc.get("bundle_hash", bundle_path)
                ),
                "manifest": manifest,
                "disposition": gate.get("candidate_disposition", ""),
                "transition_class": manifest.get("transition", {}).get(
                    "transition_class", ""
                ),
                "score": score_result,
            })

        # Discovery per task group
        for task_hash, candidates in task_groups.items():
            candidate_bundles = [
                c for c in candidates
                if c.get("transition_class") == "candidate"
            ]
            batch_result.candidates_found += len(candidate_bundles)

            if len(candidate_bundles) >= 2:
                discovery_result = self.discovery.discover(
                    task_hash, candidate_bundles
                )
                self.discovery.write_report(discovery_result)

                if discovery_result.route_synthesis:
                    batch_result.synthesis_attempted = True

                # Evidence plane: discovery route measurements
                for bundle_id in discovery_result.route_synthesis:
                    c = next((x for x in candidate_bundles
                               if x["bundle_id"] == bundle_id), {})
                    ep_dr = self.evidence.from_discovery_route(
                        c.get("bundle_path", ""),
                        task_hash, "synthesis",
                        c.get("score", {}),
                        related_bundles=[x["bundle_id"] for x in candidate_bundles
                                        if x["bundle_id"] != bundle_id],
                        lineage_depth=len(discovery_result.lineage_chain),
                    )
                    batch_result.evidence_plane_contributions.append(ep_dr.to_dict())

        # Evidence plane summary
        ep_summary = self.evidence.summarize()

        # Write batch report and receipt
        report = batch_result.to_dict()
        report["graph_summary"] = self.graph.summary()
        report["evidence_plane_summary"] = ep_summary
        write_report(
            os.path.join(self.report_dir, "batch_ingestion_report.json"),
            report
        )
        append_receipt(
            os.path.join(self.receipt_dir, "batch_ingestion_receipt.jsonl"),
            report
        )

        return batch_result
