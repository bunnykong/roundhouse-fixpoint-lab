#!/usr/bin/env python3
"""Preserve card outputs and make explicit cross-condition comparisons without changing receipts."""
from collections import Counter
import importlib.util
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

D = Path(__file__).resolve().parent
W = D / 'workshop'
C = 'structure-success-20261015-bf56edf9'
R = W / 'theory/runs' / C
index = json.loads((D / 'series-index.json').read_text())
baseline = {f'campfire-{s}': W / 'runs' / f'campfire-{s}'
            for s in ('unset', '1', '2', 'repeat-unset')}
baseline.update({f'fixture-{s}': W / 'runs' / f'structure_fixture-{s}' for s in ('unset', '1')})
fresh = json.loads((D / 'baseline-pair.json').read_text())
baseline.update({f'fresh-{s}': Path(p) for s, p in fresh.items()})
for label, path in list(baseline.items()):
    if not label.startswith('fresh-'):
        baseline['archived-' + label] = path
baseline.update({f'campfire-{s}': Path(p) for s, p in fresh.items()})
if (D / 'baseline-control-index.json').exists():
    baseline.update({label: Path(path) for label, path
                     in json.loads((D / 'baseline-control-index.json').read_text()).items()})
spec = importlib.util.spec_from_file_location('support', W / 'theory/support.py')
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


