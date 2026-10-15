#!/usr/bin/env python3
"""Verify retained bytes and reduce recorded observations; performs no native analysis."""
import csv
import hashlib
import io
import json
import lzma
from collections import Counter
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
MANIFEST=json.loads((HERE/'manifest.json').read_text())
FACT=json.loads((HERE/'result.json').read_text())['fact']

def entries(suffix):return [r for r in MANIFEST['files'] if r['recorded_file'].endswith(suffix)]
def data(suffix):
    matches=entries(suffix)
    assert len(matches)==1,(suffix,len(matches))
    r=matches[0];value=(HERE/r['file']).read_bytes()
    if r.get('compression')=='xz':value=lzma.decompress(value)
    return value
def js(suffix):return json.loads(data(suffix))
def lines(suffix):return [json.loads(s) for s in data(suffix).splitlines() if s.strip()]

def verify():
    checked=set()
    for r in MANIFEST['files']:
        p=HERE/r['file'];b=p.read_bytes()
        assert hashlib.sha256(b).hexdigest()==r['file_sha256'],r['file']
        u=lzma.decompress(b) if r.get('compression')=='xz' else b
        assert hashlib.sha256(u).hexdigest()==r['public_uncompressed_sha256'],r['file']
        if r['raw_byte_identity']:assert r['recorded_sha256']==r['public_uncompressed_sha256']
        checked.add(r['file'])
    return len(checked)

