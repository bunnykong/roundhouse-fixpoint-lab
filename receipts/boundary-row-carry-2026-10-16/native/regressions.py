import lzma
#!/usr/bin/env python3
"""boundary-carry-protocol evidence and binding regressions; never invokes the analyzer."""
import copy
import json
import random
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import row_model as r
import verdict as v

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
    def boundary(self,mutate=None):
        p=HERE/'fixtures/before-carry-boundary.jsonl'
        rows=[json.loads(line) for line in lzma.open(str(p)+".xz", "rt")]
        if mutate: mutate(next(x for x in rows if x.get('part')=='fingerprint'))
        out=Path(self.tmp.name)/'contributor-values-boundary.jsonl'
        out.write_text(''.join(json.dumps(x)+'\n' for x in rows))
        return out
    def test_boundary_inventory_both_maps(self):
        r.load(self.boundary())
        for mutate,expected in [
            (lambda h:h['parts'].pop('returns'),'fingerprint table inventory'),
            (lambda h:h['parts'].update(unknown={}), 'fingerprint table inventory'),
            (lambda h:h['digests'].pop('view_seeds'),'digest inventory'),
            (lambda h:h['digests'].pop('returns'),'digest inventory'),
            (lambda h:h['digests'].update(unknown='0'),'digest inventory'),
            (lambda h:h['digests'].update(view_seeds='0'),'table digest mismatch view_seeds')]:
            with self.subTest(expected=expected),self.assertRaisesRegex(ValueError,expected):r.load(self.boundary(mutate))
        with self.assertRaisesRegex(ValueError,'fingerprint table inventory'):r.load(self.boundary(),boundary=False)
    def test_metadata_record_and_retained_functions(self):
        record=lambda x:{'kind':'record','row':{'fields':{'x':x},'rest':None}}
        self.assertEqual(r.relation(record(v.INT),record(v.union(v.INT,v.U))),'removal')
        named_kind=lambda x:{'kind':'record','row':{'fields':{'kind':x},'rest':None}}
        self.assertEqual(r.relation(named_kind(v.INT),named_kind(v.union(v.INT,v.U))),'removal')
        c=json.loads((HERE/'fixtures/C-functions.json').read_text());ds=json.loads((HERE/'fixtures/DS-functions.json').read_text())
        relations=[r.relation(a['native_ty'],b['native_ty']) for a,b in zip(ds,c)]
        self.assertEqual(relations,['violation','equal','violation'])
        bad=record({'kind':'untyped'})
        self.assertEqual(r.relation(bad,bad),'unknown')
        fn={'kind':'fn','params':[], 'ret':v.union(v.INT,v.U),'block':None,'effects':{'raises':False}}
        a=copy.deepcopy(fn);a['ret']=v.INT
        self.assertEqual(r.relation(a,fn),'removal')
        a['effects']['raises']=True
        self.assertEqual(r.relation(a,fn),'violation')
    def test_exact_retained_alias_graph(self):
        rows=[json.loads(line) for line in lzma.open(str(HERE/'fixtures/before-carry-boundary.jsonl')+'.xz', 'rt')]
        sides={x['key']:x['native_ty'] for x in rows if x.get('part')=='side_table'}
        requests=[x for x in rows if x.get('part')=='side_table' and 'method: Symbol("request=")' in x.get('key','') and 'ClassId(Symbol("Current"))' in x.get('key','')]
        self.assertEqual(len(requests),2)
        # Graph traversal, rather than treating Rec as independent evidence.
        def leaves(t,seen):
            if t.get('kind')=='rec':
                key=t['slot']
                if key in seen:return set()
                return leaves(sides[key],seen|{key}) if key in sides else {'absent'}
            if t.get('kind')=='union':return set().union(*(leaves(x,seen) for x in t['variants']))
            if t.get('kind')=='untyped':return set(t['reasons'])
            return {'concrete'}
        self.assertTrue(all(leaves(x['native_ty'],set())=={'Pending'} for x in requests))
        sides['concrete']=v.INT
        self.assertEqual(leaves({'kind':'rec','slot':'concrete'},set()),{'concrete'})
        sides['cycle']={'kind':'rec','slot':'cycle'}
        self.assertEqual(leaves(sides['cycle'],set()),set())
        self.assertEqual(leaves(v.union(v.INT,v.P),set()),{'concrete','Pending'})
        declared=set(sides)|{'declared-absent'}
        negative={x for x in declared if x not in sides or 'Pending' in leaves(sides[x],set())}
        self.assertIn('declared-absent',negative)
        self.assertTrue(all(x['key'] in negative for x in requests))
        self.assertNotIn('concrete',negative)


