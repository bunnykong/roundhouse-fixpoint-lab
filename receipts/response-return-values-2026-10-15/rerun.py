#!/usr/bin/env python3
"""Verify retained bytes and recompute the bounded saved result; starts no analyzer."""
import hashlib,json,lzma,sys
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
MANIFEST=json.loads((HERE/'manifest.json').read_text())
FACT=json.loads((HERE/'result.json').read_text())['fact']

def data(suffix):
    rows=[x for x in MANIFEST['files'] if x['recorded_file'].endswith(suffix)]
    assert len(rows)==1,(suffix,len(rows))
    row=rows[0];b=(HERE/row['file']).read_bytes()
    return lzma.decompress(b) if row['compression']=='xz' else b

def js(suffix):return json.loads(data(suffix))

def saved():
    checked=set()
    for row in MANIFEST['files']:
        b=(HERE/row['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['file_sha256'],row['file']
        u=lzma.decompress(b) if row['compression']=='xz' else b
        assert hashlib.sha256(u).hexdigest()==row['public_uncompressed_sha256'],row['file']
        if row['raw_byte_identity']:assert row['recorded_sha256']==row['public_uncompressed_sha256']
        checked.add(row['file'])
    if FACT==63:
        v=js('experiment/receipts/verdict-all.json')
        for key,want in [('primary','CONFIRMED'),('h5','UNBLOCKED'),('discourse','CONFIRMED')]:
            assert v[key]['verdict']==want
            assert all(x['status']=='PASS' for x in v[key]['checks'])
        rows=js('independent-review/all-row-audit.json')['pairs']
        assert len(rows)==23 and sum(x['common_rows'] for x in rows)==5370451
        assert all(not x['non_nil_losses'] and x['left_only']==x['right_only']==0 for x in rows)
        summary=js('independent-review/all-row-summary.json')
        assert summary['pairs']==23 and summary['non_nil_losses']==0 and summary['structural_rows']==0
        cells=js('experiment/receipts/cell-index.json');assert len(cells)==69
        assert all(x['valid'] and x['key']['rh_flags']['RH_SKIP_RETURN_STABILIZE']=='1' for x in cells)
        population=js('experiment/receipts/population-scope.json')
        assert population['customization_rows']==72 and population['precise_customization_rows']==47
        assert sum(x['host_keys'] for x in population['frozen_population'] if x['id'] in ['F-spliced','M-suspension'])==24
        native=js('experiment/receipts/native-summary.json')
        suite=native['suite'];variants=suite.get('variants',suite.get('arms'))
        assert len(variants['off']['failed'])==24 and len(variants['on']['failed'])==25
        assert suite['new_failures']==['analyze::if_branches_union_merge'] and not suite['resolved_failures']
        assert 'data_factory_constants' in suite['selection']['excluded']
        assert native['emission']['pairs']==156 and native['emission']['identical_pairs']==128
        initial=js('initial/receipts/campfire-row-summary.json')
        assert sum(x['counts'].get('returns:NARROW_NONNIL',0) for x in initial)==12
        initial_verdict=js('initial/receipts/verdict-all.json')
        assert initial_verdict['primary']['verdict']=='INCONCLUSIVE'
        sys.path.insert(0,str(HERE/'native'))
        import verdict as V
        customization=json.loads((HERE/'native/customization.json').read_text())
        for setting in ['unset-v0-a0','1-v0-a0','2-v0-a0','repeat-v0-a0']:
            for app,expected in [('forem',6),('mastodon',18)]:
                control=js('ownership/CA/'+app+'/'+setting+'/rows.json')
                treatment=js('ownership/TA/'+app+'/'+setting+'/rows.json')
                assert len(control['hosts'])==len(treatment['hosts'])==expected
                for key,value in control['hosts'].items():
                    assert not V.admits(value,'String') and V.admits(treatment['hosts'][key],'String')
                if app=='mastodon':
                    assert len(control['customization'])==len(treatment['customization'])==72
                    assert set(control['customization'])==set(customization['keys'])
                    for key,value in control['customization'].items():
                        assert V.canon(value)==V.canon(treatment['customization'][key])
                        if key in customization['precise']:assert V.canon(value)==V.canon(customization['precise'][key])
        return dict(fact=63,files=len(checked),pairs=23,reviewed_row_comparisons=5370451,non_nil_losses=0,
            cells=69,ownership_host_slots=24,customization_rows=72,
            verdict='confirmed with stabilization off; ownership witnesses unblocked',native_runs=0)
    sys.path.insert(0,str(HERE/'native'))
    import verdict_returns as V
    import classifiers as C
    import evidence as E
    bundle=js('experiment/receipts/bundle-campfire.json')
    status,reasons,report=V.verdict(bundle)
    assert status=='INCONCLUSIVE' and bundle['integrity']['checker_frozen_before_arms'] is False
    assert any('checker_frozen_before_arms' in x for x in reasons)
    recorded=js('experiment/receipts/verdict-campfire-cli.json');assert recorded['status']==status
    for key in ['issue521','issue964']:
        for setting,row in bundle['fixtures'][key]['K'].items():
            assert row['valid'] and row['returns']==getattr(V,'FIX521' if key=='issue521' else 'FIX964')
    counts=[]
    for index in [1,2]:
        prefix='independent-review/fresh-'+str(index)
        rows={}
        for line in data(prefix+'/reference-catalog.jsonl').splitlines():
            row=json.loads(line);key=(row['part'],row['key']);assert key not in rows;rows[key]=row
        resolve=E.resolver(rows);count=0
        for line in data(prefix+'/current-return-ledger.jsonl').splitlines():
            event=json.loads(line)
            if event.get('event')=='replace' and event.get('superseded'):
                before=resolve(event['superseded']['native_ty']);after=resolve(event['current']['native_ty'])
                count+=C.family(before,after)=='premature_unresolved'
        assert count==14;counts.append(count)
    coverage=js('experiment/receipts/coverage-scope.json')
    assert coverage['K']['snapshot_slots']==883 and coverage['K']['full_final_registry_rows']==8849
    return dict(fact=64,files=len(checked),fresh_recorded_descents=counts,fixture_cases=2,
        verdict='inconclusive',collector_gap=True,whole_registry_coverage=False,native_runs=0)

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]=='saved','Usage: python3 rerun.py saved'
    print(json.dumps(saved(),sort_keys=True))
