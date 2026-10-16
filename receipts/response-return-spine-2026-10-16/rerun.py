#!/usr/bin/env python3
"""Verify retained bytes and recompute the saved result; starts no analyzer."""
import hashlib,json,lzma,sys
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
MANIFEST=json.loads((HERE/'manifest.json').read_text())
FACT=json.loads((HERE/'result.json').read_text())['fact']
def data(name):
 rows=[x for x in MANIFEST['files'] if x['recorded_file']==name]
 assert len(rows)==1,(name,len(rows))
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
 if FACT==68:
  sys.path.insert(0,str(HERE/'native'));import runtime_sets as R
  rows=[json.loads(x) for x in data('experiment/receipts/classified-rows.jsonl').splitlines()]
  assert len(rows)==104
  settings=defaultdict(list);unique=defaultdict(list);verdicts=Counter()
  for row in rows:
   before,after=row['C']['resolved_ty'],row['SK']['resolved_ty']
   relation=R.relation(before,after);assert relation==row['relation']
   admission=[(R.covers(before,w['witness']['type']),R.covers(after,w['witness']['type'])) for w in row['witnesses']]
   assert admission and all(c for c,s in admission)
   status='unsound narrowing' if relation=='NARROW' and any(not s for c,s in admission) else 'no runtime change'
   assert status==row['verdict']
   if status=='no runtime change':assert relation=='EQ' and R.top(before) and R.top(after)
   verdicts[status]+=1;settings[row['setting']].append(status)
   unique[row['row_id']].append((before,after,status))
  expected={s+'-v'+v+'-a'+v for s in ['unset','1','2','repeat'] for v in ['0','1']}
  assert set(settings)==expected and len(unique)==13
  assert all(Counter(v)=={'unsound narrowing':4,'no runtime change':9} for v in settings.values())
  assert all(len(v)==8 and all(x==v[0] for x in v) for v in unique.values())
  assert verdicts=={'unsound narrowing':32,'no runtime change':72}
  oauth=js('fresh-witness/oauth.json');assert oauth['ruby'].startswith('ruby 4.0.7')
  assert {r['provider'] for r in oauth['render_calls']}=={'google','instagram','microsoft','notion'}
  narrowed=[v[0] for v in unique.values() if v[0][2]=='unsound narrowing']
  for call in oauth['render_calls']:
   t=call['value_type'];assert any(R.covers(c,t) and not R.covers(s,t) for c,s,_ in narrowed)
  attribution=js('experiment/receipts/producer-attribution.json');assert len(attribution)==4
  for cell in attribution.values():
   assert len(cell['providers'])==4
   for provider in cell['providers'].values():
    assert provider['C']['native_join']['lost_kinds']==[]
    assert provider['SK']['native_join']['lost_kinds']==['Pending']
    assert 'Pending' in provider['SK']['native_join']['observed'] and 'Pending' not in provider['SK']['native_join']['output']
    for variant in ['C','SK']:
     writers=provider[variant]['client_body_producer'];assert len(writers)==1
     assert next(iter(writers.values()))['shapes']==['{"kind":"var","var":0}']
  equivalence=js('source-equivalence/F56-native-tree.json')
  assert equivalence['native_tree_equivalent_after_declared_public_spelling']
  return dict(fact=FACT,files=len(checked),rows=104,unique_rows=13,settings=8,unsound=4,runtime_equal=9,widenings=0,native_analyzers=0)
 board=js('experiment/receipts/analysis/scoreboard.json');cells=board['cells'];groups=defaultdict(list)
 assert len(cells)==136 and len(board['groups'])==34
 for cell in cells:
  assert cell['valid'];key=(cell['app'],cell['ownership'],cell['verification'],cell['audit']);groups[key].append(cell)
  for version in ['v2','v3']:
   prefix='scoreboard/'+version+'/'+cell['ownership']+'/'+cell['app']+'/'+cell['setting']
   result=js(prefix+'/result.json');report=js(prefix+'/report.json')
   vector=cell[version]['value_digests'];assert len(vector)==10
   assert vector==result['observations']['value_digests']==report['digest']
   assert result['key']['binary_sha256']==board['baseline_binary_sha256' if version=='v2' else 'binary_sha256']
   assert result['key']['input_manifest_sha256']==cell['input_manifest_sha256']
 assert len(groups)==34
 for group in board['groups']:
  key=(group['app'],group['ownership'],group['verification'],group['audit']);entries=groups[key]
  assert len(entries)==4 and {x['setting'].split('-')[0] for x in entries}=={'unset','1','2','repeat'}
  equal={}
  for version in ['v2','v3']:
   tables=entries[0][version]['value_digests']
   equal[version]=sorted(t for t in tables if len({x[version]['value_digests'][t] for x in entries})==1)
   assert equal[version]==sorted(group[version+'_equal_digests'])
  assert equal['v2']==equal['v3'] and not group['gained_equal_digests'] and not group['lost_equal_digests']
  expected={'campfire':10 if group['ownership']=='on' else 9,'forem':6,'chatwoot':5,'mastodon':5,'discourse':3}[group['app']]
  assert len(equal['v3'])==expected
  if group['app']=='discourse':assert group['verification']==group['audit']==0
 review=js('independent-review/receipt-check.json');assert review['issues']==[] and review['cached_cells']==136
 assert len(review['fresh_cells'])==6
 for index,fresh in enumerate(review['fresh_cells'],1):
  assert not fresh['changed_tables'] and not fresh['changed_observation_fields']
  matching=[x for x in cells if (x['app'],x['ownership'],x['setting'])==(fresh['app'],fresh['ownership'],fresh['setting'])]
  assert len(matching)==1
  assert fresh['exit_code']==matching[0]['v3']['exit_code']
  vector=fresh['value_digests'];assert len(vector)==10 and vector==matching[0]['v3']['value_digests']
  assert vector==js('independent-review/fresh-'+str(index)+'/result.json')['observations']['value_digests']
  assert vector==js('independent-review/fresh-'+str(index)+'/report.json')['digest']
 verdict=js('experiment/response-checks/verdict.json');assert verdict==js('independent-review/response-verdict.json')
 for section,expected in [('primary','CONFIRMED'),('h5','UNBLOCKED'),('discourse','CONFIRMED')]:
  assert verdict[section]['verdict']==expected and all(x['status']=='PASS' for x in verdict[section]['checks'])
 suite=js('experiment/receipts/suite.json')
 for mode,passed,failed in [('off',5915,24),('on',5914,25)]:
  record=suite[mode];assert record['passed']==passed and len(record['failed'])==failed
  assert record['complete'] and record['binaries']==861 and record['exit_code']==101
 assert set(suite['on']['failed'])-set(suite['off']['failed'])=={'analyze::if_branches_union_merge'}
 default=js('experiment/receipts/default-response.json')['results']
 assert default['default']['exit']==default['on']['exit']==0 and default['off']['exit']==1
 assert default['default']['stderr_sha256']==default['on']['stderr_sha256']!=default['off']['stderr_sha256']
 return dict(fact=FACT,files=len(checked),paired_cells=136,grounded_receipts=272,unchanged_equality_sets=34,review_fresh_digests=60,full_suite='not green',native_analyzers=0)
if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1]=='saved','Usage: python3 rerun.py saved'
 print(json.dumps(saved(),sort_keys=True))
