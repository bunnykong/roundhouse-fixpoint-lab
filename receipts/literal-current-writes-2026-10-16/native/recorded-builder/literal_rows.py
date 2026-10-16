#!/usr/bin/env python3
"""Two-variant literal-transfer reducer; preserves native keys and explicit empty parameter vectors."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
F = D.parents[1]
S = ('unset', '1', '2', 'repeat')
PARTS = ('attributes', 'block_values', 'constants', 'controller_bindings', 'controller_cache',
         'copies', 'ir', 'params', 'returns', 'side_table')
APPS = {'chatwoot': ('v1-a1', 'v0-a0'), 'mastodon': ('v1-a1',), 'forem': ('v1-a1',)}
def read(p): return json.loads(Path(p).read_text())
def save(p,x): Path(p).write_text(json.dumps(x, sort_keys=True, indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
def sig(v): return None if v is None else (v['hash'],v.get('note',0))
def load(path, selected=None):
    rows={}
    with path.open() as f:
        fp=json.loads(next(f))
        for line in f:
            v=json.loads(line);key=(v['part'],v['key'])
            if key[0] not in PARTS or (selected is not None and key not in selected): continue
            if key in rows: raise ValueError('duplicate '+str(key))
            v.setdefault('note',0);rows[key]=v
    present={k.rsplit('[',1)[0] for part,k in rows if part=='params'}
    for k,h in fp['parts'].get('params',{}).items():
        key=('params',k+'[empty]')
        if k not in present and (selected is None or key in selected):
            # With a selected load, check presence from the native parent only.
            if selected is None or key in selected:
                rows[key]={'part':'params','key':key[1],'hash':h,'note':0,'ty':None,'empty_vector':True}
    return fp,rows

def reduce(app,obs):
    out=D/'receipts/rows'/app/obs;out.mkdir(parents=True,exist_ok=True)
    sigs={};paths={};checks={}
    for arm in ('C','L'):
        label=read(D/'receipts/cache/labels'/('literal-'+arm.lower()+'-on')/'label.json')
        for schedule in S:
            ref=label['cells'][app+'/'+schedule+'-'+obs]
            native=read(ref['result']);assert ref['valid'] and native['valid']
            path=Path(native['directory'])/'contributor-values.jsonl'
            fp,rows=load(path)
            assert fp['digests']==native['observations']['value_digests'],(arm,schedule,'ten digests')
            ir=sorted([v['span']['file'],v['span']['start'],v['span']['end'],v['hash'],v['note']]
                      for (part,k),v in rows.items() if part=='ir')
            assert ir==fp['ir'],(arm,schedule,'IR multiset')
            for part in ('returns','side_table'):
                assert {k:v['hash'] for (p,k),v in rows.items() if p==part}==fp['parts'][part],(arm,schedule,part)
            parents={k.rsplit('[',1)[0] for p,k in rows if p=='params'}
            assert parents==set(fp['parts']['params']),(arm,schedule,'parameter presence')
            ident=arm+'/'+schedule;paths[ident]=path
            sigs[ident]={k:sig(v) for k,v in rows.items()}
            checks[ident]={'fingerprint_matches_native':True,'ir_multiset_exact':True,
                'returns_and_side_table_exact':True,'parameter_presence_exact':True,
                'source':str(path),'source_sha256':sha(path),'native':ref['result'],
                'native_sha256':sha(ref['result']),'row_counts':dict(Counter(p for p,k in rows))}
            del rows
    allkeys=set().union(*(set(v) for v in sigs.values()))
    changed={k for k in allkeys if len({v.get(k) for v in sigs.values()})>1}
    values={ident:load(path,changed)[1] for ident,path in paths.items()}
    rows=[]
    for part,key in sorted(changed):
        k=(part,key)
        sample=next(v[k] for v in values.values() if k in v)
        rows.append({'part':part,'key':key,'span':sample.get('span'),
            'C':{s:values['C/'+s].get(k) for s in S},'L':{s:values['L/'+s].get(k) for s in S}})
    path=out/'rows.jsonl'
    with path.open('w') as f:
        for row in rows: f.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
    reconcile=out/'reconciled.json';save(reconcile,{'complete':True,'cells':checks})
    print(app,obs,'changed-or-varying rows',len(rows),flush=True)
    return {'file':str(path),'reconciled':str(reconcile)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--app',choices=tuple(APPS));args=ap.parse_args()
    bundle=read(D/'receipts/bundle.json')
    for app,observers in APPS.items():
        if args.app and args.app!=app: continue
        for obs in observers: bundle.setdefault('rows',{}).setdefault(app,{})[obs]=reduce(app,obs)
    save(D/'receipts/bundle.json',bundle)
if __name__=='__main__':main()
