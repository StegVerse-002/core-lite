#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import zipfile
from pathlib import Path


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return 'sha256:' + h.hexdigest()


def safe_bundle_name(src: str, sh: str) -> str:
    return (
        'sv002_recovery_'
        + sh.replace('sha256:', '')[:16]
        + '_'
        + src.replace('/', '__').replace(' ', '_').replace(':', '_')
        + '.zip'
    )


def recovery_manifest(rec: dict, recovery_id: str, payload_name: str) -> dict:
    return {
        'schema': 'stegverse.recovery_manifest.v1',
        'recovery_id': recovery_id,
        'entity': 'StegVerse-002',
        'stage': 'SV002-M11',
        'created_at': now(),
        'recovery_reason': rec.get('classification', 'repo_recovery'),
        'source_path': rec['path'],
        'source_sha256': rec['sha256'],
        'source_size_bytes': rec.get('size_bytes'),
        'payload_name': payload_name,
        'payload_sha256': rec['sha256'],
        'proposed_route': 'governed_ingestion',
        'destination_authority': 'ingestion_controller_only',
        'cleanup_allowed_after': 'successful_disposition_receipt',
        'original_delete_allowed': False,
        'governance': {
            'no_broad_authority': True,
            'wraps_for_ingestion_only': True,
            'does_not_install_destinations': True,
            'does_not_delete_originals': True,
            'ingestion_decides_destination': True,
        },
    }


def transition_block(rec: dict, recovery_id: str) -> dict:
    """Non-binding evidence transition for recovery payloads.

    Recovery bundles are not install bundles. They are evidence objects that let
    the governed ingestion layer classify, compare, quarantine, or later route
    the payload. Final destination and deletion authority remain outside this
    wrapper.
    """
    return {
        'transition_class': 'evidence',
        'transition_cell': 'B7',
        'authority_class': 'evidence_only',
        'state_effect': 'evidence_state',
        'binding_level': 'non_binding',
        'target_scope': 'repo_recovery_payload',
        'execution_scope': 'none',
        'admissibility_gate': 'transition_table_ingest_gate',
        'disposition_policy': 'store_evidence_only',
        'task_ref': recovery_id,
        'task_hash': rec['sha256'],
        'formalism_refs': [
            {
                'formalism': 'Stage32-AdmissibilitySpaceCoordinates',
                'role': 'recovery_payload_is_evidence_not_execution',
            }
        ],
    }


