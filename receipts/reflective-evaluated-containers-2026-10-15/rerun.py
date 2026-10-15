"""Verify retained evidence without compiling or running the analyzer."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['saved','native'],nargs='?',default='saved')
    args=parser.parse_args()
    if args.mode=='native':
        raise SystemExit(subprocess.call(['bash',str(ROOT/'native.sh')]))
    manifest=json.loads((ROOT/'manifest.json').read_text())
    pins=json.loads((ROOT/'pins.json').read_text())
    checked=0
    for row in manifest['files']:
        data=(ROOT/row['file']).read_bytes()
        assert digest(data)==row['file_sha256'],row['file']
        if row['compression']=='xz':data=lzma.decompress(data)
        assert digest(data)==row['public_uncompressed_sha256'],row['file']
        if row['raw_byte_identity']:assert digest(data)==row['recorded_sha256'],row['file']
        checked+=1
    assert checked>0
    def load(suffix):
        candidates=[r for r in manifest['files'] if r['recorded_file'].endswith(suffix)]
        assert len(candidates)==1,(suffix,len(candidates))
        row=candidates[0]; data=(ROOT/row['file']).read_bytes()
        return json.loads(lzma.decompress(data) if row['compression']=='xz' else data)
    n=pins['fact']
    if n==44:
        v=load('experiment/gate-audit-reviewed.json')
        assert v['H1']['verdict']==v['H2']['verdict']=='confirmed'
        assert all(v['H1']['confirm'].values()) and all(v['H2']['confirm'].values())
        v=load('independent-review/rerun-audit.json')
        assert not v['failed_checks'] and all(v['checks'].values())
    elif n==45:
        v=load('factorial-summary.json')['arms']
        assert v['11']['counts']=={} and v['11']['seed_ok'] and v['11']['no_early_never']
        assert v['10']['counts']==dict(assoc=276,fold2=138,fold3=6210,pid=3)
        assert v['01']['counts']==dict(fold2=46,fold3=1656,pid=23)
        s=load('independent-review/supplemental-summary.json')
        assert s['all_A10_failure_occurrences']==6627 and s['pattern_exceptions']==0
    elif n==46:
        rows=load('independent-review/e2e-schedules-v1/summary.json')['rows']
        assert len(rows)==16
        for case,expected in [('bare-bottom','untyped'),('union-bottom','__bot__')]:
            selected=[r for r in rows if r['case']==case]
            assert len(selected)==8
            assert all(r['raw_exit']==0 and r['exports']['param']==expected and r['bound']['cuts']==0 for r in selected)
        rows=load('independent-review/native-bottom-export.json')['rows']
        assert len(rows)==8 and all(r['raw_exit']==101 and r['f29_rendered_type']=='never' for r in rows)
    elif n==47:
        v=load('independent-review/summary.json')['counterexamples']
        assert len(v)==4 and all(r['exit']==101 and len(r['missed'])==8 for r in v.values())
    elif n==48:
        a=load('experiment/evidence/audit-gate.json')
        assert a['generality'] and len(a['edits'])==6
        expected=[60698,60698,60701,136952,136947,136952]
        order=['mastodon-boolean','mastodon-return-type','mastodon-withdraw-read',
            'discourse-boolean','discourse-return-type','discourse-withdraw-read']
        for key,count in zip(order,expected):
            row=a['edits'][key]; assert row['parity']
            counters=row['audit']['1-warm']['counters']
            assert all(counters[k]==count for k in ['input_audit_comparisons','extra_audit_comparisons','guard_audit_comparisons'])
        v=load('experiment/evidence/measurement-summary.json')
        assert v['verdict']=='inconclusive' and v['promotion_blocked']
        assert sum(r['pairs'] for r in v['checks']['edits'].values())==0
        assert sum(r['parent_pairs'] for r in v['checks']['edits'].values())==1
        assert not v['checks']['cold_complete']
    elif n==49:
        v=load('discourse-bijection.json')['runs'][0]
        left={tuple(r) for r in v['L']};right={tuple(r) for r in v['R']}
        missing=left-right
        assert len(left)==1324 and len(right)==1320 and len(missing)==78
        assert len({r[0] for r in missing})==68
        v=load('independent-review/results/native-probes.json')['tests']
        assert len(v)==4
        for r in v.values():
            row=r['rows']['RESIDUAL-WITNESS-ROW']
            assert row['same_storage'] and row['var_first_residual']==0 and row['var_last_residual']==8
    elif n==50:
        v=load('experiment/evidence/audit.json')['arms']
        for key in ['lossless-g','lossless-u']:
            w=v[key]['warm']['census']['untyped_by_provenance']
            c=v[key]['cold']['census']['untyped_by_provenance']
            assert w==c==dict(pending=0,gradual=5459,unresolved=23311)
        w=v['legacy-g']['warm']['census']['untyped_by_provenance']
        c=v['legacy-g']['cold']['census']['untyped_by_provenance']
        assert w['gradual']-c['gradual']==11197 and c['unresolved']-w['unresolved']==11179
        v=load('independent-review/verification.json')
        assert v['all_original_tables_reproduced']
        for schedule in v['emission'].values():
            row=schedule['emission']['scramble']
            assert row['pairs']==105 and row['files']==11432 and row['reason_scrambled']==3804
            assert not row['file_diffs'] and not row['row_diffs']
    print(json.dumps(dict(fact=n,condition=pins['condition'],verified_files=checked,
        saved_evidence_reduction='pass',native_runs=0,experimental_verdict=pins['verdict']),sort_keys=True))

if __name__=='__main__':main()
