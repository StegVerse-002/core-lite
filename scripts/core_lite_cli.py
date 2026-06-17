#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core_lite.sdk import CoreLiteClient


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Governed Core-Lite CLI surface")
    sub = parser.add_subparsers(dest="command", required=True)

    p_resolve = sub.add_parser("resolve-transition")
    p_resolve.add_argument("manifest")

    p_ingest = sub.add_parser("ingest-bundle")
    p_ingest.add_argument("bundle")
    p_ingest.add_argument("--dry-run", action="store_true")

    p_incoming = sub.add_parser("process-incoming")
    p_incoming.add_argument("--incoming-dir", default="incoming")
    p_incoming.add_argument("--dry-run", action="store_true")

    p_review = sub.add_parser("review-candidate")
    p_review.add_argument("candidate_ref")

    p_apply = sub.add_parser("apply-candidate")
    p_apply.add_argument("candidate_ref")
    p_apply.add_argument("review_report")

    args = parser.parse_args()
    client = CoreLiteClient(REPO_ROOT)

    if args.command == "resolve-transition":
        result = client.resolve_transition(load_json(args.manifest))
    elif args.command == "ingest-bundle":
        result = client.ingest_bundle(args.bundle, dry_run=args.dry_run)
    elif args.command == "process-incoming":
        result = client.process_incoming(args.incoming_dir, dry_run=args.dry_run)
    elif args.command == "review-candidate":
        result = client.review_candidate(args.candidate_ref)
    elif args.command == "apply-candidate":
        result = client.apply_candidate(args.candidate_ref, args.review_report)
    else:
        parser.error("unknown command")
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    decision = str(result.get("decision", ""))
    return 0 if decision in {"ALLOW", "ALLOW_DRY_RUN", "ALLOW_CANDIDATE_REVIEW", "ALLOW_INSTALL", "ALLOW_CANDIDATE_ONLY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