def prepare_native(d):
    v.write_native(d)
    for carry in ('0','1'):
        body=dict.fromkeys(('alias_retracted','concrete_reference_survives','mixed_preserved','absent_in_set',
                            'parameter_restored','helper_preserved','derived_not_answered','negative_answer_unresolved'),True)
        body.update(selected_tests=['boundary_carry_boundary'],retractions=2 if carry=='1' else 0,
                    negative_size=4 if carry=='1' else 0,boundary_rows_lost=0,boundary_rows_reinserted=0,
                    stratum2_answers_outside_set=0,settled_pending=0)
        (d/('boundary_carry-boundary-'+carry+'.log')).write_text('running 1 test\ntest analyze::boundary_carry::tests::boundary_carry_boundary ... BOUNDARY_CARRY-BOUNDARY '+json.dumps(body)+'\nok\ntest result: ok. 1 passed; 0 failed; 0 ignored;\n')
        (d/('boundary_carry-boundary-'+carry+'.exit')).write_text('0\n')


def fresh_fixture():
    store,pins,kpins,targets=v.fixture()
    named=json.loads((HERE/'named-rows.json').read_text())
    for (arm,app,setting),cell in store.data.items():
        if app!='campfire' or arm not in ('C','DS','DSN'):continue
        for item in named:cell['rows'][tuple(item['id'])]={'ty':item['ty']}
        cell['obs']['value_digests']=v.digests_of(v.fake_rows(cell['rows'])[0])
        if arm=='C':pins['cells'][app+'/'+setting]['digests']=cell['obs']['value_digests']
    return store,pins,kpins,targets

class ReducerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.native=Path(self.tmp.name);prepare_native(self.native)
    def evaluate(self,mutate=lambda s,p,k:None,scope='campfire'):
        s,p,k,t=fresh_fixture();mutate(s,p,k)
        return v.evaluate(s,p,k,t,self.native,scope)
    def test_all_pass_and_exact_mandatory_inventory(self):
        for scope in ('campfire','all'):
            out=self.evaluate(scope=scope)
            self.assertEqual(out['verdict'],'CONFIRMED',[x for x in out['checks'] if x['mandatory'] and x['status']!='pass'])
            observed={(x['check'],x['scope'],x['family']) for x in out['checks'] if x['family']}
            self.assertEqual(observed,v.expected_records(scope))
            self.assertEqual(sum(x['check']=='INV-boundary_carry' for x in out['checks']),44 if scope=='campfire' else 60)
            self.assertNotIn('N',out['family_verdicts'])
    def test_failure_and_unavailability_cases(self):
        def mutate_counter(name,value):
            return lambda s,p,k:s.data[('DS','campfire','unset-v1-a1')]['report']['c6'].__setitem__(name,value)
        cases=[('lost',mutate_counter('boundary_rows_lost',1),'KILLED'),
               ('missing',mutate_counter('boundary_rows_lost',None),'INCONCLUSIVE'),
               ('settled',mutate_counter('settled_pending',1),'KILLED')]
        def late(s,p,k):s.data[('KDS','campfire','unset-v1-a1')]['census']['descents']['late_unresolved']=1
        def new_event(s,p,k):s.data[('KDS','campfire','unset-v1-a1')]['census']['events'].append('new-arm-loss')
        def multiplicity(s,p,k):s.data[('KDS','campfire','unset-v1-a1')]['census']['events']*=2
        def added(s,p,k):
            c=s.data[('DS','campfire','unset-v1-a1')];c['rows']['side_table','Current.request=[0]']={'ty':v.U};c['obs']['value_digests']=v.digests_of(v.fake_rows(c['rows'])[0])
        def boundary_missing(s,p,k):s.data[('DS','campfire','unset-v1-a1')]['boundary']=None
        def carry_wrong(s,p,k):s.data[('DS','campfire','unset-v1-a1')]['flags']['RH_DEFERRED_CARRY']='0'
        def unknown(s,p,k):
            c=s.data[('DS','campfire','unset-v1-a1')];c['rows']['params','U#u[0]']={'ty':{'kind':'untyped'}};c['obs']['value_digests']=v.digests_of(v.fake_rows(c['rows'])[0])
        cases += [('late',late,'KILLED'),('new-event',new_event,'KILLED'),('multiplicity',multiplicity,'KILLED'),
                  ('added-placeholder',added,'KILLED'),('missing-boundary',boundary_missing,'INCONCLUSIVE'),
                  ('carry-profile',carry_wrong,'INCONCLUSIVE'),('unknown',unknown,'INCONCLUSIVE')]
        for name,mutate,want in cases:
            with self.subTest(name=name):self.assertTrue(self.evaluate(mutate)['verdict'].startswith(want))
    def test_named_native_missing_empty_and_failed(self):
        for name in ('ndedup-1','ndedup-1-a0','boundary_carry-boundary-1'):
            p=self.native/(name+'.log');original=p.read_text()
            for content in ('',original.replace('1 passed;','0 passed;').replace('running 1 test','running 0 tests') if name.startswith('boundary_carry') else ''):
                p.write_text(content);self.assertTrue(self.evaluate()['verdict'].startswith('INCONCLUSIVE'))
            p.write_text(original);ex=self.native/(name+'.exit');ex.write_text('1\n')
            self.assertEqual(self.evaluate()['verdict'],'KILLED');ex.write_text('0\n')
        p=self.native/'boundary_carry-boundary-1.log';p.write_text(p.read_text().replace('"retractions": 2','"retractions": 1'))
        self.assertEqual(self.evaluate()['verdict'],'KILLED')
    def test_named_equality_and_missing_comparisons(self):
        from unittest.mock import patch
        def change(s,p,k):
            cell=s.data['DS','campfire','unset-v1-a1']
            ident=('returns','ActionView::Base#message_attachment_presentation')
            cell['rows'][ident]={'ty':v.NIL}
            cell['obs']['value_digests']=v.digests_of(v.fake_rows(cell['rows'])[0])
        out=self.evaluate(change)
        self.assertEqual(out['verdict'],'KILLED')
        self.assertTrue(any(x['check']=='H6h-named-equality' and x['status']=='fail' for x in out['checks']))
        with patch.object(v,'layered',lambda *args:[]):
            self.assertTrue(self.evaluate()['verdict'].startswith('INCONCLUSIVE'))
        for scope in ('campfire','all'):
            expected={tuple(x) for x in json.loads((HERE/('expected-'+scope+'.json')).read_text())}
            self.assertEqual(expected,v.expected_records(scope))
    def test_cli_exact_condition_binding(self):
        out=self.native/'pregate.json'
        args=[sys.executable,str(HERE/'verdict.py'),'run','--cache-root',str(self.native/'empty-cache'),
              '--native',str(self.native),'--condition',v.CONDITION,'--scope','campfire','--stage','pregate','--out',str(out)]
        p=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(p.returncode,1,p.stderr);self.assertEqual(json.loads(out.read_text())['condition'],v.CONDITION)
        args[args.index(v.CONDITION)]='wrong-condition'
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,2)
    def test_precedence_random_2000(self):
        rng=random.Random(6)
        for _ in range(2000):
            checks=[v.rec(rng.choice(('PG-test','mandatory','report')),'x',rng.choice(('pass','fail','unavailable')),
                          family=rng.choice(('A','AN',None))) for _ in range(rng.randint(1,8))]
            gate=any(x['check'].startswith('PG') and x['status']!='pass' for x in checks)
            unavailable=any(x['mandatory'] and x['status']=='unavailable' for x in checks)
            fail=any(x['mandatory'] and x['status']=='fail' for x in checks)
            want='INCONCLUSIVE (pre-gate)' if gate else 'INCONCLUSIVE (unavailable mandatory evidence)' if unavailable else 'KILLED' if fail else 'CONFIRMED'
            self.assertEqual(v.decide(checks),want)

def selftest():
    return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReducerTests)).wasSuccessful() else 1
if __name__=='__main__':
    sys.exit(0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EvidenceTests)).wasSuccessful() else 1)
