#!/usr/bin/env python3
"""Independent replay of research condition native current-writer events. Read only; no analyzer calls."""
import argparse,copy,hashlib,json
from pathlib import Path

def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def require(ok,message):
    if not ok:raise ValueError(message)

def annotated(d):
    """Check exact per-node native reasons against the independent origin census."""
    origins=set(d['origins']);used=set()
    require(isinstance(d['hash'],int) and isinstance(d['debug'],str),'type descriptor schema')
    native=copy.deepcopy(d['native_ty'])
    def go(t,path):
        require(isinstance(t,dict) and isinstance(t.get('kind'),str),'native type schema')
        kind=t['kind']
        if kind=='untyped':
            rs=set(t['reasons']);require(bool(rs) and rs<={'Pending','Gradual','Unresolved'},'per-node reasons unavailable')
            used.update(path+':'+r for r in rs);t['reasons']=sorted(rs)
        elif kind=='var':used.add(path+':LegacyAmbiguousVar')
        elif kind=='rec':used.add(path+':ReferenceRequiresDependencyAudit')
        elif kind=='array':go(t['elem'],path+'/element')
        elif kind=='hash':
            for k in ('key','value'):go(t[k],path+'/'+k)
        elif kind in ('tuple','class'):
            for i,v in enumerate(t['elems' if kind=='tuple' else 'args']):go(v,path+'/'+str(i))
        elif kind=='union':
            for v in t['variants']:go(v,path+'/arm')
        elif kind=='record':
            for k,v in t['row']['fields'].items():go(v,path+'/'+k)
        elif kind=='fn':
            for i,p in enumerate(t['params']):go(p['ty'],path+'/param/'+str(i))
            if t['block'] is not None:go(t['block'],path+'/block')
            go(t['ret'],path+'/return')
    go(native,'$');require(used==origins,'native origin paths do not cover the serialized value')
    require(semantic(native)==d['ty'],'reason-bearing native type disagrees with ordinary serialization')
    return native

def semantic(t):
    if isinstance(t,list):return [semantic(v) for v in t]
    if not isinstance(t,dict):return t
    return {k:semantic(v) for k,v in t.items() if k!='reasons'}
def merge_equal(a,b):
    if isinstance(a,list):return [merge_equal(x,y) for x,y in zip(a,b)]
    if not isinstance(a,dict):return a
    if a.get('kind')=='untyped':return dict(a,reasons=sorted(set(a['reasons'])|set(b['reasons'])))
    return {k:merge_equal(v,b[k]) for k,v in a.items()}
def pending(t):return t.get('kind')=='untyped' and t['reasons']==['Pending']
def normalize(t):
    if isinstance(t,list):return [normalize(v) for v in t]
    if not isinstance(t,dict):return t
    if t.get('kind')=='untyped':
        rs=set(t['reasons'])
        if rs-{'Pending'}:rs.discard('Pending')
        return dict(t,reasons=sorted(rs))
    if t.get('kind')=='union':
        vals=[normalize(v) for v in t['variants']]
        if not vals:return {'kind':'bottom'}
        out=vals[0]
        for v in vals[1:]:out=join(out,v)
        return out
    return {k:normalize(v) for k,v in t.items()}
def join(a,b):
    if pending(a):return normalize(b)
    if pending(b):return normalize(a)
    a,b=normalize(a),normalize(b);values=[]
    def push(t):
        if t['kind']=='union':
            for v in t['variants']:push(v)
        else:values.append(t)
    push(a);push(b)
    live=[v for v in values if v['kind']!='bottom' and not pending(v)]
    if not live:
        return {'kind':'bottom'} if any(v['kind']=='bottom' for v in values) else {'kind':'untyped','reasons':['Pending']}
    out=[]
    for v in live:
        if v['kind'] in ('array','hash'):
            old=next((x for x in out if x['kind']==v['kind']),None)
            if old is None:out.append(copy.deepcopy(v))
            elif v['kind']=='array':old['elem']=join(old['elem'],v['elem'])
            else:
                for k in ('key','value'):old[k]=join(old[k],v[k])
        else:
            old=next((i for i,x in enumerate(out) if semantic(x)==semantic(v)),None)
            if old is None:out.append(copy.deepcopy(v))
            else:out[old]=merge_equal(out[old],v)
    out.sort(key=canon)
    return out[0] if len(out)==1 else {'kind':'union','variants':out}
