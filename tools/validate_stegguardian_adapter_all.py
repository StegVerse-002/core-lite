import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    [sys.executable, "tools/validate_stegguardian_adapter_fixtures.py"],
    [sys.executable, "tools/validate_stegguardian_mock_resolution.py"],
    [sys.executable, "tools/validate_stegguardian_receipt_emission.py"],
    [sys.executable, "tools/generate_stegguardian_receipt_from_stores.py"],
]


def main():
    failures = []
    for command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())
        if result.returncode != 0:
            failures.append(" ".join(command))

    if failures:
        print("StegGuardian unified adapter validation failed:")
        for failure in failures:
            print("- " + failure)
        return 1

    print("StegGuardian unified adapter validation passed")
    return 0


main()
