#!/usr/bin/env python3
"""Validate retained hashes and recompute the bounded observation; no analyzer execution."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['saved'])
    parser.parse_args()
    manifest=json.loads((HERE/'manifest.json').read_text())
    rows={r['recorded_file']:r for r in manifest['files']}
    checked={}
    for row in manifest['files']:
        if row['file'] in checked:continue
        data=(HERE/row['file']).read_bytes()
        assert sha(data)==row['file_sha256'],row['file']
        content=lzma.decompress(data) if row['compression']=='xz' else data
        assert sha(content)==row['public_uncompressed_sha256'],row['file']
        if row['raw_byte_identity']:assert sha(content)==row['recorded_sha256']
        checked[row['file']]=content

    def data(path):return checked[rows[path]['file']]
    def obj(path):return json.loads(data(path))
    def payload(path,prefix):
        matches=[json.loads(line.split(prefix,1)[1]) for line in data(path).decode().splitlines() if prefix in line]
        assert len(matches)==1,(path,len(matches))
        return matches[0]
    def digest(path):
        value=obj(path)['digest'];assert len(value)==10;return value
    def reason_rows(path):
        result={}
        for line in data(path).splitlines():
            r=json.loads(line)
            key=json.dumps({k:v for k,v in r.items() if k not in ('untyped_kinds','type_hash')},sort_keys=True)
            assert key not in result,'duplicate expression identity'
            result[key]=(r['untyped_kinds'],r['type_hash'])
        assert len(result)==4808
        return result

    n=json.loads((HERE/'pins.json').read_text())['fact']
    result=dict(fact=n,physical_files_checked=len(checked),native_runs=0)
    if n==51:
        extended=payload('experiment/receipts/laws/storage_extended_laws/stdout.log','STORAGE-EXTENDED ')
        assert extended['samples']==36 and extended['counts']=={'idem':177,'pid':6}
        values=[digest('experiment/receipts/campfire/combined/'+s+'/report.json')
                for s in ('unset','1','2','repeat-unset')]
        assert all(v==values[0] for v in values)
        result.update(idempotence_failures=177,identity_failures=6,equal_value_tables=10,verdict='killed')
    elif n==52:
        for normalizer,counts in [('0',{'idem':177,'pid':6}),('1',{})]:
            extended=payload('experiment/matrix/n'+normalizer+'-storage_extended_laws.log','STORAGE-EXTENDED ')
            assert extended['samples']==36 and extended['counts']==counts
        values=[digest('experiment/campfire/on/'+s+'/report.json') for s in ('unset','1','2','repeat')]
        assert all(v==values[0] for v in values)
        reasons={s:reason_rows('experiment/campfire/off/'+s+'/census.jsonl') for s in ('unset','1','2','repeat')}
        assert all(set(v)==set(reasons['unset']) for v in reasons.values())
        counts=[]
        for s in ('1','2','repeat'):
            assert all(reasons[s][k][1]==v[1] for k,v in reasons['unset'].items())
            counts.append(sum(reasons[s][k][0]!=v[0] for k,v in reasons['unset'].items()))
        assert counts==[4,0,0]
        result.update(normalized_law_failures=0,reason_differences=counts,equal_value_tables=10,verdict='bounded confirmation')
    elif n==53:
        changes={}
        for app in ('forem','chatwoot','mastodon'):
            for schedule in ('unset','1','2','repeat-unset'):
                left=digest('experiment/runs/baseline/'+app+'/'+schedule+'/report.json')
                right=digest('experiment/runs/a/'+app+'/'+schedule+'/report.json')
                changed=[k for k in left if k!='copies' and left[k]!=right[k]]
                assert changed,(app,schedule)
                changes[app+'/'+schedule]=changed
        assert len(changes)==12
        result.update(changed_pairs=changes,pair_count=12,native_reports=24,verdict='killed')
    elif n==54:
        summary=obj('experiment/receipts/verification-20261015T150840514485Z/summary.json')
        assert all(summary['checks_on_available_executables'].values())
        assert not summary['strict_historical_binary_recovery']
        assert all(c['passed'] for c in summary['claims'])
        assert all(c['analyzer_runs']==0 and c['exit_code']==0 for c in summary['warm_calls'])
        warm=sum(c['cache_hits'] for c in summary['warm_calls'])
        assert warm==41,warm
        fresh=summary['fresh_comparisons']
        # Each fresh comparison explicitly retains its source/cached equality decision.
        assert len(fresh)==17,len(fresh)
        assert all(x.get('fresh_match',x.get('equal',x.get('identical_observations'))) is True for x in fresh)
        result.update(cached_cells=warm,cached_analyzer_runs=0,fresh_comparisons=len(fresh),verdict='inconclusive historical recovery')
    elif n==55:
        scoreboard=obj('experiment/evidence/scoreboard.json')
        counts={}
        for group in scoreboard['groups']:
            if group['binary']!='spine':continue
            name='/'.join([group['app'],group['ownership'],'v'+str(group['verification'])+'a'+str(group['audit'])])
            equal=sum(len(v.get('by_schedule',{}))==4 and len(set(v['by_schedule'].values()))==1
                      for v in group['value_digests'].values())
            complete=all(len(v.get('by_schedule',{}))==4 for v in group['value_digests'].values())
            counts[name]=equal if complete else None
            if group['app']!='discourse':
                expected={'campfire':10 if group['ownership']=='ownership-on' else 9,'forem':6,'chatwoot':5,'mastodon':5}[group['app']]
                assert equal==expected,(name,equal)
            elif group['verification']==0 and group['audit']==0:assert equal==3,(name,equal)
        usable=sum(r['spine'] is not None and r['main'] is not None for r in scoreboard['matched_cells'])
        assert len(scoreboard['matched_cells'])==160 and usable==138
        completed=sum(g['valid_cells'] for g in scoreboard['groups'])
        completed+=sum(s[k] is not None for s in scoreboard['shipping'] for k in ('spine','main'))
        assert completed==286
        result.update(equal_table_counts=counts,matched_research_cells=usable,completed_native_cells=completed,
                      requested_native_cells=330,verdict='partial negative scoreboard')
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
