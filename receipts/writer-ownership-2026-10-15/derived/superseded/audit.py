#!/usr/bin/env python3
"""Evaluate the unchanged advance_prediction gates against the complete receipt comparisons."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

D = Path(__file__).resolve().parent
C = 'structure-success-20261015-bf56edf9'
R = D / 'workshop/theory/runs' / C
data = json.loads((R / 'comparisons.json').read_text())
runs, pairs = data['runs'], data['pairs']
index = json.loads((D / 'series-index.json').read_text())


def empty_difference(pair, key, family='support'):
    return all(not pair[family][key][side] for side in ('left_only', 'right_only'))


def all_same(pair):
    return (pair['declarations_equal'] and all(pair['digest_equal'].values())
            and all(pair[k] for k in ('census_equal', 'loops_equal', 'warnings_equal', 'errors_equal', 'summary_equal',
                                     'diagnostics_equal'))
            and all(empty_difference(pair, k, 'identities') for k in ('attempt', 'mutation'))
            and all(empty_difference(pair, k) for k in ('attempted', 'concrete', 'mutation')))


def settled(run):
    return all(v['end'] == 'settled' for v in run['loops'].values())


baseline_diff = json.loads((D / 'baseline-diff.json').read_text())
criterion1 = (baseline_diff['declarations_equal'] and baseline_diff['attempt']['counts'] == [740, 740]
              and baseline_diff['mutation']['counts'] == [678, 678]
              and {json.loads(row[2])[2] for row in baseline_diff['mutation']['left_only']}
                  == {'require_authentication', 'terminate_current_session'}
              and {json.loads(row[2])[2] for row in baseline_diff['mutation']['right_only']}
                  == {'resume_session', 'start_new_session_for'})
candidate_pairs = [pairs['a/unset--' + s] for s in ('1', '2', 'repeat-unset')]
criterion2 = all(p['declarations_equal'] and p['identities']['attempt']['counts'] == [740, 740]
                 and empty_difference(p, 'attempt', 'identities') and empty_difference(p, 'mutation', 'identities')
                 for p in candidate_pairs)
baseline_pairs = [pairs['a/campfire-' + s + '--baseline-same'] for s in ('unset', '1', '2', 'repeat-unset')]
criterion3 = all(p['support']['attempted']['counts'] == [740, 740]
                 and p['support']['concrete']['counts'] == [556, 556]
                 and empty_difference(p, 'attempted') and empty_difference(p, 'concrete')
                 and not p['identities']['mutation']['right_only'] for p in baseline_pairs)
value_pairs = [pairs['a/campfire-' + s + '--baseline-unset'] for s in ('unset', '1', 'repeat-unset')]
criterion4 = all(all(p['digest_equal'].values())
                 and all(p[k] for k in ('census_equal', 'loops_equal', 'warnings_equal', 'errors_equal', 'summary_equal'))
                 for p in value_pairs)
criterion5 = (all_same(pairs['a/fixture-unset--1'])
              and all(all_same(pairs['a/fixture-' + s + '--baseline-same']) for s in ('unset', '1'))
              and pairs['a/fixture-unset--1']['identities']['attempt']['counts'] == [10, 10]
              and pairs['a/fixture-unset--1']['identities']['mutation']['counts'] == [10, 10])
matched_schedule_neutrality = ('off' in index and all(
    all_same(pairs['off/' + label + '--baseline-same']) for label in index['off']))
# Preserve the literal command-section demand, including its known baseline
# puzzle. Record the useful matched-schedule control separately, not as a waiver.
criterion6 = ('off' in index and all(all_same(pairs['off/campfire-' + s + '--baseline-unset'])
                                   for s in ('unset', '1', '2', 'repeat-unset')))
kills = []
if any(not empty_difference(p, 'mutation', 'identities') for p in candidate_pairs):
    kills.append('candidate mutation identity still differs between schedules')
if any(not empty_difference(p, 'concrete') for p in candidate_pairs + baseline_pairs):
    kills.append('concrete support differs at the same copied input path')
if any(not p['digest_equal'][k] for p in value_pairs[:2] for k in ('returns', 'ir')):
    kills.append('candidate unset or 1 changes baseline returns or IR')
for label in index['a']:
    run = runs['a/' + label]
    baseline = runs['baseline/' + label]
    if any(n > baseline['warnings'].get(k, 0) for k, n in run['warnings'].items()):
        kills.append(label + ': warning count rises')
    if not settled(run):
        kills.append(label + ': loop does not settle')
criteria = {str(i): value for i, value in enumerate(
    (criterion1, criterion2, criterion3, criterion4, criterion5, criterion6), 1)}
arm_a = {'verdict': 'killed' if kills else 'confirmed' if all(criteria.values()) else 'inconclusive',
         'confirm_criteria': criteria, 'kill_criteria_triggered': kills,
         'changed_categories_against_baseline_unset': [k for k, same in value_pairs[0]['digest_equal'].items() if not same],
         'flags_off_matched_schedule_neutrality': matched_schedule_neutrality,
         'flags_off_literal_unset_baseline_demand': criterion6,
         'flags_off_comparison': 'both literal unset-baseline and matched-schedule comparisons retained; no waiver'}
arm_b = {'verdict': 'inconclusive', 'reason': 'not run'}
if 'b' in index:
    pair = pairs['b/unset--2']
    left, right = runs['b/campfire-unset'], runs['b/campfire-2']
    returns_equal = pair['digest_equal']['returns']
    provenance_equal = left['census']['untyped_by_provenance'] == right['census']['untyped_by_provenance']
    loops_settle = all(settled(runs['b/' + label]) for label in index['b'])
    warnings_equal = all(pairs['b/' + label + '--baseline-same']['diagnostics_equal']
                         for label in index['b'])
    arm_b = {'verdict': 'killed' if not returns_equal or not loops_settle else
             'confirmed' if provenance_equal and warnings_equal else 'inconclusive',
             'returns_equal_unset_2': returns_equal, 'provenance_equal_unset_2': provenance_equal,
             'all_loops_settle': loops_settle,
             'warning_multiset_equal_baseline': warnings_equal,
             'warning_multiset_equal_unset_2': pair['diagnostics_equal'],
             'warning_counts_unset': left['warnings'], 'warning_counts_2': right['warnings']}

unchanged = {}
for relative, expected in json.loads((D / 'advance_prediction-inputs.json').read_text()).items():
    unchanged[relative] = hashlib.sha256((D / relative).read_bytes()).hexdigest() == expected
assert all(unchanged.values()), unchanged
commit = json.loads((D / 'candidate-commit.json').read_text())
build = json.loads((D / 'build.json').read_text())
assert build['source_commit'] == commit['commit']
assert hashlib.sha256((D / 'bin/roundhouse').read_bytes()).hexdigest() == build['binary_sha256']
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=D / 'source', text=True).strip() == commit['commit']
assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=D / 'source', text=True).strip() == 'writer-ownership-initial'
assert not subprocess.check_output(['git', 'remote'], cwd=D / 'source', text=True).strip()
for relative, expected in commit['files'].items():
    assert hashlib.sha256((D / 'source' / relative).read_bytes()).hexdigest() == expected
flags = {'a': ['RH_SPLICED_WRITER_OWNERSHIP=1'], 'b': ['RH_SKIP_RETURN_STABILIZE=1'],
         'both': ['RH_SPLICED_WRITER_OWNERSHIP=1', 'RH_SKIP_RETURN_STABILIZE=1'], 'off': []}
receipt_checks = {}
for series, paths in index.items():
    if series not in flags:
        continue
    for label in paths:
        command = runs[series + '/' + label]['command']
        check = (command['condition'] == C and command['source_commit'] == commit['commit']
                 and command['binary_sha256'] == build['binary_sha256']
                 and command['candidate_flags'] == flags[series] and command['verification'] is False
                 and command['ruby'].startswith('ruby 4.0.7 '))
        receipt_checks[series + '/' + label] = check
assert all(receipt_checks.values())
test_text = (D / 'checks-default-initial.log').read_text()
match = re.search(r'test result: FAILED\. (\d+) passed; (\d+) failed; (\d+) ignored;', test_text)
default_tests = {'passed': int(match[1]), 'failed': int(match[2]), 'ignored': int(match[3]),
                 'log': str(D / 'checks-default-initial.log'),
                 'setup_error': 'RBENV_VERSION=3.4 was not an installed exact version; generated fixtures also absent'}
assert json.loads((D / 'checks-harvest.json').read_text())['exit_code'] == 0
assert '17 passed; 0 failed' in (D / 'checks-harvest.log').read_text()
output = {'condition': C, 'arm_a': arm_a, 'arm_b': arm_b, 'advance_prediction_inputs_unchanged': unchanged,
          'candidate_receipts_verified': receipt_checks, 'default_suite': default_tests,
          'source_commit': commit['commit'], 'binary_sha256': build['binary_sha256'],
          'source_status': subprocess.check_output(['git', 'status', '--porcelain'], cwd=D / 'source', text=True)}
output['all_candidate_diagnostics_equal_matched_baseline'] = all(
    pairs[series + '/' + label + '--baseline-same']['diagnostics_equal']
    for series in index for label in index[series])
output['all_candidate_loops_settle'] = all(settled(runs[series + '/' + label])
                                         for series in index for label in index[series])
output['all_fixture_controls_match_baseline'] = all(
    all_same(pairs[series + '/' + label + '--baseline-same'])
    for series in index for label in index[series] if label.startswith('fixture-'))
assert output['all_candidate_diagnostics_equal_matched_baseline']
assert output['all_candidate_loops_settle']
assert output['all_fixture_controls_match_baseline']
assert not output['source_status']
if 'both' in index:
    combined_pairs = [pairs['both/unset--' + s] for s in ('1', '2', 'repeat-unset')]
    output['combined'] = {
        'all_ten_digests_equal_across_schedules': all(all(p['digest_equal'].values()) for p in combined_pairs),
        'mutation_sets_equal_across_schedules': all(empty_difference(p, 'mutation', 'identities') for p in combined_pairs),
        'provenance_equal_unset_2': runs['both/campfire-unset']['census']['untyped_by_provenance']
            == runs['both/campfire-2']['census']['untyped_by_provenance'],
        'all_loops_settle': all(settled(runs['both/' + label]) for label in index['both'])}
(D / 'gate-audit.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
(R / 'gate-audit.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
print(json.dumps({'condition': C, 'arm_a': arm_a, 'arm_b': arm_b, 'default_suite': default_tests}, indent=2))
