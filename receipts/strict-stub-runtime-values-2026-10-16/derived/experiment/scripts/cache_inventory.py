#!/usr/bin/env python3
"""Inventory research condition's immutable Chatwoot cells without invoking the analyzer."""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

D = Path(__file__).resolve().parents[1]
F = D.parents[1]
NATIVE_PROFILE = F / 'agents/strict-producer-reasons'


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('obs', F / 'phase2/observers/obs.py')
    obs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obs)
    labels = {arm: read(NATIVE_PROFILE / 'cache/labels' / ('strict-producer-' + arm) / 'label.json') for arm in ['C', 'SK']}
    settings = sorted({k.split('/', 1)[1] for x in labels.values() for k in x['cells'] if k.startswith('chatwoot/')})
    cells, pairs = {}, {}
    for setting in settings:
        results, reasons = {}, {}
        for arm in ['C', 'SK']:
            ref = labels[arm]['cells'].get('chatwoot/' + setting)
            assert ref and ref['valid'], (arm, setting, ref)
            result = obs.checked_result(ref['result'])
            assert result['valid']
            results[arm] = result
            folder = Path(result['directory'])
            reasons[arm] = obs.observed(result, 'reason_rows')
            cells[arm + '/' + setting] = {
                'result': ref['result'], 'result_sha256': sha(ref['result']),
                'cache_key': result['cache_key'], 'binary_sha256': result['key']['binary_sha256'],
                'input': result['input'], 'input_pin': result['input_pin'],
                'input_tree_sha256': result['input_tree_sha256'],
                'flags': result['inference_environment'], 'valid': True,
                'value_digests': obs.observed(result, 'value_digests'),
                'reason_rows': len(reasons[arm]),
                'files': {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)}
                          for p in sorted(folder.iterdir()) if p.is_file()},
                'has_serialized_final_values': (folder / 'contributor-values.jsonl').exists(),
            }
        delta = []
        for key in sorted(reasons['C'].keys() | reasons['SK'].keys()):
            c, sk = reasons['C'].get(key), reasons['SK'].get(key)
            if c != sk:
                delta.append({'identity': json.loads(key), 'C': c, 'SK': sk,
                              'same_value_hash': bool(c and sk and c['type_hash'] == sk['type_hash'])})
        save(D / 'receipts' / ('cached-reasons-' + setting + '.json'), delta)
        left, right = [cells[a + '/' + setting]['value_digests'] for a in ['C', 'SK']]
        pairs[setting] = {
            'changed_tables': {k: {'C': left.get(k), 'SK': right.get(k)}
                               for k in sorted(left.keys() | right.keys()) if left.get(k) != right.get(k)},
            'reason_delta_rows': len(delta),
            'reason_only_rows': sum(r['same_value_hash'] for r in delta),
            'reason_rows_with_changed_or_missing_value_hash': sum(not r['same_value_hash'] for r in delta),
        }
    save(D / 'receipts/cached-cell-index.json', cells)
    save(D / 'receipts/cached-pair-summary.json', pairs)
    print(json.dumps(pairs, indent=2))


if __name__ == '__main__':
    main()
