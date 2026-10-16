"""Frozen identity-complete return partition, order-A descents, and current-writer replay."""
from collections import Counter
import json
import order_a as O
import return_algebra as A
import verdict_returns as V
from evidence import require, canon, digest

def any_kind(t,kind):
 if isinstance(t,list):return any(any_kind(x,kind) for x in t)
 return isinstance(t,dict) and (t.get('kind')==kind or any(any_kind(x,kind) for x in t.values()))
def informative(t):
 return any(x.get('kind') not in ('var','untyped','nil','bottom') for x in O.arms(t))
def family(a,b):
 if O.leq(a,b,'A'):
  return 'late_unresolved' if informative(a) and not informative(b) and O.is_untyped(b) else None
 if not informative(a) and not informative(b) and any_kind(a,'var') != any_kind(b,'var'):return 'placeholder_flip'
 if not informative(a) and informative(b) and any(O.is_untyped(x) for x in O.arms(a)):return 'premature_unresolved'
 if a.get('kind')=='array' and b.get('kind')=='tuple':return 'shape_refinement'
 if any_kind(a,'rec') or any_kind(b,'rec'):return 'reference_switch'
 if a.get('kind')==b.get('kind') and a.get('kind') in ('array','hash','class','tuple','record','union'):return 'arm_loss'
 return 'other'

def replay(data):
 es=data['events'];resolve=data['resolve'];decls={};writers={};versions={};routes={};snap=None
 conversions=[];desc=Counter({k:0 for k in V.FAMILIES});examples=[];removed=0
 for i,e in enumerate(es):
  ev=e['event']
  require(snap is None,'event after snapshot')
  if ev=='inventory':
   require(i==0,'inventory order');decls={d['id']:d for d in e['declarations']}
   require(len(decls)==len(e['declarations']),'duplicate declaration')
  elif ev=='declare-external':
   d=e['declaration'];require(d['id'] not in decls,'duplicate external writer');decls[d['id']]=d
  elif ev=='replace':
   w=e['writer'];require(w in decls,'undeclared writer')
   require(e['version']==versions.get(w,0)+1 and e['superseded']==writers.get(w),'replacement identity/version mismatch')
   cur=A.annotated(e['current']);old=e['superseded']
   if old is not None:
    k=family(resolve(A.annotated(old)),resolve(cur))
    if k:
     desc[k]+=1;examples.append({'writer':w,'family':k,'version':e['version'],'superseded':resolve(A.annotated(old)),'current':resolve(cur)})
   writers[w]=e['current'];versions[w]=e['version']
  elif ev=='route':
   key=(e['destination'],e['kind']);require(routes.get(key)==e['superseded_source'],'route predecessor mismatch');routes[key]=e['source']
  elif ev=='remove-route':
   key=(e['destination'],e['kind']);require(routes.pop(key)==e['source'],'removed source identity');removed+=1
  elif ev=='permitted-var-to-u':
   require(e['writer'] in decls or e['writer'].startswith('copy:'),'conversion source unavailable')
   a=A.annotated(e['input']);b=A.annotated(e['output']);require(any_kind(a,'var') and b['kind']=='untyped' and 'Unresolved' in b['reasons'],'invalid Var conversion')
   conversions.append(e)
  elif ev=='harvest-input':pass
  elif ev=='snapshot':snap=e
  else:raise ValueError('unknown ledger event '+ev)
 require(snap is not None and snap['phase']=='before-fold-finish','snapshot phase missing')
 require({d['id']:d for d in snap['declarations']}==decls,'declaration coverage mismatch')
 require({w['writer']:w['current'] for w in snap['writers']}==writers,'current writer replay mismatch')
 require({w['writer']:w['version'] for w in snap['writers']}==versions,'version replay mismatch')
 require({(e['destination'],e['kind']):e['source'] for e in snap['routes']}==routes,'route replay mismatch')
 require(not snap['unscoped_publications'] and not snap['missing_action_results'],'unscoped/missing publication')
 require(not snap['unobserved_declared_writers'] and set(decls)<=set(writers),'declared writer has no publication')
 own={};sources={}
 for w,d in decls.items():own.setdefault(d['slot'],set()).add(w)
 for (dest,_),src in routes.items():sources.setdefault(dest,set()).add(src)
 def members(slot,seen=None):
  seen=set() if seen is None else seen
  if slot in seen:return set()
  seen.add(slot);out=set(own.get(slot,()))
  for src in sources.get(slot,()):out.update(members(src,seen))
  return out
 rows={r['slot']:r for r in snap['slots']};require(len(rows)==len(snap['slots']),'duplicate slot')
 require(set(rows)==set(own)|set(sources),'slot inventory mismatch')
 mismatches=[];losses=[];pending=0
 for slot,row in rows.items():
  ms=members(slot);require(set(row['members'])==ms,'contributor inventory mismatch '+slot)
  agg={'kind':'untyped','reasons':['Pending']}
  for w in sorted(ms):agg=A.join(agg,A.annotated(writers[w]))
  native=A.annotated(row['aggregate'])
  require(A.normal_key(native)==A.normal_key(agg),'independent aggregate replay mismatch '+slot)
  stored=A.annotated(row['stored']) if row['stored'] is not None else None
  if row['authored_signature']:
   sig=A.annotated(row['signature']);bad=stored is None or A.normal_key(stored)!=A.normal_key(sig)
  else:bad=stored is None or A.normal_key(stored)!=A.normal_key(native)
  if bad:mismatches.append(slot)
  if all(A.pending(A.annotated(writers[w])) for w in ms):pending+=1
  # Current-origin obligations compare contributor to aggregate, never superseded history.
  for w in ms:
   for atom in sorted(A.atoms(writers[w])-A.atoms(row['aggregate'])):
    losses.append({'slot':slot,'writer':w,'origin':atom})
 return {'available':True,'resolved':True,'aggregate_mismatches':len(mismatches),
 'signature_exempt_slots':sum(bool(r['authored_signature']) for r in rows.values()),
 'route_removals':removed,'orphan_destinations':sum(not members(slot) for slot in sources),
 'pending_only_destinations':pending,'route_set_digest':digest(sorted([d,k,s] for (d,k),s in routes.items())),
 'descents':dict(desc)}, {'snapshot':snap,'declarations':decls,'writers':writers,'members':members,'rows':rows,
 'origin_losses':losses,'conversions':conversions,'functional_violations':mismatches,'descent_examples':examples}

