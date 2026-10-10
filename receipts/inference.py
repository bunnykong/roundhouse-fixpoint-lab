#!/usr/bin/env python3
"""Recheck retained public traces, re-record Ruby inputs, or rerun pinned inference snapshots."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

LAB = Path(__file__).resolve().parents[1]
FORK = 'https://github.com/bunnykong/roundhouse.git'
BOT = '{ __bottom__: nil }'

def load_checker():
    spec = importlib.util.spec_from_file_location('inference_oracle', LAB / 'oracle/check.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def read(p): return json.loads(p.read_text())
def dump(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
def trace_path(id, row):
    return LAB / 'receipts' / id / ((row['program'] + '/trace.jsonl') if id == 'F19' else 'trace.jsonl')
def app_path(id, row):
    return LAB / 'reproductions' / (row['program'] if id == 'F19' else 'destructuring_matrix')
def conditions(id): return read(LAB / 'receipts' / id / 'conditions.json')

def assess(directory, trace):
    checker = load_checker()
    slots = read(directory / 'slots.json')
    raw = read(directory / 'raw.json')
    rows = []
    for stage in ['final', 'graph']:
        report = checker.check_records(checker.Grammar((directory / (stage + '.rbs')).read_text()),
                                       checker.load_records(trace), slots)
        rejected = sorted({v['slot'] for v in report['violations']})
        rows.append(dict(stage=stage, records=report['records'], rejected=report['records']-report['accepted'],
                         rejected_slots=len(rejected), rejected_slot_names=rejected,
                         selected_slots=len(slots), unresolved=sum('__var__' in t for t in raw.values()),
                         missing=sum(t == '__missing__' for t in raw.values())))
    return rows

def recompute(id):
    allrows = []
    for row in conditions(id):
        for result in assess(LAB/'receipts'/id/row['directory'], trace_path(id,row)):
            result.update(arm=row['arm'], program=row.get('program'), commit=row['commit'])
            allrows.append(result)
    if id == 'F19':
        for stage in ['final','graph']:
            totals = {arm:sum(r['rejected'] for r in allrows if r['stage']==stage and r['arm']==arm)
                      for arm in ['baseline','bottom','pending-var']}
            assert totals == {'baseline':0,'bottom':52,'pending-var':0}, totals
        for name in ['pend_bot','pend_census']:
            raw = read(LAB/'receipts/F19'/name/'pending-var/raw.json')
            keys = [k for k in raw if k.endswith('_len_ret') or k.endswith('_limit_text_ret')]
            assert len(keys) == (1 if name=='pend_bot' else 4), keys
            assert all(raw[k]=='Integer' for k in keys)
    else:
        finals = {r['arm']:r for r in allrows if r['stage']=='final'}
        assert [finals[k]['rejected_slots'] for k in ['baseline','initial','repaired']] == [155,116,0]
        base, initial = (set(finals[k]['rejected_slot_names']) for k in ['baseline','initial'])
        assert len(initial-base)==51 and len(base-initial)==90
        assert finals['repaired']['unresolved']==362
        assert all(r['selected_slots']==836 for r in allrows)
    return allrows

def record(id, output):
    output.mkdir(parents=True,exist_ok=True)
    rows = []
    seen = set()
    for row in conditions(id):
        old = trace_path(id,row)
        if old in seen: continue
        seen.add(old)
        meta = json.loads(old.read_text().splitlines()[0])
        opts = meta['options']
        name = row.get('program','destructuring_matrix')
        dest = output/(name+'.jsonl')
        command = ['ruby',str(LAB/'oracle/record.rb')]
        for p in opts['sources']: command.extend(['--source',str(LAB/p)])
        for key in ['returns','params']:
            if opts[key]: command.extend(['--'+key,','.join(opts[key])])
        command.extend(['--entry',opts['entry'],'--output',str(dest)])
        proc = subprocess.run(command,cwd=LAB,capture_output=True,text=True)
        if proc.returncode: raise RuntimeError(proc.stderr)
        def values(p):
            return [(r['slot'],r['value']) for r in map(json.loads,p.read_text().splitlines()) if r.get('kind')=='value']
        assert values(old)==values(dest), 'recorded values differ: '+name
        rows.append(dict(program=name,records=len(values(dest)),same_values=True))
    dump(output/'verification.json',rows)
    return rows

def reduced_grammar(stderr, final, roots):
    bodies = {}
    for line in stderr.splitlines():
        m = re.match(r'rh-fold-rbs: type (\w+) = (.*?)\s*(?:#.*)?$',line)
        if m: bodies[m[1]]=re.sub(r'\bbot\b',BOT,m[2].strip())
    for alias in roots: bodies.setdefault(alias,final[alias])
    pending,needed=list(roots),{}
    while pending:
        alias=pending.pop()
        if alias in needed: continue
        needed[alias]=bodies[alias]
        pending.extend(i for i in re.findall(r'\b[a-z_]\w*\b',bodies[alias]) if i in bodies and i not in needed)
    return ''.join('type '+a+' = '+b+'\n' for a,b in sorted(needed.items()))

def rerun(id, output, source=None):
    output.mkdir(parents=True,exist_ok=True)
    checkout=output/'roundhouse'
    if not checkout.exists():
        subprocess.run(['git','clone','--no-checkout',str(source or FORK),str(checkout)],check=True,
                       stdout=subprocess.DEVNULL)
    helper=output/'exporter'
    helper.mkdir(exist_ok=True)
    (helper/'sound_types.rs').write_text((LAB/'patches/inference-exporter/sound_types.rs').read_text())
    manifest='''[package]
name = "inference_exporter"
version = "0.0.0"
edition = "2024"
[[bin]]
name = "sound-types"
path = "sound_types.rs"
[dependencies]
roundhouse = { path = SOURCE }
serde_json = "1"
'''.replace('SOURCE',json.dumps(str(checkout)))
    (helper/'Cargo.toml').write_text(manifest)
    target=Path(os.environ.get('CARGO_TARGET_DIR',str(output/'target'))).resolve()
    built=None
    results=[]
    for row in conditions(id):
        if built != row['commit']:
            subprocess.run(['git','-C',str(checkout),'checkout','--detach',row['commit']],check=True,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            # Match the frozen source's dependency versions; the helper adds only its package record.
            (helper/'Cargo.lock').write_text((checkout/'Cargo.lock').read_text())
            env=dict(os.environ,CARGO_BUILD_JOBS='4',CARGO_TARGET_DIR=str(target))
            subprocess.run(['cargo','build','--manifest-path',str(helper/'Cargo.toml')],check=True,
                           cwd=checkout,env=env,stdout=subprocess.DEVNULL)
            built=row['commit']
        d=output/row['directory'];d.mkdir(parents=True,exist_ok=True)
        frozen=LAB/'receipts'/id/row['directory']
        for name in ['selection.json','slots.json']:(d/name).write_text((frozen/name).read_text())
        env={k:v for k,v in os.environ.items() if not k.startswith(('RH_','ROUNDHOUSE_','SOUND_'))}
        env.update(row['flags']);env.update(SOUND_MISSING='1',RH_FOLD_PRINT='1',NO_COLOR='1')
        p=subprocess.run([str(target/'debug/sound-types'),str(app_path(id,row)),str(d/'selection.json')],
                         cwd=checkout,env=env,capture_output=True,text=True)
        if p.returncode: raise RuntimeError(p.stderr)
        raw=json.loads(p.stdout);dump(d/'raw.json',raw)
        final={a:('untyped' if t=='__missing__' else t.replace('__var__','untyped').replace('__bot__',BOT))
               for a,t in raw.items()}
        (d/'final.rbs').write_text(''.join('type '+a+' = '+t+'\n' for a,t in sorted(final.items())))
        (d/'graph.rbs').write_text(reduced_grammar(p.stderr,final,read(d/'selection.json')))
        for r in assess(d,trace_path(id,row)):
            r.update(arm=row['arm'],program=row.get('program'),commit=row['commit']);results.append(r)
    dump(output/'results.json',results)
    # New runs retain their own numbers; use the historical reduction as a separate comparator.
    old=recompute(id)
    keys=['arm','program','stage','records','rejected','rejected_slots','unresolved','missing']
    same=[[r[k] for k in keys] for r in results]==[[r[k] for k in keys] for r in old]
    dump(output/'comparison.json',dict(same_historical_counts=same))
    assert same, 'new run differs from historical counts; inspect results.json'
    return [dict(same_historical_counts=same,conditions=len(conditions(id)))]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['recompute','record','rerun'])
    p.add_argument('id',choices=['F19','F20'])
    p.add_argument('--output',type=Path,default=LAB/'_work/inference')
    p.add_argument('--source',type=Path)
    a=p.parse_args();output=a.output.resolve()
    if a.action=='recompute':rows=recompute(a.id)
    elif a.action=='record':rows=record(a.id,output)
    else:rows=rerun(a.id,output,a.source.resolve() if a.source else None)
    print(json.dumps(rows,indent=2,sort_keys=True))

if __name__=='__main__':main()
