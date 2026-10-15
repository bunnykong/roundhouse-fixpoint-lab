#!/usr/bin/env python3
from pathlib import Path
import datetime, hashlib, json, subprocess
D=Path(__file__).resolve().parent
R=D/'week/evidence/results/pending-factorial'
C=D/'week/evidence/sources/probe-source'
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *a:subprocess.check_output(['git','-C',str(C),*a],text=True).strip()
meta=load(R/'integrity.json'); setup=load(R/'setup.json'); cleanup=load(R/'cleanup.json')
assert sha(D/'protocol.md')==setup['card_sha256']
assert sha(D/'protocol.md')==sha(D.parents[1]/'phase2/provenance-provenance/factorial_protocol.md')
assert git('rev-parse','HEAD')==meta['head']
assert git('show','-s','--format=%P','HEAD')==meta['base']
assert git('rev-list','--count',meta['base']+'..HEAD')=='1'
assert git('branch','--show-current')=='parameter-pending-reader-view'
assert git('status','--short')==''
for path,h in meta['source_sha256'].items(): assert sha(C/path)==h,path
for path,h in meta['scripts_sha256'].items(): assert sha(D/path)==h,path
assert sha(D/'patches/0001-lineage-factorial.patch')==meta['patch_sha256']
assert all(not paths for paths in cleanup['targets'].values())
for relative in cleanup['targets']:
    assert not any(p.is_file() for p in (D/relative).rglob('*')),relative
assert cleanup['clean_exit_codes']=={'laws':0,'provenance':0,'default-control':0}
for arm in ['00','10','01','11']:
    assert (R/('A'+arm+'.exit')).read_text().strip()=='0'
for arm in ['b1','b3']:
    for schedule in ['unset','seed-1','seed-2','unset-repeat']:
        assert (D/'week/evidence/results/pending-factorial-campfire'/arm/schedule/'probe.exit').read_text().strip()=='0'
assert (R/'preview.exit').read_text().strip()=='0'
assert 'no problems found' in (R/'preview.log').read_text()
assert load(R/'default-control-summary.json')['both_failures_reproduced']
assert (D/'RESULT.md').exists()
report={'condition':setup['condition'],'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'head':meta['head'],'branch':git('branch','--show-current'),'new_commits':1,'working_tree_clean':True,
 'card_unchanged':True,'committed_sources_match_integrity_receipt':True,'patch_matches_commit':True,
 'cargo_cleanup_complete':True,'markdown_preview':'no problems found',
 'result_sha256':sha(D/'RESULT.md'),'timing_claim':False}
(R/'final-integrity.json').write_text(json.dumps(report,indent=2)+'\n')
paths=[p for p in (D/'week/evidence/results').rglob('*') if p.is_file() and p.name!='sha256.json']
paths += [D/'protocol.md',D/'RESULT.md',D/'claim.md',D/'patches/0001-lineage-factorial.patch']
paths += list(D.glob('*.sh'))+list(D.glob('*.py'))
(R/'sha256.json').write_text(json.dumps({str(p.relative_to(D)):sha(p) for p in sorted(set(paths))},indent=2)+'\n')
print(json.dumps(report,indent=2))
