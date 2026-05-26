"""tools.validators.schema_validator — Validate schemas and manifests."""

import argparse
import json
import logging
from pathlib import Path

log = logging.getLogger("tools.validators.schema_validator")

REQUIRED_SCHEMAS = [
    "stegverse_knowledgevault_manifest.schema.json",
    "stegverse_memory_index.schema.json",
    "stegverse_context_packet.schema.json",
    "stegverse_multimodal_input_manifest.schema.json",
    "stegverse_memory_use_receipt.schema.json",
    "stegverse_transition_stage.schema.json",
    "stegverse_ai_tier.schema.json",
    "stegverse_llm_adapter_instruction_packet.schema.json",
    "stegverse_cge_fingerprint.schema.json",
]


def validate_schemas(schemas_dir: Path) -> dict:
    results = {"status": "ok", "schemas": {}, "missing": [], "invalid": []}
    for schema_name in REQUIRED_SCHEMAS:
        schema_path = schemas_dir / schema_name
        if not schema_path.exists():
            results["missing"].append(schema_name)
            results["schemas"][schema_name] = "missing"
        else:
            try:
                with open(schema_path) as f:
                    json.load(f)
                results["schemas"][schema_name] = "ok"
            except json.JSONDecodeError as e:
                results["invalid"].append(schema_name)
                results["schemas"][schema_name] = f"invalid: {e}"

    if results["missing"] or results["invalid"]:
        results["status"] = "warnings"
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schemas-dir", default="schemas/")
    args = parser.parse_args()

    result = validate_schemas(Path(args.schemas_dir))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
