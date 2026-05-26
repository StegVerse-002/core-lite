"""tools.scripts.update_stage_state — Update stage state after a successful run."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", default="tracking/stegverse-002/stage_map.json")
    parser.add_argument("--stage", required=True)
    parser.add_argument("--status", default="last_run_success")
    args = parser.parse_args()

    p = Path(args.state_file)
    if not p.exists():
        print(f"State file not found: {p}")
        return

    with open(p) as f:
        data = json.load(f)

    stages = data.get("stages", {})
    if args.stage in stages:
        stages[args.stage]["last_run"] = datetime.now(timezone.utc).isoformat()
        stages[args.stage]["last_status"] = args.status
        if args.status == "last_run_success":
            stages[args.stage]["status"] = "complete"

    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(p, "w") as f:
        json.dump(data, f, indent=2)

    print(json.dumps({"status": "ok", "stage": args.stage, "updated": args.status}))


if __name__ == "__main__":
    main()