def run_output(command, path):
    result = subprocess.run(command, cwd=W, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    path.write_text(result.stdout)
    return result.returncode


def load(path):
    compact = json.loads((path / 'compact.json').read_text())
    report = json.loads((path / 'report.json').read_text())
    stderr = (path / 'stderr.log').read_text()
    warnings = Counter(re.findall(r'warning\[([a-z_]+)\]', stderr))
    errors = Counter(re.findall(r'error\[([a-z_]+)\]', stderr))
    diagnostics = Counter(line for line in stderr.splitlines() if re.search(r': (?:warning|error)\[', line))
    summary = [line for line in stderr.splitlines() if line.startswith('roundhouse-check:')][-1]
    return {'path': str(path), 'command': json.loads((path / 'command.json').read_text()),
            'compact': compact, 'report': report, 'support': support.load(path),
            'warnings': dict(warnings), 'errors': dict(errors), 'summary': summary,
            'diagnostics': diagnostics,
            'diagnostic_sha256': hashlib.sha256(json.dumps(sorted(diagnostics.items())).encode()).hexdigest()}


def compare(a, b):
    identities = {}
    for category in ('attempt', 'mutation'):
        left, right = (set(map(tuple, v['compact']['identities'][category])) for v in (a, b))
        identities[category] = {'counts': [len(left), len(right)],
                                'left_only': sorted(left - right), 'right_only': sorted(right - left)}
    supports = {}
    for category in ('attempted', 'concrete', 'mutation'):
        left, right = a['support'][category], b['support'][category]
        supports[category] = {'counts': [len(left), len(right)],
                              'left_only': sorted(left - right), 'right_only': sorted(right - left)}
    ra, rb = a['report'], b['report']
    return {'left': a['path'], 'right': b['path'], 'identities': identities, 'support': supports,
            'declarations_equal': a['compact']['declaration_hashes'] == b['compact']['declaration_hashes'],
            'digest_equal': {k: ra['digest'][k] == rb['digest'][k] for k in ra['digest']},
            'census_equal': ra['census'] == rb['census'],
            'loops_equal': {k: (v['end'], v['round']) for k, v in ra['loops'].items()}
                == {k: (v['end'], v['round']) for k, v in rb['loops'].items()},
            'warnings_equal': a['warnings'] == b['warnings'], 'errors_equal': a['errors'] == b['errors'],
            'summary_equal': a['summary'] == b['summary'],
            'diagnostics_equal': a['diagnostics'] == b['diagnostics'],
            'diagnostic_left_only': sorted((a['diagnostics'] - b['diagnostics']).items()),
            'diagnostic_right_only': sorted((b['diagnostics'] - a['diagnostics']).items())}


all_runs = {'baseline/' + label: load(path) for label, path in baseline.items()}
output = {'condition': C, 'runs': {}, 'pairs': {}}
for series, paths in index.items():
    out = R / ('analysis-' + series)
    out.mkdir(exist_ok=True)
    loaded = {label: load(Path(path)) for label, path in paths.items()}
    all_runs.update({series + '/' + label: value for label, value in loaded.items()})
    for suffix in ('1', '2', 'repeat-unset'):
        key = 'campfire-' + suffix
        if key in loaded:
            for extension in ('txt', 'json'):
                command = ['./diff.sh', paths['campfire-unset'], paths[key]]
                if extension == 'json':
                    command.append('--json')
                assert run_output(command, out / ('diff-unset--' + suffix + '.' + extension)) == 0
            output['pairs'][series + '/unset--' + suffix] = compare(loaded['campfire-unset'], loaded[key])
    if 'fixture-1' in loaded:
        for extension in ('txt', 'json'):
            command = ['./diff.sh', paths['fixture-unset'], paths['fixture-1']]
            if extension == 'json':
                command.append('--json')
            assert run_output(command, out / ('diff-fixture.' + extension)) == 0
        output['pairs'][series + '/fixture-unset--1'] = compare(loaded['fixture-unset'], loaded['fixture-1'])
    for label, value in loaded.items():
        output['pairs'][series + '/' + label + '--baseline-same'] = compare(value, all_runs['baseline/' + label])
        if label.startswith('campfire-'):
            output['pairs'][series + '/' + label + '--baseline-unset'] = compare(value, all_runs['baseline/campfire-unset'])
    camps = [paths['campfire-' + s] for s in ('unset', '1', '2', 'repeat-unset') if 'campfire-' + s in paths]
    # The unchanged helper keys by basename. Keep the exact card output, then
    # supplement it using uniquely named symlinks so no run silently disappears.
    assert run_output([sys.executable, '-I', 'theory/support.py', *camps,
                       str(baseline['campfire-unset']), '--out', str(out / 'support-card.json')],
                      out / 'support-card.txt') == 0
    aliases = out / 'aliases'
    aliases.mkdir(exist_ok=True)
    unique = []
    for label, value in loaded.items():
        if label.startswith('campfire-'):
            alias = aliases / (series + '-' + label)
            if not alias.exists():
                alias.symlink_to(value['path'], target_is_directory=True)
            unique.append(str(alias))
    for schedule in ('unset', '1', '2', 'repeat-unset'):
        alias = aliases / ('baseline-campfire-' + schedule)
        if not alias.exists():
            alias.symlink_to(baseline['campfire-' + schedule], target_is_directory=True)
        unique.append(str(alias))
    assert run_output([sys.executable, '-I', 'theory/support.py', *unique, '--out', str(out / 'support.json')],
                      out / 'support.txt') == 0
    assert run_output([sys.executable, '-I', 'theory/digests.py', *camps,
                       *(str(baseline['campfire-' + s]) for s in ('unset', '1', '2'))], out / 'digests.txt') == 0
    fixtures = [paths[k] for k in ('fixture-unset', 'fixture-1') if k in paths]
    assert run_output([sys.executable, '-I', 'theory/digests.py', *fixtures,
                       str(baseline['fixture-unset']), str(baseline['fixture-1'])], out / 'fixture-digests.txt') == 0
    warning_rows = []
    for label, value in loaded.items():
        warning_rows += [label + ' ' + value['path'], json.dumps(value['warnings'], sort_keys=True),
                         json.dumps(value['errors'], sort_keys=True), value['summary'],
                         'diagnostic multiset sha256=' + value['diagnostic_sha256']]
    (out / 'warnings.txt').write_text('\n'.join(warning_rows) + '\n')
    code = run_output(['./diff.sh', paths['campfire-unset'], str(baseline['campfire-unset'])],
                      out / 'cross-condition-diff.txt')
    assert code == 2, 'the comparator should refuse different conditions'

for label, value in all_runs.items():
    report = value['report']
    output['runs'][label] = {'path': value['path'], 'command': value['command'],
                             'digest': report['digest'], 'census': report['census'],
                             'loops': {k: {'end': v['end'], 'round': v['round']} for k, v in report['loops'].items()},
                             'warnings': value['warnings'], 'errors': value['errors'], 'summary': value['summary'],
                             'diagnostic_sha256': value['diagnostic_sha256'],
                             'support': {k: len(value['support'][k]) for k in ('attempted', 'concrete', 'mutation')}}
(R / 'comparisons.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
for label, pair in output['pairs'].items():
    print(label, 'digests differing=' + ','.join(k for k, same in pair['digest_equal'].items() if not same),
          'mutation differences=' + str([len(pair['identities']['mutation'][s]) for s in ('left_only', 'right_only')]),
          'concrete differences=' + str([len(pair['support']['concrete'][s]) for s in ('left_only', 'right_only')]),
          'warning equality=' + str(pair['warnings_equal']))
print('Full comparisons:', R / 'comparisons.json')
