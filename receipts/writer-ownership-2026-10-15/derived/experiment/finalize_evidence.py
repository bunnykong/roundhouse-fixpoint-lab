#!/usr/bin/env python3
"""Attach public source locations to H3 and summarize existing comparisons."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
W = D / 'workshop'
C = 'writer-ownership-20261015-bf56edf9'
R = W / 'theory/runs' / (C + '-h3')
diagnostic = json.loads((R / 'site-list.json').read_text())
manifest = json.loads((W / 'inputs/manifest.json').read_text())['campfire']['files']
sites = []
for row in diagnostic['changed_sites']:
    owner_text, syntax_path = json.loads(row['site']['source'])
    kind, target_text, declaration_text = json.loads(owner_text)
    assert kind == 'method'
    target = json.loads(target_text)
    file = Path(json.loads(declaration_text)[0])
    relative = file.relative_to(W / 'inputs/campfire').as_posix()
    data = file.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert digest == manifest[relative]
    start, end = row['site']['span']['start'], row['site']['span']['end']
    before = data[:start]
    sites.append({'method': target[0] + ('#' if target[1] == 'instance' else '.') + target[2],
                  'file': relative, 'line': before.count(b'\n') + 1,
                  'column': len(before.rsplit(b'\n', 1)[-1].decode('utf-8')) + 1,
                  'expression': data[start:end].decode('utf-8'), 'syntax_path': syntax_path,
                  'span': [start, end], 'kinds': [row['unset_kinds'], row['two_kinds']],
                  'type_hash': [row['unset_type_hash'], row['two_type_hash']],
                  'source_sha256': digest, 'emit_body': row['emit_body']})
with (R / 'site-table.json').open('x') as out:
    out.write(json.dumps({'condition': C + '-h3', 'status': 'diagnostic only; no verdict',
                         'sites': sites}, indent=2, sort_keys=True) + '\n')

comparisons = json.loads((D / 'comparisons.json').read_text())
matched = {k: v for k, v in comparisons['matched_comparisons'].items() if k.endswith('--baseline-matched')}
shared_controls = {field: all(p[field] for p in matched.values()) for field in
                   ['declarations_equal', 'warnings_equal', 'errors_equal', 'diagnostics_equal',
                    'summary_equal', 'loops_equal', 'entries_equal']}
values = set(comparisons['runs']['a/campfire-unset']['digest']) - {'copies'}
literal_a_values = {s: all(comparisons['runs']['a/campfire-' + s]['digest'][k] ==
                          comparisons['runs']['baseline/campfire-' + ('2' if s == '2' else 'unset')]['digest'][k]
                          for k in values) for s in ('unset', '1', '2', 'repeat-unset')}
assert all(shared_controls.values()) and all(literal_a_values.values())
evidence = {'condition': C, 'matched_control_pairs': len(matched), 'shared_controls': shared_controls,
            'A_literal_card5_values': literal_a_values,
            'H1_H2': {h: json.loads((D / 'gate-audit-reviewed.json').read_text())[h]['verdict'] for h in ('H1', 'H2')},
            'H3': {'status': 'diagnostic only; no verdict', 'sites': len(sites),
                   'kind_transitions': diagnostic['kind_transitions'],
                   'all_type_hashes_equal': diagnostic['all_shared_type_hashes_equal'],
                   'no_missing_sites': not diagnostic['left_only'] and not diagnostic['right_only']},
            'cargo_target_absent': not (D / 'target').exists(),
            'card_sha256': hashlib.sha256((D / 'protocol.md').read_bytes()).hexdigest()}
assert evidence['cargo_target_absent']
with (D / 'final-evidence.json').open('x') as out:
    out.write(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
print(json.dumps(evidence, indent=2))
for site in sites:
    print('%s:%s:%s %s %s %s' % (site['file'], site['line'], site['column'],
                               site['expression'], site['syntax_path'], site['type_hash'][0]))
