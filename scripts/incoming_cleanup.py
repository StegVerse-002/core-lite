#!/usr/bin/env python3
"""
scripts/incoming_cleanup.py — StegVerse-002

Retroactive and forward cleanup of the incoming/ directory.

Scans incoming/, classifies each file, writes disposition receipts,
removes processed payloads, and leaves only README.md and .gitkeep.

Disposition classes:
  RETAINED          — README.md, .gitkeep (never removed)
  MISPLACED         — files that belong elsewhere (e.g. core-lite-intake.yml)
                      → moved to correct location if target provided, then removed
  LEGACY_PROCESSED  — bundles/files with prior receipt evidence or known processed state
                      → removed, receipt written
  LEGACY_UNKNOWN    — files with no known receipt, no known disposition
                      → moved to quarantine/incoming/legacy/, receipt written
  SKIP              — files explicitly excluded from this run

Writes:
  reports/current/incoming_cleanup_report.json
  receipts/current/incoming_cleanup_receipt.jsonl
  quarantine/incoming/legacy/  (for LEGACY_UNKNOWN files)
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys
from typing import List, Optional

# Files that must never be removed from incoming/
ALWAYS_RETAIN = {".gitkeep", "README.md"}

# Files that are misplaced — map to their correct repo-relative destination
MISPLACED_MAP = {
    "core-lite-intake.yml": ".github/workflows/core-lite-intake.yml",
}

# Filename patterns that indicate a processed/legacy bundle
LEGACY_PATTERNS = [
    "sv002_",
    "sv002 ",
    "bundle",
    ".zip",
    ".tar.gz",
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
]


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def append_receipt(path: str, record: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def classify_file(
    filename: str,
    filepath: str,
    receipt_dir: str,
) -> str:
    """
    Classify a file in incoming/ for disposition.
    Returns one of: RETAINED, MISPLACED, LEGACY_PROCESSED, LEGACY_UNKNOWN
    """
    if filename in ALWAYS_RETAIN:
        return "RETAINED"

    if filename in MISPLACED_MAP:
        return "MISPLACED"

    # Check if a receipt exists for this file
    basename = os.path.splitext(filename)[0]
    receipt_patterns = [
        os.path.join(receipt_dir, "current", "incoming_disposition_receipt.jsonl"),
        os.path.join(receipt_dir, "current", "bundle_ingestion_smoke_test_receipt.jsonl"),
        os.path.join(receipt_dir, "current", "transition_table_receipt.jsonl"),
    ]
    for rpath in receipt_patterns:
        if os.path.exists(rpath):
            try:
                with open(rpath) as f:
                    for line in f:
                        rec = json.loads(line.strip())
                        src = rec.get("source_path", "") or rec.get("bundle_path", "")
                        if filename in src or basename in src:
                            return "LEGACY_PROCESSED"
            except Exception:
                pass

    # Classify by pattern — most files in incoming/ are legacy processed bundles
    name_lower = filename.lower()
    for pat in LEGACY_PATTERNS:
        if name_lower.startswith(pat.lower()) or name_lower.endswith(pat.lower()):
            return "LEGACY_PROCESSED"

    return "LEGACY_UNKNOWN"


def run_cleanup(
    incoming_dir: str,
    repo_root: str,
    receipt_dir: str,
    report_dir: str,
    quarantine_dir: str,
    dry_run: bool = False,
) -> dict:
    """
    Main cleanup logic. Returns summary dict.
    """
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(receipt_dir, exist_ok=True)

    summary = {
        "schema": "stegverse.incoming_cleanup_report.v1",
        "timestamp_utc": now_utc(),
        "incoming_dir": incoming_dir,
        "dry_run": dry_run,
        "retained": [],
        "misplaced_moved": [],
        "misplaced_failed": [],
        "legacy_processed_removed": [],
        "legacy_unknown_quarantined": [],
        "errors": [],
        "total_scanned": 0,
        "total_removed": 0,
        "total_retained": 0,
        "total_quarantined": 0,
    }

    if not os.path.exists(incoming_dir):
        summary["errors"].append(f"incoming_dir not found: {incoming_dir}")
        return summary

    entries = sorted(os.listdir(incoming_dir))
    summary["total_scanned"] = len(entries)

    for filename in entries:
        filepath = os.path.join(incoming_dir, filename)

        # Skip subdirectories
        if os.path.isdir(filepath):
            continue

        disposition = classify_file(filename, filepath, receipt_dir)
        file_hash = sha256_file(filepath) if os.path.exists(filepath) else ""

        receipt_base = {
            "schema": "stegverse.incoming_cleanup_receipt.v1",
            "timestamp_utc": now_utc(),
            "filename": filename,
            "filepath": filepath,
            "sha256": file_hash,
            "disposition": disposition,
            "dry_run": dry_run,
        }

        if disposition == "RETAINED":
            summary["retained"].append(filename)
            summary["total_retained"] += 1
            receipt_base["action"] = "retained"
            append_receipt(
                os.path.join(receipt_dir, "incoming_cleanup_receipt.jsonl"),
                receipt_base
            )

        elif disposition == "MISPLACED":
            dest_rel = MISPLACED_MAP.get(filename, "")
            dest_abs = os.path.join(repo_root, dest_rel) if dest_rel else ""
            receipt_base["misplaced_dest"] = dest_rel

            moved = False
            if dest_abs:
                # Only move if the target doesn't already exist with same content
                if os.path.exists(dest_abs):
                    receipt_base["action"] = "misplaced_target_exists_removed_from_incoming"
                    if not dry_run:
                        os.remove(filepath)
                    moved = True
                else:
                    if not dry_run:
                        os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
                        shutil.move(filepath, dest_abs)
                    receipt_base["action"] = "misplaced_moved_to_correct_location"
                    moved = True

            if moved:
                summary["misplaced_moved"].append({"filename": filename, "dest": dest_rel})
                summary["total_removed"] += 1
            else:
                receipt_base["action"] = "misplaced_no_dest_quarantined"
                qpath = os.path.join(quarantine_dir, "misplaced", filename)
                if not dry_run:
                    os.makedirs(os.path.dirname(qpath), exist_ok=True)
                    shutil.move(filepath, qpath)
                summary["misplaced_failed"].append(filename)
                summary["total_quarantined"] += 1

            append_receipt(
                os.path.join(receipt_dir, "incoming_cleanup_receipt.jsonl"),
                receipt_base
            )

        elif disposition == "LEGACY_PROCESSED":
            receipt_base["action"] = "legacy_processed_removed"
            if not dry_run:
                os.remove(filepath)
            summary["legacy_processed_removed"].append(filename)
            summary["total_removed"] += 1
            append_receipt(
                os.path.join(receipt_dir, "incoming_cleanup_receipt.jsonl"),
                receipt_base
            )

        elif disposition == "LEGACY_UNKNOWN":
            qpath = os.path.join(quarantine_dir, "legacy", filename)
            receipt_base["action"] = "legacy_unknown_quarantined"
            receipt_base["quarantine_path"] = qpath
            if not dry_run:
                os.makedirs(os.path.dirname(qpath), exist_ok=True)
                shutil.move(filepath, qpath)
            summary["legacy_unknown_quarantined"].append(filename)
            summary["total_quarantined"] += 1
            append_receipt(
                os.path.join(receipt_dir, "incoming_cleanup_receipt.jsonl"),
                receipt_base
            )

    # Write report inside run_cleanup so callers can verify it
    report_path = os.path.join(report_dir, "incoming_cleanup_report.json")
    os.makedirs(report_dir, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Ensure README.md exists in incoming/
    readme_path = os.path.join(incoming_dir, "README.md")
    if not os.path.exists(readme_path) and not dry_run:
        with open(readme_path, "w") as f:
            f.write(
                "# Incoming\n\n"
                "Ephemeral ingestion mailbox.\n\n"
                "Only README.md and .gitkeep should remain after ingestion runs.\n\n"
                "Push bundles here to activate the ingestion pipeline.\n"
                "The workflow removes only payloads with disposition records.\n"
            )

    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--incoming-dir", default="incoming")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--receipt-dir", default="receipts")
    parser.add_argument("--report-dir", default="reports/current")
    parser.add_argument("--quarantine-dir", default="quarantine/incoming")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    summary = run_cleanup(
        incoming_dir=args.incoming_dir,
        repo_root=args.repo_root,
        receipt_dir=args.receipt_dir,
        report_dir=args.report_dir,
        quarantine_dir=args.quarantine_dir,
        dry_run=args.dry_run,
    )

    # Write report
    report_path = os.path.join(args.report_dir, "incoming_cleanup_report.json")
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print(json.dumps({
        "status": "success" if not summary["errors"] else "partial",
        "dry_run": args.dry_run,
        "total_scanned": summary["total_scanned"],
        "total_removed": summary["total_removed"],
        "total_retained": summary["total_retained"],
        "total_quarantined": summary["total_quarantined"],
        "retained": summary["retained"],
        "removed": summary["legacy_processed_removed"],
        "misplaced_moved": [m["filename"] for m in summary["misplaced_moved"]],
        "quarantined": summary["legacy_unknown_quarantined"],
        "errors": summary["errors"],
    }, indent=2))

    if summary["errors"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
