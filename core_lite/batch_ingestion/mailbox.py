"""
core_lite/batch_ingestion/mailbox.py — StegVerse-002

Routes incoming bundles to incoming/mailbox/{task_hash}/{slot}/
based on transition_class and candidate disposition.

Slots:
  candidates/   — CANDIDATE_ACCEPTED_FOR_COMPARISON or SYNTHESIS
  evidence/     — evidence class bundles
  repairs/      — repair candidates
  installs/     — install candidates that passed TT+CGE
  superseded/   — bundles superseded by a newer candidate
  quarantine/   — FAIL_CLOSED, QUARANTINED, or irreparable
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import zipfile
from typing import Optional

SLOTS = ["candidates", "evidence", "repairs", "installs", "superseded", "quarantine"]

TRANSITION_CLASS_TO_SLOT = {
    "candidate": "candidates",
    "evidence": "evidence",
    "repair": "repairs",
    "install": "installs",
}

DISPOSITION_TO_SLOT = {
    "CANDIDATE_ACCEPTED_FOR_COMPARISON": "candidates",
    "CANDIDATE_ACCEPTED_FOR_SYNTHESIS": "candidates",
    "CANDIDATE_SUPERSEDES_PREVIOUS": "candidates",
    "CANDIDATE_REQUIRES_REVIEW": "candidates",
    "CANDIDATE_FAIL_CLOSED": "quarantine",
    "CANDIDATE_QUARANTINED": "quarantine",
    "INSTALL_ALLOWED": "installs",
    "INSTALL_DENIED": "quarantine",
    "REPAIR_ACCEPTED": "repairs",
    "EVIDENCE_STORED": "evidence",
}


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


class MailboxRouter:
    """
    Routes a bundle to the correct mailbox slot under
    incoming/mailbox/{task_hash}/{slot}/
    """

    def __init__(self, mailbox_root: str = "incoming/mailbox"):
        self.mailbox_root = mailbox_root

    def task_dir(self, task_hash: str) -> str:
        # Use first 16 chars of hash for directory name (readable)
        safe_hash = task_hash.replace("sha256:", "")[:16]
        return os.path.join(self.mailbox_root, safe_hash)

    def slot_dir(self, task_hash: str, slot: str) -> str:
        return os.path.join(self.task_dir(task_hash), slot)

    def ensure_slots(self, task_hash: str) -> str:
        task_dir = self.task_dir(task_hash)
        for slot in SLOTS:
            os.makedirs(os.path.join(task_dir, slot), exist_ok=True)
        return task_dir

    def route(
        self,
        bundle_path: str,
        task_hash: str,
        transition_class: str,
        candidate_disposition: str = "",
        dry_run: bool = False,
    ) -> dict:
        """
        Copy bundle to the correct mailbox slot.
        Returns routing result dict.
        """
        # Determine slot
        slot = None
        if candidate_disposition and candidate_disposition in DISPOSITION_TO_SLOT:
            slot = DISPOSITION_TO_SLOT[candidate_disposition]
        elif transition_class in TRANSITION_CLASS_TO_SLOT:
            slot = TRANSITION_CLASS_TO_SLOT[transition_class]
        else:
            slot = "quarantine"

        task_dir = self.task_dir(task_hash)
        dest_dir = os.path.join(task_dir, slot)
        dest_path = os.path.join(dest_dir, os.path.basename(bundle_path))

        result = {
            "schema": "stegverse.mailbox_routing.v1",
            "timestamp_utc": now_utc(),
            "bundle_path": bundle_path,
            "task_hash": task_hash,
            "transition_class": transition_class,
            "candidate_disposition": candidate_disposition,
            "slot": slot,
            "task_dir": task_dir,
            "dest_path": dest_path,
            "dry_run": dry_run,
            "success": False,
            "error": "",
        }

        if not os.path.exists(bundle_path):
            result["error"] = f"bundle not found: {bundle_path}"
            return result

        if not dry_run:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(bundle_path, dest_path)
            result["bundle_sha256"] = sha256_file(dest_path)

        result["success"] = True
        return result

    def supersede(
        self,
        task_hash: str,
        bundle_filename: str,
        from_slot: str = "candidates",
        dry_run: bool = False,
    ) -> dict:
        """Move a bundle from its current slot to superseded/."""
        src = os.path.join(self.slot_dir(task_hash, from_slot), bundle_filename)
        dst_dir = self.slot_dir(task_hash, "superseded")
        dst = os.path.join(dst_dir, bundle_filename)

        result = {
            "schema": "stegverse.mailbox_supersede.v1",
            "timestamp_utc": now_utc(),
            "task_hash": task_hash,
            "bundle_filename": bundle_filename,
            "from_slot": from_slot,
            "dest_path": dst,
            "dry_run": dry_run,
            "success": False,
            "error": "",
        }

        if not os.path.exists(src):
            result["error"] = f"source not found: {src}"
            return result

        if not dry_run:
            os.makedirs(dst_dir, exist_ok=True)
            shutil.move(src, dst)

        result["success"] = True
        return result

    def list_slot(self, task_hash: str, slot: str) -> list:
        """List bundles in a slot."""
        d = self.slot_dir(task_hash, slot)
        if not os.path.exists(d):
            return []
        return [f for f in sorted(os.listdir(d))
                if f.endswith(".zip") or f.endswith(".tar.gz")]

    def list_all_slots(self, task_hash: str) -> dict:
        """List all slots and their contents for a task."""
        return {slot: self.list_slot(task_hash, slot) for slot in SLOTS}

    def all_task_hashes(self) -> list:
        """Return all task hash directories in the mailbox."""
        if not os.path.exists(self.mailbox_root):
            return []
        return [d for d in sorted(os.listdir(self.mailbox_root))
                if os.path.isdir(os.path.join(self.mailbox_root, d))]
