#!/usr/bin/env python3
"""Additional evidence-boundary tests; no analyzer or builds."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import suite_receipt as S
import test_verdict as T

class Binding(unittest.TestCase):
    def test_complete_suite_and_truncation(self):
        text = ('Running tests/analyze.rs (target/release/deps/analyze-abc)\n'
                'running 2 tests\ntest good ... ok\ntest if_branches_union_merge ... FAILED\n'
                'test result: FAILED. 1 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out\n'
                '   Doc-tests roundhouse\nrunning 0 tests\n'
                'test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out\n')
        inventory = {'analyze': ['good', 'if_branches_union_merge'], 'doc:roundhouse': []}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'suite.log';p.write_text(text)
            self.assertTrue(S.parse(p, inventory, {'completed': True, 'exit_code': 101})['complete'])
            p.write_text(text + 'Running tests/later.rs (target/release/deps/later-def)\nrunning 8 tests\n')
            self.assertFalse(S.parse(p, inventory, {'completed': True, 'exit_code': 101})['complete'])
            self.assertEqual(S.parse(p, inventory, {})['failed'], ['analyze::if_branches_union_merge'])

    def test_missing_suite_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'suite.log';p.write_text('')
            self.assertFalse(S.parse(p, {'later': ['x']}, {'completed': True, 'exit_code': 0})['complete'])

    def test_missing_verification_counter(self):
        w = T.World()
        records = w.observations('T', 'forem', 'unset-v1-a1', w.cells[('T','forem','unset-v1-a1')])['verify']
        del records[0]['moved']['view_seeds']
        w.obs_override[('T','forem','unset-v1-a1')] = {'verify': records}
        self.assertEqual(T.primary(w.verdict()[1]), 'INCONCLUSIVE')

    def test_native_flags_bound(self):
        w = T.World();w.emission['arms']['off'] = {'RH_FOLD': '1'}
        self.assertEqual(T.primary(w.verdict()[1]), 'INCONCLUSIVE(PRE)')

    def test_malformed_emission_preserves_independent_kill(self):
        w = T.World();del w.emission['rows'][0]['exit']
        w.emission['rows'][1]['identical'] = False
        self.assertEqual(T.primary(w.verdict()[1]), 'KILLED')

    def test_incomplete_suite_preserves_independent_failure(self):
        w = T.World(stage='campfire');w.suite['on']['complete'] = False
        w.suite['on']['failed'].append('lib::regression')
        self.assertEqual(T.primary(w.verdict()[1]), 'KILLED')

    def test_h1_per_setting_control(self):
        w = T.World()
        for k in T.KEYS['F-process']:
            w.cells[('C', 'forem', 'repeat-v0-a0')][('returns', k)] = T.UNT
        self.assertEqual(T.primary(w.verdict()[1]), 'INCONCLUSIVE')

    def test_missing_customization_is_unavailable(self):
        w = T.World();del w.cells[('TA','mastodon','2-v0-a0')][('returns','Api::V1::Admin::AccountsController#log_action')]
        self.assertEqual(w.verdict()[1]['h5']['verdict'], 'INCONCLUSIVE')

if __name__ == '__main__':
    unittest.main()
