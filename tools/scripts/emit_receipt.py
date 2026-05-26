"""tools.scripts.emit_receipt — CLI wrapper for receipt emission."""

import argparse
import json
from pathlib import Path
from core_lite.receipts import append_receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--gate", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--decision", default="ALLOW")
    parser.add_argument("--basis", default="")
    parser.add_argument("--output", default="receipts/current/receipt.jsonl")
    parser.add_argument("--stop-condition", default="")
    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    receipt = append_receipt(
        args.output,
        actor=args.actor,
        stage=args.stage,
        gate=args.gate,
        task_id=args.task_id,
        decision=args.decision,
        basis=args.basis,
        stop_condition=args.stop_condition,
    )
    print(json.dumps({"status": "ok", "receipt_hash": receipt.receipt_hash}, indent=2))


if __name__ == "__main__":
    main()
