#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core_lite.incoming import IncomingMailbox

ARTIFACT_PATH = Path("dist/run_artifacts/incoming-mailbox.zip")


def main() -> int:
    report = IncomingMailbox(REPO_ROOT, "incoming", stage="SV002-M12", dry_run=False).process()
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARTIFACT_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [
            Path("reports/current/incoming_mailbox_report.json"),
            Path("receipts/current/incoming_mailbox_receipt.jsonl"),
            Path("outputs/incoming_mailbox.md"),
        ]:
            full = REPO_ROOT / path
            if full.exists():
                archive.write(full, path.as_posix())
    compact = {
        "decision": report.get("decision"),
        "status": report.get("status"),
        "processed_count": len(report.get("processed", [])),
        "rejected_count": len(report.get("rejected", [])),
        "ignored_count": len(report.get("ignored", [])),
        "report_path": "reports/current/incoming_mailbox_report.json",
        "artifact_path": str(ARTIFACT_PATH),
    }
    print(json.dumps(compact, indent=2, sort_keys=True))
    return 0 if report.get("decision") == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
