import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUESTS = [
    ROOT / "automation" / "stegguardian-workflow-install-request.json",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_target_from_request(request):
    display = request["target_path_display"]
    if display.startswith("github/"):
        return ROOT / ".github" / display.removeprefix("github/")
    return ROOT / display


def process_workflow_install(request_path):
    request = load_json(request_path)
    source = ROOT / request["source_path"]
    target = canonical_target_from_request(request)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return {
        "request_id": request["request_id"],
        "source_path": str(source.relative_to(ROOT)),
        "target_path_display": request["target_path_display"],
        "installed": True,
        "validation_command": request["validation_command"],
    }


def main():
    results = []
    for request_path in REQUESTS:
        if request_path.exists():
            results.append(process_workflow_install(request_path))

    receipt_dir = ROOT / "receipts"
    receipt_dir.mkdir(exist_ok=True)
    receipt_path = receipt_dir / "automation-processing-receipt.json"
    receipt_path.write_text(json.dumps({"processed": results}, indent=2) + "\n", encoding="utf-8")

    print(f"Processed automation requests: {len(results)}")
    print(f"Receipt written: {receipt_path.relative_to(ROOT)}")
    return 0


main()
