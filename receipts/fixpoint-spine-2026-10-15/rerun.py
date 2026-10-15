#!/usr/bin/env python3
"""Check retained identities and recompute bounded results; starts no analyzers."""
import hashlib,json,lzma,re,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
MANIFEST=json.loads((HERE/'manifest.json').read_text())

def data(suffix):
    matches=[r for r in MANIFEST['files'] if r['recorded_file'].endswith(suffix)]
    assert len(matches)==1,(suffix,len(matches))
    r=matches[0];b=(HERE/r['file']).read_bytes()
    return lzma.decompress(b) if r['compression']=='xz' else b

def js(suffix):return json.loads(data(suffix))

def saved():
    checked=set()
    for r in MANIFEST['files']:
        b=(HERE/r['file']).read_bytes()
        assert hashlib.sha256(b).hexdigest()==r['file_sha256'],r['file']
        u=lzma.decompress(b) if r['compression']=='xz' else b
        assert hashlib.sha256(u).hexdigest()==r['public_uncompressed_sha256'],r['file']
        if r['raw_byte_identity']:assert r['recorded_sha256']==r['public_uncompressed_sha256']
        checked.add(r['file'])
    score=js('experiment/receipts/analysis/scoreboard.json')
    assert score['valid_cells']==score['expected_cells']==len(score['cells'])==136
    assert len(score['groups'])==34
    baseline=js('experiment/receipts/baseline/scoreboard.json')
    previous={(g['app'],g['ownership'],g['verification'],g['audit']):g
        for g in baseline['groups'] if g['binary']=='spine'}
    tables=['attributes','block_values','constants','controller_bindings','controller_cache','copies','ir','params','returns','side_table']
    for g in score['groups']:
        assert g['complete'] and g['valid_cells']==4
        actual=[];reasons=[]
        for setting in g['settings']:
            prefix='native-cells/'+g['app']+'/'+g['ownership']+'/'+setting
            r=js(prefix+'/result.json');assert r['valid']
            actual.append(r['observations']['value_digests'])
            if g['app']=='campfire':
                rows=js(prefix+'/reason-rows.json')
                assert len(rows)==r['observations']['reason_rows']['count']
                reasons.append(rows)
        equal=[t for t in tables if all(v[t]==actual[0][t] for v in actual)]
        assert equal==g['v2_equal_digests']==g['v1_equal_digests']
        old=previous[g['app'],'ownership-'+g['ownership'],g['verification'],g['audit']]
        for t in tables:
            values=[old['value_digests'][t]['by_schedule'][s] for s in ['unset','1','2','repeat']]
            assert all(v is not None for v in values)
            assert (t in equal)==all(v==values[0] for v in values)
        if g['app']=='campfire':
            assert len(equal)==(10 if g['ownership']=='on' else 9)
            assert all(r==reasons[0] for r in reasons)
            assert g['reason_rows']['status']=='equal'
        for schedule,v in zip(['unset','1','2','repeat'],actual):assert v==g['value_digests'][schedule]
    profiles=[js('experiment/profiles/research-'+x+'.json') for x in ['on','off']]
    for p,v in zip(profiles,['1','0']):
        assert p['RH_SPLICED_WRITER_OWNERSHIP']==p['RH_SKIP_RETURN_STABILIZE']==v
    kit=js('experiment/receipts/integrated-kit-validation.json')
    assert kit['all_checks_passed']
    part=kit['writer_partition_expected_negative_counters']
    assert part['schedules']==32928 and part['membership_checks']==418656
    c=part['counts']
    for n in ['partition_plain','partition_reflective']:assert c[n]==2104
    for n in ['replay_plain','replay_reflective']:assert c[n]==548
    assert c['reflective_bound']==c['plain_bound']==c['membership_plain']==c['membership_reflective']==0
    log=data('experiment/receipts/native/writer-partition-census.log').decode()
    m=re.search(r'WRITER-PARTITION-SUMMARY (\{[^\n]+\})',log)
    assert m and json.loads(m[1])==part
    assert log.count('WRITER-PARTITION-CELL ')==2104
    negative=data('experiment/receipts/native/writer-partition-original.log').decode()
    assert 'test result: FAILED. 0 passed; 1 failed;' in negative
    native=js('experiment/receipts/native/index.json')
    assert all(r['exit']==(101 if r['name'] in ['cargo-test-lib','writer-partition-original'] else 0) for r in native)
    lib=js('experiment/receipts/native/cargo-test-lib-serialized.json');assert lib['exit']==0
    assert b'1245 passed; 0 failed; 26 ignored' in data('experiment/receipts/native/cargo-test-lib-serialized.log')
    assert all(x['exit']==0 for x in js('experiment/receipts/kits/index.json'))
    review=js('independent-review/scoreboard-audit.json')
    assert review['checked_cells']==136 and review['checked_groups']==34 and review['checked_delta_files']==272
    assert not review['errors']
    for sample in js('independent-review/fresh/comparison.json'):
        assert sample['valid_old'] and sample['valid_fresh'] and not sample['observation_changes']
        old=js('independent-review/samples/'+sample['name']+'/old/reason-rows.json')
        fresh=js('independent-review/samples/'+sample['name']+'/fresh/reason-rows.json')
        assert old==fresh
    return dict(files=len(checked),valid_cells=136,groups=34,campfire_reason_groups=8,
        library_passed=1245,partition_differences=2104,replay_differences=548,reflective_bound_violations=0,
        verdict='bounded integration confirmed; partition law still fails; larger-app equalities unchanged',native_runs=0)

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]=='saved','Usage: python3 rerun.py saved'
    print(json.dumps(saved(),sort_keys=True))
