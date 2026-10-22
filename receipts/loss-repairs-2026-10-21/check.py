"""Check the headline numbers of this receipt against its data. Python 3.9+, standard library only.

Starts no analyzer. Admission reuses the F73 receipt's checker (the census's rules over the F61 runtime-set
relation in tools/probe/runtime_sets.py). Exits 1 if any number quoted in README.md disagrees with the data.
"""
import collections
import csv
import importlib.util
import io
import json
import lzma
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'f73_check', HERE.parent / 'mutation-writers-census-2026-10-21' / 'witnesses' / 'check.py')
f73 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f73)
sets = f73.sets

ARMS = ('f75', 'route_per_class_and_class_body_sites', 'plus_string_parameter_keys')


def strip_u(t):
    """The type with every Unresolved arm removed, at any depth; None if only Unresolved remains."""
    kind = t.get('kind')
    if kind in ('untyped', 'var'):
        return None
    if kind == 'union':
        arms = [a for a in (strip_u(v) for v in t['variants']) if a is not None]
        if not arms:
            return None
        return arms[0] if len(arms) == 1 else {'kind': 'union', 'variants': arms}
    bottom = {'kind': 'bottom'}
    if kind == 'hash':
        return dict(t, key=strip_u(t['key']) or bottom, value=strip_u(t['value']) or bottom)
    if kind == 'array':
        return dict(t, elem=strip_u(t['elem']) or bottom)
    if kind == 'class' and t.get('args'):
        return dict(t, args=[strip_u(a) or bottom for a in t['args']])
    return t


def admitted(row_type, witness):
    t = row_type
    if witness['position'] == '$/ret' and t.get('kind') == 'fn':
        t = t['ret']
    return f73.admits(t, witness['type']) is True


def tsv(text):
    return list(csv.DictReader(io.StringIO(text), delimiter='\t'))


def main():
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f'{label}: {got} != {want}')

    rows = json.loads((HERE / 'f73-rows.json').read_text())['rows']
    admits = {arm: {r['census_id'] for r in rows if all(admitted(r['types'][arm], w) for w in r['witnesses'])}
              for arm in ARMS}
    check('F73 rows', len(rows), 21)
    check('admitted with F75', admits['f75'], set())
    first = {'A010', 'A013', 'A014', 'C1855', 'C1856', 'M945', 'M1273', 'M1786', 'M1848', 'M1904'}
    check('admitted with routes and class-body sites', admits['route_per_class_and_class_body_sites'], first)
    check('admitted with String keys too', admits['plus_string_parameter_keys'], first | {'M130', 'M131', 'M650'})
    remaining = {r['census_id'] for r in rows} - admits['plus_string_parameter_keys']
    check('remaining losses', len(remaining), 8)
    check('recorded four-schedule admissions', {r['census_id']: r['admits_on_four_schedules']['plus_string_parameter_keys']
                                               for r in rows}, {r['census_id']: ('4/4' if r['census_id'] not in remaining
                                                                                 else '0/4') for r in rows})
    check('F72 rows among them', {r['f72_census_id']: r['census_id'] for r in rows if r['f72_census_id']},
          {'C2311': 'C1748', 'C2428': 'C1856', 'M586': 'M385', 'M2643': 'M1848'})

    t = json.loads((HERE / 'tables.json').read_text())
    a = t['against_f75']
    check('equal tables', {k: v['candidate']['equal_tables'] for k, v in a.items()},
          {'campfire': 10, 'forem': 10, 'chatwoot': 10, 'mastodon': 10})
    check('varying rows', sum(v['candidate']['varying_rows'] for v in a.values()), 0)
    check('narrowed / widened', {k: (v['unset']['narrowed'], v['unset']['widened']) for k, v in a.items()},
          {'campfire': (9, 148), 'forem': (1, 375), 'chatwoot': (0, 644), 'mastodon': (65, 867)})
    check('identity changes', sum(v['unset']['missing'] for v in a.values()), 2308)
    ids = t['parameter_identity_changes']
    check('identity changes split', (ids['added'], ids['removed'], ids['removed_empty_rows'],
                                     ids['removed_moved_to_class_side_equal'], ids['removed_with_value_change']),
          (2007, 301, 295, 6, 0))

    narrow = tsv((HERE / 'narrowings.tsv').read_text())
    check('narrowings', len(narrow), 75)
    check('narrowings drop only Unresolved', all(strip_u(json.loads(n['control'])) is None or
                                                 sets.covers(json.loads(n['candidate']), strip_u(json.loads(n['control'])))
                                                 for n in narrow), True)
    check('bare / arm', collections.Counter(n['drops'] for n in narrow), {'bare Unresolved': 57, 'Unresolved arm': 18})
    check('verdicts', collections.Counter(n['verdict'] for n in narrow), {'admit': 74, 'guarded-skip': 1})
    check('Proc-encoded admissions', sum(1 for n in narrow if 'Proc encoded' in n['note']), 2)

    wid = tsv(lzma.decompress((HERE / 'widenings.tsv.xz').read_bytes()).decode())
    causes = collections.Counter(w['cause'] for w in wid)
    check('widenings', len(wid), 2034)
    check('widenings by cause', dict(causes), {'per-class routes': 1962, 'class-body sites': 61, 'both flags': 11})

    timing = tsv((HERE / 'timing.tsv').read_text())
    ratio = collections.defaultdict(list)
    extra = collections.defaultdict(list)
    for r in timing:
        app = r['cell'].split('/')[0]
        ratio[app].append(float(r['ratio']))
        extra[app].append(float(r['seconds_with_flags']) - float(r['seconds_f75_same_moment']))
    check('Forem time', (round(100 * min(ratio['forem']) - 100), round(100 * max(ratio['forem']) - 100)), (21, 22))
    check('Chatwoot and Mastodon time', (round(100 * min(ratio['chatwoot'] + ratio['mastodon']) - 100),
                                         round(100 * max(ratio['chatwoot'] + ratio['mastodon']) - 100)), (12, 14))
    check('Campfire seconds', (round(min(extra['campfire']), 1), round(max(extra['campfire']), 1)), (0.5, 0.9))

    if failures:
        print('\n'.join(failures))
        return 1
    print('F73 rows: 10 admitted with routes and class-body sites, 13 with String keys too; 8 remain')
    print('against F75: 10/10 equal tables, no varying rows; 75 narrowings drop only Unresolved; 2,034 widenings, '
          '1,962 from per-class routes')
    print('time: +21-22% Forem, +12-14% Chatwoot and Mastodon, +0.5-0.9 s Campfire')
    return 0


if __name__ == '__main__':
    sys.exit(main())
