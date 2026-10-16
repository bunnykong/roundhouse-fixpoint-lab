#!/usr/bin/env python3
"""Reuse research condition's value loader; reconcile every changed row to research condition's cached fingerprints."""
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

D = Path(__file__).resolve().parents[1]
F = D.parents[1]
RESEARCH_PROFILE = F / 'agents/ownership-runtime-values'
NATIVE_PROFILE = F / 'agents/strict-producer-reasons'
sys.path.insert(0, str(RESEARCH_PROFILE))
import rows as contributor_rows


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def has_rec(value):
    if isinstance(value, dict):
        return value.get('kind') == 'rec' or any(has_rec(v) for v in value.values())
    if isinstance(value, list):
        return any(has_rec(v) for v in value)
    return False


def main():
    originals = {a: read(NATIVE_PROFILE / 'cache/labels' / ('strict-producer-' + a) / 'label.json') for a in ['C', 'SK']}
    labels = {a: read(D / 'cache/labels' / ('sk-values-' + a) / 'label.json') for a in ['C', 'SK']}
    settings = [s + '-' + va for s in ['unset', 'repeat', '1', '2'] for va in ['v0-a0', 'v1-a1']]
    all_rows, cell_checks, pair_checks = [], {}, {}
    for setting in settings:
        values, fps, files = {}, {}, {}
        for arm in ['C', 'SK']:
            name = 'chatwoot/' + setting
            reference = labels[arm]['cells'][name]
            result = read(reference['result'])
            original = read(originals[arm]['cells'][name]['result'])
            assert result['valid'] and original['valid']
            path = Path(result['directory']) / 'contributor-values.jsonl'
            fp, rows = contributor_rows.load(path)
            assert fp['digests'] == original['observations']['value_digests'] == result['observations']['value_digests']
            assert result['input_tree_sha256'] == original['input_tree_sha256']
            ir_rows = sorted([r['span']['file'], r['span']['start'], r['span']['end'], r['hash'], r['note']]
                             for (part, _), r in rows.items() if part == 'ir')
            assert ir_rows == fp['ir'], (arm, setting, 'incomplete IR dump')
            for part in ['returns', 'side_table']:
                assert {k: r['hash'] for (p, k), r in rows.items() if p == part} == fp['parts'][part]
            flag_delta = {k: [original['inference_environment'].get(k), result['inference_environment'].get(k)]
                          for k in original['inference_environment'].keys() | result['inference_environment'].keys()
                          if original['inference_environment'].get(k) != result['inference_environment'].get(k)}
            assert set(flag_delta) <= {'RH_CONTRIBUTOR_VALUES', 'RH_REASON_SITE_CENSUS', 'RH_STRUCT_DUMP', 'RH_DECL_DUMP'}
            cell_checks[arm + '/' + setting] = {
                'source': str(path), 'sha256': contributor_rows.sha(path), 'bytes': path.stat().st_size,
                'result': reference['result'], 'original_result': originals[arm]['cells'][name]['result'],
                'input_tree_sha256': result['input_tree_sha256'],
                'binary_sha256': result['key']['binary_sha256'],
                'all_ten_original_digests_reproduced': True, 'complete_ir_multiset': True,
                'complete_returns_and_side_table': True, 'flag_delta': flag_delta,
                'rows': dict(Counter(k[0] for k in rows)), 'digests': fp['digests'],
            }
            values[arm], fps[arm], files[arm] = rows, fp, path
        a, b = values['C'], values['SK']
        changed = sorted(k for k in a.keys() | b.keys() if contributor_rows.sig(a.get(k)) != contributor_rows.sig(b.get(k)))
        coverage = {}
        for part in ['returns', 'params', 'controller_cache', 'side_table']:
            left, right = fps['C']['parts'][part], fps['SK']['parts'][part]
            native = {k for k in left.keys() | right.keys() if left.get(k) != right.get(k)}

            def parent(key):
                if part == 'params':
                    return key.rsplit('[', 1)[0]
                if part == 'controller_cache':
                    return key.split('#', 1)[0]
                return key

            captured = {parent(k) for p, k in changed if p == part}
            assert captured == native, (setting, part, captured, native)
            coverage[part] = {'all_changed_parents_accounted_for': True, 'parents': sorted(native)}
        if any(has_rec(values[arm][key].get('ty')) for arm in ['C', 'SK'] for key in changed if key in values[arm]):
            for arm in ['C', 'SK']:
                _, resolved = contributor_rows.load(files[arm], set(changed))
                values[arm].update(resolved)
        for part, key in changed:
            entry = {'setting': setting, 'part': part, 'key': key,
                     'C': values['C'].get((part, key)), 'SK': values['SK'].get((part, key))}
            for arm in ['C', 'SK']:
                if entry[arm] is not None:
                    entry[arm].setdefault('resolved_ty', entry[arm].get('ty'))
            all_rows.append(entry)
        pair_checks[setting] = {'changed_rows': len(changed), 'parts': dict(Counter(p for p, _ in changed)),
                               'fingerprint_coverage': coverage}
        print(setting, pair_checks[setting]['parts'], flush=True)
    identities = sorted({(r['part'], r['key']) for r in all_rows})
    ids = {key: 'CW%03d' % (i + 1) for i, key in enumerate(identities)}
    for row in all_rows:
        row['row_id'] = ids[(row['part'], row['key'])]
    with (D / 'receipts/all-value-rows.jsonl').open('w') as f:
        for row in all_rows:
            f.write(json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n')
    save(D / 'receipts/value-coverage.json', {'cells': cell_checks, 'pairs': pair_checks,
        'unique_changed_keys': len(identities), 'changed_row_observations': len(all_rows),
        'reused_loader': str(RESEARCH_PROFILE / 'rows.py'), 'loader_sha256': contributor_rows.sha(RESEARCH_PROFILE / 'rows.py')})


if __name__ == '__main__':
    main()
