#!/usr/bin/env python3
"""Collect expression-level cause evidence without treating a reference as missing evidence.

Stage attribution is a controlled sensitivity test, not proof that every lost
expression was sound on main. Explicit unresolved evidence remains explicit.
"""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import re
P=Path(__file__).resolve().parent
APPS=('campfire','mastodon','chatwoot','forem','discourse')
RANK={'full':2,'var':1,'untyped':0}

def primary(r):return r['file'],r['start'],r['end'],r['kind']
def identity(r):return primary(r)+(json.dumps(r['owner'],sort_keys=True),r['symbol'],r['root'],r['seq'])
def read_subset(path,wanted):
    out={};buckets=defaultdict(list)
    if not path.exists() or not (path.parent/'counts.json').exists():return out
    pkeys={k[:4] for k in wanted}
    for line in path.open():
        row=json.loads(line)
        if primary(row) in pkeys:buckets[primary(row)].append(row)
    for k in wanted:
        candidates=buckets.get(k[:4],[])
        exact=[r for r in candidates if identity(r)==k]
        if len(exact)==1:out[k]=exact[0];continue
        same=[r for r in candidates if identity(r)[4:6]==k[4:6]]
        if len(same)>1:same=[r for r in same if r['root']==k[6]]
        # Never use the type as a discriminator or guess among duplicate producers.
        if len(same)==1:out[k]=same[0]
    return out

def refs(t):
    if not isinstance(t,dict):return []
    out=[t['slot']] if t.get('kind')=='rec' else []
    for k,v in t.items():
        if isinstance(v,dict):out+=refs(v)
        elif isinstance(v,list):
            for x in v:out+=refs(x)
    return out

def graph_walk(starts,slots):
    """Record raw leaves and guarded/unguarded back edges separately."""
    leaves=Counter();origins={};edges=set();missing=set();seen=set();witnesses=[]
    nodes=0
    def go(slot,path,ctor):
        active=[x[0] for x in path]
        if slot in active:
            i=active.index(slot)
            edges.add((tuple(active[i:]+[slot]),ctor!=path[i][1]));return
        if slot in seen:return
        seen.add(slot)
        row=slots.get(slot)
        if row is None or row['type'] is None:missing.add(slot);return
        origins[slot]=row['origin']
        visit(row['type'],path+[(slot,ctor)],ctor)
    def visit(t,path,ctor):
        nonlocal nodes
        if not isinstance(t,dict):return
        kind=t.get('kind')
        if kind:nodes+=1
        if kind=='rec':go(t['slot'],path,ctor);return
        if kind in ('untyped','var','bottom'):
            leaves[kind]+=1
            witnesses.append(dict(kind=kind,slot_path=[x[0] for x in path],
                                  origins=[origins[x[0]] for x in path if x[0] in origins]))
        depth=ctor+int(bool(kind) and kind!='union')
        for v in t.values():
            if isinstance(v,dict):visit(v,path,depth)
            elif isinstance(v,list):
                for x in v:visit(x,path,depth)
    for slot in starts:go(slot,[],0)
    return dict(slots=len(seen),raw_nodes=nodes,leaf_counts=dict(leaves),origins=origins,
                back_edges=[dict(slots=list(path),guarded=guarded) for path,guarded in sorted(edges)],
                missing=sorted(missing),leaf_witnesses=witnesses)

def sensitivity(main,s3,control):
    if control is None:return None
    return dict(type=control['type'],category=control['category'],
                recovers=RANK[control['category']]>RANK[s3['category']],
                reaches_main_category=RANK[control['category']]>=RANK[main['category']])

def source(app,row):
    if row['file']=='<synthetic>':return None
    f=P.parents[1]/'corpus/apps'/app/row['file']
    if not f.is_file():return None
    b=f.read_bytes();start=row['start'];end=row['end']
    return dict(file=row['file'],line=b[:start].count(b'\n')+1,
                expression=b[start:end].decode('utf-8',errors='replace'))

