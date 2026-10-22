#!/usr/bin/env python3
"""Join the checker's verdicts with F73's census: agreement with the 176 hand proofs, the negative controls,
counts per stratum, reader class and pattern, and the recomputed bound. Python 3.9+, standard library only.

Usage: python3 -B validate.py [DIR]
DIR holds verdicts.jsonl, f72-verdicts.jsonl and f72-ablated.jsonl from checker.rb; without it the published
outputs next to this file are used. Writes agreement.tsv and bound.json into DIR (or prints them only, without
DIR). Exits 1 if any number quoted in README.md disagrees with the data.
"""
import collections
import csv
import io
import json
import lzma
from math import comb
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
F73 = HERE.parent / 'mutation-writers-census-2026-10-21'
READERS = HERE.parent / 'census-by-reader-2026-10-22' / 'population-readers.tsv.xz'
CENSUS_PATTERNS = ['fresh constructor', 'fixed key schema', 'dominating guard', 'closed caller set',
                   'exhaustive returns', 'other']
VISIBLE = {'a', 'b'}
CIRCULAR = ('M1708', 'M1745')


def tsv(text):
    return list(csv.DictReader(io.StringIO(text), delimiter='\t'))


def jsonl(path):
    raw = lzma.decompress(path.read_bytes()).decode() if path.suffix == '.xz' else path.read_text()
    return [json.loads(line) for line in raw.splitlines()]


