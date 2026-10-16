#!/usr/bin/env python3
"""Classify research condition value deltas with F61/CARD-research condition set semantics and CRuby witnesses."""
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

D = Path(__file__).resolve().parents[1]
F = D.parents[1]
sys.path.insert(0, str(F / 'agents/ownership-runtime-values'))
from classify import short, normalize

spec = importlib.util.spec_from_file_location('runtime_sets', F / 'phase2/contributor-ownership/contributor-protocol/verdict.py')
sets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sets)

CLASSES = ['unsound narrowing', 'sound narrowing consistent with witnesses', 'widening', 'no runtime change']
CONDITION = 'strict-producer-reasons-20261015-ea3ec744'


def read(path):
    return json.loads(Path(path).read_text())


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def row_witnesses(row, oauth, imap):
    if row['part'] == 'params' and '#render[0]' in row['key']:
        match = re.fullmatch(r'Api::V1::Accounts::(Google|Instagram|Microsoft|Notion)::AuthorizationsController#render\[0\]', row['key'])
        assert match, row['key']
        name = match[1].lower()
        call = next(c for c in oauth['render_calls'] if c['provider'] == name)
        return [{'id': name + '/render-keywords', 'receipt': 'oauth-witnesses.json',
                 'type': call['value_type'], 'value': call['options'], 'source': call['source']}]
    assert 'Imap::Authentication' in row['key'], row['key']
    receiver = row['part'] == 'params' or row['C'].get('node') == 'Var'
    selected = []
    branch = row['C'].get('path', [])
    for event in imap['events']:
        if event['event'] != ('call' if receiver else 'return'):
            continue
        label = event['witness']
        if len(branch) >= 2:
            if branch[1] == 1 and label != 'authenticate!/mechanism="cram-md5"':
                continue
            if branch[1] == 2 and label != 'authenticate!/mechanism="login"':
                continue
            if branch[1] == 3 and label not in ['authenticate!/mechanism="plain"', 'authenticate!/mechanism=nil', 'authenticate!/mechanism=""']:
                continue
        value = event['imap' if receiver else 'returned']
        selected.append({'id': label + ('/receiver' if receiver else '/return'),
                         'receipt': 'runtime-witnesses.json',
                         'type': {'kind': 'class', 'id': value['ruby_class'], 'args': []},
                         'value': value['value'], 'source_line': event['line'],
                         'mapping': 'parameter/receiver read' if receiver else 'tail send, case result and method-body result coincide'})
    assert selected, row
    return selected


def main():
    oauth = read(D / 'receipts/oauth-witnesses.json')
    imap = read(D / 'receipts/runtime-witnesses.json')
    assert all('ruby 4.0.7 ' in w['ruby'] for w in [oauth, imap])
    rows = [json.loads(line) for line in (D / 'receipts/all-value-rows.jsonl').open()]
    totals, by_setting, unique, sensitivity = Counter(), defaultdict(Counter), {}, Counter()
    memberships = []
    for row in rows:
        assert row['C'] is not None and row['SK'] is not None, 'structural change needs separate review'
        before, after = [row[a]['resolved_ty'] for a in ['C', 'SK']]
        relation = sets.relation(before, after)
        witnesses = row_witnesses(row, oauth, imap)
        checks = [{'witness': w, 'C_admits': sets.covers(before, w['type']),
                   'SK_admits': sets.covers(after, w['type'])} for w in witnesses]
        excluded = any(c['C_admits'] and not c['SK_admits'] for c in checks)
        if relation == 'EQ':
            verdict = 'no runtime change'
            assert all(c['C_admits'] and c['SK_admits'] for c in checks)
        elif relation == 'WIDEN':
            verdict = 'widening'
        elif relation == 'NARROW':
            verdict = 'unsound narrowing' if excluded else 'sound narrowing consistent with witnesses'
            assert excluded or all(c['SK_admits'] for c in checks)
        else:
            raise AssertionError(('unclassified relation', row['row_id'], relation))
        sets.VAR_TOP = False
        alternate = sets.relation(before, after)
        alternate_excluded = any(sets.covers(before, w['type']) and not sets.covers(after, w['type']) for w in witnesses)
        sets.VAR_TOP = True
        sensitivity[(alternate, alternate_excluded)] += 1
        row.update(relation=relation, verdict=verdict, witnesses=checks,
                   C_value=short(normalize(before)), SK_value=short(normalize(after)),
                   var_pending_sensitivity={'relation': alternate, 'excludes_witness': alternate_excluded})
        if row['part'] == 'ir':
            span = row['C']['span']
            source = row['C']['source']
            data = Path(source).read_bytes()
            row['source'] = source
            row['span'] = span
            row['line'] = data[:span['start']].count(b'\n') + 1
            row['expression'] = data[span['start']:span['end']].decode()
            row['method'] = json.loads(row['C']['root'].split(':occurrence:', 1)[0])['declaration']
        else:
            row['method'] = row['key']
        totals[verdict] += 1
        by_setting[row['setting']][verdict] += 1
        signature = (row['part'], row['key'], row['C_value'], row['SK_value'], relation, verdict)
        if row['row_id'] in unique:
            assert unique[row['row_id']]['signature'] == signature, 'setting-dependent value transition'
            unique[row['row_id']]['settings'].append(row['setting'])
        else:
            unique[row['row_id']] = {'signature': signature, 'row': row, 'settings': [row['setting']]}
        memberships.append({'row_id': row['row_id'], 'setting': row['setting'], 'relation': relation,
                            'verdict': verdict, 'checks': checks})
    with (D / 'receipts/classified-rows.jsonl').open('w') as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n')
    columns = ['row_id', 'setting', 'part', 'method', 'line', 'C_value', 'SK_value', 'relation', 'verdict']
    with (D / 'receipts/classified-rows.tsv').open('w') as f:
        f.write('\t'.join(columns) + '\n')
        for row in rows:
            f.write('\t'.join(str(row.get(c, '')).replace('\t', ' ').replace('\n', ' ') for c in columns) + '\n')
    save(D / 'receipts/witness-membership.json', memberships)
    save(D / 'receipts/unique-rows.json', {k: {'settings': v['settings'], 'row': v['row']} for k, v in unique.items()})
    summary = {
        'condition': CONDITION, 'app': 'chatwoot', 'source': '2233e2e7e639b9f66ecda41fac34475b2d0f2559',
        'runtime_reading': 'F61: untyped and raw Var admit all Ruby values; Pending is not reinterpreted as completed evidence.',
        'total_row_observations': len(rows), 'unique_rows': len(unique),
        'counts': {k: totals[k] for k in CLASSES},
        'unique_counts': dict(Counter(v['row']['verdict'] for v in unique.values())),
        'settings': {s: {k: c[k] for k in CLASSES} for s, c in by_setting.items()},
        'unset_V0_and_V1_counts': {k: sum(c[k] for s, c in by_setting.items() if s.startswith('unset-')) for k in CLASSES},
        'parity_gate_unset_and_repeat_counts': {k: sum(c[k] for s, c in by_setting.items() if s.startswith(('unset-', 'repeat-'))) for k in CLASSES},
        'every_unique_transition_same_at_all_settings': all(len(v['settings']) == 8 for v in unique.values()),
        'var_pending_sensitivity': [{'relation': r, 'excludes_witness': e, 'rows': n} for (r, e), n in sensitivity.items()],
        'verdict': 'soundness loss' if totals['unsound narrowing'] and not totals['sound narrowing consistent with witnesses'] else 'requires review',
    }
    save(D / 'receipts/classification-summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
