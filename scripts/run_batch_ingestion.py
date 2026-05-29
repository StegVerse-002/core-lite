#!/usr/bin/env python3
"""
scripts/run_batch_ingestion.py — StegVerse-002

CLI entry point for the batch ingestion controller.
Called by declared-input-route in the workflow when a bundle is detected.

Usage:
    python3 scripts/run_batch_ingestion.py \
        --bundles incoming/bundle1.zip incoming/bundle2.zip \
        --entity StegVerse-002 \
        --stage SV002-M11 \
        [--dry-run] \
        [--repo-root .] \
        [--report-dir reports/current] \
        [--receipt-dir receipts/current]

Exit codes:
    0 — batch processed, all admitted or candidate-classified
    1 — one or more bundles quarantined or failed
    2 — controller error
"""
import argparse
import json
import os
import sys

# Add repo root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundles", nargs="+", required=True,
                        help="Paths to bundle zip files to process")
    parser.add_argument("--entity", default="StegVerse-002")
    parser.add_argument("--stage", default="SV002-M11")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--report-dir", default="reports/current")
    parser.add_argument("--receipt-dir", default="receipts/current")
    parser.add_argument("--mailbox-root", default="incoming/mailbox")
    parser.add_argument("--tracking-root", default="tracking")
    parser.add_argument("--quarantine-dir", default="quarantine/incoming")
    parser.add_argument("--dist-dir", default="dist/bundles")
    parser.add_argument("--sandbox-dist-dir", default="dist/sandbox")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Validate bundle paths
    missing = [b for b in args.bundles if not os.path.exists(b)]
    if missing:
        print(json.dumps({
            "status": "error",
            "error": f"bundles not found: {missing}",
        }))
        sys.exit(2)

    try:
        from core_lite.batch_ingestion import BatchIngestionController

        controller = BatchIngestionController(
            repo_root=args.repo_root,
            mailbox_root=args.mailbox_root,
            tracking_root=args.tracking_root,
            report_dir=args.report_dir,
            receipt_dir=args.receipt_dir,
            quarantine_dir=args.quarantine_dir,
            dist_dir=args.dist_dir,
            sandbox_dist_dir=args.sandbox_dist_dir,
            entity=args.entity,
            stage=args.stage,
            dry_run=args.dry_run,
        )

        result = controller.process_batch(args.bundles)

        summary = {
            "status": "success",
            "batch_id": result.batch_id,
            "bundles_processed": result.bundles_processed,
            "bundles_admitted": result.bundles_admitted,
            "bundles_quarantined": result.bundles_quarantined,
            "bundles_sandboxed": result.bundles_sandboxed,
            "bundles_installed": result.bundles_installed,
            "candidates_found": result.candidates_found,
            "synthesis_attempted": result.synthesis_attempted,
            "errors": result.errors,
            "dry_run": args.dry_run,
        }

        print(json.dumps(summary, indent=2))

        # Exit 1 if any quarantined (signal to workflow)
        if result.bundles_quarantined > 0 and result.bundles_admitted == 0:
            sys.exit(1)
        sys.exit(0)

    except ImportError as e:
        print(json.dumps({
            "status": "error",
            "error": f"import error — core_lite.batch_ingestion not installed: {e}",
        }))
        sys.exit(2)
    except Exception as e:
        import traceback
        print(json.dumps({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }))
        sys.exit(2)


if __name__ == "__main__":
    main()
