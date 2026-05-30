#!/usr/bin/env python3
"""
core_lite/batch_ingestion/task_awareness.py — StegVerse-002

Task awareness and agreement enforcement.

Every data packet passing through ingestion must declare what task
it addresses and that declaration must agree with the actual content.

Task awareness is an admissibility condition, not optional metadata.

Agreement levels:
  FULL     — task_hash matches, files address declared task, content relevant
  PARTIAL  — task_hash matches, some files relevant, some not
  UNKNOWN  — no task_hash declared, cannot verify
  MISMATCH — task_hash declared but files don't address it
  NONE     — no task reference at all

Routing by agreement:
  FULL     → proceed through TT + CGE
  PARTIAL  → route to SYNTHESIS — extract relevant fragments
  UNKNOWN  → route to SANDBOX — task reference missing
  MISMATCH → route to REVIEW — candidate claims wrong task
  NONE     → FAIL_CLOSED — no task context, cannot govern
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_str(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Task awareness result
# ---------------------------------------------------------------------------

@dataclass
class TaskAwarenessResult:
    """
    Result of task awareness check for a single bundle/candidate.
    Failures are fully visible with specific reasons.
    """
    bundle_path: str
    task_hash_declared: str
    task_ref_declared: str
    agreement: str          # FULL | PARTIAL | UNKNOWN | MISMATCH | NONE
    routing: str            # proceed | synthesis | sandbox | review | fail_closed
    timestamp_utc: str = field(default_factory=now_utc)

    # What was checked
    checks_performed: List[dict] = field(default_factory=list)

    # Failures — loud and specific
    failures: List[dict] = field(default_factory=list)
    warnings: List[dict] = field(default_factory=list)

    # Evidence
    files_checked: List[str] = field(default_factory=list)
    files_task_relevant: List[str] = field(default_factory=list)
    files_task_irrelevant: List[str] = field(default_factory=list)

    def add_check(self, name: str, expected: str, found: str,
                  passed: bool, routing_if_fail: str = "") -> None:
        check = {
            "check": name,
            "expected": expected,
            "found": found,
            "passed": passed,
            "routing_if_fail": routing_if_fail,
            "action": f"Route to {routing_if_fail or 'fail_closed'}: "
                      f"expected {expected!r}, found {found!r}",
        }
        self.checks_performed.append(check)
        if not passed:
            self.failures.append({
                "check": name,
                "expected": expected,
                "found": found,
                "routing": routing_if_fail or self.routing,
                "action": f"Route to {routing_if_fail or self.routing}: "
                          f"expected {expected!r}, found {found!r}",
            })

    def add_warning(self, name: str, detail: str) -> None:
        self.warnings.append({"warning": name, "detail": detail})

    def is_admissible(self) -> bool:
        return self.agreement in ("FULL", "PARTIAL")

    def to_dict(self) -> dict:
        return {
            "schema": "stegverse.task_awareness_result.v1",
            "timestamp_utc": self.timestamp_utc,
            "bundle_path": self.bundle_path,
            "task_hash_declared": self.task_hash_declared,
            "task_ref_declared": self.task_ref_declared,
            "agreement": self.agreement,
            "routing": self.routing,
            "admissible": self.is_admissible(),
            "checks_performed": self.checks_performed,
            "failures": self.failures,
            "warnings": self.warnings,
            "files_checked": self.files_checked,
            "files_task_relevant": self.files_task_relevant,
            "files_task_irrelevant": self.files_task_irrelevant,
            "summary": self._summary(),
        }

    def _summary(self) -> str:
        if not self.failures:
            return (f"TASK_AGREEMENT={self.agreement} "
                    f"({len(self.files_task_relevant)}/{len(self.files_checked)} "
                    f"files task-relevant) → {self.routing}")
        failure_names = [f["check"] for f in self.failures]
        return (f"TASK_AGREEMENT={self.agreement} "
                f"FAILURES={failure_names} → {self.routing}")

    def print_visible(self) -> None:
        """Print fully visible failure report to stdout."""
        print(f"\n{'='*60}")
        print(f"TASK AWARENESS CHECK: {self.bundle_path}")
        print(f"{'='*60}")
        print(f"  Agreement:   {self.agreement}")
        print(f"  Routing:     {self.routing}")
        print(f"  Admissible:  {self.is_admissible()}")
        print(f"  Task hash:   {self.task_hash_declared or '[NOT DECLARED]'}")
        print(f"  Task ref:    {self.task_ref_declared or '[NOT DECLARED]'}")
        print()

        if self.checks_performed:
            print("  Checks:")
            for c in self.checks_performed:
                status = "✓" if c["passed"] else "✗"
                print(f"    {status} {c['check']}")
                if not c["passed"]:
                    print(f"      expected: {c['expected']}")
                    print(f"      found:    {c['found']}")
                    print(f"      action:   {c['action']}")

        if self.failures:
            print()
            print(f"  FAILURES ({len(self.failures)}):")
            for f in self.failures:
                print(f"    ✗ {f['check']}")
                print(f"      → {f['action']}")

        if self.warnings:
            print()
            print(f"  Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"    ⚠ {w['warning']}: {w['detail']}")

        if self.files_task_irrelevant:
            print()
            print(f"  Task-irrelevant files:")
            for f in self.files_task_irrelevant:
                print(f"    - {f}")

        print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Task context loader
# ---------------------------------------------------------------------------

def load_task_context(task_ref: str, repo_root: str = ".") -> Optional[dict]:
    """
    Load task context from task_ref path.
    Returns dict with task content and hash, or None if not found.
    """
    if not task_ref:
        return None

    task_path = os.path.join(repo_root, task_ref)
    if not os.path.exists(task_path):
        # Try common locations
        for candidate_path in [
            task_ref,
            os.path.join(repo_root, "task.md"),
            os.path.join(repo_root, "tasks", task_ref),
        ]:
            if os.path.exists(candidate_path):
                task_path = candidate_path
                break
        else:
            return None

    with open(task_path) as f:
        content = f.read()

    return {
        "path": task_path,
        "content": content,
        "hash": sha256_str(content),
        "keywords": _extract_keywords(content),
    }


def _extract_keywords(text: str) -> List[str]:
    """Extract significant keywords from task content."""
    import re
    # Extract words from code blocks and key sections
    words = set()
    # File paths mentioned
    for m in re.finditer(r'`([^`]+\.[a-z]+)`', text):
        words.add(m.group(1).lower())
    # Significant nouns (capitalized words, technical terms)
    for m in re.finditer(r'\b([A-Z][a-zA-Z]{3,})\b', text):
        words.add(m.group(1).lower())
    # python module paths
    for m in re.finditer(r'core_lite[\w./]+', text):
        words.add(m.group(0).lower())
    return list(words)


# ---------------------------------------------------------------------------
# Task awareness checker
# ---------------------------------------------------------------------------

class TaskAwarenessChecker:
    """
    Checks task awareness and agreement for a bundle/candidate.
    Failures are fully visible.
    """

    def __init__(
        self,
        repo_root: str = ".",
        report_dir: str = "reports/current",
        receipt_dir: str = "receipts/current",
    ):
        self.repo_root = repo_root
        self.report_dir = report_dir
        self.receipt_dir = receipt_dir

    def check(
        self,
        bundle_path: str,
        manifest: dict,
        candidate_files: List[dict] = None,
    ) -> TaskAwarenessResult:
        """
        Check task awareness for a bundle.

        manifest: the bundle_manifest.json dict
        candidate_files: list of {path, operation, content} dicts
                         (from synthesized candidate if available)
        """
        t = manifest.get("transition", {})
        task_hash_declared = t.get("task_hash", "")
        task_ref_declared = t.get("task_ref", "")
        files = candidate_files or manifest.get("files", [])

        result = TaskAwarenessResult(
            bundle_path=bundle_path,
            task_hash_declared=task_hash_declared,
            task_ref_declared=task_ref_declared,
            agreement="NONE",
            routing="fail_closed",
        )

        result.files_checked = [f.get("path", "") for f in files]

        # --- Check 1: task_hash declared ---
        result.add_check(
            name="task_hash_declared",
            expected="non-empty sha256 hash",
            found=task_hash_declared or "[empty]",
            passed=bool(task_hash_declared),
            routing_if_fail="fail_closed",
        )

        if not task_hash_declared:
            result.agreement = "NONE"
            result.routing = "fail_closed"
            result.print_visible()
            self._write(result)
            return result

        # --- Check 2: task_ref declared ---
        result.add_check(
            name="task_ref_declared",
            expected="path to task file (e.g. task.md)",
            found=task_ref_declared or "[empty]",
            passed=bool(task_ref_declared),
            routing_if_fail="sandbox",
        )

        # --- Check 3: task file exists ---
        task_context = load_task_context(task_ref_declared, self.repo_root)
        task_exists = task_context is not None

        result.add_check(
            name="task_file_exists",
            expected=f"file exists at {task_ref_declared}",
            found="found" if task_exists else "NOT FOUND",
            passed=task_exists,
            routing_if_fail="sandbox",
        )

        # --- Check 4: task_hash matches task file ---
        if task_exists and task_hash_declared:
            actual_hash = task_context["hash"]
            hash_matches = (task_hash_declared == actual_hash or
                           task_hash_declared == "sha256:pending-bind-at-install")
            result.add_check(
                name="task_hash_matches_file",
                expected=task_hash_declared[:24] + "...",
                found=actual_hash[:24] + "...",
                passed=hash_matches,
                routing_if_fail="review",
            )
            if not hash_matches:
                result.add_warning(
                    "task_hash_drift",
                    f"declared hash {task_hash_declared[:16]} "
                    f"!= actual {actual_hash[:16]} — "
                    f"task may have changed since candidate was generated"
                )

        # --- Check 5: files address the task ---
        if files and task_context:
            keywords = task_context["keywords"]
            for f in files:
                path = f.get("path", "")
                content = f.get("content", "").lower()
                # Check if file path or content relates to task keywords
                relevant = any(
                    kw in path.lower() or kw in content
                    for kw in keywords
                ) if keywords else True

                if relevant:
                    result.files_task_relevant.append(path)
                else:
                    result.files_task_irrelevant.append(path)

            relevance_ratio = (len(result.files_task_relevant) /
                               len(files)) if files else 0

            result.add_check(
                name="files_address_task",
                expected="at least one file relevant to task",
                found=f"{len(result.files_task_relevant)}/{len(files)} "
                      f"files task-relevant "
                      f"({relevance_ratio:.0%})",
                passed=len(result.files_task_relevant) > 0,
                routing_if_fail="review",
            )

        elif files and not task_context:
            result.add_warning(
                "cannot_verify_file_relevance",
                "task file not found — cannot verify files address task"
            )

        # --- Determine agreement level ---
        failures = [c for c in result.checks_performed if not c["passed"]]
        critical_failures = [f for f in failures
                              if f["routing_if_fail"] == "fail_closed"]
        review_failures = [f for f in failures
                           if f["routing_if_fail"] == "review"]
        sandbox_failures = [f for f in failures
                            if f["routing_if_fail"] == "sandbox"]

        if critical_failures:
            result.agreement = "NONE"
            result.routing = "fail_closed"
        elif review_failures:
            result.agreement = "MISMATCH"
            result.routing = "review"
        elif sandbox_failures:
            result.agreement = "UNKNOWN"
            result.routing = "sandbox"
        elif result.files_task_irrelevant and result.files_task_relevant:
            result.agreement = "PARTIAL"
            result.routing = "synthesis"
        else:
            result.agreement = "FULL"
            result.routing = "proceed"

        result.print_visible()
        self._write(result)
        return result

    def _write(self, result: TaskAwarenessResult) -> None:
        """Write report and receipt."""
        os.makedirs(self.report_dir, exist_ok=True)
        os.makedirs(self.receipt_dir, exist_ok=True)

        report_path = os.path.join(self.report_dir,
                                   "task_awareness_report.json")
        existing = []
        if os.path.exists(report_path):
            try:
                with open(report_path) as f:
                    existing = json.load(f)
                if not isinstance(existing, list):
                    existing = [existing]
            except Exception:
                existing = []
        existing.append(result.to_dict())
        with open(report_path, "w") as f:
            json.dump(existing, f, indent=2)

        receipt_path = os.path.join(self.receipt_dir,
                                    "task_awareness_receipt.jsonl")
        with open(receipt_path, "a") as f:
            f.write(json.dumps(result.to_dict(), sort_keys=True) + "\n")

        # Write to GitHub step summary if available
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
        if summary_path:
            with open(summary_path, "a") as f:
                f.write("## Task Awareness Check\n\n")
                f.write(f"**Agreement:** `{result.agreement}`  \n")
                f.write(f"**Routing:** `{result.routing}`  \n")
                f.write(f"**Admissible:** `{result.is_admissible()}`  \n\n")

                if result.failures:
                    f.write("### Failures\n\n")
                    for failure in result.failures:
                        f.write(f"- **{failure['check']}**\n")
                        f.write(f"  - expected: `{failure['expected']}`\n")
                        f.write(f"  - found: `{failure['found']}`\n")
                        f.write(f"  - action: {failure['action']}\n\n")

                if result.warnings:
                    f.write("### Warnings\n\n")
                    for w in result.warnings:
                        f.write(f"- **{w['warning']}**: {w['detail']}\n")
                f.write("\n")
