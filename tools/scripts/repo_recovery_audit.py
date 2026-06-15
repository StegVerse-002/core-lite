#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, hashlib, json
from pathlib import Path
PROTECTED_DIRS={'.git','.github','core_lite','tools','scripts','tests','schemas','config','reports','receipts','tracking','dist','quarantine','outputs','agent_history','__pycache__'}
PROTECTED_ROOT={'README.md','MANUAL_INSTALL.md','bundle_manifest.json','pyproject.toml','setup.py','requirements.txt','.gitignore'}
EXTS={'.zip','.json','.jsonl','.md','.txt','.py','.yml','.yaml','.toml','.csv'}
HINTS=('task catalog','task_catalog','task dispatcher','task_dispatcher','ci smoke ingestion loop','ci_smoke_ingestion_loop','candidate','bundle','patch','manifest')
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return 'sha256:'+h.hexdigest()
def rel(p,r): return p.relative_to(r).as_posix()
def skip(p,r):
    parts=p.relative_to(r).parts
    return '.git' in parts or '__pycache__' in parts
def classify(p,r):
    rp=rel(p,r); parts=Path(rp).parts; low=p.name.lower(); suf=p.suffix.lower()
    rec={'path':rp,'sha256':sha(p),'size_bytes':p.stat().st_size,'protected':False}
    if parts[0]=='incoming':
        if p.name in ('README.md','.gitkeep'):
            rec.update(classification='incoming_retained_control_file', proposed_action='retain', reason='incoming control file')
        elif len(parts)>1 and parts[1]=='recovery':
            rec.update(classification='recovery_lane_payload', proposed_action='retain', reason='already in recovery lane')
        else:
            rec.update(classification='stranded_incoming_payload', proposed_action='wrap_for_ingestion', reason='incoming payload requires manifest-bearing recovery before cleanup')
    elif parts[0] in {'reports','receipts','tracking','dist','quarantine','outputs','agent_history'}:
        rec.update(classification='evidence_or_artifact_path', proposed_action='retain', reason='evidence/artifact path is not relocated by recovery audit')
    elif parts[0] in PROTECTED_DIRS:
        rec.update(protected=True, classification='protected_repo_path', proposed_action='retain', reason='protected repo path')
    elif len(parts)==1 and p.name in PROTECTED_ROOT:
        rec.update(protected=True, classification='protected_root_file', proposed_action='retain', reason='protected root file')
    elif len(parts)==1 and (suf in EXTS or any(h in low for h in HINTS)):
        rec.update(classification='root_misplaced_semantic_file', proposed_action='wrap_for_ingestion', reason='root-level semantic file should be wrapped, not directly moved')
    elif len(parts)==1:
        rec.update(classification='root_unclassified', proposed_action='fail_closed', reason='root-level file is not known safe')
    elif suf in EXTS:
        rec.update(classification='repo_unresolved_semantic_file', proposed_action='wrap_for_ingestion', reason='semantic file outside canonical protected/evidence lanes')
    else:
        rec.update(classification='repo_unclassified', proposed_action='fail_closed', reason='not enough policy to classify')
    return rec
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--report-dir',default='reports/current'); ap.add_argument('--receipt-dir',default='receipts/current'); ap.add_argument('--max-file-bytes',type=int,default=25*1024*1024); a=ap.parse_args()
    root=Path(a.repo_root).resolve(); rd=root/a.report_dir; cd=root/a.receipt_dir; rd.mkdir(parents=True,exist_ok=True); cd.mkdir(parents=True,exist_ok=True)
    records=[]; skipped=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() or skip(p,root): continue
        size=p.stat().st_size
        if size>a.max_file_bytes: skipped.append({'path':rel(p,root),'reason':'file_too_large_for_recovery_audit','size_bytes':size}); continue
        try: records.append(classify(p,root))
        except Exception as e: skipped.append({'path':rel(p,root),'reason':'classification_failed:'+str(e)})
    ac={}; cc={}
    for x in records:
        ac[x['proposed_action']]=ac.get(x['proposed_action'],0)+1; cc[x['classification']]=cc.get(x['classification'],0)+1
    decision='ALLOW' if ac.get('fail_closed',0)==0 else 'FAIL_CLOSED'
    report={'schema':'stegverse.repo_recovery.audit.v1','entity':'StegVerse-002','stage':'SV002-M11','generated_at':now(),'decision':decision,'read_only':True,'records':records,'skipped':skipped,'summary':{'total_records':len(records),'skipped':len(skipped),'action_counts':ac,'classification_counts':cc,'wrap_for_ingestion_count':ac.get('wrap_for_ingestion',0),'fail_closed_count':ac.get('fail_closed',0)},'governance':{'no_broad_authority':True,'cleanup_may_move_to_final_destination':False,'wrap_required_for_unresolved_semantic_content':True,'ingestion_decides_destination':True,'originals_deleted':False}}
    rp=rd/'repo_recovery_audit_report.json'; cp=cd/'repo_recovery_audit_receipt.jsonl'; rp.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    receipt={'schema':'stegverse.repo_recovery.audit_receipt.v1','timestamp_utc':now(),'decision':decision,'report_path':rp.relative_to(root).as_posix(),'report_sha256':sha(rp),'wrap_for_ingestion_count':report['summary']['wrap_for_ingestion_count'],'fail_closed_count':report['summary']['fail_closed_count'],'authority':'read_only','originals_deleted':False}
    with cp.open('a') as f: f.write(json.dumps(receipt,sort_keys=True)+'\n')
    print(json.dumps({'status':'success' if decision=='ALLOW' else 'fail_closed','decision':decision,'report':rp.relative_to(root).as_posix(),'receipt':cp.relative_to(root).as_posix(),'summary':report['summary']},indent=2,sort_keys=True))
    return 0 if decision=='ALLOW' else 1
if __name__=='__main__': raise SystemExit(main())
