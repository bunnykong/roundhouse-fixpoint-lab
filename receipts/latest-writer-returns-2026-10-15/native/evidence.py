"""Frozen research condition raw receipt adapter. Missing native fields are errors, never zero."""
import hashlib, importlib.util, json, re
from pathlib import Path
D=Path(__file__).resolve().parent
F=D.parents[1]
spec=importlib.util.spec_from_file_location('current_return_obs',D.parents[2]/'tools/observers/obs.py')
obs=importlib.util.module_from_spec(spec);spec.loader.exec_module(obs)
import verdict_returns as V
import return_algebra as A

def read(p): return json.loads(Path(p).read_text())
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def digest(x): return hashlib.sha256(canon(x).encode()).hexdigest()
def sha(p): return obs.sha(Path(p))
def save(p,x): obs.save(p,x)
def require(ok,why):
 if not ok: raise ValueError(why)
def events(p):
 with Path(p).open() as f: return [json.loads(l) for l in f]

def raw_cell(cache,label,app,setting):
 cache=Path(cache);entry=read(cache/'labels'/label/'label.json')['cells'][app+'/'+setting]
 r=obs.checked_result(Path(entry['result']));p=Path(r['directory'])
 require(entry['cache_key']==r['cache_key']==obs.digest(r['key']),'cache key mismatch')
 require(entry.get('fresh_match') is not False,'cache repeat mismatch')
 require(not (p/'inconsistent.json').exists() and not p.parents[1].joinpath('inconsistent.json').exists(),'inconsistent cache')
 manifest=read(cache/'inputs'/(r['key']['input_manifest_sha256']+'.json'))
 require(obs.digest(manifest)==r['key']['input_manifest_sha256'],'input manifest hash mismatch')
 return r,p

def resolver(rows):
 refs={}
 for (part,key),v in rows.items():
  if part=='returns':refs['return:'+key]=v.get('native_ty',v.get('ty'))
  elif part=='side_table':refs[key]=v.get('native_ty',v.get('ty'))
 def resolve(t,seen=frozenset()):
  if isinstance(t,list):return [resolve(x,seen) for x in t]
  if not isinstance(t,dict):return t
  if t.get('kind')=='rec':
   key=t['slot'];lookup=key
   m=re.fullmatch(r'Some\(Ret \{ class: ClassId\(Symbol\(("(?:\\.|[^"])*")\)\), method: Symbol\(("(?:\\.|[^"])*")\), class_side: (true|false) \}\)',str(key))
   if m:
    c,n,side=m.groups();lookup='return:'+json.loads(c)+('.' if side=='true' else '#')+json.loads(n)
   # Exactly the research condition row rule: unresolved missing/cyclic references remain explicit.
   if key in seen or lookup not in refs:return t
   return resolve(refs[lookup],seen|{key})
  return {k:resolve(v,seen) for k,v in t.items()}
 return resolve

def row_data(p):
 es=events(Path(p)/'contributor-values.jsonl');fp=es[0];rows={}
 for e in es[1:]:
  key=(e['part'],e['key']);require(key not in rows,'duplicate research condition identity');rows[key]=e
 resolve=resolver(rows)
 for row in rows.values():row['resolved_ty']=resolve(row.get('native_ty',row.get('ty')))
 # These are the expanded tables used for H4, not a fabricated full row inventory.
 for part in ('returns','side_table'):
  require({k:v['hash'] for (q,k),v in rows.items() if q==part}==fp['parts'].get(part,{}),part+' coverage')
 ir=sorted([r['span']['file'],r['span']['start'],r['span']['end'],r['hash'],r['note']] for (q,k),r in rows.items() if q=='ir')
 require(ir==fp['ir'],'IR multiset incomplete')
 return fp,rows,resolve