def upper(N, n, k, alpha_denominator):
    """Largest K with P[Hypergeometric(N, K, n) <= k] > 1/alpha_denominator, in exact integers.

    Written independently of F73's bounds.py; main() checks that it reproduces F73's recorded counts."""
    if N == 0:
        return 0
    total = comb(N, n)

    def accepted(K):
        tail = sum(comb(K, x) * comb(N - K, n - x) for x in range(max(0, n - (N - K)), min(k, K, n) + 1))
        return tail * alpha_denominator > total

    lo, hi = k, N
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if accepted(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# Misses read by hand: (category, detail). The other misses are classified from the checker's reason.
CALLEE = 'callee proved, call not resolved'
BY_HAND = {
    'M1708': ('IR-only evidence', 'per-call-site copy of `**kwargs`; other pinned vary_by callers pass unless:/if:'),
    'M1745': ('IR-only evidence', 'per-call-site copy of `**kwargs`; other pinned vary_by callers pass unless:/if:'),
    'M403': ('stricter trust base', 'is_a?(Hash) admits Hash subclasses (HashWithIndifferentAccess); hash types exclude them'),
    'C1528': ('stricter trust base', 'to_s on an unknown receiver is not assumed to return a String'),
    'F126': ('stricter trust base', 'map on an unknown receiver is not assumed to return an Array'),
    'C648': (CALLEE, 'callee row C1920 Contact#prepare_jsonb_attributes is proved'),
    'C503': (CALLEE, 'callee row C1903 PortalsController#live_chat_widget_params is proved'),
    'F034': (CALLEE, 'callee row F531 Search::ReadingList.search_documents is proved'),
    'F246': (CALLEE, 'callee row F531 Search::ReadingList.search_documents is proved'),
    'F434': ('instance variable', 'ERB view reads an ivar binding set by the controller'),
    'F465': ('caller enumeration', 'vacuous explicit-argument slot'),
    'A023': ('caller enumeration', "KeywordSplat of the helper's **attributes"),
}


def cause(row_id, reason):
    if row_id in BY_HAND:
        return BY_HAND[row_id]
    if reason.startswith('synthetic IR node'):
        return 'IR-only evidence', 'synthetic constructor without a source span'
    if 'row: no source expression' in reason or 'parameter ' in reason:
        return 'caller enumeration', reason
    if 'instance_variable' in reason or 'Ivar' in reason:
        return 'instance variable', reason
    return 'interprocedural or library call', reason


def bound(strata, rows, status, closed, readers=None):
    """F73's conservative bound with `closed` rows removed from every stratum.

    Closed rows contribute zero. In each stratum the remaining N' rows are bounded by the sampled rows among
    them (a simple random sample of the N', given n'), counting losses and witness-only rows as possible
    losses, at 0.05/4 per sampled stratum; censused strata contribute exact counts."""
    out, total_upper, total_N = [], 0, 0
    for s in strata:
        key = (s['app'], s['stratum'])
        pop = [i for i, r in rows.items() if (r['app'], r['stratum']) == key and (readers is None or readers[i] in VISIBLE)]
        if not pop:
            continue
        rest = [i for i in pop if i not in closed]
        smp = [i for i in rest if i in status]
        k = sum(status[i] == 'UNSOUND' for i in smp)
        u = sum(status[i] == 'WITNESS_ONLY' for i in smp)
        censused = s['population'] == s['sample']
        up = k + u if censused else upper(len(rest), len(smp), k + u, 80)
        out.append(dict(app=s['app'], stratum=s['stratum'], N=len(pop), closed=len(pop) - len(rest), N_rest=len(rest),
                        n_rest=len(smp), k=k, u=u, upper=up, censused=censused))
        total_upper += up
        total_N += len(pop)
    return out, total_upper, total_N


def projection(detail, N, target_rate=0.10, resolved=True):
    """Extra sampled rows that bring the simultaneous bound under the target.

    New rows are drawn from each sampled stratum's unproved remainder, in proportion to its size, and show the
    remainder's observed rate: losses only (resolved=True: every new row ends proved or lossy) or losses plus
    witness-only rows (resolved=False: F73's conservative rule). Returns (extra rows or None, floor); the floor
    is what a full census of the remainder would give."""
    limit = int(target_rate * N)
    sampled = [d for d in detail if not d['censused']]
    fixed = sum(d['upper'] for d in detail if d['censused'])
    rate = {id(d): (d['k'] if resolved else d['k'] + d['u']) / d['n_rest'] for d in sampled}
    floor = fixed + sum(round(rate[id(d)] * d['N_rest']) for d in sampled)
    pool = sum(d['N_rest'] - d['n_rest'] for d in sampled)

    def total(extra):
        out = fixed
        for d in sampled:
            add = min(d['N_rest'] - d['n_rest'], round(extra * (d['N_rest'] - d['n_rest']) / pool))
            n = d['n_rest'] + add
            out += upper(d['N_rest'], n, round(rate[id(d)] * n), 80)
        return out

    if total(pool) > limit:
        return None, floor
    lo, hi = 0, pool
    while lo < hi:
        mid = (lo + hi) // 2
        if total(mid) <= limit:
            hi = mid
        else:
            lo = mid + 1
    return lo, floor


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    src = out_dir or HERE
    verdicts = {v['id']: v for v in jsonl(src / ('verdicts.jsonl' if out_dir else 'verdicts.jsonl.xz'))}
    rows = {r['id']: r for r in jsonl(HERE / 'rows.jsonl.xz')}
    sample = {r['census_id']: r for r in tsv((F73 / 'sample.tsv').read_text())}
    args = {r['census_id']: r for r in tsv((F73 / 'source-arguments.tsv').read_text())}
    patterns = {r['title']: r['pattern'] for r in tsv((HERE / 'hand-proof-patterns.tsv').read_text())}
    losses = json.loads((F73 / 'losses.json').read_text())['rows']
    strata = json.loads((F73 / 'bounds.json').read_text())['strata']
    readers = {r['census_id']: r['reader'] for r in tsv(lzma.decompress(READERS.read_bytes()).decode())}
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f'{label}: {got} != {want}')

    check('rows', (len(rows), len(verdicts), set(rows) == set(verdicts)), (4652, 4652, True))
    proved = {i for i, v in verdicts.items() if v['verdict'] == 'PROVED'}
    status = {i: r['status'] for i, r in sample.items()}

    # F73 reproduction: the independent `upper` gives F73's counts with nothing closed.
    _, base, N = bound(strata, rows, status, set())
    _, vbase, vN = bound(strata, rows, status, set(), readers)
    check('F73 bound reproduced', (base, N, vbase, vN), (2202, 4652, 1907, 3974))

    # 1. Agreement with the 176 hand proofs.
    hand = {i: patterns[a['title']] for i, a in args.items()}
    check('hand proofs', (len(hand), all(sample[i]['status'] == 'SOURCE_SUPPORTED' for i in hand)), (176, True))
    per = collections.OrderedDict((p, [0, 0]) for p in CENSUS_PATTERNS)
    causes, same_label, lines = collections.Counter(), 0, []
    for i in sorted(hand, key=lambda x: (CENSUS_PATTERNS.index(hand[x]), x)):
        v = verdicts[i]
        ok = v['verdict'] == 'PROVED'
        per[hand[i]][0 if ok else 1] += 1
        cat, detail = ('', '') if ok else cause(i, v.get('reason') or '')
        same_label += ok and v['pattern'] == hand[i]
        causes[cat] += not ok
        lines.append([i, hand[i], v['verdict'], v.get('pattern') or '', v.get('value') or '', v.get('reason') or '',
                      cat, detail, args[i]['title']])
    check('agreement by census pattern', {p: tuple(x) for p, x in per.items()},
          {'fresh constructor': (66, 12), 'fixed key schema': (20, 8), 'dominating guard': (2, 12),
           'closed caller set': (0, 13), 'exhaustive returns': (0, 41), 'other': (0, 2)})
    check('agreed rows with the census label', same_label, 87)
    check('causes of the misses', {k: v for k, v in causes.items() if v},
          {'caller enumeration': 40, 'interprocedural or library call': 27, 'IR-only evidence': 11,
           CALLEE: 4, 'stricter trust base': 3, 'instance variable': 3})
    outside = [l[0] for l in lines if 'outside' in l[5]]
    check('misses that name a value outside the type', outside, ['M403'])

    # 2. Negative controls.
    loss_ids = [r['census_id'] for r in losses]
    witness_only = [i for i, s in status.items() if s == 'WITNESS_ONLY']
    check('F73 losses proved', (len(loss_ids), sorted(set(loss_ids) & proved)), (21, []))
    check('F73 witness-only rows proved', (len(witness_only), sorted(set(witness_only) & proved)), (34, []))
    labels = {r['f72_census_id']: r['label'] for r in tsv((HERE / 'f72-labels.tsv').read_text())}
    f72 = {}
    for name in ('f72-verdicts.jsonl', 'f72-ablated.jsonl'):
        ver = {v['id']: v for v in jsonl(src / name)}
        check(f'{name} rows', set(ver), set(labels))
        bad = sorted((i for i, l in labels.items() if l != 'SOUND' and ver[i]['verdict'] == 'PROVED'),
                     key=lambda x: (x[0], int(x[1:])))
        sound = [i for i, l in labels.items() if l == 'SOUND']
        f72[name] = dict(losses=sum(l != 'SOUND' for l in labels.values()), losses_proved=bad, sound=len(sound),
                         sound_proved=sum(ver[i]['verdict'] == 'PROVED' for i in sound))
    check('F72 labels', dict(collections.Counter(labels.values())), {'UNSOUND': 56, 'INHERITED_UNSOUND': 6, 'SOUND': 75})
    check('F72 control', (f72['f72-verdicts.jsonl']['losses_proved'], f72['f72-verdicts.jsonl']['sound_proved']), ([], 60))
    check('F72 control without mutation analysis', f72['f72-ablated.jsonl']['losses_proved'],
          ['C761', 'C1176', 'C1431', 'C1432', 'F127', 'F218', 'F219', 'F287', 'M1299'])

    # 3. Proved rows in the population.
    by_stratum = collections.Counter((rows[i]['app'], rows[i]['stratum']) for i in proved)
    check('proved', len(proved), 1922)
    check('proved per stratum', {f'{a}/{s}': n for (a, s), n in sorted(by_stratum.items())},
          {'campfire/unknown': 27, 'chatwoot/unknown': 923, 'forem/unknown': 202, 'mastodon/concrete_nil': 20,
           'mastodon/unknown': 750})
    check('proved per reader class', dict(collections.Counter(readers[i] for i in proved)), {'a': 1199, 'b': 348, 'c': 375})
    check('proved per pattern', dict(collections.Counter(verdicts[i]['pattern'] for i in proved)),
          {'fresh constructor': 1397, 'fixed key schema': 447, 'exhaustive returns': 53, 'dominating guard': 25})
    check('proved per table', dict(collections.Counter(rows[i]['table'] for i in proved)),
          {'ir': 1493, 'controller_cache': 376, 'returns': 53})

    # 4. The bound with proved rows closed, with F73's statuses and with the two circular proofs unproved.
    detail, up, _ = bound(strata, rows, status, proved)
    vdetail, vup, _ = bound(strata, rows, status, proved, readers)
    det = sum(d['k'] if d['censused'] else upper(d['N_rest'], d['n_rest'], d['k'], 80) for d in detail)
    check('bound with proved rows closed', (up, vup, det), (2112, 1824, 1055))
    unknown = [d for d in detail if not d['censused']]
    check('sampled possible losses kept', (sum(d['k'] + d['u'] for d in unknown), sum(d['n_rest'] for d in unknown)), (44, 92))
    corrected = dict(status, **{i: 'WITNESS_ONLY' for i in CIRCULAR})
    _, cbase, _ = bound(strata, rows, corrected, set())
    _, cvbase, _ = bound(strata, rows, corrected, set(), readers)
    _, cup, _ = bound(strata, rows, corrected, proved)
    _, cvup, _ = bound(strata, rows, corrected, proved, readers)
    check('bounds with the two circular proofs unproved', (cbase, cvbase, cup, cvup), (2301, 2009, 2183, 1899))
    runs_c, floor_c = projection(detail, N, resolved=False)
    runs_r, floor_r = projection(detail, N, resolved=True)
    check('projection', (runs_c, floor_c, runs_r, floor_r), (None, 1523, 1571, 409))

    result = dict(
        proved=len(proved), agreement={p: x for p, x in per.items()}, disagreement_causes=dict(causes),
        f73_losses_proved=[], f73_witness_only_proved=[], f72_control=f72,
        per_stratum={f'{a}/{s}': [by_stratum[(a, s)], sum(1 for r in rows.values() if (r['app'], r['stratum']) == (a, s))]
                     for a, s in sorted({(r['app'], r['stratum']) for r in rows.values()})},
        bound=dict(upper=up, population=N, strata=detail),
        bound_reader_visible=dict(upper=vup, population=vN, strata=vdetail),
        detection_bound=dict(upper=det),
        circular_proofs_unproved=dict(rows=list(CIRCULAR), f73=cbase, f73_reader_visible=cvbase, closed=cup,
                                      closed_reader_visible=cvup),
        projection=dict(conservative=dict(extra_rows=runs_c, floor=floor_c),
                        resolved=dict(extra_rows=runs_r, floor=floor_r)))
    if out_dir:
        buf = io.StringIO()
        w = csv.writer(buf, delimiter='\t', lineterminator='\n')
        w.writerow(['census_id', 'census_pattern', 'checker', 'checker_pattern', 'value', 'reason', 'cause',
                    'cause_detail', 'census_title'])
        w.writerows(lines)
        (out_dir / 'agreement.tsv').write_text(buf.getvalue())
        (out_dir / 'bound.json').write_text(json.dumps(result, indent=2) + '\n')

    if failures:
        print('\n'.join(failures))
        return 1
    print(f'proved {len(proved)} of {N} rows ({100 * len(proved) / N:.1f}%): fresh constructor 1,397, fixed key '
          'schema 447, exhaustive returns 53, dominating guard 25')
    print('hand proofs: 88 of 176 proved, none contradicted')
    print('controls: 0 of F73\'s 21 losses and 34 witness-only rows, 0 of F72\'s 62 losses; 9 with mutation analysis off')
    print(f'bound: {base}/{N} = {100 * base / N:.1f}% -> {up}/{N} = {100 * up / N:.1f}%; reader-visible '
          f'{vbase}/{vN} = {100 * vbase / vN:.1f}% -> {vup}/{vN} = {100 * vup / vN:.1f}%')
    print(f'with M1708 and M1745 unproved: {cbase} ({100 * cbase / N:.1f}%) -> {cup} ({100 * cup / N:.1f}%); '
          f'reader-visible {cvbase} ({100 * cvbase / vN:.1f}%) -> {cvup} ({100 * cvup / vN:.1f}%)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
