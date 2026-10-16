#!/usr/bin/env python3
"""Tests for the literal-transfer verdict. Run: python3 -I -m unittest discover -s phase2/literal-current-writes/card -p 'test_verdict.py'"""
import copy
import hashlib
import importlib.util
import itertools
import json
import os
import random
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('literal_verdict', os.path.join(HERE, 'verdict.py'))
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

S = V.SCHEDULES
VAR = {'kind': 'var', 'var': 0}
UNT = {'kind': 'untyped'}
STR = {'kind': 'str'}
NIL = {'kind': 'nil'}
INT = {'kind': 'int'}


def arr(e):
    return {'kind': 'array', 'elem': e}


def union(*xs):
    return {'kind': 'union', 'variants': list(xs)}


def val(ty, h=None, note=1):
    return {'ty': ty, 'hash': h if h is not None else json.dumps(ty, sort_keys=True), 'note': note}


IG = 'Webhooks::InstagramController#channel_meta_app_secrets'
WA = 'Webhooks::WhatsappController#channel_meta_app_secrets'
SRC = '/in/chatwoot/app/controllers/concerns/meta_token_verify_concern.rb'


def ir_key(decl, path, start=1586, end=1794):
    head = json.dumps({'declaration': decl, 'kind': 'Seq', 'source': SRC, 'span': {'end': end, 'file': 932, 'start': start}},
                      separators=(',', ':'), sort_keys=True)
    return head + ':occurrence:0:' + path


def obs(app, sched, setting, digest_tag='x', settled=True, verify_ir=0):
    v1 = setting.startswith('v1')
    return {
        'value_digests': {t: '%s-%s-%s' % (app, t, digest_tag) for t in V.TABLES},
        'diagnostics': {'warning/gradual_untyped': 10},
        'reason_census': {'typed': 100, 'untyped_anywhere': 5},
        'reason_rows': {'count': 5, 'file': 'reason-rows.json', 'sha256': '%s-%s-rr' % (app, setting)},
        'loops': {'production': {'end': 'settled' if settled else 'cap', 'round': 3},
                  'views_and_tests': {'end': 'settled', 'round': 1}, 'absorb': {'end': 'settled', 'round': 1}},
        'verify': [{'loop': 'production', 'moved': {t: (verify_ir if t == 'ir' else 0) for t in V.TABLES}},
                   {'loop': 'absorb', 'moved': {t: 0 for t in V.TABLES}}] if v1 else None,
        'exit_code': 0,
        'law_violation_counts': {'producer_evidence_0': {'parameter_output_origin_losses': 6}} if setting.endswith('a1') else None,
    }


