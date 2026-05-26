"""tools.scripts.resolve_stage — Resolve the active stage from stage_map.json."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-override", default="")
    parser.add_argument("--state-file", default="tracking/stegverse-002/stage_map.json")
    parser.add_argument("--output-env", default="")
    args = parser.parse_args()

    if args.stage_override:
        active = args.stage_override
    else:
        p = Path(args.state_file)
        if p.exists():
            with open(p) as f:
                data = json.load(f)
            active = data.get("current_stage", "SV002-M5")
        else:
            active = "SV002-M5"

    if args.output_env:
        with open(args.output_env, "a") as f:
            f.write(f"active_stage={active}\n")

    print(f"active_stage={active}")


if __name__ == "__main__":
    main()
