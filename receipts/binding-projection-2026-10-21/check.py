"""Check the headline numbers of this receipt against its tables. Standard library only.

Starts no analyzer: it reads tables.json, binding-changes.tsv, missed-bindings.tsv and the patch,
and exits 1 if any number quoted in README.md disagrees with them.
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
    changes, missed = rows('binding-changes.tsv'), rows('missed-bindings.tsv')
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f'{label}: {got} != {want}')

    check('equal tables, guard -> projection', {a: (v['strict_guard'], v['projection']) for a, v in t['equal_tables'].items()},
          {'campfire': (10, 10), 'forem': (9, 10), 'chatwoot': (9, 10), 'mastodon': (10, 10)})
    check('varying rows with the projection', sum(sum(v['projection'].values()) for v in t['varying_rows'].values()), 0)
    check('guard binding rows that varied', {a: v['strict_guard']['controller_bindings'] for a, v in t['varying_rows'].items()},
          {'campfire': 0, 'forem': 4, 'chatwoot': 2, 'mastodon': 0})
    check('typed-table narrowings and widenings', sum(v['narrowed'] + v['widened'] for v in t['typed_table_changes'].values()), 0)
    check('Mastodon, twelve schedules', (t['mastodon_twelve_schedules']['equal_tables'],
                                         sum(t['mastodon_twelve_schedules']['varying_rows'].values())), (10, 0))
    check('independent rerun cells', len(t['independent_rerun']['fresh_cells']), 12)

    kinds = collections.Counter((r['change'], r['detail']) for r in changes)
    check('added bindings', sum(n for (c, _), n in kinds.items() if c == 'added'), 472)
    check('added by path', {d: n for (c, d), n in kinds.items() if c == 'added'},
          {'direct': 439, 'filter-transitive': 31, 'super': 2})
    check('widened values', (kinds[('widened', 'loss')], kinds[('widened', 'repair')]), (104, 9))
    check('losses in Chatwoot', sum(1 for r in changes if r['change'] == 'widened' and r['detail'] == 'loss'
                                    and r['app'] == 'chatwoot'), 95)
    check('rows changed in meaning', len({(r['app'], r['row']) for r in changes if r['change'] in ('added', 'widened')}), 482)
    check('rows that differ only in JSON form', kinds[('json-form-only', '')], 45)
    check('bindings removed', t['bindings']['totals']['bindings_removed'], 0)

    m = collections.Counter(r['kind'] for r in missed)
    check('missed bindings', m['missed binding'], 45)
    check('missed bindings by app', dict(collections.Counter(r['app'] for r in missed if r['kind'] == 'missed binding')),
          {'chatwoot': 9, 'mastodon': 36})
    check('rows holding missed bindings', len({(r['app'], r['row']) for r in missed if r['kind'] == 'missed binding'}), 27)
    check('absent Chatwoot rows', len({r['row'] for r in missed if r['kind'] == 'absent row' and r['app'] == 'chatwoot'}), 4)
    check('unexplained around-block bindings', m['unexplained around-block binding'], 12)

    patch = (HERE / 'binding-projection.patch').read_text()
    check('files in the patch', patch.count('diff --git '), 2)
    check('new module lines', sum(1 for l in patch.split('diff --git ')[1].splitlines() if l.startswith('+') and not l.startswith('+++')), 237)

    if failures:
        print('\n'.join(failures))
        return 1
    print('equal tables: Forem and Chatwoot 9/10 -> 10/10, Campfire and Mastodon stay 10/10; no varying rows; '
          'Mastodon 10/10 over twelve schedules')
    print('bindings: 482 rows change in meaning, 45 only in JSON form; 472 added (439 direct, 31 filter, 2 super); '
          '104 losses (95 Chatwoot), 9 repairs')
    print('both tables miss 45 bindings in 27 rows (36 Mastodon, 9 Chatwoot) and 4 Chatwoot rows')
    return 0


if __name__ == '__main__':
    sys.exit(main())