class World(object):
    """An all-good bundle on disk; tests mutate `self.*` and call write()."""

    def __init__(self, root):
        self.root = root
        self.cells = {}  # label -> {cell: observations or None}
        for prof, label_ref in (('on', 'ref_on'), ('off', 'ref_off')):
            for app, settings in V.APP_SETTINGS.items():
                for p, setting in settings:
                    if p != prof:
                        continue
                    for s in S:
                        key = '%s/%s-%s' % (app, s, setting)
                        base = obs(app, s, setting)
                        self.cells.setdefault(label_ref, {})[key] = copy.deepcopy(base)
                        self.cells.setdefault('C_' + prof, {})[key] = copy.deepcopy(base)
                        lobs = copy.deepcopy(base)
                        if app != 'campfire':
                            lobs['value_digests']['ir'] = app + '-ir-L'
                        self.cells.setdefault('L_' + prof, {})[key] = lobs
        self.purity = [{'case': c, 'rule': r, 'equal': not (r == 'legacy' and c in V.PREDICTED_LEGACY_FAIL)}
                       for c in V.CASES for r in ('legacy', 'law')]
        self.suite_off = 'running 1250 tests\ntest result: ok. 1250 passed; 0 failed; 26 ignored; 0 measured\n'
        self.suite_on = self.suite_off
        lit_c = {'unset': val(arr(UNT)), '1': val(arr(VAR)), '2': val(arr(UNT)), 'repeat': val(arr(UNT))}
        lit_l = {s: val(arr(VAR)) for s in S}
        self.rows = {
            ('chatwoot', 'v1-a1'): [
                {'part': 'ir', 'key': ir_key(IG, '1/0'), 'span': {'start': 1629, 'end': 1631, 'file': 932}, 'C': lit_c, 'L': lit_l},
                {'part': 'returns', 'key': IG, 'span': None, 'C': copy.deepcopy(lit_c), 'L': copy.deepcopy(lit_l)},
                {'part': 'ir', 'key': ir_key('Other#m', '0'), 'span': {'start': 1, 'end': 2, 'file': 1},
                 'C': {'unset': val(STR), '1': val(INT), '2': val(STR), 'repeat': val(STR)},
                 'L': {'unset': val(STR), '1': val(INT), '2': val(STR), 'repeat': val(STR)}},
            ],
            ('mastodon', 'v1-a1'): [
                {'part': 'ir', 'key': ir_key('Mast#m', '0'), 'span': {'start': 5, 'end': 9, 'file': 3},
                 'C': {'unset': val(arr(UNT)), '1': val(arr(VAR)), '2': val(arr(UNT)), 'repeat': val(arr(UNT))},
                 'L': {s: val(arr(VAR)) for s in S}},
                {'part': 'ir', 'key': ir_key('Mast#m', '1'), 'span': {'start': 10, 'end': 12, 'file': 3},
                 'C': {s: val(arr(UNT)) for s in S},
                 'L': {'unset': val(arr(UNT)), '1': val(arr(VAR)), '2': val(arr(UNT)), 'repeat': val(arr(UNT))}},
            ],
            ('forem', 'v1-a1'): [
                {'part': 'ir', 'key': ir_key('Forem#m', '0'), 'span': {'start': 1, 'end': 3, 'file': 2},
                 'C': {'unset': val(STR), '1': val(INT), '2': val(STR), 'repeat': val(STR)},
                 'L': {'unset': val(STR), '1': val(INT), '2': val(STR), 'repeat': val(STR)}},
            ],
        }
        self.rows[('chatwoot', 'v0-a0')] = copy.deepcopy(self.rows[('chatwoot', 'v1-a1')])
        self.reconciled = {k: True for k in self.rows}
        self.keys = {'webhook_declarations': [IG, WA], 'apps': {
            'chatwoot': {'rows': [{'part': 'ir', 'key': ir_key(IG, '1/0')}, {'part': 'returns', 'key': IG}]},
            'mastodon': {'rows': [{'part': 'ir', 'key': ir_key('Mast#m', '0')}]},
            'forem': {'rows': []}}}
        self.witness_maps = [os.path.join(HERE, 'witness', 'webhook_map.json'),
                             os.path.join(HERE, 'witness', 'featured_tags_map.json')]
        self.omit = set()
        self.frozen_override = {}

    def write(self):
        bundle = {'condition': 'test', 'labels': {}, 'native': {}, 'rows': {}}
        for label, cells in self.cells.items():
            if label in self.omit:
                continue
            d = os.path.join(self.root, 'labels', label)
            os.makedirs(d, exist_ok=True)
            refs = {}
            for key, o in cells.items():
                rp = os.path.join(d, key.replace('/', '_') + '.json')
                with open(rp, 'w') as f:
                    json.dump({'valid': o is not None, 'observations': o}, f)
                refs[key] = {'valid': o is not None, 'result': rp}
            with open(os.path.join(d, 'label.json'), 'w') as f:
                json.dump({'cells': refs}, f)
            bundle['labels'][label] = os.path.join(d, 'label.json')
        if 'purity' not in self.omit:
            p = os.path.join(self.root, 'purity.json')
            with open(p, 'w') as f:
                json.dump({'cases': self.purity}, f)
            bundle['native']['purity'] = p
        for name in ('suite_off', 'suite_on'):
            if name in self.omit:
                continue
            p = os.path.join(self.root, name + '.log')
            with open(p, 'w') as f:
                f.write(getattr(self, name))
            bundle['native'][name] = p
        for (app, o), rows in self.rows.items():
            if (app, o) in self.omit:
                continue
            rp = os.path.join(self.root, 'rows-%s-%s.jsonl' % (app, o))
            with open(rp, 'w') as f:
                for r in rows:
                    f.write(json.dumps(r) + '\n')
            cp = os.path.join(self.root, 'reconcile-%s-%s.json' % (app, o))
            ok = self.reconciled[(app, o)]
            with open(cp, 'w') as f:
                json.dump({'complete': ok, 'cells': {'%s/%s' % (arm, s): {'fingerprint_matches_native': ok}
                                                     for arm in ('C', 'L') for s in S}}, f)
            bundle['rows'].setdefault(app, {})[o] = {'file': rp, 'reconciled': cp}
        if 'keys' not in self.omit:
            kp = os.path.join(self.root, 'keys.json')
            with open(kp, 'w') as f:
                json.dump(self.keys, f)
            bundle['keys'] = kp
        bundle['witness_maps'] = [] if 'witness' in self.omit else self.witness_maps
        if 'frozen' not in self.omit:
            card = os.path.dirname(HERE)
            files = [os.path.join(card, 'source-equivalence.json')] + [os.path.join(HERE, n) for n in (
                'verdict.py', 'test_verdict.py', 'schedule-row-literal-keys.json', 'witness/webhook_secrets.rb',
                'witness/webhook_secrets.json', 'witness/webhook_map.json', 'witness/featured_tags.rb',
                'witness/featured_tags.json', 'witness/featured_tags_map.json', 'profiles/c-on.json', 'profiles/l-on.json',
                'profiles/c-off.json', 'profiles/l-off.json', 'claims/campfire-on.json', 'claims/campfire-off.json')]
            builder = os.path.abspath(os.path.join(HERE, 'recorded-builder'))
            files += [os.path.join(builder, 'literal_rows.py'),
                      os.path.join(builder, 'repo/src/analyze/body/literal_transfer_purity.rs')]
            lp = os.path.join(self.root, 'frozen.sha256')
            with open(lp, 'w') as f:
                for fp in files:
                    with open(fp, 'rb') as g:
                        digest = hashlib.sha256(g.read()).hexdigest()
                    f.write('%s  %s\n' % (self.frozen_override.get(os.path.basename(fp), digest), os.path.relpath(fp, card)))
            bundle['frozen'] = {'list': lp, 'root': card}
        path = os.path.join(self.root, 'bundle.json')
        with open(path, 'w') as f:
            json.dump(bundle, f)
        return path


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.w = World(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_stage(self, stage='final'):
        return V.evaluate(self.w.write(), stage)

    def status(self, report, prefix):
        found = [c['status'] for c in report['criteria'] if c['name'].startswith(prefix)]
        self.assertEqual(len(found), 1, prefix)
        return found[0]


class Outcomes(Base):
    def test_occurrence_path_selects_the_probe(self):
        decl = 'ProcessHashtagsService#update_featured_tags!'
        key_int = ir_key(decl, '2/2/0/1/1/1/0', 516, 1029)
        key_tag = ir_key(decl, '2/2/0/1/1/1/0/0', 516, 1029)
        tag = {'kind': 'class', 'id': 'Tag', 'args': []}
        rows = [
            {'part': 'ir', 'key': key_int, 'span': {'start': 691, 'end': 694, 'file': 697},
             'C': {s: val(UNT) for s in S}, 'L': {s: val(INT) for s in S}},
            {'part': 'ir', 'key': key_tag, 'span': {'start': 691, 'end': 694, 'file': 697},
             'C': {s: val(UNT) for s in S}, 'L': {s: val(union(tag, NIL)) for s in S}},
        ]
        self.w.rows[('mastodon', 'v1-a1')].extend(rows)
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'CONFIRMED', r['reasons'])
        self.w.rows[('mastodon', 'v1-a1')][-1]['L'] = {s: val(INT) for s in S}
        self.assertEqual(self.run_stage()['outcome'], 'KILLED')

    def test_good_world_is_confirmed(self):
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'CONFIRMED', r['reasons'])

    def test_good_world_passes_campfire_stage(self):
        r = self.run_stage('campfire')
        self.assertEqual(r['outcome'], 'PASSED', r['reasons'])
        self.assertFalse([c for c in r['criteria'] if c['name'].startswith(('WEBHOOK_ORDER', 'RUNTIME_ADMISSION', 'V1'))])

    def test_campfire_stage_never_confirms(self):
        r = self.run_stage('campfire')
        self.assertNotEqual(r['outcome'], 'CONFIRMED')

    def test_changed_frozen_input_is_inconclusive(self):
        self.w.frozen_override['verdict.py'] = '0' * 64
        r = self.run_stage('campfire')
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')
        self.assertEqual(self.status(r, 'V3'), V.NOT_MET)

    def test_missing_frozen_list_is_inconclusive(self):
        self.w.omit.add('frozen')
        self.assertEqual(self.run_stage()['outcome'], 'INCONCLUSIVE')

    def test_missing_purity_is_inconclusive(self):
        self.w.omit.add('purity')
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')
        self.assertEqual(self.status(r, 'LITERAL_PURITY'), V.UNAVAILABLE)

    def test_partial_purity_is_inconclusive(self):
        self.w.purity = [e for e in self.w.purity if e['case'] != 'K']
        self.assertEqual(self.run_stage()['outcome'], 'INCONCLUSIVE')

    def test_law_failure_kills(self):
        for e in self.w.purity:
            if e['case'] == 'H' and e['rule'] == 'law':
                e['equal'] = False
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'KILLED')
        self.assertIn('LITERAL_PURITY native purity census', r['reasons'])

    def test_legacy_split_mismatch_kills(self):
        for e in self.w.purity:
            if e['case'] == 'A' and e['rule'] == 'legacy':
                e['equal'] = True
        self.assertEqual(self.run_stage('campfire')['outcome'], 'KILLED')

    def test_campfire_difference_kills_both_stages(self):
        self.w.cells['L_on']['campfire/2-v0-a0']['reason_rows']['sha256'] = 'other'
        self.assertEqual(self.run_stage('campfire')['outcome'], 'KILLED')
        self.assertEqual(self.run_stage('final')['outcome'], 'KILLED')

    def test_campfire_off_profile_is_checked(self):
        self.w.cells['L_off']['campfire/repeat-v1-a1']['diagnostics'] = {'warning/gradual_untyped': 11}
        self.assertEqual(self.run_stage('campfire')['outcome'], 'KILLED')

    def test_campfire_cell_missing_is_inconclusive(self):
        del self.w.cells['L_on']['campfire/1-v1-a1']
        r = self.run_stage('campfire')
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')
        self.assertEqual(self.status(r, 'CONTROL_EQUALITY'), V.UNAVAILABLE)

    def test_invalid_cell_is_inconclusive(self):
        self.w.cells['L_on']['campfire/1-v1-a1'] = None
        self.assertEqual(self.run_stage('campfire')['outcome'], 'INCONCLUSIVE')

    def test_control_unlike_spine_is_inconclusive_not_killed(self):
        self.w.cells['C_on']['chatwoot/unset-v1-a1']['diagnostics'] = {'warning/gradual_untyped': 9}
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')
        self.assertEqual(self.status(r, 'V0'), V.NOT_MET)

    def test_kill_dominates_validity_gap(self):
        self.w.cells['C_on']['chatwoot/unset-v1-a1']['diagnostics'] = {'warning/gradual_untyped': 9}
        self.w.cells['L_on']['campfire/unset-v1-a1']['value_digests']['ir'] = 'changed'
        self.assertEqual(self.run_stage()['outcome'], 'KILLED')

    def test_missing_reference_label_is_inconclusive(self):
        self.w.omit.add('ref_off')
        self.assertEqual(self.run_stage('campfire')['outcome'], 'INCONCLUSIVE')

    def test_webhook_still_varying_kills(self):
        self.w.rows[('chatwoot', 'v0-a0')][0]['L']['2'] = val(arr(UNT))
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'KILLED')
        self.assertIn('WEBHOOK_ORDER Chatwoot webhook family is schedule-equal under L', r['reasons'])

    def test_webhook_input_variance_makes_it_uninformative(self):
        self.w.rows[('chatwoot', 'v1-a1')].append(
            {'part': 'params', 'key': IG + '[0]', 'span': None,
             'C': {s: val(STR) for s in S},
             'L': {'unset': val(STR), '1': val(INT), '2': val(STR), 'repeat': val(STR)}})
        r = self.run_stage()
        self.assertEqual(self.status(r, 'WEBHOOK_ORDER'), V.UNAVAILABLE)
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')

    def test_webhook_input_variance_does_not_hide_a_kill_elsewhere(self):
        self.w.rows[('chatwoot', 'v1-a1')].append(
            {'part': 'params', 'key': IG + '[0]', 'span': None,
             'C': {s: val(STR) for s in S},
             'L': {'unset': val(STR), '1': val(INT), '2': val(STR), 'repeat': val(STR)}})
        self.w.rows[('chatwoot', 'v0-a0')][0]['L']['2'] = val(arr(UNT))
        self.assertEqual(self.run_stage()['outcome'], 'KILLED')

    def test_webhook_power_at_one_observer_suffices(self):
        for row in self.w.rows[('chatwoot', 'v0-a0')][:2]:
            row['C'] = {s: val(arr(VAR)) for s in S}
        r = self.run_stage()
        self.assertEqual(self.status(r, 'WEBHOOK_ORDER'), V.MET)
        self.assertEqual(r['outcome'], 'CONFIRMED', r['reasons'])

    def test_webhook_new_variance_without_power_still_kills(self):
        for o in ('v1-a1', 'v0-a0'):
            for row in self.w.rows[('chatwoot', o)][:2]:
                row['C'] = {s: val(arr(VAR)) for s in S}
        self.w.rows[('chatwoot', 'v0-a0')][0]['L'] = {'unset': val(arr(VAR)), '1': val(arr(UNT)),
                                                      '2': val(arr(VAR)), 'repeat': val(arr(VAR))}
        self.assertEqual(self.run_stage()['outcome'], 'KILLED')

    def test_webhook_not_varying_in_control_is_inconclusive(self):
        for o in ('v1-a1', 'v0-a0'):
            for row in self.w.rows[('chatwoot', o)][:2]:
                row['C'] = {s: val(arr(UNT)) for s in S}
        r = self.run_stage()
        self.assertEqual(self.status(r, 'WEBHOOK_ORDER'), V.UNAVAILABLE)
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')

    def test_unwitnessed_narrowing_is_inconclusive(self):
        self.w.rows[('mastodon', 'v1-a1')][0]['L'] = {s: val(arr(STR)) for s in S}
        r = self.run_stage()
        self.assertEqual(self.status(r, 'RUNTIME_ADMISSION'), V.UNAVAILABLE)
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')

    def test_witnessed_sound_narrowing_confirms(self):
        sound = val(arr(union(STR, NIL)))
        for o in ('v1-a1', 'v0-a0'):
            self.w.rows[('chatwoot', o)][0]['L'] = {s: copy.deepcopy(sound) for s in S}
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'CONFIRMED', r['reasons'])

    def test_witnessed_unsound_narrowing_kills(self):
        for o in ('v1-a1', 'v0-a0'):
            self.w.rows[('chatwoot', o)][0]['L'] = {s: val(arr(STR)) for s in S}
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'KILLED')
        self.assertEqual(self.status(r, 'RUNTIME_ADMISSION'), V.NOT_MET)

    def test_unsound_incomparable_change_kills_even_if_control_was_unsound(self):
        for o in ('v1-a1', 'v0-a0'):
            row = self.w.rows[('chatwoot', o)][0]
            row['C'] = {'unset': val(arr(INT)), '1': val(arr(VAR)), '2': val(arr(INT)), 'repeat': val(arr(INT))}
            row['L'] = {s: val(arr(STR)) for s in S}
        r = self.run_stage()
        self.assertEqual(self.status(r, 'RUNTIME_ADMISSION'), V.NOT_MET)
        self.assertEqual(r['outcome'], 'KILLED')

    def test_unchanged_unsound_value_is_preexisting(self):
        for o in ('v1-a1', 'v0-a0'):
            row = self.w.rows[('chatwoot', o)][1]
            row['C'] = {s: val(arr(INT)) for s in S}
            row['L'] = {s: val(arr(INT)) for s in S}
        r = self.run_stage()
        literal_check_5 = [c for c in r['criteria'] if c['name'].startswith('RUNTIME_ADMISSION')][0]
        self.assertEqual(literal_check_5['status'], V.MET)
        self.assertTrue(literal_check_5['detail']['preexisting_unsound'])

    def test_same_print_and_widening_need_no_witness(self):
        self.w.rows[('forem', 'v1-a1')].append(
            {'part': 'ir', 'key': ir_key('Forem#n', '0'), 'span': {'start': 3, 'end': 4, 'file': 2},
             'C': {s: val(arr(STR)) for s in S}, 'L': {s: val(arr(union(STR, INT))) for s in S}})
        self.assertEqual(self.run_stage()['outcome'], 'CONFIRMED')

    def test_unknown_comparison_needs_a_witness(self):
        rec1, rec2 = {'kind': 'rec', 'slot': 'a'}, {'kind': 'rec', 'slot': 'b'}
        self.w.rows[('forem', 'v1-a1')].append(
            {'part': 'ir', 'key': ir_key('Forem#n', '0'), 'span': {'start': 3, 'end': 4, 'file': 2},
             'C': {s: val(rec1) for s in S}, 'L': {s: val(rec2) for s in S}})
        self.assertEqual(self.run_stage()['outcome'], 'INCONCLUSIVE')

    def test_presence_change_is_recorded_only(self):
        self.w.rows[('forem', 'v1-a1')].append(
            {'part': 'side_table', 'key': 'slot-x', 'span': None,
             'C': {s: val(STR) for s in S}, 'L': {s: None for s in S}})
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'CONFIRMED')
        pres = [x for x in r['recorded_predictions'] if x['name'] == 'forem presence changes'][0]
        self.assertEqual(pres['result'], 'miss')

    def test_loop_cap_kills(self):
        self.w.cells['L_on']['mastodon/2-v1-a1']['loops']['production']['end'] = 'cap'
        self.assertEqual(self.run_stage()['outcome'], 'KILLED')

    def test_cap_in_both_arms_is_not_a_kill(self):
        for arm in ('C_on', 'L_on', 'ref_on'):
            self.w.cells[arm]['mastodon/2-v1-a1']['loops']['production']['end'] = 'cap'
        self.assertEqual(self.run_stage()['outcome'], 'CONFIRMED')

    def test_verify_rise_outside_campfire_is_recorded(self):
        for schedule in ('unset', 'repeat'):
            self.w.cells['L_on']['forem/'+schedule+'-v1-a1']['verify'][0]['moved']['ir'] = 2
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'CONFIRMED', r['reasons'])
        rec = [x for x in r['recorded_predictions'] if x['name'] == 'forem verification movement under L'][0]
        self.assertEqual(rec['result'], 'miss')

    def test_verify_change_on_campfire_kills_through_literal_check_3(self):
        self.w.cells['L_on']['campfire/1-v1-a1']['verify'][0]['moved']['ir'] = 1
        r = self.run_stage('campfire')
        self.assertEqual(r['outcome'], 'KILLED')
        self.assertIn('CONTROL_EQUALITY Campfire: L equals C on every field', r['reasons'])

    def test_value_only_under_l_needs_a_witness(self):
        self.w.rows[('forem', 'v1-a1')].append(
            {'part': 'side_table', 'key': 'slot-new', 'span': None,
             'C': {s: None for s in S}, 'L': {s: val(arr(STR)) for s in S}})
        r = self.run_stage()
        self.assertEqual(self.status(r, 'RUNTIME_ADMISSION'), V.UNAVAILABLE)
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')

    def test_untyped_value_only_under_l_needs_no_witness(self):
        self.w.rows[('forem', 'v1-a1')].append(
            {'part': 'side_table', 'key': 'slot-new', 'span': None,
             'C': {s: None for s in S}, 'L': {s: val(UNT) for s in S}})
        self.assertEqual(self.run_stage()['outcome'], 'CONFIRMED')

    def test_missing_probe_in_witness_is_unavailable_not_a_crash(self):
        bad = os.path.join(self.tmp, 'bad_map.json')
        with open(os.path.join(HERE, 'witness', 'webhook_map.json')) as f:
            m = json.load(f)
        m['witness'] = os.path.join(HERE, 'witness', 'webhook_secrets.json')
        m['by_span'][2]['probes'] = ['no_such_probe']
        with open(bad, 'w') as f:
            json.dump(m, f)
        self.w.witness_maps = [bad]
        r = self.run_stage()
        self.assertEqual(self.status(r, 'RUNTIME_ADMISSION'), V.UNAVAILABLE)
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')

    def test_malformed_verify_outside_campfire_makes_d6_unavailable(self):
        self.w.cells['L_on']['mastodon/unset-v1-a1']['verify'] = {'oops': 1}
        r = self.run_stage()
        self.assertEqual(self.status(r, 'D6'), V.UNAVAILABLE)
        self.assertEqual(r['outcome'], 'INCONCLUSIVE', r['reasons'])
        rec = [x for x in r['recorded_predictions'] if x['name'] == 'mastodon verification movement under L'][0]
        self.assertEqual(rec['result'], 'unavailable')

    def test_malformed_verify_on_campfire_is_not_a_crash(self):
        for arm in ('C_on', 'L_on', 'ref_on'):
            for s in S:
                self.w.cells[arm]['campfire/%s-v1-a1' % s]['verify'] = {'oops': 1}
        r = self.run_stage('campfire')
        self.assertIn(r['outcome'], ('INCONCLUSIVE', 'PASSED'))
        self.assertNotEqual(r['outcome'], 'KILLED')

    def test_row_that_is_a_list_is_unavailable(self):
        self.w.rows[('forem', 'v1-a1')].append(['not', 'a', 'row'])
        self.assertEqual(self.run_stage()['outcome'], 'INCONCLUSIVE')

    def test_crash_exits_inconclusive(self):
        real = V.evaluate
        try:
            V.evaluate = lambda path, stage: (_ for _ in ()).throw(RuntimeError('boom'))
            self.assertEqual(V.main([self.w.write()]), 2)
        finally:
            V.evaluate = real

    def test_field_missing_from_both_arms_is_unavailable(self):
        for arm in ('C_on', 'L_on', 'ref_on'):
            self.w.cells[arm]['campfire/2-v1-a1']['law_violation_counts'] = None
        r = self.run_stage('campfire')
        self.assertEqual(self.status(r, 'CONTROL_EQUALITY'), V.UNAVAILABLE)
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')

    def test_missing_digest_table_is_unavailable(self):
        for arm in ('C_on', 'L_on', 'ref_on'):
            for s in S:
                del self.w.cells[arm]['campfire/%s-v0-a0' % s]['value_digests']['copies']
        r = self.run_stage('campfire')
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')
        self.assertEqual(self.status(r, 'CONTROL_EQUALITY'), V.UNAVAILABLE)

    def test_duplicate_census_line_is_unavailable(self):
        self.w.purity.append({'case': 'A', 'rule': 'law', 'equal': True})
        r = self.run_stage('campfire')
        self.assertEqual(self.status(r, 'LITERAL_PURITY'), V.UNAVAILABLE)

    def test_unknown_census_rule_is_unavailable(self):
        self.w.purity = [dict(e, rule='new' if e['rule'] == 'law' else e['rule']) for e in self.w.purity]
        r = self.run_stage('campfire')
        self.assertEqual(self.status(r, 'LITERAL_PURITY'), V.UNAVAILABLE)

    def test_verify_fall_is_fine(self):
        for arm in ('C_on', 'ref_on'):
            self.w.cells[arm]['mastodon/unset-v1-a1']['verify'][0]['moved']['ir'] = 1
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'CONFIRMED', r['reasons'])
        rec = [x for x in r['recorded_predictions'] if x['name'] == 'mastodon production verify ir movement'][0]
        self.assertEqual(rec['result'], 'hit')

    def test_repeat_disagreement_kills(self):
        self.w.cells['L_on']['chatwoot/repeat-v0-a0']['reason_census'] = {'typed': 99}
        self.assertEqual(self.run_stage()['outcome'], 'KILLED')

    def test_suite_failure_with_flag_kills(self):
        self.w.suite_on = 'test result: FAILED. 1249 passed; 1 failed; 26 ignored; 0 measured\n'
        self.assertEqual(self.run_stage('campfire')['outcome'], 'KILLED')

    def test_suite_failure_without_flag_is_inconclusive(self):
        self.w.suite_off = 'test result: FAILED. 1249 passed; 1 failed; 26 ignored; 0 measured\n'
        self.assertEqual(self.run_stage('campfire')['outcome'], 'INCONCLUSIVE')

    def test_suite_log_without_result_is_inconclusive(self):
        self.w.suite_on = 'error: could not compile\n'
        self.assertEqual(self.run_stage('campfire')['outcome'], 'INCONCLUSIVE')

    def test_too_few_tests_is_inconclusive(self):
        self.w.suite_off = 'test result: ok. 1200 passed; 0 failed; 26 ignored; 0 measured\n'
        self.w.suite_on = self.w.suite_off
        self.assertEqual(self.run_stage('campfire')['outcome'], 'INCONCLUSIVE')

    def test_unreconciled_rows_are_inconclusive(self):
        self.w.reconciled[('mastodon', 'v1-a1')] = False
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')
        self.assertEqual(self.status(r, 'V1'), V.UNAVAILABLE)

    def test_missing_row_file_is_inconclusive(self):
        self.w.omit.add(('forem', 'v1-a1'))
        self.assertEqual(self.run_stage()['outcome'], 'INCONCLUSIVE')

    def test_malformed_row_is_inconclusive(self):
        del self.w.rows[('forem', 'v1-a1')][0]['L']['repeat']
        self.assertEqual(self.run_stage()['outcome'], 'INCONCLUSIVE')

    def test_missing_witness_is_inconclusive(self):
        self.w.omit.add('witness')
        r = self.run_stage()
        self.assertEqual(self.status(r, 'RUNTIME_ADMISSION'), V.UNAVAILABLE)
        self.assertEqual(r['outcome'], 'INCONCLUSIVE')

    def test_missing_keys_is_inconclusive(self):
        self.w.omit.add('keys')
        self.assertEqual(self.run_stage()['outcome'], 'INCONCLUSIVE')

    def test_recorded_misses_do_not_decide(self):
        self.w.rows[('chatwoot', 'v1-a1')].append(
            {'part': 'ir', 'key': ir_key('New#m', '0'), 'span': {'start': 1, 'end': 2, 'file': 9},
             'C': {s: val(STR) for s in S}, 'L': {'unset': val(STR), '1': val(UNT), '2': val(STR), 'repeat': val(STR)}})
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'CONFIRMED', r['reasons'])
        rec = [x for x in r['recorded_predictions'] if x['name'] == 'chatwoot new varying rows under L'][0]
        self.assertEqual(rec['result'], 'miss')

    def test_recorded_predictions_hit_in_good_world(self):
        r = self.run_stage()
        got = {x['name']: x['result'] for x in r['recorded_predictions']}
        self.assertEqual(got['chatwoot matched RETURN_HELPERS keys removed'], 'hit')
        self.assertEqual(got['mastodon matched RETURN_HELPERS keys removed'], 'hit')
        self.assertEqual(got['mastodon new varying rows under L'], 'hit')
        self.assertEqual(got['forem varying rows removed'], 'hit')
        self.assertEqual(got['webhook literal prints Array[untyped] under L'], 'hit')
        self.assertEqual(got['chatwoot census untyped_anywhere at unset V1A1'], 'hit')

    def test_census_rise_is_a_recorded_miss_only(self):
        self.w.cells['L_on']['chatwoot/unset-v1-a1']['reason_census']['untyped_anywhere'] = 6
        self.w.cells['L_on']['chatwoot/repeat-v1-a1']['reason_census']['untyped_anywhere'] = 6
        r = self.run_stage()
        self.assertEqual(r['outcome'], 'CONFIRMED', r['reasons'])
        got = {x['name']: x['result'] for x in r['recorded_predictions']}
        self.assertEqual(got['chatwoot census untyped_anywhere at unset V1A1'], 'miss')

    def test_empty_bundle_is_inconclusive(self):
        p = os.path.join(self.tmp, 'empty.json')
        with open(p, 'w') as f:
            f.write('{}')
        for stage in ('campfire', 'final'):
            self.assertEqual(V.evaluate(p, stage)['outcome'], 'INCONCLUSIVE')

    def test_unreadable_bundle_exits_inconclusive(self):
        self.assertEqual(V.main([os.path.join(self.tmp, 'nope.json'), '--stage', 'final']), 2)

    def test_exit_codes(self):
        self.assertEqual(V.main([self.w.write()]), 0)
        self.w.cells['L_on']['campfire/unset-v1-a1']['exit_code'] = 1
        self.assertEqual(V.main([self.w.write()]), 1)


