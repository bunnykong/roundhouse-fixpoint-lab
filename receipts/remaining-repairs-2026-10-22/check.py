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

EARLIER = {'A010', 'A013', 'A014', 'M945', 'M1273', 'M130', 'M131', 'M650', 'C1855', 'C1856', 'M1786', 'M1848',
           'M1904'}
NEW = {'sidekiq_rows': {'M385', 'M1491'}, 'render_bindings': {'C1748'}, 'ivar_call_joins': {'C575', 'C578'},
       'memo_aliases': {'M1545'}}


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
    if t is None:
        return False
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
    by_id = {r['census_id']: r for r in rows}

    def admits(arm, which=None):
        return {r['census_id'] for r in rows if (which is None or r['census_id'] in which)
                and arm in r['types'] and all(admitted(r['types'][arm], w) for w in r['witnesses'])}

    new = set().union(*NEW.values())
    check('F73 rows', len(rows), 21)
    check('admitted under F77', admits('f77'), EARLIER)
    check('admitted with the four flags', admits('sound_rest'), EARLIER | new)
    check('recorded four-schedule admissions', {r['census_id']: r['admits_on_four_schedules'] for r in rows},
          {cid: {'f77': '4/4' if cid in EARLIER else '0/4', 'sound_rest': '4/4' if cid in EARLIER | new else '0/4'}
           for cid in by_id})
    open_rows = set(by_id) - EARLIER
    for arm, own in NEW.items():
        check(f'{arm} alone admits its own rows', admits(arm, open_rows), own)
    check('admitted without Unresolved arms', {cid for cid in new if strip_u(by_id[cid]['types']['sound_rest'])
                                               is not None and all(admitted(strip_u(by_id[cid]['types']['sound_rest']), w)
                                                                   for w in by_id[cid]['witnesses'])}, {'M385'})
    check('M385 gains Str', [v['kind'] for v in by_id['M385']['types']['sound_rest']['variants']],
          ['bool', 'str', 'untyped', 'nil'])
    tally = collections.defaultdict(set)
    for r in rows:
        tally[r['reader_visible_repair']].add(r['census_id'])
    check('reader-visible repairs', tally['yes'], {'A010', 'A013', 'A014', 'M945', 'M1273', 'M130', 'M650'} | new - {'C575'})
    check('repairs no reader sees', tally['no'], {'C1855', 'C1856', 'M1786', 'M1848', 'M1904', 'M131', 'C575'})
    check('remaining', tally['remains'], {'C1376', 'C1465'})
    check('census rule: unread rows', {r['census_id'] for r in rows if r['reader']['census_rule'] == 'c'},
          {'C1855', 'C1856', 'M1786', 'M1848', 'M1904', 'M131'})

    t = json.loads((HERE / 'tables.json').read_text())
    a = t['against_f77']
    check('equal tables', {k: (v['f77']['equal_tables'], v['candidate']['equal_tables']) for k, v in a.items()},
          {k: (10, 10) for k in a})
    check('varying rows', sum(v['f77']['varying_rows'] + v['candidate']['varying_rows'] for v in a.values()), 0)
    check('narrowed / widened / incomparable', {k: (v['unset']['narrowed'], v['unset']['widened'],
                                                    v['unset']['incomparable']) for k, v in a.items()},
          {'campfire': (0, 0, 0), 'forem': (160, 1010, 6), 'chatwoot': (1, 166, 2), 'mastodon': (117, 701, 1)})
    check('diagnostics', {k: (v['f77']['diagnostics'], v['candidate']['diagnostics']) for k, v in a.items()},
          {'campfire': (485, 485), 'forem': (8820, 8915), 'chatwoot': (8150, 8170), 'mastodon': (7176, 7168)})
    check('Chatwoot errors added', a['chatwoot']['diagnostic_delta'].get('error/unsupported'), 2)
    split = collections.Counter()
    for v in a.values():
        split.update(v['unclassified_split'])
    check('unclassified rows', (sum(v['unset']['missing'] for v in a.values()), dict(split)),
          (1243, {'row absent from control': 1139, 'row absent from candidate': 88,
                  'changed fingerprint has no serialized type': 16}))
    check('flags off equals F77', [(p['cell'], p['equal_to_f77_on_nine_fields']) for p in t['flags_off_parity']],
          [('campfire/unset', True), ('forem/unset', True)])

    narrow = tsv((HERE / 'narrowings.tsv').read_text())
    check('narrowings', len(narrow), 278)
    check('narrowings by app', dict(collections.Counter(n['app'] for n in narrow)),
          {'forem': 160, 'chatwoot': 1, 'mastodon': 117})
    check('what they drop', dict(collections.Counter(n['drops'] for n in narrow)),
          {'bare Unresolved': 201, 'nested Unresolved': 43, 'Unresolved arm': 33, 'concrete arms': 1})
    keeps = [n for n in narrow if strip_u(json.loads(n['control'])) is None or
             sets.covers(json.loads(n['candidate']), strip_u(json.loads(n['control'])))]
    check('narrowings that drop only Unresolved', len(keeps), 277)
    verdict = collections.Counter()
    for n in narrow:
        ok = f73.admits(json.loads(n['candidate']), json.loads(n['witness_type'])) is True
        verdict[(n['verdict'], ok)] += 1
    check('witness verdicts', dict(verdict), {('admit', True): 270, ('guarded', True): 4, ('reject', False): 4})
    rejects = [n for n in narrow if n['verdict'] == 'reject']
    check('rejections', {(n['app'], n['flag'], 'co_author_ids' in n['note'], n['witness']) for n in rejects},
          {('forem', 'render bindings', True, '[2, 3]')})
    check('admitted through a runtime-value encoding', sum(1 for n in narrow if 'encoding' in n['note']), 22)
    check('narrowings by flag', dict(collections.Counter(n['flag'] for n in narrow)),
          {'Sidekiq rows': 219, 'render bindings': 50, 'memo aliases': 7, 'Sidekiq rows and ivar call joins': 2})

    wid = tsv(lzma.decompress((HERE / 'widenings.tsv.xz').read_bytes()).decode())
    check('widenings', len(wid), 1877)
    check('widenings by table', dict(collections.Counter(w['table'] for w in wid)),
          {'ir': 1075, 'controller_cache': 672, 'params': 82, 'returns': 44, 'side_table': 4})
    check('widenings by kind', dict(collections.Counter(w['kind'] for w in wid)),
          {'to bare Unresolved': 632, 'gains Unresolved': 921, 'Unresolved on both sides': 123, 'no Unresolved': 201})
    check('kinds recomputed', all(
        (json.loads(w['candidate']).get('kind') == 'untyped') == (w['kind'] == 'to bare Unresolved') for w in wid), True)
    flags = collections.Counter(w['flag'] for w in wid)
    check('widenings by flag', (flags['ivar call joins'], flags['Sidekiq rows'], flags['render bindings'],
                                flags['memo aliases'], flags['two flags'] + flags['Sidekiq rows and ivar call joins']),
          (1528, 176, 101, 61, 11))
    check('ivar call joins to bare Unresolved', sum(1 for w in wid if w['flag'] == 'ivar call joins' and
                                                     w['kind'] == 'to bare Unresolved'), 606)

    readers = tsv((HERE / 'widening-readers.tsv').read_text())
    check('widening reader sample', dict(collections.Counter(r['reader_class'] for r in readers)),
          {'analyzed body': 24, 'analyzed body (view seed)': 1, 'cached controller body': 9, 'none': 6})

    timing = tsv((HERE / 'timing.tsv').read_text())
    ratio = collections.defaultdict(list)
    for r in timing:
        ratio[(r['source'], r['cell'].split('/')[0])].append(float(r['ratio']))

    def pct(xs):
        return round(100 * min(xs) - 100), round(100 * max(xs) - 100)

    check('Forem time', pct(ratio[('check', 'forem')]), (14, 17))
    check('Chatwoot and Mastodon time', pct(ratio[('check', 'chatwoot')] + ratio[('check', 'mastodon')]), (1, 3))
    check('Campfire time', pct(ratio[('check', 'campfire')]), (4, 4))
    medians = {app: round(sorted(ratio[('original', app)])[1] / 2 + sorted(ratio[('original', app)])[2] / 2, 2)
               for app in ('campfire', 'forem', 'chatwoot', 'mastodon')}
    check('original medians', medians, {'campfire': 1.16, 'forem': 1.1, 'chatwoot': 1.03, 'mastodon': 1.03})

    if failures:
        print('\n'.join(failures))
        return 1
    print("F73 rows: 13 admitted under F77, 19 with the four flags; C1376 and C1465 remain")
    print('readers: 12 reader-visible repairs, 7 repairs no reader sees; 5 of the 6 new ones admit only through '
          'Unresolved')
    print('against F77: 10/10 equal tables, no varying rows; 278 narrowings, 274 admit and 4 reject; 1,877 '
          'widenings, 632 to bare Unresolved, 1,528 from ivar call joins')
    print('time: +14-17% Forem, +1-3% Chatwoot and Mastodon, +4% Campfire (same-moment pairs)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