def normal_key(t):
    t=normalize(t)
    def order(v):
        if isinstance(v,list):return [order(x) for x in v]
        if not isinstance(v,dict):return v
        out={k:order(x) for k,x in v.items()}
        if out.get('kind')=='union':out['variants'].sort(key=canon)
        return out
    return canon(order(t))
def atoms(d):
    out={p.replace('/arm','') for p in d['origins'] if not p.endswith(':Pending') and not p.endswith(':ReferenceRequiresDependencyAudit')}
    def refs(t,path):
        if isinstance(t,list):
            for v in t:refs(v,path)
        elif isinstance(t,dict):
            k=t.get('kind')
            if k=='rec':out.add(path+':Reference['+str(t['slot'])+']')
            elif k=='array':refs(t['elem'],path+'/element')
            elif k=='hash':
                for x in ('key','value'):refs(t[x],path+'/'+x)
            elif k in ('tuple','class'):
                for i,v in enumerate(t['elems' if k=='tuple' else 'args']):refs(v,path+'/'+str(i))
            elif k=='union':
                for v in t['variants']:refs(v,path)
            elif k=='record':
                for key,v in t['row']['fields'].items():refs(v,path+'/'+key)
            elif k=='fn':
                for i,p in enumerate(t['params']):refs(p['ty'],path+'/param/'+str(i))
                if t['block'] is not None:refs(t['block'],path+'/block')
                refs(t['ret'],path+'/return')
    refs(d['ty'],'$');return out