class CheckerCorrections(Base):
    def test_reason_only_repeat_difference_kills(self):
        self.w.cells['L_on']['chatwoot/repeat-v0-a0']['reason_rows']['sha256'] = 'different'
        self.assertEqual(self.status(self.run_stage(), 'D6'), V.NOT_MET)

    def test_every_named_repeat_field_is_checked(self):
        for field, value in [('loops', {'production': {'end': 'cap', 'round': 9},
                                     'views_and_tests': {'end': 'settled', 'round': 1},
                                     'absorb': {'end': 'settled', 'round': 1}}),
                             ('verify', []), ('law_violation_counts', {'different': 1}), ('exit_code', 3)]:
            with self.subTest(field=field):
                previous = copy.deepcopy(self.w.cells['L_on']['forem/repeat-v1-a1'][field])
                self.w.cells['L_on']['forem/repeat-v1-a1'][field] = value
                self.assertEqual(self.status(self.run_stage(), 'D6'), V.NOT_MET)
                self.w.cells['L_on']['forem/repeat-v1-a1'][field] = previous

    def test_missing_production_loop_is_unavailable(self):
        del self.w.cells['L_on']['forem/1-v1-a1']['loops']['production']
        self.assertEqual(self.status(self.run_stage(), 'D6'), V.UNAVAILABLE)

    def test_settlement_is_compared_per_loop(self):
        self.w.cells['C_on']['forem/1-v1-a1']['loops']['absorb']['end'] = 'cap'
        self.w.cells['L_on']['forem/1-v1-a1']['loops']['production']['end'] = 'cap'
        self.assertEqual(self.status(self.run_stage(), 'D6'), V.NOT_MET)

    def test_missing_hash_note_or_type_is_unavailable(self):
        for field in ('hash', 'note', 'ty'):
            with self.subTest(field=field):
                value = self.w.rows[('forem', 'v1-a1')][0]['L']['unset']
                old = value.pop(field)
                r = self.run_stage()
                self.assertEqual(self.status(r, 'V1'), V.UNAVAILABLE)
                self.assertEqual(self.status(r, 'RUNTIME_ADMISSION'), V.UNAVAILABLE)
                value[field] = old

    def test_new_row_missing_type_is_unavailable(self):
        self.w.rows[('forem', 'v1-a1')].append({'part':'side_table','key':'new','span':None,
            'C':{s:None for s in S},'L':{s:{'hash':'x','note':0} for s in S}})
        self.assertEqual(self.status(self.run_stage(), 'RUNTIME_ADMISSION'), V.UNAVAILABLE)

    def test_incomplete_nested_type_is_unavailable(self):
        self.w.rows[('forem','v1-a1')][0]['L']['unset']['ty'] = {'kind':'array'}
        self.assertEqual(self.status(self.run_stage(), 'V1'), V.UNAVAILABLE)

    def test_explicit_empty_parameter_vector_is_valid(self):
        self.w.rows[('forem', 'v1-a1')].append({'part':'params','key':'P#m[empty]','span':None,
            'C':{s:{'hash':7,'note':0,'ty':None,'empty_vector':True} for s in S},
            'L':{s:{'hash':7,'note':0,'ty':None,'empty_vector':True} for s in S}})
        self.assertEqual(self.status(self.run_stage(), 'V1'), V.MET)

    def test_added_untyped_row_counts_as_presence(self):
        self.w.rows[('forem', 'v1-a1')].append({'part':'side_table','key':'new','span':None,
            'C':{s:None for s in S},'L':{s:val(UNT) for s in S}})
        report=self.run_stage()
        rec=next(x for x in report['recorded_predictions'] if x['name']=='forem presence changes')
        self.assertEqual(rec['observed'], 1)
        self.assertEqual(rec['result'], 'miss')

    def test_disappearance_is_not_literal_check_4_power_or_repaired_variance(self):
        for observer in V.ROW_APPS['chatwoot']:
            for row in self.w.rows[('chatwoot',observer)]:
                if V.declaration_of(row['part'],row['key']) in (IG,WA):
                    row['L']={s:None for s in S}
        report=self.run_stage()
        self.assertEqual(self.status(report,'WEBHOOK_ORDER'),V.UNAVAILABLE)
        rec=next(x for x in report['recorded_predictions'] if x['name']=='chatwoot matched RETURN_HELPERS keys removed')
        self.assertTrue(rec['observed'].startswith('0 of '))
        rec=next(x for x in report['recorded_predictions'] if x['name']=='chatwoot matched RETURN_HELPERS keys disappeared')
        self.assertEqual(rec['observed'],2)

    def test_incomparable_changed_value_rejected_by_both_still_kills(self):
        row={'part':'ir','key':'x','span':{'start':1,'end':2},'declaration':'Example#m',
             'C':{s:val(arr(STR)) for s in S},'L':{s:val(arr(INT)) for s in S}}
        witnesses=[({'app':'forem','declarations':['Example#m'],
                     'by_span':[{'span':[1,2],'probes':['value']}]},
                    {'probes':{'value':[{'class':'Array','elems':[{'class':'NilClass'}]}]}})]
        self.assertEqual(V.c_soundness({('forem','v1-a1'):[row]},witnesses,('forem',))['status'],V.NOT_MET)


