#!/usr/bin/env python3
"""Verify retained F71 evidence; no analyzer or omitted app stream is executed."""
import hashlib,json,lzma,re,sys
from collections import Counter
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
 report=js('standard-reports/v0-v1-report.json');independent=js('independent-review/independent-checks.json')
 assert report['complete'] is False and len(independent['recounts'])==16
 expected_before={'campfire':10,'forem':6,'chatwoot':5,'mastodon':5}
 expected_after={'campfire':10,'forem':10,'chatwoot':6,'mastodon':5}
 for app,groups in report['apps'].items():
  assert set(groups)=={'v0-a0','v1-a1'}
  for observer,group in groups.items():
   assert len(group['settings'])==4
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
    equal=sorted(t for t in vectors[0] if len({v[t] for v in vectors})==1)
    assert equal==sorted(group[role]['digest_equality']['equal_tables'])
    assert len(equal)==(expected_before if role=='control' else expected_after)[app]
    recount=[x for x in independent['recounts'] if (x['app'],x['observer'],x['role'])==(app,observer,role)]
    assert len(recount)==1 and sorted(recount[0]['equal_tables'])==equal
    assert recount[0]['varying_rows']=={p:x['varying_rows'] for p,x in group[role]['varying_rows'].items()}
   if app=='mastodon':
    assert group['control']['varying_rows']['ir']['varying_rows']==1920
    assert group['candidate']['varying_rows']['ir']['varying_rows']==269
   assert group['unset_values']['counts']['missing']=={'campfire':18,'forem':59,'chatwoot':873,'mastodon':340}[app]
 for app,expected in [('campfire',(1,1,0)),('forem',(105,105,0)),('chatwoot',(202,199,3)),('mastodon',(272,269,3))]:
  difference=independent['narrowing_identity_differences'][app]
  assert (difference['m461_narrowed'],difference['canon_narrowed'],len(difference['removed']))==expected
  assert not difference['added']
  for row in difference['changed_common_type_encodings']:
   assert row['relation']=='EQ' and membership.sets.relation(row['old'],row['new'])=='EQ'
 assert len(independent['fresh'])==5
 for row in independent['fresh']:
  assert row['valid'] and row['fresh_match'] and not row['differences']
  result=js('independent-review/fresh/'+row['cell']+'/result.json')
  old=js('native-cells/candidate/'+row['cell']+'/result.json')
  assert result['observations']['value_digests']==old['observations']['value_digests']
  assert result['observations']['value_digests']==js('independent-review/fresh/'+row['cell']+'/report.json')['digest']
 witness=js('independent-review/witness-checks.json');assert len(witness['checks'])==64
 losses={app:set() for app in expected_before};inherited=set()
 for row in witness['checks']:
  admitted=membership.admits(row['control'],row['witness_type']);rejected=membership.admits(row['candidate'],row['witness_type'])
  assert admitted==row['control_admits'] and rejected==row['candidate_admits'] is False
  if row['new_loss']:
   assert admitted is True;losses[row['app']].add(row['id'])
  else:inherited.add(row['id'])
 assert {a:len(v) for a,v in losses.items()}=={'campfire':1,'forem':6,'chatwoot':44,'mastodon':10}
 assert inherited=={'C114'}
 for app in expected_before:
  old=js('classification/'+app+'-witnesses.json');fresh=js('fresh-witness/'+app+'-witnesses.json')
  observed=lambda v:[(x['label'],x['rows'],x['ruby_class'],x['type'],x.get('expression')) for x in v['observations']]
  assert observed(old)==observed(fresh)
  assert [x['sha256'] for x in old['sources']]==[x['sha256'] for x in fresh['sources']]
  assert 'ruby 4.0.7 ' in fresh['ruby']
 cause=js('independent-review/cause-checks.json')
 for app,file,start,end,routed,typed in [('campfire',79,829,952,2,6),('forem',19,3430,3493,10,2)]:
  value=cause['apps'][app];assert value['all_ten_digests_match_canon'] and not value['standard_observation_differences']
  assert len(value['routed_writer_spans'])==routed and value['lost_call_span']==[file,start,end]
  assert sum(value['receiver_states'].values())==typed
  assert all(x['span']!=[str(file),str(start),str(end)] for x in value['routed_writer_spans'])
  lines=data('cause/'+app+'-trace.txt').decode().splitlines()
  prefix='WRITER typed span=Span { file: FileId(%s), start: %s, end: %s }'%(file,start,end)
  events=[x for x in lines if x.startswith(prefix)];assert len(events)==typed
  states=Counter(x.split(' recv=',1)[1].split(' args=',1)[0] for x in events)
  assert dict(states)==value['receiver_states']
 top=js('followup/unresolved-route/membership-unresolved-route-followup-44182d62.json')
 failed=[x for x in top['checks'] if not x['passed']]
 assert len(failed)==4 and {x['id'] for x in failed}=={'M192'}
 assert sum(x['passed'] for x in top['checks'])==244 and len(top['checks'])==248
 assert all(x['passed'] for x in top['checks'] if x['id'] in ['A001','F075'])
 metrics=js('followup/unresolved-route/metrics.json')
 assert len(metrics['apps']['forem']['equal_tables']['top'])==6
 assert len(metrics['apps']['chatwoot']['equal_tables']['top'])==5
 for name in ['cargo-test-lib.log','cargo-test-lib-canon.log']:
  log=data('experiment/'+name).decode()
  assert '1258 passed; 0 failed; 37 ignored; 0 measured; 0 filtered out' in log
  assert len(re.findall(r'^test .* \.\.\. ok$',log,re.M))==1258
 return dict(fact=71,retained_files=len(checked),native_grid_cells=64,apps=4,observers=['V0A0','V1A1'],review='WEAKENED',new_runtime_loss_rows={a:len(v) for a,v in losses.items()},inherited_mismatches=1,narrowing_sets='different',routing='still fails M192',standard_report='incomplete',native_analyzers=0)
if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1]=='saved','Usage: python3 rerun.py saved'
 print(json.dumps(saved(),sort_keys=True))
