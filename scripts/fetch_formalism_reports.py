#!/usr/bin/env python3
"""
scripts/fetch_formalism_reports.py — StegVerse-002

Fetches Stage 32-34 admissibility-space reports from Data-Continuation/formalism-tests.

Option A (primary): Clone repo, run declared tasks, copy reports.
Option B (fallback): Verify committed snapshot against snapshot_manifest.json.

Writes:
  formalisms/transition-table/reports/stage32_admissibility_space_report.json
  formalisms/transition-table/reports/stage33_transition_graph_geometry_report.json
  formalisms/transition-table/reports/stage34_repair_nearest_admissible_transition_report.json
  formalisms/transition-table/snapshot_manifest.json  (updated on live success)
  reports/current/formalism_fetch_report.json
  receipts/current/formalism_fetch_receipt.jsonl

Exit codes:
  0 — reports available (live or snapshot)
  1 — both options failed, reports unavailable
  2 — snapshot hash mismatch, routed to REVIEW
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

FORMALISM_REPO = "https://github.com/Data-Continuation/formalism-tests.git"
TASK_MANIFEST = "tools/tasks/stage32_to_34_admissibility_space_tasks.json"
TASK_RUNNER = "tools/run_declared_tasks.py"

REPORT_MAP = {
    32: {
        "task_id": "stage32_admissibility_space_coordinates_tests",
        "source_path": "reports/stage32_admissibility_space_report.json",
        "dest_name": "stage32_admissibility_space_report.json",
    },
    33: {
        "task_id": "stage33_transition_graph_geometry_tests",
        "source_path": "reports/stage33_transition_graph_geometry_report.json",
        "dest_name": "stage33_transition_graph_geometry_report.json",
    },
    34: {
        "task_id": "stage34_repair_nearest_admissible_transition_tests",
        "source_path": "reports/stage34_repair_nearest_admissible_transition_report.json",
        "dest_name": "stage34_repair_nearest_admissible_transition_report.json",
    },
}


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
    with open(path, "w") as f:
        json.dump(record, f, indent=2)


def get_formalism_commit(clone_dir: str) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=clone_dir,
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Option A: Live execution
# ---------------------------------------------------------------------------

def try_live_execution(dest_dir: str, timeout: int = 120) -> dict:
    """
    Clone formalism-tests, run stage32-34 tasks, copy reports to dest_dir.
    Returns result dict with success, commit, reports, errors.
    """
    result = {
        "method": "live_execution",
        "success": False,
        "formalism_repo": FORMALISM_REPO,
        "formalism_commit": "",
        "reports": {},
        "errors": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        clone_dir = os.path.join(tmpdir, "formalism-tests")

        # Clone
        try:
            subprocess.run(
                ["git", "clone", "--depth=1", FORMALISM_REPO, clone_dir],
                capture_output=True, text=True, timeout=60, check=True
            )
        except subprocess.TimeoutExpired:
            result["errors"].append("git clone timed out after 60s")
            return result
        except subprocess.CalledProcessError as e:
            result["errors"].append(f"git clone failed: {e.stderr.strip()}")
            return result

        result["formalism_commit"] = get_formalism_commit(clone_dir)

        # Install dependencies if pyproject.toml or setup.py exists
        for setup_file in ["pyproject.toml", "setup.py", "setup.cfg"]:
            if os.path.exists(os.path.join(clone_dir, setup_file)):
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-e", ".",
                         "--break-system-packages", "-q"],
                        cwd=clone_dir,
                        capture_output=True, text=True, timeout=60
                    )
                except Exception:
                    pass  # Non-fatal — scripts may run without install
                break

        # Run task manifest
        task_manifest_path = os.path.join(clone_dir, TASK_MANIFEST)
        runner_path = os.path.join(clone_dir, TASK_RUNNER)

        if not os.path.exists(task_manifest_path):
            result["errors"].append(f"task manifest not found: {TASK_MANIFEST}")
            return result

        if not os.path.exists(runner_path):
            result["errors"].append(f"task runner not found: {TASK_RUNNER}")
            return result

        try:
            proc = subprocess.run(
                [sys.executable, TASK_RUNNER, TASK_MANIFEST],
                cwd=clone_dir,
                capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            result["errors"].append(f"task runner timed out after {timeout}s")
            return result

        if proc.returncode != 0:
            result["errors"].append(
                f"task runner exited {proc.returncode}: {proc.stderr.strip()[:500]}"
            )
            return result

        # Copy reports to dest_dir
        os.makedirs(dest_dir, exist_ok=True)
        all_copied = True
        for stage, info in REPORT_MAP.items():
            src = os.path.join(clone_dir, info["source_path"])
            dst = os.path.join(dest_dir, info["dest_name"])
            if os.path.exists(src):
                shutil.copy2(src, dst)
                result["reports"][stage] = {
                    "dest": dst,
                    "sha256": sha256_file(dst),
                }
            else:
                result["errors"].append(f"stage {stage} report not found: {src}")
                all_copied = False

        result["success"] = all_copied
        return result


# ---------------------------------------------------------------------------
# Option B: Snapshot verification
# ---------------------------------------------------------------------------

def try_snapshot_verification(dest_dir: str, snapshot_manifest_path: str) -> dict:
    """
    Verify committed snapshot reports against snapshot_manifest.json.
    Returns result dict with success, source, reports, errors.
    """
    result = {
        "method": "snapshot",
        "success": False,
        "source": "committed_snapshot",
        "reports": {},
        "errors": [],
        "hash_mismatches": [],
    }

    if not os.path.exists(snapshot_manifest_path):
        result["errors"].append(
            f"snapshot_manifest.json not found: {snapshot_manifest_path}"
        )
        return result

    with open(snapshot_manifest_path) as f:
        snapshot = json.load(f)

    all_ok = True
    for entry in snapshot.get("reports", []):
        stage = entry.get("stage")
        path = entry.get("path", "")
        expected_hash = entry.get("sha256", "")

        if not os.path.exists(path):
            result["errors"].append(f"snapshot report missing: {path}")
            all_ok = False
            continue

        actual_hash = sha256_file(path)
        if expected_hash and actual_hash != expected_hash:
            result["hash_mismatches"].append({
                "stage": stage,
                "path": path,
                "expected": expected_hash,
                "actual": actual_hash,
            })
            all_ok = False
        else:
            result["reports"][stage] = {
                "dest": path,
                "sha256": actual_hash,
            }

    result["success"] = all_ok and len(result["hash_mismatches"]) == 0
    return result


# ---------------------------------------------------------------------------
# Snapshot manifest update
# ---------------------------------------------------------------------------

def update_snapshot_manifest(
    dest_dir: str,
    snapshot_manifest_path: str,
    formalism_commit: str,
    source: str,
) -> None:
    """Update snapshot_manifest.json after a successful live run."""
    entries = []
    for stage, info in REPORT_MAP.items():
        path = os.path.join(dest_dir, info["dest_name"])
        if os.path.exists(path):
            entries.append({
                "stage": stage,
                "artifact": info["task_id"],
                "path": path,
                "sha256": sha256_file(path),
            })

    manifest = {
        "schema": "stegverse.formalism_snapshot_manifest.v1",
        "generated_utc": now_utc(),
        "source": source,
        "formalism_repo": FORMALISM_REPO,
        "formalism_commit": formalism_commit,
        "reports": entries,
    }

    os.makedirs(os.path.dirname(snapshot_manifest_path), exist_ok=True)
    with open(snapshot_manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest-dir",
                        default="formalisms/transition-table/reports")
    parser.add_argument("--snapshot-manifest",
                        default="formalisms/transition-table/snapshot_manifest.json")
    parser.add_argument("--report-dir", default="reports/current")
    parser.add_argument("--receipt-dir", default="receipts/current")
    parser.add_argument("--timeout", type=int, default=120,
                        help="Timeout in seconds for live execution")
    parser.add_argument("--skip-live", action="store_true",
                        help="Skip Option A and go straight to snapshot")
    args = parser.parse_args()

    os.makedirs(args.dest_dir, exist_ok=True)
    os.makedirs(args.report_dir, exist_ok=True)
    os.makedirs(args.receipt_dir, exist_ok=True)

    fetch_result = {
        "schema": "stegverse.formalism_fetch_report.v1",
        "timestamp_utc": now_utc(),
        "live_attempted": False,
        "live_success": False,
        "snapshot_attempted": False,
        "snapshot_success": False,
        "final_source": "",
        "formalism_commit": "",
        "reports_available": False,
        "route": "ALLOW",
        "errors": [],
        "warnings": [],
    }

    # --- Option A: Live execution ---
    if not args.skip_live:
        fetch_result["live_attempted"] = True
        print("Option A: attempting live execution from formalism-tests...")
        live = try_live_execution(args.dest_dir, timeout=args.timeout)

        if live["success"]:
            fetch_result["live_success"] = True
            fetch_result["final_source"] = "live_execution"
            fetch_result["formalism_commit"] = live["formalism_commit"]
            fetch_result["reports_available"] = True
            fetch_result["route"] = "ALLOW"
            print(f"Option A: SUCCESS — commit {live['formalism_commit']}")

            # Update snapshot manifest with fresh hashes
            update_snapshot_manifest(
                args.dest_dir,
                args.snapshot_manifest,
                formalism_commit=live["formalism_commit"],
                source="live_execution",
            )
            print(f"Snapshot manifest updated: {args.snapshot_manifest}")
        else:
            fetch_result["warnings"].extend(live["errors"])
            print(f"Option A: FAILED — {live['errors']}")
            print("Falling back to Option B: snapshot verification...")

    # --- Option B: Snapshot fallback ---
    if not fetch_result["live_success"]:
        fetch_result["snapshot_attempted"] = True
        snap = try_snapshot_verification(args.dest_dir, args.snapshot_manifest)

        if snap["success"]:
            fetch_result["snapshot_success"] = True
            fetch_result["final_source"] = "committed_snapshot"
            fetch_result["reports_available"] = True
            fetch_result["route"] = "ALLOW"
            print("Option B: snapshot verification PASSED")
        elif snap["hash_mismatches"]:
            fetch_result["errors"].extend(
                [f"hash mismatch: {m}" for m in snap["hash_mismatches"]]
            )
            fetch_result["final_source"] = "stale_snapshot"
            fetch_result["reports_available"] = False
            fetch_result["route"] = "REVIEW"
            print("Option B: HASH MISMATCH — routing to REVIEW")
        else:
            fetch_result["errors"].extend(snap["errors"])
            fetch_result["final_source"] = "unavailable"
            fetch_result["reports_available"] = False
            fetch_result["route"] = "REVIEW"
            print(f"Option B: FAILED — {snap['errors']}")

    # Write report and receipt
    write_report(
        os.path.join(args.report_dir, "formalism_fetch_report.json"),
        fetch_result
    )
    append_receipt(
        os.path.join(args.receipt_dir, "formalism_fetch_receipt.jsonl"),
        fetch_result
    )

    print(f"\nResult: source={fetch_result['final_source']}, "
          f"route={fetch_result['route']}, "
          f"available={fetch_result['reports_available']}")

    if not fetch_result["reports_available"]:
        if fetch_result["route"] == "REVIEW":
            sys.exit(2)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