class Decide(unittest.TestCase):
    def test_every_combination_has_exactly_one_outcome(self):
        states = (V.MET, V.NOT_MET, V.UNAVAILABLE)
        for n in range(0, 4):
            for roles in itertools.product(('decisive', 'validity'), repeat=n):
                for sts in itertools.product(states, repeat=n):
                    cs = [V.crit('c%d' % i, ro, st, '') for i, (ro, st) in enumerate(zip(roles, sts))]
                    for stage in ('campfire', 'final'):
                        out, _ = V.decide(cs, stage)
                        kill = any(c['role'] == 'decisive' and c['status'] == V.NOT_MET for c in cs)
                        gap = any((c['role'] == 'decisive' and c['status'] == V.UNAVAILABLE) or
                                  (c['role'] == 'validity' and c['status'] != V.MET) for c in cs)
                        expect = 'KILLED' if kill else 'INCONCLUSIVE' if gap or not cs else (
                            'PASSED' if stage == 'campfire' else 'CONFIRMED')
                        self.assertEqual(out, expect)

    def test_validity_never_kills(self):
        cs = [V.crit('v', 'validity', V.NOT_MET, ''), V.crit('d', 'decisive', V.MET, '')]
        self.assertEqual(V.decide(cs, 'final')[0], 'INCONCLUSIVE')


