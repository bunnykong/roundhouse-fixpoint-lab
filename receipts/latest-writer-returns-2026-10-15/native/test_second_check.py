"""All ten second-check probes plus fixture inventory and collector contract regressions."""
import copy, math, unittest
import test_verdict_returns as T
import verdict_returns as V
import run_fixture as FX
import classifiers as C

def status(b):return V.verdict(b)[0]
def cells(b):return [c for arm in b['cells'].values() for c in arm.values()]
class SecondCheck(unittest.TestCase):
 def test_complete_control(self):self.assertEqual(status(T.good()),'CONFIRMED FOR THIS CONDITION')
 def test_app_gate_cannot_bypass_campfire(self):
  b=T.good();b['campfire_first_stage']=False;b['ledger']['K']['1-v1-a1']['descents']['premature_unresolved']=1
  s,_,r=V.verdict(b);self.assertEqual(s,'INCONCLUSIVE');self.assertTrue(any('premature_unresolved' in x for x in r['observed_counterexamples_despite_gap']))
 def test_null_census(self):
  b=T.good()
  for c in cells(b):c['reason_census']['untyped_anywhere']=None
  self.assertEqual(status(b),'INCONCLUSIVE')
 def test_null_diagnostic(self):
  b=T.good()
  for c in cells(b):c['diagnostics_by_kind']['warning/unresolved_type']=None
  self.assertEqual(status(b),'INCONCLUSIVE')
 def test_negative_counts(self):
  b=T.good()
  for c in cells(b):c['caps']['cap_hits']=-1
  b['returns']['K']['nested_var_rows']=-1;b['returns']['K']['new_varying_rows_vs_C']=-1
  self.assertEqual(status(b),'INCONCLUSIVE')
 def test_duplicate_partition(self):
  b=T.good();b['returns']['K'].update(varying_rows=['X#a']*2,upstream_rows=['X#a']*2)
  b['returns']['K']['targets'].update(invariant=8,upstream=['t1']*2)
  self.assertEqual(status(b),'INCONCLUSIVE')
 def test_unknown_verify_table(self):
  b=T.good()
  for c in cells(b):
   if isinstance(c['verify'],dict):
    for loop in c['verify'].values():loop['not_a_native_table']=0
  self.assertEqual(status(b),'INCONCLUSIVE')
 def test_h5_includes_v0(self):
  b=T.good();b['ledger']['K']['unset-v0-a0']['descents']['premature_unresolved']=1
  self.assertEqual(status(b),'KILLED')
 def test_invalid_cell_is_not_a_counterexample(self):
  b=T.good();c=b['cells']['K']['1-v1-a1'];c['valid']=False;c['errors_by_kind']={'error/send_dispatch_failed':1}
  s,_,r=V.verdict(b);self.assertEqual(s,'INCONCLUSIVE');self.assertFalse(r['observed_counterexamples_despite_gap']);self.assertTrue(r['untrusted_observations'])
 def test_control_losses_report_only(self):
  b=T.good();b['cells']['C']['1-v1-a1']['audit']['origin_loss_current']=1
  s,_,r=V.verdict(b);self.assertEqual(s,'CONFIRMED FOR THIS CONDITION');self.assertEqual(r['control_origin_losses_report_only']['1-v1-a1']['origin_loss_current'],1)
 def test_fixture_specific_table_count(self):
  self.assertTrue(FX.tables_valid('issue521','C',FX.BASE));self.assertTrue(FX.tables_valid('issue964','C',FX.BASE|{'attributes'}))
  self.assertFalse(FX.tables_valid('issue521','C',FX.BASE|{'attributes'}));self.assertFalse(FX.tables_valid('issue964','C',FX.BASE))
 def test_fixture_additions_known_only(self):
  self.assertTrue(FX.tables_valid('issue521','K',FX.BASE|{'side_table'}));self.assertFalse(FX.tables_valid('issue521','K',FX.BASE|{'invented'}))
 def test_target_membership_bound_to_manifest(self):
  b=T.good();b['returns']['K']['targets']['upstream']=['invented'];self.assertEqual(status(b),'INCONCLUSIVE')
  b=T.good();b['returns']['K']['targets']['total']=11;self.assertEqual(status(b),'INCONCLUSIVE')
 def test_target_bounds(self):
  for vals in ({'present':11},{'invariant':11},{'invariant':-1}):
   b=T.good();b['returns']['K']['targets'].update(vals);self.assertEqual(status(b),'INCONCLUSIVE')
 def test_finite_nonnegative_performance(self):
  for x in (-1,float('nan'),float('inf')):
   b=T.good();b['cells']['C']['unset-v1-a1']['performance']['wall_s']=x;self.assertEqual(status(b),'INCONCLUSIVE')
 def test_all_app_identities(self):
  for app in ('campfire','forem','chatwoot','mastodon'):self.assertEqual(status(T.good(app)),'CONFIRMED FOR THIS CONDITION')
  b=T.good('discourse');self.assertEqual(status(b),'INCONCLUSIVE')
 def test_invalid_timedout_cell_excluded(self):
  b=T.good();b['cells']['K']['2-v1-a1']['timed_out']=True;b['cells']['K']['2-v1-a1']['verify']['absorb']['returns']=1
  self.assertFalse(V.verdict(b)[2]['observed_counterexamples_despite_gap'])
 def test_three_way_partition_disjoint(self):
  b=T.good();b['returns']['K']['unclassified_rows']=['X#a'];self.assertEqual(status(b),'INCONCLUSIVE')
 def test_unknown_nested_census_table(self):
  b=T.good();b['cells']['C']['1-v1-a1']['reason_census']['unknown']=0;self.assertEqual(status(b),'INCONCLUSIVE')
 def test_descent_uses_order_a(self):
  u={'kind':'untyped','reasons':['Unresolved']};s={'kind':'str'}
  self.assertEqual(C.family(u,s),'premature_unresolved');self.assertEqual(C.family(s,u),'late_unresolved')
if __name__=='__main__':unittest.main()
