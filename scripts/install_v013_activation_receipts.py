#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/current/v013_activation_receipt_install_report.json'
RECEIPT = ROOT / 'receipts/current/v013_activation_receipt_install_receipt.jsonl'
BUNDLE = ROOT / 'dist/bundles/proposed_transition_bundle.zip'
INGEST_RECEIPT = ROOT / 'receipts/current/transition_bundle_ingest_receipt.jsonl'
REQUIRED_OUTPUTS = [
    'receipts/current/v013_activation_receipt_install_receipt.jsonl',
    'reports/current/v013_activation_receipt_install_report.json',
    'receipts/current/transition_bundle_ingest_receipt.jsonl',
    'receipts/current/heartbeat_evaluation_receipt.jsonl',
    'receipts/current/scheduler_liveness_receipt.jsonl',
    'receipts/current/repo_structure_verification_receipt.jsonl',
    'reports/current/repo_structure_verification.json',
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def run_cmd(args: list[str], name: str) -> dict:
    out = ROOT / f'reports/current/{name}_stdout.txt'
    err = ROOT / f'reports/current/{name}_stderr.txt'
    out.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    out.write_text(p.stdout, encoding='utf-8')
    err.write_text(p.stderr, encoding='utf-8')
    return {'name': name, 'exit_code': p.returncode, 'stdout': str(out.relative_to(ROOT)), 'stderr': str(err.relative_to(ROOT))}


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj, sort_keys=True, separators=(',', ':')) + '\n')


def output_state() -> dict:
    present = [x for x in REQUIRED_OUTPUTS if (ROOT / x).exists()]
    missing = [x for x in REQUIRED_OUTPUTS if not (ROOT / x).exists()]
    total = len(REQUIRED_OUTPUTS)
    return {
        'total': total,
        'present_count': len(present),
        'missing_count': len(missing),
        'percent_present': round((len(present) / total) * 100, 2),
        'present': present,
        'missing': missing,
    }


def main() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    steps: list[dict] = []

    if BUNDLE.exists() and not INGEST_RECEIPT.exists():
        steps.append(run_cmd([sys.executable, 'scripts/ingest_transition_bundle.py', str(BUNDLE.relative_to(ROOT)), '--repo-root', '.'], 'v013_install_ingest'))
    elif INGEST_RECEIPT.exists():
        steps.append({'name': 'v013_install_ingest', 'exit_code': 0, 'skipped': True, 'reason': 'ingest_receipt_already_present'})
    else:
        steps.append({'name': 'v013_install_ingest', 'exit_code': 2, 'skipped': True, 'reason': 'bundle_missing'})

    steps.append(run_cmd([sys.executable, 'scripts/check_transition_bundle_proof.py', '--repo-root', '.'], 'v013_install_proof_check'))
    steps.append(run_cmd([sys.executable, 'scripts/evaluate_heartbeat_mode.py', '--repo-root', '.'], 'v013_install_heartbeat_eval'))
    steps.append(run_cmd([sys.executable, 'scripts/check_scheduler_liveness.py', '--repo-root', '.', '--max-age-minutes', '20'], 'v013_install_scheduler_liveness'))
    steps.append(run_cmd([sys.executable, 'scripts/verify_repo_structure.py', '--repo-root', '.'], 'v013_install_repo_structure'))

    outputs = output_state()
    status = 'INSTALLED_WITH_RECEIPTS' if INGEST_RECEIPT.exists() else 'INSTALLED_PARTIAL_RECEIPTS'
    report = {
        'schema': 'stegverse.v013_activation_receipt_install.v1',
        'timestamp': now(),
        'version': '0.1.3-gllm',
        'entity': 'StegVerse-002',
        'repo': 'StegVerse-002/core-lite',
        'status': status,
        'bundle_present': BUNDLE.exists(),
        'ingest_receipt_present': INGEST_RECEIPT.exists(),
        'required_outputs': outputs,
        'steps': steps,
        'authority': {
            'candidate_evidence_only': True,
            'canonical_authority': False,
            'broad_authority': False,
            'may_bind_repo_state': False
        }
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    append_jsonl(RECEIPT, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if status == 'INSTALLED_WITH_RECEIPTS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