def origin(row,flow,graph):
    k=row['kind'];name=row['symbol'];owner=row.get('owner') or {}
    if k=='Ivar':return 'ivar'
    if k=='Const':return 'constant'
    if k=='Lambda':return 'block value'
    if k=='Var':
        if name in owner.get('params',[]):return 'parameter row'
        if flow and flow.get('binding'):
            rr=refs(flow['binding'])
            oo=[graph.get('origins',{}).get(x,{}) for x in rr]
            if any(x.get('kind')=='parameter' for x in oo):return 'parameter row via local'
            if any(x.get('kind')=='return' for x in oo):return 'method return via local'
        return 'local binding; upstream trace required'
    if k in ('Send','MethodRef'):return 'method return'
    if k in ('If','Case','Match','Rescue','Seq','Return','Next','Break'):
        return 'block/branch value'
    if k in ('Assign','Let','MultiAssign','OpAssign'):return 'assigned value'
    if k in ('Array','Hash','Tuple','Lit'):return 'container/literal value'
    return 'expression children'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline',default='paired-v2')
    ap.add_argument('--controls',default='controls-v1')
    ap.add_argument('--other-controls',default='controls-v2')
    ap.add_argument('--flow',default='flow-v1')
    a=ap.parse_args();d=P/'results'/a.baseline;c=P/'results'/a.controls;f=P/'results'/a.flow
    c2=P/'results'/a.other_controls
    changes=[json.loads(s) for s in (d/'main-S3-changes.jsonl').open()]
    losses=[x for x in changes if x['direction']=='loss']
    result=[];totals=Counter();stage_counts=Counter();origin_counts=Counter()
    for app in APPS:
        selected=[x for x in losses if x['app']==app]
        wanted={identity(x['right']) for x in selected}
        ctrls={arm:read_subset(c/app/arm/'rows.jsonl',wanted) for arm in
               ('S2b','S2c','allarms-only','join-only','S3-no-allarms','S3-no-join','S3-no-slots','S3-no-tail')}
        for arm,matched in ctrls.items():
            if not matched:matched.update(read_subset(c2/app/arm/'rows.jsonl',wanted))
        phases={ph:read_subset(d/app/'S3'/('rows.jsonl.'+ph+'.jsonl'),wanted)
                for ph in ('pre-expand','post-expand','post-settle')}
        fp=d/app/'S3'/'rows.jsonl.fold-slots.json'
        slots={x['slot']:x for x in json.loads(fp.read_text())} if fp.exists() else {}
        flows=defaultdict(list);fp=f/app/'S3'/'flow.jsonl'
        if fp.exists() and (fp.parent/'counts.json').exists():
            for line in fp.open():
                v=json.loads(line);flows[tuple(v['span'])].append(v)
        for x in selected:
            y=x['right'];k=identity(y)
            control={arm:sensitivity(x['left'],y,rows.get(k)) for arm,rows in ctrls.items()}
            phase={ph:rows.get(k) for ph,rows in phases.items()}
            pre=phase.get('pre-expand');starts=[int(i) for i in re.findall(r'Rec\[(\d+)\]',pre['type'] if pre else '')]
            graph=graph_walk(starts,slots)
            flowlist=flows.get((y['file_id'],y['start'],y['end']),[])
            own=y.get('owner') or {}
            flow=next((z for z in flowlist if z['symbol']==y['symbol'] and
                       (not own.get('class') or own['class'] in json.dumps(z.get('self_type')))),
                      flowlist[0] if len(flowlist)==1 else None)
            def recovered(arm):return bool(control.get(arm) and control[arm]['recovers'])
            if recovered('S2c'):stage='S3 worklist/order sensitivity'
            elif recovered('S3-no-allarms'):stage='S2b all-arms sensitivity'
            elif recovered('S3-no-join'):stage='S2b join sensitivity'
            elif recovered('S3-no-slots'):stage='S2c slot-cycle sensitivity'
            elif recovered('S3-no-tail'):stage='S2c tail elimination sensitivity'
            elif recovered('S2b'):stage='S2c reference/slot sensitivity'
            elif recovered('join-only') and not recovered('allarms-only'):stage='S2b all-arms or interaction'
            elif recovered('allarms-only') and not recovered('join-only'):stage='S2b join or interaction'
            elif any(z is None for z in control.values()):stage='control data incomplete'
            else:stage='persistent staged loss; trace required'
            root_bottom=bool(pre and len(starts)==1 and pre['type']=='Rec[%d]'%starts[0]
                             and (slots.get(starts[0],{}).get('type') or {}).get('kind')=='bottom')
            graph['root_explicit_bottom']=root_bottom
            if pre and pre['category']=='untyped':
                mechanism='untyped already present before expansion'
            elif pre and starts and y['category']=='untyped':
                if root_bottom:mechanism='reference expansion prints a known Bottom as untyped'
                elif graph['leaf_counts'].get('untyped'):mechanism='reference expansion carries explicit untyped'
                elif graph['missing']:mechanism='reference expansion missing slot'
                elif any(z['guarded'] for z in graph['back_edges']):mechanism='reference expansion guarded cycle cut'
                elif graph['back_edges']:mechanism='reference expansion unproductive tail cycle'
                else:mechanism='acyclic expansion; exact cut not established'
            elif pre and starts and y['category']=='var' and graph['leaf_counts'].get('var'):
                mechanism='reference expansion carries explicit Var'
            elif pre and pre['category']=='var' and y['category']=='var':
                mechanism='Var already present before expansion'
            else:mechanism='analysis/type propagation; trace required'
            direct_origin=origin(y,flow,graph)
            r=dict(x,stage=stage,mechanism=mechanism,origin=direct_origin,controls=control,
                   phases=phase,graph=graph,flow=flow,flow_candidates=len(flowlist),source=source(app,y))
            result.append(r);stage_counts[stage]+=1;totals[mechanism]+=1;origin_counts[direct_origin]+=1
        print(app,len(selected),'loss evidence records',flush=True)
    with (d/'loss-evidence.jsonl').open('w') as w:
        for r in result:w.write(json.dumps(r,sort_keys=True)+'\n')
    out=dict(losses=len(losses),classified_records=len(result),stage=dict(stage_counts),
             mechanism=dict(totals),direct_origin=dict(origin_counts))
    (d/'loss-evidence-summary.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out),flush=True)
if __name__=='__main__':main()
