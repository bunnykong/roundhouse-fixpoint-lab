import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D/'deferred_unresolved'))
import verdict as v
import row_model as r

class EvidenceTests(unittest.TestCase):
    def raw(self, changes=None, rows=()):
        folder=Path(tempfile.mkdtemp(dir=D/'tmp'))
        header={'part':'fingerprint','parts':{t:{} for t in v.TABLES if t!='ir'},
                'ir':[], 'digests':{}, 'cache_binding_methods':{},
                'components':{t:{} for t in ('params','controller_cache','controller_bindings')}}
        if changes: changes(header)
        header['digests']={t:format(r.native_hash.sip(r.native_hash.mapping(parts)),'016x') for t,parts in header['parts'].items()}
        header['digests']['ir']=format(r.native_hash.sip(r.native_hash.ir_vector(header['ir'])),'016x')
        path=folder/'contributor-values.jsonl'
        path.write_text('\n'.join(json.dumps(x) for x in [header]+list(rows))+'\n')
        return path
    def test_explicit_empty_aggregates(self):
        def change(h):
            for t in h['components']:
                h['parts'][t]['Empty#m']=r.native_hash.sip(r.native_hash.vec([])) if t=='params' else r.native_hash.sip(r.native_hash.mapping({})+(r.native_hash.mapping({}) if t=='controller_cache' else b''))
                h['components'][t]['Empty#m']=[]
                if t=='controller_cache': h['cache_binding_methods']['Empty#m']=[]
        r.load(self.raw(change))
    def test_missing_empty_inventory_is_not_empty(self):
        with self.assertRaises(ValueError): r.load(self.raw(lambda h:h.pop('components')))
    def test_inventory_lies_about_empty_parameter(self):
        def change(h):
            h['parts']['params']['M#m']=r.native_hash.sip(r.native_hash.vec([123]))
            h['components']['params']['M#m']=[]
        with self.assertRaises(ValueError): r.load(self.raw(change))
    def test_inventory_lies_about_empty_binding(self):
        def change(h):
            h['parts']['controller_bindings']['M#m']=r.native_hash.sip(r.native_hash.mapping({'x':123}))
            h['components']['controller_bindings']['M#m']=[]
        with self.assertRaises(ValueError): r.load(self.raw(change))
    def test_missing_empty_cache_method(self):
        def change(h):
            h['parts']['controller_cache']['M']=r.native_hash.sip(r.native_hash.mapping({'m':r.native_hash.sip(r.native_hash.mapping({}))})+r.native_hash.mapping({}))
            h['components']['controller_cache']['M']=[]
            h['cache_binding_methods']['M']=[]
        with self.assertRaises(ValueError): r.load(self.raw(change))
    def test_native_hash_oracle(self):
        h=r.native_hash
        self.assertEqual([h.sip(h.vec([])),h.sip(h.vec([1,2,3])),h.sip(h.mapping({'a':1,'b':2})),h.sip(h.ir_vector([[1,2,3,4,5]]))],
                         [13646096770106105413,1561758979349565031,6782827763378956021,11714817560547373665])
    def test_omitted_parameter_component(self):
        def change(h):
            h['parts']['params']['M#m']=123
            h['components']['params']['M#m']=['M#m[0]']
        with self.assertRaises(ValueError): r.load(self.raw(change))
    def test_omitted_binding_component(self):
        def change(h):
            h['parts']['controller_bindings']['M#m']=123
            h['components']['controller_bindings']['M#m']=['M#m:binding:x']
        with self.assertRaises(ValueError): r.load(self.raw(change))
    def test_partial_ir(self):
        with self.assertRaises(ValueError): r.load(self.raw(lambda h:h.update(ir=[[1,0,1,2,3]])))
    def test_exact_table_hash(self):
        def change(h): h['parts']['returns']['M#m']=123
        row={'part':'returns','key':'M#m','hash':124,'native_ty':v.INT}
        with self.assertRaises(ValueError): r.load(self.raw(change,[row]))
    def test_unchanged_missing_provenance(self):
        row={'part':'returns','key':'M#m','hash':123,'native_ty':{'kind':'untyped'}}
        def change(h): h['parts']['returns']['M#m']=123
        with self.assertRaises(ValueError): r.load(self.raw(change,[row]))
    def test_provenance_loss_with_n(self):
        before=v.union({'kind':'array','elem':v.G},{'kind':'array','elem':v.U})
        after={'kind':'array','elem':v.U}
        self.assertEqual(r.relation(after,before,ndedup=True),'violation')
    def test_pending_loss_with_n(self):
        before=v.union({'kind':'array','elem':v.G},{'kind':'array','elem':v.P})
        self.assertEqual(r.relation({'kind':'array','elem':v.G},before,ndedup=True),'violation')
    def test_unknown_precedes_compound_failure(self):
        self.assertEqual(r.relation({'kind':'tuple','elems':[v.STR,{'kind':'untyped'}]},
                                    {'kind':'tuple','elems':[v.INT,v.U]}),'unknown')
    def result(self, mutate=None, **kwargs):
        store,pins,kpins,targets=v.fixture()
        if mutate: mutate(store)
        native=Path(tempfile.mkdtemp(dir=D/'tmp'));v.write_native(native)
        return v.evaluate(store,pins,kpins,targets,native,scope='campfire',**kwargs)
    def test_malformed_boundary_without_value_change(self):
        def mutate(store):
            for s in v.S:
                store.data['DS','campfire',s+'-v1-a1']['boundary'][('returns','Bad#m')]={'ty':{'kind':'union','variants':42}}
        self.assertTrue(self.result(mutate)['family_verdicts']['A'].startswith('INCONCLUSIVE'))
    def test_family_guard(self):
        def broken(*args): raise ValueError('probe')
        with patch.object(v,'direction',broken):
            result=self.result()
        for family in ('A','N','AN'): self.assertTrue(result['family_verdicts'][family].startswith('INCONCLUSIVE'))
    def test_mandatory_record_inventory(self):
        with patch.object(v,'direction',lambda *args:[]):
            result=self.result()
        for family in ('A','N','AN'): self.assertTrue(result['family_verdicts'][family].startswith('INCONCLUSIVE'))
    def test_changed_same_census_event_is_killed(self):
        def mutate(store): store.data['KN','campfire','unset-v1-a1']['census']['events'][0]='replacement-event'
        self.assertEqual(self.result(mutate)['family_verdicts']['N'],'KILLED')
    def test_n_cannot_change_ir_decision_note(self):
        def mutate(store):
            for schedule in v.S:
                cell=store.data['N','campfire',schedule+'-v1-a1']
                cell['rows'][('returns','K#k')]['decisions']='changed'
        self.assertEqual(self.result(mutate)['family_verdicts']['N'],'KILLED')
    def test_event_transition_identity_accepts_only_preserving_coalescing(self):
        before=v.union({'kind':'array','elem':v.G},{'kind':'array','elem':v.U},v.NIL)
        after=v.union({'kind':'array','elem':{'kind':'untyped','reasons':['Gradual','Unresolved']}},v.NIL)
        self.assertEqual(r.normalize_n(before),r.normalize_n(after))
        self.assertNotEqual(r.normalize_n(before),r.normalize_n(v.union({'kind':'array','elem':v.U},v.NIL)))
    def test_legal_n_merge_both_audits(self):
        before=v.union({'kind':'array','elem':v.G},{'kind':'array','elem':v.U},v.NIL)
        after=v.union({'kind':'array','elem':{'kind':'untyped','reasons':['Gradual','Unresolved']}},v.NIL)
        for audit in (0,1): self.assertEqual(r.relation(after,before,ndedup=True),'equal',audit)

if __name__=='__main__': unittest.main(verbosity=2)