def varying(data):
 maps={s:{k:r for (p,k),r in data[s]['rows'].items() if p=='returns'} for s in V.SCHEDULES}
 keys=set().union(*(set(x) for x in maps.values()))
 # Stored row equality uses native storage hashes; resolution is the contributor proxy.
 var={k for k in keys if len({canon(maps[s].get(k,{}).get('hash')) for s in V.SCHEDULES})>1}
 return var,maps

def partition(data,states):
 var,maps=varying(data);out={'varying_rows':sorted(var),'machinery_rows':[],'upstream_rows':[],'unclassified_rows':[]};proof={}
 for slot in sorted(var):
  sets={s:set(states[s]['members'](slot)) for s in V.SCHEDULES}
  contributors=set().union(*sets.values());missing=not contributors or len({canon(sorted(x)) for x in sets.values()})!=1
  varies=False;detail={}
  for w in sorted(contributors):
   values={}
   for s in V.SCHEDULES:
    d=states[s]['declarations'].get(w)
    if d is None:missing=True;continue
    if d['source_kind']=='declared-body':
     rs=[]
     for (part,k),r in data[s]['rows'].items():
      if part!='ir':continue
      root=json.loads(r['root'].rsplit(':occurrence:',1)[0]);span=root['span']
      if root.get('declaration')==d['slot'] and span['start']==d['start'] and span['end']==d['end'] and root.get('source')==d['source']:
       rs.append([r['node'],r['path'],digest(r['resolved_ty'])])
     if not rs:missing=True;continue
     values[s]=sorted(rs,key=canon)
    else:
     publication=states[s]['writers'].get(w)
     if publication is None:missing=True;continue
     values[s]=data[s]['resolve'](publication['native_ty'])
   if len(values)!=4:missing=True
   if len({canon(v) for v in values.values()})>1:varies=True
   detail[w]={s:digest(v) for s,v in values.items()}
  cat='unclassified_rows' if missing else 'upstream_rows' if varies else 'machinery_rows'
  out[cat].append(slot);proof[slot]={'category':cat,'contributors':detail}
 return out,proof
