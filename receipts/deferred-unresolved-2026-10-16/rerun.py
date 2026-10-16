#!/usr/bin/env python3
"""Verify retained bytes and reduce the saved negative result; starts no analyzer."""
import hashlib,json,lzma,sys,tempfile
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
MANIFEST=json.loads((HERE/'manifest.json').read_text())
FACT=json.loads((HERE/'result.json').read_text())['fact']
def data(suffix):
 rows=[x for x in MANIFEST['files'] if x['recorded_file'].endswith(suffix)]
 assert len(rows)==1,(suffix,len(rows))
 row=rows[0];b=(HERE/row['file']).read_bytes()
 return lzma.decompress(b) if row['compression']=='xz' else b
def js(suffix):return json.loads(data(suffix))
def saved():
 checked=set()
 for row in MANIFEST['files']:
  b=(HERE/row['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['file_sha256'],row['file']
  u=lzma.decompress(b) if row['compression']=='xz' else b
  assert hashlib.sha256(u).hexdigest()==row['public_uncompressed_sha256'],row['file']
  if row['raw_byte_identity']:assert row['recorded_sha256']==row['public_uncompressed_sha256']
  checked.add(row['file'])
 sys.path.insert(0,str(HERE/'native'))
 import verdict as V
 if FACT==65:
  report=js('experiment/receipts/verdict-final.json')
  status,reasons=V.decide(report['criteria'],report['stage'])
  assert status==report['outcome']=='KILLED'
  failed=[x for x in report['criteria'] if x['status']=='not_met'];assert len(failed)==1 and failed[0]['name'].endswith('every changed value is sound')
  row=js('experiment/receipts/decisive-counterexample.json');witness=js('experiment/witness/heatmap.json')
  probes=witness['probes']['outer_block_result']
  assert V.admits_probe(row['C'],probes) is True and V.admits_probe(row['L'],probes) is False
  sparse=witness['returns']['sparse'];assert any(type(x) is int for line in sparse for x in line) and any(x is None for line in sparse for x in line)
  assert row['source_sha256']==witness['source_sha256']=='1dbca1411cf6ec0c6babc7364edf336ae821a60c3b74780a691d32e9ebf13a69'
  return dict(fact=FACT,files=len(checked),verdict=status,control_admits=True,candidate_admits=False,native_runs=0)
 with tempfile.TemporaryDirectory() as tmp:
  native=Path(tmp)
  for row in MANIFEST['files']:
   if not row['recorded_file'].startswith('experiment/native/'):continue
   b=(HERE/row['file']).read_bytes()
   if row['compression']=='xz':b=lzma.decompress(b)
   (native/Path(row['recorded_file']).name).write_bytes(b)
  records=V.native(native)+V.native_provenance(native)+V.strict_producer_protocol_native(native)
  if FACT==67:records+=V.boundary_native(native)
  assert records and all(x['status']=='pass' for x in records),[(x['check'],x['status'],x['detail']) for x in records if x['status']!='pass']
 report=js('experiment/receipts/verdict-campfire.json');checks=report['checks']
 assert V.decide(checks)==report['verdict']
 mandatory=[x for x in checks if x['mandatory']]
 totals=Counter(x['status'] for x in mandatory)
 expected={tuple(x) for x in V.expected_records('campfire')}
 assert {(x['check'],x['scope'],x['family']) for x in checks if x['family']}==expected
 for family,status in report['family_verdicts'].items():
  assert V.decide([x for x in checks if x['family']==family or x['check'].startswith('PG')])==status
 sys.path.insert(0,str(HERE.parent/'latest-writer-returns-2026-10-15/native'))
 import classifiers as C
 import row_model as R
 if FACT==66:
  assert totals=={'pass':239,'fail':50,'unavailable':108}
  assert report['verdict'].startswith('INCONCLUSIVE') and report['family_verdicts']['N']=='KILLED'
  evidence=js('independent-review/decisive-evidence.json')
  for setting,pair in evidence['descent_census'].items():
   assert pair['K']['n_events']==pair['KN']['n_events']==2
   assert pair['KN']['descents']['arm_loss']==5
  events=evidence['fresh_raw_normalizer_events'];assert len(events)==2
  assert all(C.family(x['superseded'],x['current'])==x['family']=='arm_loss' for x in events)
  assert all(R.relation(x['candidate'],x['control'])=='unknown' for x in evidence['actual_comparator_rows'])
  assert 'view_seeds' in evidence['boundary']['builder']['tables']
  measured=js('experiment/receipts/measurements.json')
  assert measured['DS']['campfire/unset-v1-a1']['c6']['settled_pending']==75
  assert measured['C']['campfire/unset-v1-a1']['c6']['settled_pending']==0
  return dict(fact=FACT,files=len(checked),verdict='inconclusive',deduplication='killed',mandatory=dict(totals),targeted_events=2,native_runs=0)
 assert totals=={'pass':301,'fail':208} and report['verdict']=='KILLED'
 summary=js('experiment/receipts/summary.json')
 for variant,count in [('DS',26),('DSN',26),('KDS',584),('KDSN',584)]:
  cell=summary['cells'][variant+'/campfire/unset-v1-a1']
  assert cell['c6']['settled_pending']==count and cell['pending']==0
 evidence=js('independent-review/fresh-comparison.json')
 assert evidence['fresh_cells']['DS']['c6']['settled_pending']==26
 assert evidence['fresh_cells']['KDSN']['c6']['settled_pending']==584
 forbidden=evidence['KDSN_forbidden_events'];assert len(forbidden)==3
 assert {x['family'] for x in forbidden}=={'reference_switch','late_unresolved','placeholder_flip'}
 # The reference-bearing witnesses retain the original resolved classifier labels; do not reclassify unresolved references.
 plain=next(x for x in forbidden if x['family']=='placeholder_flip')
 assert C.family(plain['superseded'],plain['current'])=='placeholder_flip'
 assert len(evidence['KDSN_events_outside_K'])==13
 assert R.relation(evidence['DS_named_rows'][0]['candidate_type'],evidence['DS_named_rows'][0]['control_type'])=='violation'
 return dict(fact=FACT,files=len(checked),verdict='killed',mandatory=dict(totals),settlement_rewrites=[26,584],forbidden_families=3,native_runs=0)
if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1]=='saved','Usage: python3 rerun.py saved'
 print(json.dumps(saved(),sort_keys=True))
