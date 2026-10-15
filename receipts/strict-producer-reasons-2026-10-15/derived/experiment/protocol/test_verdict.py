"""Synthetic regressions for the second card check; no analyzer executions."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import verdict as v

F = v.F
PIN = F / 'agents/storage-repair-five-apps/evidence/spine-main-a5d73fdf-v1'
REPORT = json.loads((PIN / 'campfire/ownership-on/on/unset/report.json').read_text())


def make_cell():
    report = copy.deepcopy(REPORT)
    return {'valid': True, 'directory': '/synthetic', 'report': report, 'observations': {
        'value_digests': copy.deepcopy(report['digest']), 'reason_rows': {},
        'reason_census': copy.deepcopy(report['census']), 'loops': copy.deepcopy(report['loops']),
        'verify': copy.deepcopy(report['verify']),
        'law_violation_counts': {'producer_evidence_0': {'parameter_losses_by_kind': {}}}}}


def inv(a, b=None, setting='unset-v1-a1', control_gate=False, absolute=True):
    data = {'C': {'campfire/' + setting: b or a}, 'SK': {'campfire/' + setting: a}}
    with patch.object(v, 'records', side_effect=lambda cache, label: data[label]), \
         patch.object(v, 'report_json', side_effect=lambda c: c['report']):
        return v.invariants(F, 'SK', 'C', [setting], control_gate=control_gate, absolute=absolute)[0]


class VerdictTests(unittest.TestCase):
    def test_complete_invariants_pass(self):
        self.assertEqual(inv(make_cell(), control_gate=True)['status'], 'pass')

    def test_control_absolute_loops_and_counters(self):
        for loop in v.LOOPS:
            a = make_cell()
            a['observations']['loops'][loop]['end'] = 'cap'
            self.assertEqual(inv(a, control_gate=True)['status'], 'fail')
            self.assertEqual(inv(a, absolute=False)['status'], 'pass')
        for key in ('cap_hits', 'frozen_units', 'budget_exhausted', 'fold_budget_cuts'):
            a = make_cell()
            if key == 'fold_budget_cuts':
                a['report']['fold']['expansion']['budget_cuts'] = 1
            else:
                a['report']['worklist']['engine'][key] = 1
            self.assertEqual(inv(a, control_gate=True)['status'], 'fail')
            self.assertEqual(inv(a, absolute=False)['status'], 'pass')

    def test_missing_mandatory_fields(self):
        mutations = [
            lambda a: a['observations'].pop('loops'),
            lambda a: a['observations']['loops'].pop('production'),
            lambda a: a['observations'].__setitem__('verify', []),
            lambda a: a['observations']['verify'][0]['moved'].pop('ir'),
            lambda a: a['observations']['law_violation_counts']['producer_evidence_0'].pop('parameter_losses_by_kind'),
            lambda a: a['observations'].pop('law_violation_counts'),
            lambda a: a['report']['worklist'].__setitem__('engine', {}),
            lambda a: a['report'].__setitem__('fold', {}),
            lambda a: a['observations']['reason_census']['untyped_by_provenance'].pop('pending'),
        ]
        for mutate in mutations:
            a = make_cell()
            mutate(a)
            self.assertEqual(inv(a)['status'], 'unavailable')
        # V0/A0 does not require verify or audit receipts.
        a = make_cell()
        a['observations'].pop('verify')
        a['observations'].pop('law_violation_counts')
        self.assertEqual(inv(a, setting='unset-v0-a0')['status'], 'pass')

    def test_unavailable_precedes_failure_campfire(self):
        a = make_cell()
        a['observations']['verify'][0]['moved']['ir'] = 1
        a['observations'].pop('law_violation_counts')
        check = inv(a)
        self.assertIn('verify movement', check['detail']['problems'])
        self.assertEqual(v.decide([check]), 'INCONCLUSIVE (unavailable mandatory evidence)')
        a = make_cell()
        a['observations']['verify'][0]['moved']['ir'] = 1
        self.assertEqual(v.decide([inv(a)]), 'KILLED')

    def populate_native(self, d):
        for f in ('000', '100', '010', '110', '001', '111'):
            stubs, xfer, cong = map(int, f)
            got = {'flags': {'stubs': stubs, 'xfer': xfer, 'congruent': cong},
                   'strictness': dict.fromkeys(('p1','p2','p3','p4','p5','p6','p7b'), 0 if xfer else 1),
                   'deferred_var': {'p7': 1}, 'identity': {'p8': 0 if xfer else 1,
                   'p9': 0 if stubs or xfer else 1}, 'equality': {'p10_distinguishes': bool(cong)}}
            (d / ('harness-' + f + '.log')).write_text('test analyze::body::provenance_strict_producer_strictness ... provenance-STRICT ' + json.dumps(got) + '\nok\n')
            (d / ('harness-' + f + '.exit')).write_text('0\n')
        for x in (0, 1):
            for test in ('storage_extended_laws', 'provenance_lineage_factorial'):
                stem = 'laws-x%d-%s' % (x, test)
                (d / (stem + '.log')).write_text((PIN / ('receipts/n1-' + test + '.log')).read_text())
                (d / (stem + '.exit')).write_text('0\n')

    def test_cargo_prefix_and_recorded_law_receipts(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            self.populate_native(d)
            results = v.native(d)
            self.assertEqual(len(results), 10)
            self.assertTrue(all(r['status'] == 'pass' for r in results), results)

    def test_malformed_missing_duplicate_native(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            self.populate_native(d)
            for malformed in ('provenance-STRICT {broken\n', 'provenance-STRICT []\n', 'provenance-STRICT {}\n', ''):
                (d / 'harness-000.log').write_text(malformed)
                self.assertEqual(v.native(d)[0]['status'], 'unavailable')
            self.populate_native(d)
            p = d / 'harness-000.log'
            p.write_text(p.read_text() * 2)
            self.assertEqual(v.native(d)[0]['status'], 'unavailable')
            for obj in ({'seed_ok': True, 'no_early_never': True},
                        {'counts': None, 'seed_ok': True, 'no_early_never': True}):
                (d / 'laws-x0-storage_extended_laws.log').write_text('STORAGE-EXTENDED ' + json.dumps(obj) + '\n')
                self.assertEqual(v.native(d)[6]['status'], 'unavailable')
            (d / 'laws-x0-storage_extended_laws.log').write_text('STORAGE-EXTENDED {broken\n')
            self.assertEqual(v.native(d)[6]['status'], 'unavailable')

    def general_data(self):
        return {arm: {app + '/' + setting: make_cell()
                      for app in ('forem', 'chatwoot', 'mastodon', 'discourse')
                      for setting in v.V0 + (v.V1 if app != 'discourse' else ['unset-v1-a1'])}
                for arm in ('C', 'S', 'SK')}

    def general(self, data):
        with patch.object(v, 'records', side_effect=lambda cache, label: data[label]), \
             patch.object(v, 'report_json', side_effect=lambda c: c['report']), \
             patch.object(v.obs, 'observed', side_effect=lambda c, field: c['observations'].get(field)):
            return v.general(SimpleNamespace(cache_root=F), {arm: arm for arm in data})

    def test_report_only_S_never_changes_generalization(self):
        data = self.general_data()
        self.assertEqual(self.general(data)['verdict'], 'GENERALIZES')
        data['S'] = {}
        result = self.general(data)
        self.assertEqual(result['verdict'], 'GENERALIZES')
        self.assertTrue(result['apps']['forem']['report_missing'])

    def test_general_known_failure_precedes_missing(self):
        data = self.general_data()
        data['SK']['forem/unset-v0-a0']['observations']['value_digests']['ir'] = 'changed'
        data['SK'].pop('forem/1-v0-a0')
        self.assertEqual(self.general(data)['apps']['forem']['status'], 'fail')

    def test_general_parity_unset_stable_and_scheduled_v1(self):
        data = self.general_data()
        data['SK']['forem/repeat-v1-a1']['observations']['value_digests']['ir'] = 'changed'
        result = self.general(data)
        self.assertIn('SK value parity repeat-v1-a1', result['apps']['forem']['problems'])

    def test_main_malformed_artifact_emits_verdict(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / 'verdict.json'
            with patch.object(v, 'campfire', side_effect=json.JSONDecodeError('bad', '', 0)):
                self.assertEqual(v.main(['campfire', '--cache-root', tmp, '--native', tmp, '--out', str(out)]), 0)
            self.assertTrue(json.loads(out.read_text())['verdict'].startswith('INCONCLUSIVE'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
