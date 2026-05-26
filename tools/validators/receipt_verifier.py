"""tools.validators.receipt_verifier — Verify receipt chain integrity."""

import argparse
import hashlib
import json
import logging
from pathlib import Path

log = logging.getLogger("tools.validators.receipt_verifier")


def verify_chain(receipts_dir: Path) -> dict:
    results = {"status": "ok", "files": {}, "chain_breaks": []}

    for receipts_file in sorted(receipts_dir.rglob("*.jsonl")):
        file_results = {"entries": 0, "valid": 0, "breaks": []}
        prev_hash = ""

        with open(receipts_file) as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    file_results["entries"] += 1

                    # Verify previous hash chain
                    stored_prev = entry.get("previous_receipt_hash", "")
                    if i > 0 and stored_prev != prev_hash:
                        break_info = {
                            "line": i + 1,
                            "stored_prev": stored_prev,
                            "expected_prev": prev_hash,
                        }
                        file_results["breaks"].append(break_info)
                        results["chain_breaks"].append({
                            "file": str(receipts_file),
                            **break_info,
                        })
                    else:
                        file_results["valid"] += 1

                    prev_hash = entry.get("receipt_hash", "")
                except json.JSONDecodeError:
                    log.warning("Invalid JSON at line %d in %s", i + 1, receipts_file)

        results["files"][str(receipts_file)] = file_results

    if results["chain_breaks"]:
        results["status"] = "chain_breaks_detected"

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts-dir", default="receipts/")
    args = parser.parse_args()

    result = verify_chain(Path(args.receipts_dir))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
