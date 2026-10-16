#!/usr/bin/env python3
"""Record final custody and equality checks without rerunning native analyses."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

D = Path(__file__).resolve().parents[1]
F = D.parents[1]
NATIVE_PROFILE = D.parent / 'strict-producer-reasons'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    coverage = read(D / 'receipts/value-coverage.json')
    cells = {}
    for name, row in sorted(coverage['cells'].items()):
        original = read(row['original_result'])
        observed = read(row['result'])
        assert original['valid'] and observed['valid'], name
        equal = {key: value == observed['observations'].get(key)
                 for key, value in original['observations'].items()}
        assert set(original['observations']) == set(observed['observations']), name
        assert all(equal.values()), (name, equal)
        assert original['input_tree_sha256'] == observed['input_tree_sha256'], name
        reason_file = original['observations']['reason_rows']['file']
        reason_hashes = [sha(Path(r['directory']) / reason_file) for r in [original, observed]]
        assert reason_hashes[0] == reason_hashes[1] == original['observations']['reason_rows']['sha256'], name
        cells[name] = {
            'original_result': row['original_result'],
            'original_result_sha256': sha(row['original_result']),
            'value_probe_result': row['result'],
            'value_probe_result_sha256': sha(row['result']),
            'equal_observations': equal,
            'reason_file_sha256': reason_hashes[0],
            'equal_table_digests': len(original['observations']['value_digests']),
        }
    freeze = read(NATIVE_PROFILE / 'receipts/source-freeze.json')
    assert all(sha(NATIVE_PROFILE / 'repo' / p) == h for p, h in freeze['source_files'].items())
    pins = read(D / 'receipts/probe-pins.json')
    assert sha(D / 'bin/roundhouse') == pins['binary_sha256']
    assert not (D / 'target').exists()
    rows = [json.loads(line) for line in (D / 'receipts/classified-rows.jsonl').open()]
    summary = read(D / 'receipts/classification-summary.json')
    assert len(rows) == summary['total_row_observations'] == 104
    actual = Counter(row['verdict'] for row in rows)
    assert {key: actual[key] for key in summary['counts']} == summary['counts']
    for row in rows:
        assert row['witnesses']
        if row['verdict'] == 'unsound narrowing':
            assert any(w['C_admits'] and not w['SK_admits'] for w in row['witnesses'])
        elif row['verdict'] == 'no runtime change':
            assert row['relation'] == 'EQ'
            assert all(w['C_admits'] and w['SK_admits'] for w in row['witnesses'])
        else:
            raise AssertionError(row['verdict'])
    for witness in ['oauth-witnesses', 'runtime-witnesses']:
        assert 'ruby 4.0.7 ' in read(D / 'receipts' / (witness + '.json'))['ruby']
        assert not (D / 'receipts' / (witness + '.stderr')).read_bytes()
    files = [D / 'RESULT.md']
    files += sorted((D / 'scripts').glob('*.py'))
    files += sorted((D / 'witnesses').glob('*.rb'))
    files += [p for p in sorted((D / 'receipts').iterdir())
              if p.is_file() and p.name != 'final-integrity.json']
    result = {
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'condition': summary['condition'], 'source': freeze['commit'],
        'cells': cells, 'all_observations_equal': True,
        'original_table_digests_reproduced': sum(c['equal_table_digests'] for c in cells.values()),
        'frozen_source_files_unchanged': len(freeze['source_files']),
        'owned_target_cleaned': True, 'classified_rows_checked': len(rows),
        'artifact_sha256': {str(p.relative_to(D)): sha(p) for p in files},
    }
    (D / 'receipts/final-integrity.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['cells', 'artifact_sha256']}, indent=2))


if __name__ == '__main__':
    main()
