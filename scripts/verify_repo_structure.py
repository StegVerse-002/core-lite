#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def write_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj, sort_keys=True, separators=(',', ':')) + '\n')


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--repo-root', default='.')
    p.add_argument('--targets', default='config/repo_structure_targets.json')
    p.add_argument('--report', default='reports/current/repo_structure_verification.json')
    p.add_argument('--receipt', default='receipts/current/repo_structure_verification_receipt.jsonl')
    args = p.parse_args()

    root = Path(args.repo_root).resolve()
    targets = json.loads((root / args.targets).read_text(encoding='utf-8'))
    groups = {
        'activation_required': targets.get('activation_required', []),
        'health_observability': targets.get('health_observability', []),
    }

    result = {}
    total = 0
    present_count = 0
    for name, paths in groups.items():
        present = [x for x in paths if (root / x).exists()]
        missing = [x for x in paths if not (root / x).exists()]
        total += len(paths)
        present_count += len(present)
        result[name] = {
            'total': len(paths),
            'present_count': len(present),
            'missing_count': len(missing),
            'percent_present': round((len(present) / len(paths)) * 100, 2) if paths else 100.0,
            'present': present,
            'missing': missing,
        }

    combined_percent = round((present_count / total) * 100, 2) if total else 100.0
    report = {
        'schema': 'stegverse.repo_structure_verification.v1',
        'timestamp': now(),
        'version': targets.get('version', '0.1.3-gllm'),
        'entity': targets.get('entity', 'StegVerse-002'),
        'repo': targets.get('repo', 'StegVerse-002/core-lite'),
        'combined': {
            'total': total,
            'present_count': present_count,
            'missing_count': total - present_count,
            'percent_present': combined_percent,
        },
        'groups': result,
        'line_4_delta_formula': 'structure_percent_present - stated_repo_percent_complete',
    }

    report_path = root / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    write_jsonl(root / args.receipt, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
