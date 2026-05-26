#!/usr/bin/env python3
"""CLI wrapper for governed bundle ingestion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from core_lite.bundles.ingest import BundleIngestor


def main() -> None:
    parser = argparse.ArgumentParser(prog="tools.scripts.ingest_bundle")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--entity", default="StegVerse-002")
    parser.add_argument("--stage", default="SV002-M10")
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    result = BundleIngestor(
        Path(args.repo_root),
        entity=args.entity,
        stage=args.stage,
        dry_run=args.dry_run,
    ).ingest(args.input_path)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
