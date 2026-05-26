"""tools.scripts.bootstrap_identity — SV002-M0 identity declaration."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entity", default="StegVerse-002")
    parser.add_argument("--repo", default="StegVerse-002/core-lite")
    parser.add_argument("--gate", default="SV002-M0")
    parser.add_argument("--version", default="1.0.0-sv002-m10")
    args = parser.parse_args()

    state = {
        "schema": "stegverse_identity_declaration.v1",
        "entity": args.entity,
        "repo": args.repo,
        "gate": args.gate,
        "version": args.version,
        "declared_at": datetime.now(timezone.utc).isoformat(),
        "role": "governed-ai-intellect-block",
        "authority_flags": {
            "mutation_authority": False,
            "workflow_change_authority": False,
            "incoming_submission_authority": False,
            "production_authority": False,
            "identity_authority": False,
        },
        "forbidden_actions": [
            "production_mutation",
            "deploy_without_review",
            "bypass_cge",
            "identity_verification_claim",
            "training_data_use",
        ],
        "active_stop_condition": "Identity and scope recorded — no operational action taken",
        "node_status": "NOT_A_NODE",
        "finco_participation_allowed": False,
    }

    out = Path("tracking/stegverse-002/identity_declaration.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(state, f, indent=2)

    # Also initialize stage map
    stage_map_path = Path("tracking/stegverse-002/stage_map.json")
    if not stage_map_path.exists():
        stage_map = {
            "schema": "stegverse_stage_map.v1",
            "entity": args.entity,
            "current_stage": "SV002-M0",
            "current_gate": "SV002-M0 — Identity and scope declaration",
            "active_stop_condition": "Identity and scope recorded",
            "stages": {
                "SV002-M0":  {"status": "complete", "name": "Identity and scope declaration"},
                "SV002-M1":  {"status": "pending",  "name": "Observation and reporting"},
                "SV002-M2":  {"status": "pending",  "name": "Declared task execution + receipts"},
                "SV002-M3":  {"status": "pending",  "name": "Remote target inspection"},
                "SV002-M4":  {"status": "pending",  "name": "Candidate preparation"},
                "SV002-M5":  {"status": "pending",  "name": "Core-Lite Intake Enablement"},
                "SV002-M6":  {"status": "pending",  "name": "CGE + sandbox loop"},
                "SV002-M7":  {"status": "pending",  "name": "LLM Adapter Gate"},
                "SV002-M8":  {"status": "pending",  "name": "KnowledgeVault context-packet integration"},
                "SV002-M9":  {"status": "pending",  "name": "TV/TVC encryption layer"},
                "SV002-M10": {"status": "pending",  "name": "Governed mutation proposal + quorum"},
            },
        }
        with open(stage_map_path, "w") as f:
            json.dump(stage_map, f, indent=2)

    print(json.dumps({"status": "ok", "entity": args.entity, "gate": args.gate}, indent=2))


if __name__ == "__main__":
    main()
