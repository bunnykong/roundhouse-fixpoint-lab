"""Lightweight checks of the Response-return verdict machinery; no analyzer or build calls."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
KIT = ROOT
sys.dont_write_bytecode = True
tempfile.tempdir = None
sys.path.insert(0, str(KIT))
import test_verdict as T
import verdict as V

spec = importlib.util.spec_from_file_location('response_returns_suite_receipt', KIT / 'suite_receipt.py')
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
results = []


def record(name, actual, expected, detail=None):
    row = dict(probe=name, actual=actual, expected=expected)
    if detail is not None:
        row['detail'] = detail
    results.append(row)


with tempfile.TemporaryDirectory(dir=tempfile.tempdir) as tmp:
    tmp = Path(tmp)
    logs = {}
    for arm in ['off', 'on']:
        status = 'ok' if arm == 'off' else 'FAILED'
        passed, failed = (2, 0) if arm == 'off' else (1, 1)
        path = tmp / (arm + '.log')
        path.write_text(
            'Running tests/analyze.rs (target/release/deps/analyze-abc)\n'
            'running 2 tests\n'
            'test good ... ok\n'
            f'test if_branches_union_merge ... {status}\n'
            f'test result: {status}. {passed} passed; {failed} failed; 0 ignored; 0 measured; 0 filtered out\n'
            'Running tests/later.rs (target/release/deps/later-def)\n'
            'running 8 tests\n'
        )
        logs[arm] = S.parse(path)
    w = T.World()
    w.suite = logs
    out = w.verdict()[1]
    record('truncated_suite', T.primary(out), 'INCONCLUSIVE', logs)

w = T.World(stage='campfire')
w.suite['on']['failed'].append('lib::unrelated_regression')
record('campfire_ignores_known_suite_failure', T.primary(w.verdict()[1]), 'KILLED')

w = T.World()
w.obs_override[('T', 'forem', 'unset-v1-a1')] = {'verify': []}
record('missing_verification_records', T.primary(w.verdict()[1]), 'INCONCLUSIVE')

w = T.World()
for setting in ['1-v0-a0', '2-v0-a0', 'repeat-v0-a0']:
    for arm in ['CA', 'TA']:
        for key in T.KEYS['F-spliced']:
            w.cells[(arm, 'forem', setting)][('returns', key)] = T.STR
out = w.verdict()[1]
check = next(c for c in out['h5']['checks'] if c['name'] == 'H5b defect reproduced')
record('h5b_control_absent_at_three_settings', out['h5']['verdict'], 'INCONCLUSIVE', check['details'])

w = T.World()
for (arm, app, setting), cell in w.cells.items():
    if arm in ('CA', 'TA') and app == 'mastodon':
        for part, key in list(cell):
            if key.endswith(('#log_action', '#pundit_user')) and key not in ('Api::V1::Admin::AccountsController#log_action', 'ActivityPub::FeatureAuthorizationsController#pundit_user'):
                del cell[(part, key)]
out = w.verdict()[1]
check = next(c for c in out['h5']['checks'] if c['name'] == 'H5c customization kept')
record('h5c_only_two_customization_rows', out['h5']['verdict'], 'INCONCLUSIVE', check['details'])

w = T.World()
for key in list(w.cells):
    if key[0] == 'C' and key[1] == 'discourse':
        del w.cells[key]
record('discourse_treatment_only', w.verdict()[1]['discourse']['verdict'], 'INCONCLUSIVE')

w = T.World()
next(r for r in w.emission['rows'] if r['input'] == 'void-app')['exit'] = [-9, 0]
record('void_positive_control_crashed', T.primary(w.verdict()[1]), 'INCONCLUSIVE or KILLED; never CONFIRMED')

w = T.World()
w.emission['binary_sha256'] = {'off': 'OTHER', 'on': 'OTHER'}
record('emission_from_different_binary', T.primary(w.verdict()[1]), 'INCONCLUSIVE(PRE)')

w = T.World()
del w.emission['rows'][0]['exit']
try:
    out = w.verdict()[1]
    actual = T.primary(out)
except Exception as exc:
    actual = type(exc).__name__ + ': ' + str(exc)
record('emission_missing_exit_field', actual, 'INCONCLUSIVE, with other checks still evaluated')

output = json.dumps(results, indent=2) + '\n'
expected = ['INCONCLUSIVE', 'KILLED', 'INCONCLUSIVE', 'INCONCLUSIVE', 'INCONCLUSIVE',
            'INCONCLUSIVE', 'INCONCLUSIVE', 'INCONCLUSIVE(PRE)', 'INCONCLUSIVE']
for row, want in zip(results, expected):
    assert row['actual'] == want, row
assert len(results) == 9
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(output)
print(json.dumps([{'probe': r['probe'], 'actual': r['actual']} for r in results], indent=1))
