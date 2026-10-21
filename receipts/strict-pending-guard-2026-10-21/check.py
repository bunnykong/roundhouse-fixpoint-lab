"""Check the headline numbers of this receipt against its tables. Standard library only.

Starts no analyzer: it reads tables.json, widenings.tsv, structural-identities.tsv and the
two patches, and exits 1 if any number quoted in README.md disagrees with them.
"""
import csv
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def main():
    t = json.loads((HERE / 'tables.json').read_text())
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f'{label}: {got} != {want}')

    added = []
    for name in ('research-base.patch', 'main-port.patch'):
        lines = (HERE / name).read_text().splitlines()
        added.append([l[1:] for l in lines if l.startswith('+') and not l.startswith('+++')])
        check(f'{name} removed lines', [l for l in lines if l.startswith('-') and not l.startswith('---')], [])
    check('six added lines', len(added[0]), 6)
    check('same lines on both bases', added[0], added[1])

    r = t['research_base']
    check('research equal tables', {a: (v['mutation_writers'], v['strict_guard']) for a, v in r['equal_tables'].items()},
          {'campfire': (10, 10), 'forem': (9, 9), 'chatwoot': (9, 9), 'mastodon': (5, 10)})
    check('research Mastodon varying rows', (sum(r['varying_rows']['mastodon']['mutation_writers'].values()),
                                             sum(r['varying_rows']['mastodon']['strict_guard'].values())), (138, 0))
    for app in ('forem', 'chatwoot'):
        check(f'{app} rows unchanged', r['varying_rows'][app]['mutation_writers'], r['varying_rows'][app]['strict_guard'])
    check('research narrowed', sum(s['narrowed'] for a in r['value_changes'].values() for s in a.values()), 0)
    check('research Mastodon widened', {s: v['widened'] for s, v in r['value_changes']['mastodon'].items()},
          {'unset': 24, '1': 24, '2': 24, 'repeat': 24})
    check('research other apps widened', sum(s['widened'] for a, v in r['value_changes'].items() if a != 'mastodon'
                                             for s in v.values()), 0)
    check('research Hash arm', r['hash_arm_in_page_return'],
          {'mutation_writers': {'unset': True, '1': True, '2': False, 'repeat': True},
           'strict_guard': {'unset': False, '1': False, '2': False, 'repeat': False}})
    check('cycle component size', len(r['cycle_component']), 6)

    i = t['independent_check']
    check('fresh recount', {a: v['equal_tables'] for a, v in i['recount_v0a0'].items()},
          {'campfire': 10, 'forem': 9, 'chatwoot': 9, 'mastodon': 10})
    check('V1A1 final equal tables', {a: v['equal_tables'] for a, v in i['v1a1'].items()}, {'campfire': 10, 'mastodon': 10})

    m = t['main_port']
    check('main Mastodon equal tables', (m['mastodon']['guard_off']['equal_tables'], m['mastodon']['guard_on']['equal_tables']),
          (5, 10))
    check('main Mastodon varying rows', (sum(m['mastodon']['guard_off']['varying_rows'].values()),
                                         sum(m['mastodon']['guard_on']['varying_rows'].values())), (147, 0))
    off = {s for s, v in m['hash_arm_in_page_return'].items() if v['guard_off']}
    check('main Hash arm without guard', sorted(off), sorted(['unset', '1', '2', 'repeat', '3', '9']))
    check('main Hash arm with guard', any(v['guard_on'] for v in m['hash_arm_in_page_return'].values()), False)
    check('seeds that break equality', sorted(int(s) for s, v in m['extra_seed_varying_tables'].items() if v),
          [4, 5, 6, 7, 8, 10])
    check('main regression apps', {a: (v['guard_off']['equal_tables'], v['guard_on']['equal_tables'])
                                   for a, v in m['regression_apps'].items()},
          {'campfire': (10, 10), 'forem': (9, 9), 'chatwoot': (9, 9)})
    check('main widened rows', (m['value_changes']['unique_rows'], m['value_changes']['row_schedule_directions']),
          (24, {'widened': 288}))
    check('main structural identities', m['structural_identities'], 12)

    with open(HERE / 'widenings.tsv', newline='') as f:
        widenings = list(csv.DictReader(f, delimiter='\t'))
    check('widened rows listed', len(widenings), 24)
    check('widened rows in ResolveAccountService', {w['method'].split('#')[0] for w in widenings}, {'ResolveAccountService'})
    with open(HERE / 'structural-identities.tsv', newline='') as f:
        ident = list(csv.DictReader(f, delimiter='\t'))
    check('structural identities, research base', sum(r['condition'].startswith('research') for r in ident), 13)
    check('structural identities, main port', sum(r['condition'].startswith('main') for r in ident), 12)

    if failures:
        print('\n'.join(failures))
        return 1
    print('research base: Mastodon 5/10 -> 10/10 equal tables, 138 -> 0 varying rows; other apps unchanged')
    print('main port: Mastodon 5/10 -> 10/10 over twelve schedules, 147 -> 0 varying rows; seeds 4-8 and 10 break it without the guard')
    print('value sets: 0 narrowed; the same 24 Mastodon rows widened; structural identities 13 (research) and 12 (main)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