def load(cache,label,app,setting,arm):
 r,p=raw_cell(cache,label,app,setting)
 require(r['valid'] is True and not r['metrics']['timed_out'],'invalid native cell')
 require(r['app']==app and r['setting']==obs.setting(setting),'app/setting mismatch')
 require(r['key']['binary_sha256']==sha(D/'bin/roundhouse'),'binary identity')
 require(r['key']['runtime']['ruby_version'].startswith('ruby 4.0.7 '),'runtime identity')
 profile=read(D/'profile.json');expected=dict(obs.COMMON,**profile,RH_CONTRIBUTOR_VALUES='1',RH_CURRENT_RETURN_REPLACE=str(int(arm=='K')))
 expected.update(RH_FIXPOINT_VERIFY=str(int('-v1-' in setting)),RH_PROVENANCE_AUDIT=str(int(setting.endswith('a1'))))
 if setting.startswith(('1-','2-')):expected['RH_SHUFFLE']=setting[0]
 actual={k:v for k,v in r['key']['rh_flags'].items() if k not in obs.DUMPS}
 require(actual==expected,'effective profile mismatch')
 pins=read(F/'phase2/observers/apps.json');pin=pins.get('apps',pins)[app]
 require(r['input_pin']==pin['commit'] and r['input_tree_sha256']==pin['tree_sha256'],'input pin/tree mismatch')
 fp,rows,resolve=row_data(p)
 o=r['observations'];require(fp['digests']==o['value_digests'],'research condition/native fingerprint mismatch')
 native=read(p/'report.json');reason=obs.observed(r,'reason_rows')
 require(isinstance(reason,dict),'exact reason rows unavailable')
 counts={n:sum(bool(v['untyped_kinds']&(1<<i)) for v in reason.values()) for i,n in enumerate(('pending','gradual','unresolved'))}
 reconcile=len(reason)==o['reason_census']['untyped_anywhere'] and counts==o['reason_census']['untyped_by_provenance']
 require(reconcile,'native reason census mismatch')
 audits=[]
 for line in (p/'stderr.log').read_text().splitlines():
  if line.startswith('rh-provenance-audit: '):audits.append(json.loads(line[12:]))
 errs=[]
 # Source-facing CLI diagnostics have `file:line:col: error[kind]: ...`.
 text=(p/'stderr.log').read_text()
 for m in re.finditer(r'([^\n]+?):(\d+):(\d+):\s*error\[([^\]]+)\]',text):
  errs.append([m[1],int(m[2]),int(m[3]),m[4]])
 ek={k:n for k,n in o['diagnostics'].items() if k.startswith('error/')}
 # Never certify empty identities merely because a parser did not recognize the layout.
 require(len(errs)==sum(ek.values()),'error identity parser did not cover printed errors')
 aliases={k:v['module'] for (q,k),v in rows.items() if q=='aliases'}
 c={'valid':r['valid'],'exit':r['metrics']['exit_code'],'timed_out':r['metrics']['timed_out'],
 'digests':o['value_digests'],'loops':o['loops'],
 'caps':{k:native['worklist']['engine'][k] for k in V.CAPS[:4]},
 'verify':{x['loop']:x['moved'] for x in o['verify']} if '-v1-' in setting else 'disabled',
 'audit':'disabled','reason_rows_digest':digest(reason),'reason_census':o['reason_census'],
 'reason_census_reconciles':reconcile,'errors_by_kind':ek,'error_identities':errs,
 'diagnostics_by_kind':o['diagnostics'],'diagnostic_kinds':sorted(o['diagnostics']),
 'alias_identity_digest':digest(aliases),
 'performance':{'wall_s':r['metrics']['wall_seconds'],'cpu_s':r['metrics']['cpu_seconds'],'peak_rss_bytes':r['metrics']['peak_rss_bytes']}}
 c['caps'].update(cuts=native['bound']['cuts'],budget_cuts=native['fold']['expansion']['budget_cuts'])
 return {'cell':c,'raw':r,'path':p,'fp':fp,'rows':rows,'resolve':resolve,'events':events(p/'current-return-ledger.jsonl'),'audits':audits}

def parameter_losses(audits):
 require(len(audits)==1,'parameter audit unavailable')
 a=audits[0];losses={};paths=0;illegal=0
 for e in a['parameter_native_events']:
  n=e['count'];require(isinstance(n,int) and n>0,'event multiplicity')
  lost=set(e['input_origins'])-set(e['output_origins']);require(lost==set(e['lost_origins']),'parameter origin replay')
  paths+=len(lost)*n
  illegal+=sum(not x.endswith(':Pending') for x in lost)*n
  for kind in e['lost_kinds']:losses[kind]=losses.get(kind,0)+n
 require(paths==a['parameter_output_origin_losses'] and losses==a['parameter_losses_by_kind'],'parameter counters reconcile')
 return illegal
