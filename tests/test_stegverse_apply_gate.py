import json
import subprocess
import sys
from pathlib import Path


def run_gate(tmp_path, request):
    req_path = tmp_path / "request.json"
    report_path = tmp_path / "report.json"
    receipt_path = tmp_path / "receipt.jsonl"
    output_path = tmp_path / "output.md"
    req_path.write_text(json.dumps(request), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/stegverse_apply_gate.py",
            "--request",
            str(req_path),
            "--entity",
            "StegVerse-002",
            "--stage",
            "SV002-M11",
            "--report",
            str(report_path),
            "--receipt",
            str(receipt_path),
            "--output",
            str(output_path),
        ],
        text=True,
        capture_output=True,
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return proc, report


def safe_doc_request(dry_run=False):
    return {
        "schema": "stegverse.apply_request.v1",
        "request_id": "test-doc-safe",
        "entity": "StegVerse-002",
        "stage": "SV002-M11",
        "capability": "sv002-m105-sandbox-proof",
        "requester": "adapter-candidate-sandbox/openai",
        "transition_class": "documentation",
        "authority_ref": "SV002-M10.5/scoped-candidate-review-only",
        "policy_ref": "triad/default-deny/no-broad-authority/review-only",
        "dry_run": dry_run,
        "target_files": [
            {"path": "docs/SV002_M10_5_SANDBOX_PROOF_OUTPUT.md", "operation": "review"}
        ],
    }


def test_safe_documentation_binding_allows(tmp_path):
    proc, report = run_gate(tmp_path, safe_doc_request(False))
    assert proc.returncode == 0
    assert report["decision"] == "ALLOW"
    assert report["checks"]["gcat_bcat_admissible"] is True
    assert report["checks"]["ecat_icat_coherent"] is True
    assert report["checks"]["existence_recoverable"] is True


def test_broad_authority_denies(tmp_path):
    req = safe_doc_request(False)
    req["authority_ref"] = "root/all/admin"
    proc, report = run_gate(tmp_path, req)
    assert proc.returncode == 1
    assert report["decision"] == "DENY"


def test_workflow_path_denies(tmp_path):
    req = safe_doc_request(False)
    req["target_files"] = [{"path": ".github/workflows/core-lite-intake.yml", "operation": "review"}]
    proc, report = run_gate(tmp_path, req)
    assert proc.returncode == 1
    assert report["decision"] == "DENY"


def test_tooling_binding_still_defers_without_triad_resolution(tmp_path):
    req = safe_doc_request(False)
    req["transition_class"] = "tooling"
    req["target_files"] = [{"path": "scripts/example.py", "operation": "review"}]
    proc, report = run_gate(tmp_path, req)
    assert proc.returncode == 1
    assert report["decision"] == "DEFER"
