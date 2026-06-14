#!/usr/bin/env python3
"""
scripts/incoming_cleanup.py — StegVerse-002

Scoped cleanup of the incoming/ directory.

This cleanup task is intentionally conservative. It does not relocate semantic
content to final repo destinations. Unresolved payloads are quarantined for later
manifest wrapping / governed re-ingestion. Only files with existing disposition
receipt evidence may be removed from incoming/.

Disposition classes:
  RETAINED             — README.md, .gitkeep, protected diagnostic fixtures
  LEGACY_DISPOSITIONED — files with existing receipt/disposition evidence
                         → removed from incoming/, receipt written
  LEGACY_UNKNOWN       — files with no known receipt/disposition
                         → moved to quarantine/incoming/legacy/, receipt written
  SKIP_DIR             — directories are inventoried and left untouched

Writes:
  reports/current/incoming_cleanup_report.json
  receipts/incoming_cleanup_receipt.jsonl
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
from typing import List

# Files that must never be removed from incoming/.
ALWAYS_RETAIN = {".gitkeep", "README.md"}

# Known diagnostic fixtures retained because declared tasks may depend on them.
PROTECTED_FIXTURES = {
    "sv002_diagnostics_bundle.zip",
}

RECEIPT_FILES = [
    os.path.join("current", "incoming_disposition_receipt.jsonl"),
    os.path.join("current", "bundle_ingestion_smoke_test_receipt.jsonl"),
    os.path.join("current", "transition_table_receipt.jsonl"),
    "incoming_cleanup_receipt.jsonl",
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


def iter_receipt_paths(receipt_dir: str) -> List[str]:
    paths: List[str] = []
    for rel in RECEIPT_FILES:
        paths.append(os.path.join(receipt_dir, rel))
    return paths


def has_disposition_receipt(filename: str, filepath: str, receipt_dir: str) -> bool:
    basename = os.path.splitext(filename)[0]
    for rpath in iter_receipt_paths(receipt_dir):
        if not os.path.exists(rpath):
            continue
        try:
            with open(rpath) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    fields = [
                        rec.get("source_path", ""),
                        rec.get("bundle_path", ""),
                        rec.get("filepath", ""),
                        rec.get("filename", ""),
                    ]
                    haystack = "\n".join(str(v) for v in fields if v)
                    if filepath in haystack or filename in haystack or basename in haystack:
                        return True
        except Exception:
            continue
    return False


def classify_path(name: str, path: str, receipt_dir: str) -> str:
    if os.path.isdir(path):
        return "SKIP_DIR"
    if name in ALWAYS_RETAIN or name in PROTECTED_FIXTURES:
        return "RETAINED"
    if has_disposition_receipt(name, path, receipt_dir):
        return "LEGACY_DISPOSITIONED"
    return "LEGACY_UNKNOWN"


def run_cleanup(
    incoming_dir: str,
    receipt_dir: str,
    report_dir: str,
    quarantine_dir: str,
    dry_run: bool = False,
) -> dict:
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(receipt_dir, exist_ok=True)

    summary = {
        "schema": "stegverse.incoming_cleanup_report.v2",
        "timestamp_utc": now_utc(),
        "incoming_dir": incoming_dir,
        "dry_run": dry_run,
        "policy": "quarantine_unresolved_no_final_relocation",
        "retained": [],
        "directories_skipped": [],
        "legacy_dispositioned_removed": [],
        "legacy_unknown_quarantined": [],
        "errors": [],
        "total_scanned": 0,
        "total_removed": 0,
        "total_retained": 0,
        "total_quarantined": 0,
        "total_directories_skipped": 0,
    }

    if not os.path.exists(incoming_dir):
        summary["errors"].append(f"incoming_dir not found: {incoming_dir}")
        return summary

    entries = sorted(os.listdir(incoming_dir))
    summary["total_scanned"] = len(entries)

    receipt_path = os.path.join(receipt_dir, "incoming_cleanup_receipt.jsonl")

    for name in entries:
        path = os.path.join(incoming_dir, name)
        disposition = classify_path(name, path, receipt_dir)
        file_hash = sha256_file(path) if os.path.isfile(path) else ""

        receipt = {
            "schema": "stegverse.incoming_cleanup_receipt.v2",
            "timestamp_utc": now_utc(),
            "name": name,
            "path": path,
            "sha256": file_hash,
            "disposition": disposition,
            "dry_run": dry_run,
            "policy": "quarantine_unresolved_no_final_relocation",
        }

        if disposition == "SKIP_DIR":
            receipt["action"] = "directory_skipped_left_in_place"
            summary["directories_skipped"].append(name)
            summary["total_directories_skipped"] += 1
            append_receipt(receipt_path, receipt)
            continue

        if disposition == "RETAINED":
            receipt["action"] = "retained"
            summary["retained"].append(name)
            summary["total_retained"] += 1
            append_receipt(receipt_path, receipt)
            continue

        if disposition == "LEGACY_DISPOSITIONED":
            receipt["action"] = "removed_from_incoming_existing_disposition_receipt"
            if not dry_run:
                os.remove(path)
            summary["legacy_dispositioned_removed"].append(name)
            summary["total_removed"] += 1
            append_receipt(receipt_path, receipt)
            continue

        if disposition == "LEGACY_UNKNOWN":
            qpath = os.path.join(quarantine_dir, "legacy", name)
            receipt["action"] = "quarantined_unresolved_payload"
            receipt["quarantine_path"] = qpath
            if not dry_run:
                os.makedirs(os.path.dirname(qpath), exist_ok=True)
                shutil.move(path, qpath)
            summary["legacy_unknown_quarantined"].append(name)
            summary["total_quarantined"] += 1
            append_receipt(receipt_path, receipt)
            continue

    readme_path = os.path.join(incoming_dir, "README.md")
    if not os.path.exists(readme_path) and not dry_run:
        with open(readme_path, "w") as f:
            f.write(
                "# Incoming\n\n"
                "Ephemeral ingestion mailbox.\n\n"
                "Only README.md, .gitkeep, and protected diagnostic fixtures should remain after ingestion runs.\n\n"
                "Payload bundles/files may be pushed here to activate ingestion. The workflow removes only payloads with disposition records. Unresolved payloads are quarantined for governed re-ingestion; cleanup does not relocate semantic content to final repo destinations.\n"
            )

    report_path = os.path.join(report_dir, "incoming_cleanup_report.json")
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)

    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--incoming-dir", default="incoming")
    parser.add_argument("--repo-root", default=".")  # retained for CLI compatibility; intentionally unused
    parser.add_argument("--receipt-dir", default="receipts")
    parser.add_argument("--report-dir", default="reports/current")
    parser.add_argument("--quarantine-dir", default="quarantine/incoming")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    summary = run_cleanup(
        incoming_dir=args.incoming_dir,
        receipt_dir=args.receipt_dir,
        report_dir=args.report_dir,
        quarantine_dir=args.quarantine_dir,
        dry_run=args.dry_run,
    )

    print(json.dumps({
        "status": "success" if not summary["errors"] else "partial",
        "dry_run": args.dry_run,
        "policy": summary["policy"],
        "total_scanned": summary["total_scanned"],
        "total_removed": summary["total_removed"],
        "total_retained": summary["total_retained"],
        "total_quarantined": summary["total_quarantined"],
        "total_directories_skipped": summary["total_directories_skipped"],
        "retained": summary["retained"],
        "removed": summary["legacy_dispositioned_removed"],
        "quarantined": summary["legacy_unknown_quarantined"],
        "directories_skipped": summary["directories_skipped"],
        "errors": summary["errors"],
    }, indent=2, sort_keys=True))

    if summary["errors"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