def bundle_manifest(rec: dict, recovery_id: str, payload_name: str) -> dict:
    return {
        'schema': 'stegverse.bundle_manifest.v1',
        'bundle_id': recovery_id,
        'bundle_type': 'repo_recovery_payload',
        'entity': 'StegVerse-002',
        'stage': 'SV002-M11',
        'created_at': now(),
        'description': 'Manifest-bearing recovery bundle. Ingestion decides final disposition; original source is not deleted by wrap.',
        'transition': transition_block(rec, recovery_id),
        'files': [
            {
                'path': 'payload/' + payload_name,
                'source_path': rec['path'],
                'sha256': rec['sha256'],
                'size_bytes': rec.get('size_bytes'),
                'purpose': 'repo_recovery_payload',
            },
            {
                'path': 'recovery_manifest.json',
                'purpose': 'recovery_metadata',
            },
        ],
        'governance': {
            'no_broad_authority': True,
            'wraps_for_ingestion_only': True,
            'does_not_install_destinations': True,
            'does_not_delete_originals': True,
            'ingestion_decides_destination': True,
            'transition_block_written': True,
            'transition_class': 'evidence',
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--audit-report', default='reports/current/repo_recovery_audit_report.json')
    ap.add_argument('--report-dir', default='reports/current')
    ap.add_argument('--receipt-dir', default='receipts/current')
    ap.add_argument('--incoming-recovery-dir', default='incoming/recovery')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    root = Path(a.repo_root).resolve()
    audit = root / a.audit_report
    report_dir = root / a.report_dir
    receipt_dir = root / a.receipt_dir
    incoming_recovery = root / a.incoming_recovery_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    receipt_dir.mkdir(parents=True, exist_ok=True)
    if not a.dry_run:
        incoming_recovery.mkdir(parents=True, exist_ok=True)

    if not audit.exists():
        raise SystemExit('audit report missing: ' + str(audit))

    data = json.loads(audit.read_text())
    candidates = [r for r in data.get('records', []) if r.get('proposed_action') == 'wrap_for_ingestion']
    wrapped = []
    failed = []

    for rec in candidates:
        source = root / rec['path']
        if not source.exists() or not source.is_file():
            failed.append({'path': rec['path'], 'reason': 'source_missing'})
            continue
        current_sha = sha(source)
        if current_sha != rec.get('sha256'):
            failed.append({
                'path': rec['path'],
                'reason': 'source_hash_changed',
                'audit_sha256': rec.get('sha256'),
                'current_sha256': current_sha,
            })
            continue

        recovery_id = 'sv002-recovery-' + current_sha.replace('sha256:', '')[:16]
        payload_name = Path(rec['path']).name
        bundle_name = safe_bundle_name(rec['path'], current_sha)
        bundle_path = incoming_recovery / bundle_name
        recovery_meta = recovery_manifest(rec, recovery_id, payload_name)
        bundle_meta = bundle_manifest(rec, recovery_id, payload_name)

        entry = {
            'source_path': rec['path'],
            'source_sha256': current_sha,
            'recovery_id': recovery_id,
            'bundle_path': bundle_path.relative_to(root).as_posix(),
            'bundle_manifest_schema': bundle_meta['schema'],
            'recovery_manifest_schema': recovery_meta['schema'],
            'transition_class': bundle_meta['transition']['transition_class'],
            'transition_block_written': True,
            'dry_run': a.dry_run,
            'original_deleted': False,
            'destination_installed': False,
        }
        if not a.dry_run:
            with zipfile.ZipFile(bundle_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr('bundle_manifest.json', json.dumps(bundle_meta, indent=2, sort_keys=True) + '\n')
                z.writestr('recovery_manifest.json', json.dumps(recovery_meta, indent=2, sort_keys=True) + '\n')
                z.write(source, arcname='payload/' + payload_name)
                z.writestr(
                    'README_RECOVERY.md',
                    '# StegVerse Recovery Bundle\n\n'
                    'Cleanup/recovery wrapped this object. Ingestion decides final disposition. '
                    'Originals are not deleted by this task. The manifest declares a non-binding evidence transition.\n',
                )
            entry['bundle_sha256'] = sha(bundle_path)
        wrapped.append(entry)

    decision = 'ALLOW' if not failed else 'FAIL_CLOSED'
    report = {
        'schema': 'stegverse.repo_recovery.wrap.v3',
        'entity': 'StegVerse-002',
        'stage': 'SV002-M11',
        'generated_at': now(),
        'decision': decision,
        'dry_run': a.dry_run,
        'audit_report': audit.relative_to(root).as_posix(),
        'audit_report_sha256': sha(audit),
        'wrapped': wrapped,
        'failed': failed,
        'summary': {
            'candidates': len(candidates),
            'wrapped': len(wrapped),
            'failed': len(failed),
            'bundles_created': 0 if a.dry_run else len(wrapped),
            'transition_blocks_written': len(wrapped),
        },
        'governance': {
            'no_broad_authority': True,
            'does_not_delete_originals': True,
            'does_not_install_destinations': True,
            'wraps_for_ingestion_only': True,
            'ingestion_decides_destination': True,
            'bundle_manifest_written': True,
            'transition_block_written': True,
            'transition_class': 'evidence',
        },
    }

    report_path = report_dir / 'repo_recovery_wrap_report.json'
    receipt_path = receipt_dir / 'repo_recovery_wrap_receipt.jsonl'
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    receipt = {
        'schema': 'stegverse.repo_recovery.wrap_receipt.v3',
        'timestamp_utc': now(),
        'decision': decision,
        'dry_run': a.dry_run,
        'report_path': report_path.relative_to(root).as_posix(),
        'report_sha256': sha(report_path),
        'wrapped': len(wrapped),
        'failed': len(failed),
        'originals_deleted': False,
        'destinations_installed': False,
        'transition_blocks_written': len(wrapped),
        'authority': 'read_only' if a.dry_run else 'scoped_repo_write',
    }
    with receipt_path.open('a') as f:
        f.write(json.dumps(receipt, sort_keys=True) + '\n')

    print(json.dumps({
        'status': 'success' if decision == 'ALLOW' else 'fail_closed',
        'decision': decision,
        'dry_run': a.dry_run,
        'report': report_path.relative_to(root).as_posix(),
        'receipt': receipt_path.relative_to(root).as_posix(),
        'summary': report['summary'],
    }, indent=2, sort_keys=True))
    return 0 if decision == 'ALLOW' else 1


if __name__ == '__main__':
    raise SystemExit(main())
