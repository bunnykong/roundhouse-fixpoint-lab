#!/usr/bin/env python3
"""Verify retained F72 evidence; this starts no analyzer and boots no application."""
import csv,hashlib,io,json,lzma,os,re,subprocess,sys,tempfile
from collections import Counter,defaultdict
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
 sys.path.insert(0,str(HERE/'native'));import membership
 report=js('standard-reports/report.json');support=js('independent-review/support-check.json')
 assert report['complete'] is False
 before={'campfire':10,'forem':6,'chatwoot':5,'mastodon':5}
 after={'campfire':10,'forem':9,'chatwoot':10,'mastodon':5}
 measurement=js('experiment/measurement.json')
 for app,groups in report['apps'].items():
  group=groups['v0-a0'];assert len(group['settings'])==4
  for role in ['control','candidate']:
   vectors=[]
   for setting,cell in group[role]['cells'].items():
    prefix='native-cells/'+role+'/'+app+'/'+setting
    native=js(prefix+'/report.json');result=js(prefix+'/result.json')
    assert result['valid'] and result['setting']['name']==setting
    v=result['observations']['value_digests'];assert len(v)==10 and v==native['digest']
    assert result['key']['binary_sha256']==cell['binary_sha256']
    assert result['key']['input_manifest_sha256']==cell['input_manifest_sha256']
    vectors.append(v)
    if role=='candidate':
     assert result['observations']['reason_census']['untyped_by_provenance']['pending']==0
     phases={x['phase']:x for x in measurement['apps'][app][setting]['completion']}
     assert phases['completion-finished']['total']==phases['settlement-safety-net']['total']==0
     assert phases['completion-finished']['closed'] is True
   equal=sorted(t for t in vectors[0] if len({v[t] for v in vectors})==1)
   assert equal==sorted(group[role]['digest_equality']['equal_tables'])
   assert len(equal)==(before if role=='control' else after)[app]==support['equal_counts'][app][role]
  assert group['unset_values']['counts']['missing']=={'campfire':1574,'forem':9158,'chatwoot':10582,'mastodon':14429}[app]
 assert len(support['pending'])==16 and all(x['completion_and_settlement_pending']==0 for x in support['pending'])
 fresh=js('independent-review/fresh-comparison.json');assert fresh['passed'] and len(fresh['checks'])==2
 for row in fresh['checks']:
  assert row['same_binary_input_runtime_profile'] and not row['observation_differences']
  assert set(row['unavailable_fields'])=={'successful_writes','law_violation_counts','verify'}
  d=row['dumps']['contributor-values.jsonl']
  assert d['parsed_rows_identical_after_normalizing_debug_rec_ids'] and d['rows']==254601 and d['semantic_row_differences']==0
  setting=row['setting'];new=js('independent-review/fresh/chatwoot/'+setting+'/result.json')
  old=js('native-cells/candidate/chatwoot/'+setting+'/result.json')
  assert new['observations']==old['observations']
  assert new['key']['binary_sha256']==old['key']['binary_sha256']
  assert new['observations']['value_digests']==js('independent-review/fresh/chatwoot/'+setting+'/report.json')['digest']
  assert next(x for x in row['completion'] if x['phase']=='completion-round')['retype_iterations']==11
 witness_review=js('independent-review/witness-check.json')
 assert witness_review['passed'] and witness_review['all_23_runtime_types_match_retained'] and witness_review['observations_rerun']==23
 for identifier,row in witness_review['rows'].items():
  assert identifier in ['C1431','C1432','C134','C1007']
  for key,check in row['native_checks'].items():
   assert membership.admits(check['resolved_type'],row['runtime_type'])==check['admitted']==key.startswith('control/')
  if identifier in ['C1431','C1432']:
   assert row['control_signature_count']==2 and row['candidate_signature_count']==1 and row['selected'] is False
 rows=list(csv.DictReader(io.StringIO(data('census/rows.tsv').decode()),delimiter='\t'))
 by_id={x['id']:x for x in rows};assert len(by_id)==6233
 for app in ['chatwoot','mastodon','forem']:
  reported={(x['table'],x['key']):x for x in report['apps'][app]['v0-a0']['unset_values']['narrowings']}
  captured={(x['table'],x['key']):x for x in rows if x['app']==app}
  assert set(captured)==set(reported),app
  for key,row in captured.items():
   for field in ['control','candidate','control_reference_expansions','candidate_reference_expansions']:
    assert json.loads(row[field])==reported[key][field],(app,key,field)
 with tempfile.TemporaryDirectory(prefix='census-replay-') as folder:
  root=Path(folder)
  for name in ['rows.tsv','summary.json']:(root/name).write_bytes(data('census/'+name))
  env=dict(os.environ,CENSUS_ROOT=str(root))
  r=subprocess.run([sys.executable,'-B',str(HERE/'native/check_census.py')],cwd=root,env=env,capture_output=True,text=True)
  assert r.returncode==0,(r.stdout,r.stderr)
  census=json.loads((root/'census-check.json').read_text())
  assert census['passed'] and census['sample_verdicts']=={'SOUND':75,'UNSOUND':54,'INHERITED_UNSOUND':6}
  assert census['targeted_outside_sample']==['C1431','C1432'] and census['unadjudicated']==6096
  retained=js('independent-review/census-check.json')
  for app,body in census['apps'].items():
   original=retained['apps'][app]
   # Only the display label changes; integer seeds preserve the original selection.
   for stratum in body['strata']:
    assert body['strata'][stratum].pop('seed').endswith('/'+app+'/'+stratum)
    original['strata'][stratum].pop('seed')
   assert body==original,app
 runtime=js('census/witness-membership.json');assert len(runtime)==63
 new_loss=set();inherited=set()
 for check in runtime:
  row=by_id[check['id']];a=json.loads(row['control']);b=json.loads(row['candidate'])
  if check['position']=='$/ret':a,b=a['ret'],b['ret']
  assert membership.admits(a,check['type'])==check['control_admits']
  assert membership.admits(b,check['type'])==check['candidate_admits']
  if row['verdict']=='UNSOUND':
   assert check['control_admits'] is True and check['candidate_admits'] is False
   new_loss.add(check['id'])
  if row['verdict']=='INHERITED_UNSOUND':
   assert check['control_admits'] is check['candidate_admits'] is False;inherited.add(check['id'])
 assert len(new_loss)==56 and len(inherited)==6
 for app in ['forem','chatwoot','mastodon']:
  old=js('census/'+app+'-witnesses.json');new=js('fresh-witness/'+app+'-witnesses.json')
  observed=lambda v:[(x['label'],x['rows'],x['ruby_class'],x['type'],x.get('expression'),x.get('boundary')) for x in v['observations']]
  assert observed(old)==observed(new)
  assert [x['sha256'] for x in old['sources']]==[x['sha256'] for x in new['sources']]
  assert 'ruby 4.0.7 ' in new['ruby']
 stable=js('census/stabilizing-loss-checks.json')
 assert {x['id'] for x in stable['rows']}=={'C1431','C1432'}
 for row in stable['rows']:
  for label,t in row['types'].items():assert membership.admits(t,row['value_type'])==row['membership'][label]==label.startswith('response-return-spine-control/')
 cause=js('census/cause-analysis.json')
 assert {k:len(v['rows']) for k,v in cause['groups'].items()}=={'array contents lost after mutation':35,'hash contents lost after update or merge':14,'caller or writer contribution omitted':5}
 assert set().union(*(set(v['rows']) for v in cause['groups'].values()))=={r['id'] for r in rows if r['selected']=='True' and r['verdict']=='UNSOUND'}
 # Recheck the exact saved gate against its original Ruby value types.
 original=js('regression/prior-membership.json')['checks'];observations=defaultdict(list)
 for v in original:observations[v['id']].append(v['observation']['type'])
 gate=js('regression/membership-integrated-current-writers-f9a7e620.json')
 oauth=js('regression/oauth-witnesses.json');formatter=js('regression/formatter-witnesses.json')
 assert len(gate['checks'])==248 and len(gate['extra'])==40
 for c in gate['checks']+gate['extra']:
  if 'id' in c:values=observations[c['id']]
  elif c['family']=='F68':
   provider=next(v.lower() for v in ['Google','Instagram','Microsoft','Notion'] if '::'+v+'::' in c['key'])
   values=[v['value_type'] for v in oauth['render_calls'] if v['provider']==provider]
  else:values=[v['type'] for v in formatter['observations'] if 'M461' in v['rows']]
  assert values and c['type'] is not None
  assert [membership.admits(c['type'],v) for v in values]==c['admitted']
  assert c['passed'] is True and all(x is True for x in c['admitted'])
 for name,n in [('export-admission.json',8),('indifferent-admission.json',4)]:
  v=js('regression/witness/'+name)
  for c in v['checks']:assert membership.admits(c['type'],c['witness'])==c['admitted']
  selected=[c for c in v['checks'] if c['label']=='integrated-current-writers-f9a7e620']
  assert len(selected)==n and all(c['admitted'] is True for c in selected)
 assert measurement['gate_checks']==measurement['gate_passed']==support['gate_checks']==support['gate_passed']==300
 log=data('experiment/cargo-test-lib.log').decode()
 assert '1288 passed; 0 failed; 54 ignored; 0 measured; 0 filtered out' in log
 blocks=re.findall(r'^test \S+ \.\.\. (.*?)(?=^test \S+ \.\.\. |^test result:|\Z)',log,re.M|re.S)
 assert len(blocks)==1342
 assert sum(x.rstrip().endswith('ok') for x in blocks)==1288
 assert sum(x.startswith('ignored') for x in blocks)==54
 return dict(fact=72,retained_files=len(checked),native_grid_cells=32,review_fresh_cells=2,apps=4,observer='V0A0',review='UPHELD',sampled_rows=135,new_sampled_losses=54,inherited_errors=6,targeted_losses_outside_rates=2,unadjudicated=6096,saved_regression_checks=300,public_ruby_programs=3,standard_report='incomplete',native_analyzers=0,omitted_full_streams_recounted=False)
if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1]=='saved','Usage: python3 rerun.py saved'
 print(json.dumps(saved(),sort_keys=True))
