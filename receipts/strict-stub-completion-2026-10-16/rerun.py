#!/usr/bin/env python3
"""Verify retained files and recompute bounded F70 checks; runs no analyzer."""
import hashlib,json,lzma,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
MANIFEST=json.loads((HERE/'manifest.json').read_text())
def data(name):
 rows=[x for x in MANIFEST['files'] if x['recorded_file']==name];assert len(rows)==1,(name,len(rows))
 row=rows[0];b=(HERE/row['file']).read_bytes()
 return lzma.decompress(b) if row['compression']=='xz' else b
def js(name):return json.loads(data(name))
def saved():
 checked=set()
 for row in MANIFEST['files']:
  b=(HERE/row['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['file_sha256'],row['file']
  u=lzma.decompress(b) if row['compression']=='xz' else b
  assert hashlib.sha256(u).hexdigest()==row['public_uncompressed_sha256'],row['file']
  if row['raw_byte_identity']:assert row['recorded_sha256']==row['public_uncompressed_sha256']
  checked.add(row['file'])
 sys.path.insert(0,str(HERE.parents[1]/'tools/probe'))
 import probe
 _,_,sets=probe.dependencies()
 report=js('standard-report/report.json');assert report['complete'] is False
 independent=js('independent-review/standard-report.json')
 assert {k:v for k,v in report.items() if k!='report_seconds'}=={k:v for k,v in independent.items() if k!='report_seconds'}
 assert set(report['apps'])=={'campfire','forem','chatwoot','mastodon'}
 recount=js('independent-review/recount.json')['apps'];variance=js('experiment/varying-summary.json')
 settings={s+'-v0-a0' for s in ['unset','1','2','repeat']}
 for app,groups in report['apps'].items():
  assert set(groups)=={'v0-a0'};group=groups['v0-a0'];assert set(group['settings'])==settings
  for role in ['control','candidate']:
   records=[]
   for setting in settings:
    prefix='native-cells/'+role+'/'+app+'/'+setting
    result=js(prefix+'/result.json');native=js(prefix+'/report.json')
    assert result['valid'] and result['app']==app and result['setting']['name']==setting
    vector=result['observations']['value_digests'];assert len(vector)==10 and vector==native['digest']
    assert result['key']['binary_sha256']==group[role]['cells'][setting]['binary_sha256']
    assert result['key']['input_manifest_sha256']==group[role]['cells'][setting]['input_manifest_sha256']
    assert result['observations']['diagnostics']==js('native-cells/control/'+app+'/'+setting+'/result.json')['observations']['diagnostics']
    records.append(vector)
    counts=recount[app]['settings'][setting]['counts_after_exact_graph_check']
    assert counts['narrowed']==counts['missing']==counts['incomparable']==0
    if app=='campfire':assert vector==js('native-cells/control/'+app+'/'+setting+'/result.json')['observations']['value_digests']
   equal=sorted(t for t in records[0] if len({x[t] for x in records})==1)
   assert equal==sorted(group[role]['digest_equality']['equal_tables'])
   for table,value in group[role]['varying_rows'].items():
    assert value['varying_rows']==variance[app][table][role]
    if value['varying_rows']:
     text=data('experiment/varying/'+app+'-'+role+'-'+table+'.txt').decode()
     keys=re.findall(r'^- key: (.*)$',text,re.M)
     assert len(keys)==len(set(keys))==value['varying_rows']
     original_role='candidate' if role=='candidate' else 'control'
     other='control' if role=='candidate' else 'candidate'
     othertext=data('experiment/varying/'+app+'-'+other+'-'+table+'.txt').decode()
     otherkeys=set(re.findall(r'^- key: (.*)$',othertext,re.M))
     if role=='candidate':
      assert not set(keys)-otherkeys
      assert sorted(otherkeys-set(keys))==variance[app][table]['stopped_varying']
  for table,value in variance[app].items():assert value==recount[app]['varying_rows'][table] and not value['newly_varying']
  for setting in settings:
   raw=recount[app]['settings'][setting]['standard_counts'];corrected=recount[app]['settings'][setting]['counts_after_exact_graph_check']
   assert raw['narrowed']==0
   if app=='chatwoot':assert raw['missing']==2 and corrected['unchanged']==raw['unchanged']+2
   else:assert raw==corrected
 assert variance['mastodon']['params']['control']==240 and variance['mastodon']['params']['candidate']==236
 cycles=js('independent-review/cycle-proof.json');assert len(cycles)==4
 def refs(value):
  if isinstance(value,list):return set().union(*(refs(x) for x in value))
  if isinstance(value,dict):return {value['slot']} if value.get('kind')=='rec' else set().union(*(refs(x) for x in value.values()))
  return set()
 for cell,proof in cycles.items():
  assert proof['exact_graph_equality'] and proof['reachable_nodes']==2 and len(proof['unclassified'])==2
  graph=proof['graphs']['control'];assert graph==proof['graphs']['candidate'] and not graph['missing']
  definitions=graph['definitions'];assert len(definitions)==2
  assert all(refs(x)<=set(definitions) for x in definitions.values())
  assert {x['key'] for x in graph['roots']}==set(definitions)
  assert all(root['ty']==definitions[root['key']] for root in graph['roots'])
 oauth=js('independent-review/oauth-admission.json');all_oauth=js('independent-review/oauth-all-schedules.json')
 assert len(oauth['providers'])==4 and set(all_oauth)==settings
 for provider,row in oauth['providers'].items():
  witness=row['witness_type'];assert not sets.covers(row['values']['control'],witness)
  for role in ['candidate','fresh_candidate']:assert sets.covers(row['values'][role],witness)
  assert sets.relation(row['values']['control'],row['values']['candidate'])=='WIDEN'
  for setting in settings:assert sets.covers(all_oauth[setting][provider]['candidate'],witness)
 pending=js('independent-review/pending-census.json')
 for app,before,after in [('campfire',0,0),('forem',55,0),('chatwoot',170,0),('mastodon',721,23)]:
  item=pending[app];assert item['candidate_pending_counts_equal_across_schedules']
  assert not item['off_vs_spine3_observation_differences']
  baseline=js('native-cells/flag-off/'+app+'/unset-v0-a0/settlement-census.json')
  assert baseline==item['off_unset'] and baseline['pending_leaves']['total']==before
  for setting in settings:
   value=js('native-cells/candidate/'+app+'/'+setting+'/settlement-census.json');assert value==item['candidate'][setting]
   counts=value['pending_leaves'];assert counts['total']==after==sum(counts['stub'].values())+counts['param_seed']+counts['ivar_attr']+sum(counts['other'].values())
   if app=='mastodon':assert counts['param_seed']==20 and counts['other']=={'return':2,'ir':1,'local':0}
 fresh=js('independent-review/fresh-comparisons.json');assert len(fresh)==3
 for cell,value in fresh.items():
  assert value['same_condition_excluding_capture_paths'] and not value['observation_differences']
  assert value['contributor_rows_equal_by_identity'] and value['strict_stub_completion_census_equal'] and not value['contributor_changed_rows']
  result=js('independent-review/fresh/'+cell+'/result.json')
  original=js('native-cells/candidate/'+cell+'/result.json')
  assert result['observations']['value_digests']==original['observations']['value_digests']
  assert result['observations']['value_digests']==js('independent-review/fresh/'+cell+'/report.json')['digest']
 log=data('experiment/cargo-test-lib-ready.log').decode()
 assert '1249 passed; 0 failed; 26 ignored; 0 measured; 0 filtered out' in log
 assert len(re.findall(r'^test .* \.\.\. ok$',log,re.M))==1249
 assert len(re.findall(r'^test .*strict_stub_completion::tests::.* \.\.\. ok$',log,re.M))==4
 return dict(fact=70,retained_files=len(checked),native_grid_cells=32,apps=4,settings=4,oauth_admissions=16,narrowings=0,newly_varying=0,mastodon_varying_params=[240,236],pending_after={'forem':0,'chatwoot':0,'mastodon':23},standard_report='incomplete; two cycles separately proved equal',native_analyzers=0)
if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1]=='saved','Usage: python3 rerun.py saved'
 print(json.dumps(saved(),sort_keys=True))
