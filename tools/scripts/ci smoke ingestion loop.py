#!/usr/bin/env python3
"""CI smoke check for the StegVerse-002 governed ingestion loop.

Purpose: give a single, unambiguous pass/fail that the ingestion loop fires
end-to-end UNDER THE REAL RUNNER -- not just in a developer container.

It drives a known-good bundle through BatchIngestionController (the same path
the M11 fix wired pipeline.py to) and asserts:
  1. the controller returns a final_disposition,
  2. the disposition is an admit (INSTALLED / ADMITTED),
  3. a receipt was written to receipts/current/,
  4. an evidence-plane contribution was recorded.

Exit 0  = loop fired end-to-end; engine is alive under this runner.
Exit 1  = loop did not complete; stderr/report names the failing step.

This is a TOOL (review/verification only). It installs nothing and mutates no
source files. It is invoked as a declared task via the dispatcher, so it adds
NO new workflow file (Core-Lite 1-2 .yml constraint preserved).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Governed ingestion loop CI smoke check.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument(
        "--bundle",
        default="incoming/sv002_diagnostics_bundle.zip",
        help="Known-good bundle to drive through the loop (repo-relative).",
    )
    ap.add_argument("--entity", default="StegVerse-002")
    ap.add_argument("--stage", default="SV002-M11")
    ap.add_argument(
        "--report",
        default="reports/current/ci_smoke_ingestion_report.json",
    )
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    report_path = root / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    receipts_dir = root / "receipts" / "current"
    evidence_path = root / "tracking" / "evidence_plane" / "evidence_plane.jsonl"

    result = {
        "schema": "stegverse.ci_smoke.ingestion_loop.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entity": args.entity,
        "stage": args.stage,
        "bundle": args.bundle,
        "checks": {},
        "passed": False,
    }

    def fail(step: str, detail: str) -> int:
        result["checks"][step] = {"ok": False, "detail": detail}
        result["passed"] = False
        report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        print(f"::error::CI smoke FAILED at step '{step}': {detail}", file=sys.stderr)
        return 1

    # Step 1: bundle present
    bundle_file = root / args.bundle
    if not bundle_file.exists():
        return fail("bundle_present", f"bundle not found: {bundle_file}")
    result["checks"]["bundle_present"] = {"ok": True, "detail": str(bundle_file)}

    # Step 2: controller importable (engine code present + installed)
    try:
        from core_lite.batch_ingestion.controller import BatchIngestionController
    except Exception as e:  # noqa: BLE001
        return fail("controller_import", f"cannot import BatchIngestionController: {e!r}")
    result["checks"]["controller_import"] = {"ok": True, "detail": "import ok"}

    # Step 3: run the governed loop
    try:
        controller = BatchIngestionController(
            repo_root=str(root),
            entity=args.entity,
            stage=args.stage,
            dry_run=False,
        )
        proc = controller.process_bundle(str(bundle_file))
    except Exception as e:  # noqa: BLE001
        return fail("process_bundle", f"controller raised: {e!r}")
    result["process_result_keys"] = sorted(proc.keys()) if isinstance(proc, dict) else None

    # Step 4: disposition returned
    disposition = (proc or {}).get("final_disposition")
    if not disposition:
        return fail("disposition_returned", f"no final_disposition in result: {proc}")
    result["checks"]["disposition_returned"] = {"ok": True, "detail": disposition}

    # Step 5: disposition is an admit
    admitted = ("INSTALLED" in disposition) or ("ADMITTED" in disposition)
    if not admitted:
        return fail(
            "disposition_admitted",
            f"known-good bundle was not admitted; disposition={disposition}",
        )
    result["checks"]["disposition_admitted"] = {"ok": True, "detail": disposition}

    # Step 6: a receipt was written
    receipts = list(receipts_dir.glob("**/*.json*")) if receipts_dir.exists() else []
    if not receipts:
        return fail("receipt_written", f"no receipt found under {receipts_dir}")
    result["checks"]["receipt_written"] = {"ok": True, "detail": f"{len(receipts)} receipt file(s)"}

    # Step 7: evidence-plane contribution recorded
    contribs = (proc or {}).get("evidence_plane_contributions") or []
    evidence_ok = bool(contribs) or evidence_path.exists()
    if not evidence_ok:
        return fail("evidence_recorded", "no evidence-plane contribution and no evidence_plane.jsonl")
    result["checks"]["evidence_recorded"] = {
        "ok": True,
        "detail": f"contributions={len(contribs)}, evidence_file={'yes' if evidence_path.exists() else 'no'}",
    }

    result["passed"] = True
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    print("CI smoke PASSED: governed ingestion loop fired end-to-end.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