def replay(path,expected=None):
    path=Path(path);path=path/'current-return-ledger.jsonl' if path.is_dir() else path
    declarations={};writers={};versions={};routes={};destinations=set();snapshot=None;header=None
    retired_atoms=retired_pending=changes=0;failures=[]
    with path.open() as stream:
        for n,line in enumerate(stream,1):
            e=json.loads(line);kind=e['event'];require(snapshot is None,'events after final snapshot')
            if kind=='inventory':
                require(n==1 and e['schema']==1,'inventory schema/order');header=e
                require(expected is None or e['candidate']==expected,'audit arm identity')
                for d in e['declarations']:
                    require(d['id'] not in declarations,'duplicate declared identity');declarations[d['id']]=d
            else:
                require(header is not None,'missing inventory')
                if kind=='declare-external':
                    d=e['declaration'];require(d['id'] not in declarations,'duplicate external identity');declarations[d['id']]=d
                elif kind=='replace':
                    key=e['writer'];require(key in declarations,'unscoped replacement')
                    require(e['version']==versions.get(key,0)+1,'writer version gap')
                    require(e['superseded']==writers.get(key),'superseded entry belongs to another writer/version')
                    if key in writers:
                        retired_atoms+=len(atoms(writers[key])-atoms(e['current']))
                        retired_pending+=sum(p.endswith(':Pending') for p in writers[key]['origins'])
                    annotated(e['current']);writers[key]=e['current'];versions[key]=e['version'];changes+=1
                elif kind=='route':
                    key=(e['destination'],e['kind']);require(routes.get(key)==e['superseded_source'],'copy route version mismatch')
                    routes[key]=e['source'];destinations.add(e['destination'])
                elif kind=='remove-route':
                    key=(e['destination'],e['kind']);require(routes.get(key)==e['source'],'removing unavailable route');del routes[key]
                elif kind=='snapshot':snapshot=e
                else:raise ValueError('unsupported audit event '+kind)
    require(snapshot is not None and snapshot['schema']==1 and snapshot['phase']=='before-fold-finish','final audit snapshot unavailable')
    require(snapshot['candidate']==header['candidate'],'snapshot arm identity')
    require({d['id']:d for d in snapshot['declarations']}==declarations,'declaration coverage drift')
    require({d['writer']:d['current'] for d in snapshot['writers']}==writers,'current writer replay mismatch')
    require({d['writer']:d['version'] for d in snapshot['writers']}==versions,'current writer version mismatch')
    require({(e['destination'],e['kind']):e['source'] for e in snapshot['routes']}==routes,'copy route replay mismatch')
    require(not snapshot['unscoped_publications'] and not snapshot['missing_action_results'],'unscoped or unavailable native publication')
    unobserved=set(declarations)-set(writers)
    require(set(snapshot['unobserved_declared_writers'])==unobserved,'unobserved-writer census mismatch')
    require(not unobserved,'unobserved declared writers: '+str(sorted(unobserved)[:5]))
    require(snapshot['publications']>=changes and snapshot['replacements']==sum(v-1 for v in versions.values()),'publication counters do not reconcile')
    own={}
    for key,d in declarations.items():own.setdefault(d['slot'],set()).add(key)
    sources={}
    for (dest,_),src in routes.items():sources.setdefault(dest,set()).add(src)
    def members(slot,seen=None):
        seen=set() if seen is None else seen
        if slot in seen:return set()
        seen.add(slot);out=set(own.get(slot,()))
        for src in sources.get(slot,()):out.update(members(src,seen))
        return out
    rows={r['slot']:r for r in snapshot['slots']};require(len(rows)==len(snapshot['slots']),'duplicate aggregate slots')
    require(set(rows)==set(own)|destinations,'aggregate slot coverage mismatch')
    current_losses=[];mismatch=[];live_atoms=0
    for slot,row in rows.items():
        keys=members(slot);require(set(row['members'])==keys,'incomplete writer/context coverage for '+slot)
        agg=annotated(row['aggregate']);require('stored' in row,'stored observation unavailable '+slot)
        require(row['stored'] is not None or not header['candidate'],'stored aggregate unavailable '+slot)
        stored=annotated(row['stored']) if row['stored'] is not None else None
        expected_type={'kind':'untyped','reasons':['Pending']}
        for key in sorted(keys):expected_type=join(expected_type,annotated(writers[key]))
        if normal_key(agg)!=normal_key(expected_type):mismatch.append([slot,'independent aggregate replay differs'])
        signature=row['authored_signature'];require(not signature or (stored is not None and stored['kind']=='fn'),'signature exemption schema')
        if signature:continue
        if header['candidate'] and (not row['aggregate_matches_stored'] or normal_key(agg)!=normal_key(stored)):
            mismatch.append([slot,'stored value differs from current aggregate'])
        for key in keys:
            live=atoms(writers[key]);live_atoms+=len(live)
            for atom in sorted(live-atoms(row['aggregate'])):current_losses.append({'slot':slot,'writer':key,'origin':atom})
    failures.extend(mismatch)
    if header['candidate']:failures.extend(current_losses)
    return {'status':'KILLED' if failures else 'LEDGER_PASS','candidate':header['candidate'],'declarations':len(declarations),
        'body_writers':sum(d['source_kind']=='declared-body' for d in declarations.values()),'observed_writers':len(writers),
        'slots':len(rows),'signature_exemptions':sum(r['authored_signature'] for r in rows.values()),'routes':len(routes),'changed_publications':changes,'retired_history_atoms':retired_atoms,
        'retired_pending_occurrences':retired_pending,'live_atom_checks':live_atoms,'current_losses':len(current_losses),
        'failures':failures[:40],'failure_count':len(failures),'path':str(path),
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},declarations,routes

def safe(path,expected=None):
    try:return replay(path,expected)
    except (OSError,ValueError,KeyError,TypeError,AssertionError,RecursionError) as e:
        return {'status':'INCONCLUSIVE','unavailable':str(e),'path':str(path)},None,None

def main():
    p=argparse.ArgumentParser();p.add_argument('--control',type=Path);p.add_argument('--candidate',type=Path);p.add_argument('--single',type=Path);a=p.parse_args()
    results={};states={};failures=[]
    for arm,path,expected in [('control',a.control,False),('candidate',a.candidate,True),('single',a.single,None)]:
        if path is not None:results[arm],d,r=safe(path,expected);states[arm]=(d,r)
    if 'control' in states and 'candidate' in states and all(x[0] is not None for x in states.values()):
        if states['control'][0]!=states['candidate'][0]:failures.append('declared writer/context identities changed between arms')
        if states['control'][1]!=states['candidate'][1]:failures.append('copy routing changed between arms')
    status='INCONCLUSIVE' if not results or any(r['status']=='INCONCLUSIVE' for r in results.values()) else 'KILLED' if failures or any(r['status']=='KILLED' for r in results.values()) else 'LEDGER_PASS'
    print(json.dumps({'condition':'current-return-ledger-replay-20261015','status':status,'arms':results,'failures':failures},indent=2))
    return 2 if status=='INCONCLUSIVE' else 1 if status=='KILLED' else 0
if __name__=='__main__':raise SystemExit(main())
