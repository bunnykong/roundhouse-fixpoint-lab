"""Check the headline numbers of this receipt against its tables. Standard library only.

Starts no analyzer: it reads tables.json, the TSV files and reason-row.json, and exits 1 if any
number quoted in README.md disagrees with them.
"""
import collections
import csv
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def rows(name):
    with open(HERE / name, newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def main():
    t = json.loads((HERE / 'tables.json').read_text())
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f'{label}: {got} != {want}')

    eq = t['equal_tables_and_varying_rows']
    check('equal tables', {a: v['equal_tables'] for a, v in eq.items()},
          {'campfire': 10, 'forem': 10, 'chatwoot': 10, 'mastodon': 10})
    check('varying rows', sum(v['varying_rows'] for v in eq.values()), 0)
    check('Mastodon cells', eq['mastodon']['cells'], 12)
    comps = t['value_comparisons']
    check('narrowed or widened', sum(c['narrowed'] + c['widened'] for a in comps.values() for c in a.values()), 0)
    check('added per schedule', {a: sorted({c['missing'] for c in v.values()}) for a, v in comps.items()},
          {'campfire': [0], 'forem': [0], 'chatwoot': [31], 'mastodon': [7]})
    form_only = sum(n for a in ('chatwoot', 'mastodon') for k, n in comps[a]['unset']['changed_signatures'].items()
                    if k.split('/')[1].startswith('EQ'))
    check('rows that change form only', form_only, 53)
    check('fresh cells', len(t['independent_rerun']['fresh_cells']), 8)
    check('fresh cells match', t['independent_rerun']['all_match_originals'], True)
    check('flag-off parity', all(all(v.values()) for v in t['flag_off_parity'].values()), True)

    laws = t['laws']
    off, on = laws['profile-audit-off'], laws['profile-audit-on']
    check('law rows', (off['rows'], on['rows']), (5022, 5022))
    check('catalog strictness, flag pair', (off['catalog_strictness'].get('FAIL'), on['catalog_strictness'].get('FAIL', 0),
                                            on['catalog_strictness']['PASS']), (21, 0, 85))
    check('other laws with the flag', (on['status']['FAIL'], on['status']['UNKNOWN']), (916, 123))
    check('only the catalog rows change', off['status']['FAIL'] - on['status']['FAIL'], 21)
    strict = rows('catalog-strictness.tsv')
    check('fixed projections', (len(strict), {(r['before_status'], r['after_status']) for r in strict}), (21, {('FAIL', 'PASS')}))

    added = rows('added-identities.tsv')
    check('added identities', dict(collections.Counter(r['kind'] for r in added)), {'Narrow': 7, 'Param': 30, 'At': 1})
    check('Param slots equal unchanged rows', all(r['relation'] == 'EQ' and r['params_row_unchanged'] == 'true'
                                                  for r in added if r['kind'] == 'Param'), True)

    barrier = rows('completion-barrier.tsv')
    increases = [100 * (int(r['f76']) - int(r['f75'])) / int(r['f75']) for r in barrier]
    check('barrier cells', len(barrier), 24)
    check('more Pending in every cell', all(x > 0 for x in increases), True)
    check('barrier range', (round(min(increases), 1), round(max(increases), 1)), (3.6, 7.7))

    reason = json.loads((HERE / 'reason-row.json').read_text())['rows']
    check('schedule-dependent reason rows', len(reason), 1)
    r = reason[0]
    check('F75 provenance', {s: v['untyped_kinds'] for s, v in r['f75'].items()}, {'unset': 4, '1': 4, '2': 4, 'repeat': 4})
    check('F76 provenance', {s: v['untyped_kinds'] for s, v in r['f76'].items()}, {'unset': 4, '1': 2, '2': 2, 'repeat': 4})
    check('type unchanged', len({v['type_hash'] for v in list(r['f75'].values()) + list(r['f76'].values())}), 1)

    if failures:
        print('\n'.join(failures))
        return 1
    print('four apps 10/10, no varying rows, no narrowing or widening; 38 added identities (30 Param, 7 Narrow, 1 At)')
    print('laws, flag pair: catalog strictness 21 FAIL -> 0; other laws 916 FAIL, 123 UNKNOWN')
    print(f'costs: {min(increases):.1f}-{max(increases):.1f}% more Pending at the barrier; one Chatwoot reason row '
          'Unresolved at unset/repeat, Gradual at 1/2')
    return 0


if __name__ == '__main__':
    sys.exit(main())