class Types(unittest.TestCase):
    def test_print(self):
        self.assertEqual(V.print_ty(arr(VAR)), 'Array[untyped]')
        self.assertEqual(V.print_ty(arr(union(VAR, UNT))), 'Array[untyped]')
        self.assertEqual(V.print_ty(union(STR, NIL)), '(nil | str)')
        self.assertEqual(V.print_ty(union(STR, UNT)), 'untyped')

    def test_covers(self):
        self.assertTrue(V.covers(arr(UNT), arr(STR)))
        self.assertFalse(V.covers(arr(STR), arr(UNT)))
        self.assertTrue(V.covers(union(STR, NIL), STR))
        self.assertFalse(V.covers(STR, union(STR, NIL)))
        self.assertTrue(V.covers({'kind': 'hash', 'key': VAR, 'value': VAR}, {'kind': 'hash', 'key': VAR, 'value': STR}))
        self.assertIsNone(V.covers({'kind': 'rec', 'slot': 'a'}, {'kind': 'rec', 'slot': 'b'}))
        self.assertTrue(V.covers(arr(STR), {'kind': 'tuple', 'elems': [STR, STR]}))
        self.assertFalse(V.covers({'kind': 'tuple', 'elems': [STR]}, {'kind': 'tuple', 'elems': [STR, STR]}))
        self.assertTrue(V.covers(STR, {'kind': 'bottom'}))

    def test_fn_types_compare_on_their_return(self):
        f1 = {'kind': 'fn', 'params': [], 'block': None, 'ret': arr(union(VAR, UNT)), 'effects': {'effects': []}}
        f2 = {'kind': 'fn', 'params': [], 'block': None, 'ret': arr(VAR), 'effects': {'effects': []}}
        f3 = {'kind': 'fn', 'params': [], 'block': None, 'ret': arr(STR), 'effects': {'effects': []}}
        self.assertEqual(V.classify_pair(val(f1), val(f2)), 'same_print')
        self.assertEqual(V.classify_pair(val(f1), val(f3)), 'narrowed')
        self.assertEqual(V.classify_pair(val(f3), val(f1)), 'widened')
        g = {'kind': 'fn', 'params': [{'name': 'x', 'ty': INT, 'kind': 'req'}], 'block': None, 'ret': arr(STR)}
        self.assertIsNone(V.covers(g, f3))

    def test_fn_admits_recorded_calls(self):
        fn_int = {'kind': 'fn', 'params': [], 'block': None, 'ret': INT}
        fn_str = {'kind': 'fn', 'params': [], 'block': None, 'ret': STR}
        proc = {'class': 'Proc', 'args': [[{'class': 'Tag'}]], 'returns': [{'class': 'Integer'}]}
        self.assertTrue(V.admits(fn_int, proc))
        self.assertFalse(V.admits(fn_str, proc))
        self.assertIsNone(V.admits(fn_int, {'class': 'Proc'}))
        self.assertFalse(V.admits(fn_int, {'class': 'String'}))

    def test_classify(self):
        self.assertEqual(V.classify_pair(val(arr(UNT)), val(arr(VAR))), 'same_print')
        self.assertEqual(V.classify_pair(val(arr(STR)), val(arr(UNT))), 'widened')
        self.assertEqual(V.classify_pair(val(arr(UNT)), val(arr(STR))), 'narrowed')
        self.assertEqual(V.classify_pair(val(STR), val(INT)), 'incomparable')
        self.assertEqual(V.classify_pair(val(STR), None), 'presence')
        self.assertEqual(V.classify_pair(val(STR), val(STR)), 'same')

    def test_admits_against_the_real_witness(self):
        with open(os.path.join(HERE, 'witness', 'webhook_secrets.json')) as f:
            w = json.load(f)
        lit, ret = w['probes']['literal_at_exit'], w['probes']['return_value']
        self.assertTrue(V.admits_probe(arr(VAR), lit))
        self.assertTrue(V.admits_probe(arr(union(STR, NIL)), lit))
        self.assertFalse(V.admits_probe(arr(STR), lit))
        self.assertTrue(V.admits_probe(arr(STR), ret))
        self.assertFalse(V.admits_probe(arr(INT), ret))
        self.assertTrue(w['ruby'].startswith('ruby 4.0.7 '))

    def test_declaration_of(self):
        self.assertEqual(V.declaration_of('ir', ir_key(IG, '1/0')), IG)
        self.assertEqual(V.declaration_of('controller_cache', IG + ':body:1/0'), IG)
        self.assertEqual(V.declaration_of('params', IG + '[0]'), IG)
        self.assertEqual(V.declaration_of('returns', IG), IG)
        self.assertIsNone(V.declaration_of('side_table', 'x'))


if __name__ == '__main__':
    unittest.main()
