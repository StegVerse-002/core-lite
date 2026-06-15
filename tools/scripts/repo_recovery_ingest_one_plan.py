#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return 'sha256:' + h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', default='.')
    parser.add_argument('--wrap-report', default='reports/current/repo_recovery_wrap_report.json')
    parser.add_argument('--report-dir', default='reports/current')
    parser.add_argument('--receipt-dir', default='receipts/current')
    parser.add_argument('--index', type=int, default=0)
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    wrap_report_path = root / args.wrap_report
    report_dir = root / args.report_dir
    receipt_dir = root / args.receipt_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    receipt_dir.mkdir(parents=True, exist_ok=True)

    if not wrap_report_path.exists():
        raise SystemExit(f'wrap report missing: {wrap_report_path}')

    wrap_report = json.loads(wrap_report_path.read_text())
    wrapped = wrap_report.get('wrapped', [])
    if not wrapped:
        raise SystemExit('wrap report has no recovery bundles')
    if args.index < 0 or args.index >= len(wrapped):
        raise SystemExit(f'index {args.index} outside wrapped range 0..{len(wrapped)-1}')

    selected = wrapped[args.index]
    bundle_path = root / selected['bundle_path']
    if not bundle_path.exists():
        raise SystemExit(f'selected recovery bundle missing: {bundle_path}')

    bundle_sha = sha256_file(bundle_path)
    report = {
        'schema': 'stegverse.repo_recovery.ingest_one_plan.v1',
        'entity': 'StegVerse-002',
        'stage': 'SV002-M11',
        'generated_at': now(),
        'decision': 'ALLOW_ONE_PROOF_INGESTION',
        'selected_index': args.index,
        'selected_bundle_path': selected['bundle_path'],
        'selected_bundle_sha256': bundle_sha,
        'source_path': selected.get('source_path'),
        'source_sha256': selected.get('source_sha256'),
        'recovery_id': selected.get('recovery_id'),
        'manual_declared_input': {
            'task_id': '',
            'input_type': 'bundle',
            'input_path': selected['bundle_path'],
            'stage_override': 'SV002-M11',
            'dry_run': 'false',
            'agent_provider': 'none',
        },
        'governance': {
            'single_bundle_only': True,
            'bulk_ingestion': False,
            'does_not_delete_originals': True,
            'does_not_install_directly': True,
            'declared_input_route_required': True,
            'receipt_before_claim': True,
        },
    }

    report_path = report_dir / 'repo_recovery_ingest_one_plan.json'
    receipt_path = receipt_dir / 'repo_recovery_ingest_one_plan_receipt.jsonl'
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    receipt = {
        'schema': 'stegverse.repo_recovery.ingest_one_plan_receipt.v1',
        'timestamp_utc': now(),
        'decision': report['decision'],
        'report_path': report_path.relative_to(root).as_posix(),
        'report_sha256': sha256_file(report_path),
        'selected_bundle_path': selected['bundle_path'],
        'selected_bundle_sha256': bundle_sha,
        'authority': 'plan_only',
        'bulk_ingestion': False,
    }
    with receipt_path.open('a') as f:
        f.write(json.dumps(receipt, sort_keys=True) + '\n')

    print(json.dumps({
        'status': 'success',
        'decision': report['decision'],
        'report': report_path.relative_to(root).as_posix(),
        'receipt': receipt_path.relative_to(root).as_posix(),
        'manual_declared_input': report['manual_declared_input'],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