def reduce():
    if FACT==56:
        v=js('experiment/receipts/campfire-verdict.json')
        mandatory=[r for r in v['checks'] if r['mandatory']]
        assert len(mandatory)==207 and all(r['status']=='pass' for r in mandatory)
        general=js('experiment/receipts/general-verdict.json')['apps']
        assert general['forem']['status']=='pass'
        assert all(general[a]['status']=='fail' for a in ['chatwoot','mastodon','discourse'])
        assert general['discourse']['missing']
        pair=js('experiment/receipts/chatwoot-parity-counterexample.json')
        for setting in ['unset-v0-a0','unset-v1-a1','repeat-v0-a0','repeat-v1-a1']:
            changed=pair[setting]['changed_tables'];assert set(changed)=={'ir','params'}
            assert changed['ir']==dict(C='b49a2d63d056da93',SK='0e1b938af3af3593')
            assert changed['params']==dict(C='d7ede1c7606c79af',SK='5c3afa7cfbcc6023')
        # Complete saved candidate reason rows, independently of the gate's stored pass bits.
        for audit in [0,1]:
            rows=[js('supplement/campfire/complete-reads/'+s+'-v0-a'+str(audit)+'/reason-rows.json') for s in ['unset','1','2','repeat']]
            assert all(x==rows[0] for x in rows[1:]) and len(rows[0])==4815
        return dict(mandatory_passes=len(mandatory),reason_rows_per_setting=4815,generalization='failed',discourse='incomplete with observed failure')
    if FACT==57:
        final=js('experiment/results/verdict-final.json')
        assert final['verdict']=='CONFIRMED' and final['original_cells_unchanged']==36 and final['new_cells']==2
        check=js('experiment/results/check-apps-final.json')
        assert check['status']=='pass' and not check['failures'] and not check['problems']
        total=0
        for name,count in [('witness-4.0.7.json',66),('witness-3.4.4.json',66),('witness-twins-4.0.7.json',21)]:
            w=js('experiment/results/'+name)
            assert w['fixtures']==len(w['rows'])==count and w['mismatches']==0
            assert all(r['ok'] and r['written']==r['expected'] for r in w['rows'])
            if name!='witness-3.4.4.json':total+=count
        cells=js('supplement/app-evidence.json')['cells']
        assert len(cells)==38 and all(r['label_valid'] for r in cells)
        return dict(runtime_predictions=total,required_app_cells=len(cells),earlier_cells_unchanged=36,completed_controls=2,verdict='bounded confirmation')
    if FACT==58:
        v=js('experiment/evidence/H1.json')
        failures=Counter(r['check'] for r in v['checks'] if r['status']=='fail')
        assert v['verdict']=='KILLED' and failures['C-schedules']==2 and failures['K4-aliases']==8
        residual=js('experiment/evidence/return-residual.json')['settings']
        for observer in ['v0-a0','v1-a1']:
            states=[residual[s+'-'+observer]['values'] for s in ['unset','1','2','repeat']]
            own=[r['ApplicationController#require_authentication']['join'] for r in states]
            module=[r['Authentication#require_authentication']['join'] for r in states]
            assert all(x==own[0] for x in own) and module[0]==module[3] and module[1]==module[2] and module[0]!=module[1]
        return dict(verdict='killed',schedule_failures=2,alias_failure_settings=8,larger_app_stages='not run')
    if FACT==59:
        totals={};primary={};headline={}
        for app,n,probe,want,new in [('forem',72,'P',51,0),('chatwoot',757,'P',243,34),('mastodon',2915,'R',1037,1171)]:
            catalog=lines('experiment/receipts/'+app+'/attribution.jsonl')
            raw=lines('experiment/receipts/'+app+'/varying-rows.jsonl')
            assert len(catalog)==len(raw)==n
            assert len({r['id'] for r in catalog})==n
            assert {r['id'] for r in catalog}=={r['id'] for r in raw}
            count=sum(probe in r['sensitivities'] for r in catalog)
            assert count==want
            summary=js('experiment/receipts/'+app+'/attribution-summary.json')
            assert summary['interventions'][probe]['new_varying_rows']==new
            assert sum(summary['primary_mediators'].values())==n
            assert Counter(r['source'] for r in catalog)==summary['primary_mediators']
            totals[app]=n;headline[app]=dict(removed_original_variance=count,new_variance=new)
            if app=='mastodon':
                capped=sum(r['status'].endswith('-capped') for r in catalog);assert capped==1294
        assert sum(totals.values())==3744
        return dict(rows=totals,headlines=headline,unresolved_capped_mastodon=1294,verdict='attribution only')
    if FACT==60:
        records={}
        for pin in ['f47','spine','strict-producers-complete-reads','closure-application']:
            census=js('experiment/receipts/'+pin+'-census.json')['census_summary'][0]
            c=census['counts'];assert c['partition_plain']==2104 and c['replay_plain']==548
            assert census['schedules']==32928 and census['membership_checks']==418656
            expected=19056 if pin in ['spine','strict-producers-complete-reads'] else 0
            assert c['reflective_bound']==expected and c['membership_plain']==c['membership_reflective']==0
            # Recount the actual failure rows, without treating observer exit zero as law success.
            counts=Counter()
            for line in data('experiment/receipts/'+pin+'-census.log').decode().splitlines():
                marker='WRITER-PARTITION-CELL '
                if marker in line:
                    row=json.loads(line.split(marker,1)[1]);counts.update(row['failures'])
            assert counts['partition_plain']==2104 and counts['replay_plain']==548 and counts['reflective_bound']==expected
            records[pin]=c
        return dict(verdict='negative partition/replay counts preserved',schedules_per_form=32928,counts=records)
    if FACT==61:
        namespace={'__name__':'retained_runtime_sets','__file__':str(HERE/'native/runtime_sets.py')}
        exec(compile(data('integration/scripts/runtime_sets.py'),'retained_runtime_sets.py','exec'),namespace)
        rows=lines('experiment/receipts/rows.jsonl')
        tally=Counter(namespace['relation']((r.get('baseline_row') or {}).get('resolved_ty'),(r.get('arm_row') or {}).get('resolved_ty')) for r in rows)
        assert len(rows)==2658 and tally==dict(EQ=764,STRUCT=328,WIDEN=2,NARROW=1564)
        verdicts=Counter(r['verdict'] for r in csv.DictReader(io.StringIO(data('integration/evidence/narrow-verdicts.tsv').decode()),delimiter='\t'))
        assert verdicts==dict(UNSOUND_W=578,SOUND_W=900,SOUND_GUARD=57,BOUNDARY=16,UNWITNESSED=13)
        sample=js('independent-review/sample-admission.json')
        assert sample['passing_samples']==len(sample['samples'])==10
        assert all(r['main_admits'] and not r['variant_admits'] for r in sample['samples'])
        review=js('independent-review/recount.json');assert review['replayed_observations']==35
        return dict(observations=len(rows),relations=tally,narrowing_classes=verdicts,sampled_counterexamples=10,original_runtime_observations=35,verdict='finite witness classification')
    raise ValueError(FACT)

def main():
    if len(sys.argv)>1 and sys.argv[1]=='extract':
        assert len(sys.argv)==4,'extract RECORDED_SUFFIX DESTINATION'
        Path(sys.argv[3]).write_bytes(data(sys.argv[2]));return
    assert len(sys.argv)==2 and sys.argv[1]=='saved','Use saved, or extract RECORDED_SUFFIX DESTINATION'
    files=verify();result=reduce()
    print(json.dumps(dict(fact=FACT,verified_files=files,native_runs=0,reduction=result),indent=2,sort_keys=True))

if __name__=='__main__':main()
