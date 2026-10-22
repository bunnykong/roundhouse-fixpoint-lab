"""Recompute F73's census bound on reader-visible rows only. Python 3.9+, standard library only.

Starts no analyzer and runs no Ruby. Reuses `upper` (exact hypergeometric inversion) and the strata of the F73
receipt unchanged. Given n', the sampled reader-visible rows of a stratum are a simple random sample of the
stratum's N' reader-visible rows, so the same inversion applies to (N', n', k'). Exits 1 if any number quoted in
README.md disagrees with the data.
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
F73 = HERE.parent / 'mutation-writers-census-2026-10-21'
spec = importlib.util.spec_from_file_location('f73_bounds', F73 / 'bounds.py')
f73 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f73)
VISIBLE = {'a', 'b'}
SAMPLED_STRATA = 4  # 0.05/4 in each sampled unknown-only stratum, as in F73


def tsv(text):
    return list(csv.DictReader(io.StringIO(text), delimiter='\t'))


def census(strata, rows, population):
    """Per-stratum counts and F73's bounds for one choice of rows."""
    out, conf, det, est, pop = [], 0, 0, 0.0, 0
    for s in strata:
        key = (s['app'], s['stratum'])
        mine = [r for r in rows if (r['app'], r['stratum']) == key]
        N, n = population[key], len(mine)
        k = sum(r['status'] == 'UNSOUND' for r in mine)
        u = sum(r['status'] == 'WITNESS_ONLY' for r in mine)
        alpha = 20 * SAMPLED_STRATA if s['population'] > s['sample'] else 20
        c, d = f73.upper(N, n, k + u, alpha), f73.upper(N, n, k, alpha)
        conf, det, pop = conf + c, det + d, pop + N
        est += N * k / n if n else 0.0
        out.append(dict(app=s['app'], stratum=s['stratum'], N=N, n=n, k=k, u=u, conf=c))
    return out, conf, det, est, pop


def main():
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f'{label}: {got} != {want}')

    recorded = json.loads((F73 / 'bounds.json').read_text())
    strata = recorded['strata']
    sample = tsv((HERE / 'sample-readers.tsv').read_text())
    tags = tsv(lzma.decompress((HERE / 'population-readers.tsv.xz').read_bytes()).decode())
    published = {r['census_id']: r for r in tsv((F73 / 'sample.tsv').read_text())}
    tag = {r['census_id']: r for r in tags}

    check('sample rows', len(sample), 229)
    check('population rows', len(tags), 4652)
    check('sample matches the F73 receipt', all(
        (published[r['census_id']]['status'], published[r['census_id']]['key']) == (r['status'], r['key'])
        for r in sample), True)
    check('sample tags match the population', all(tag[r['census_id']]['reader'] == r['reader'] for r in sample), True)
    check('sample by reader', dict(collections.Counter(r['reader'] for r in sample)), {'a': 168, 'b': 29, 'c': 32})
    check('sample by reader and status', {k: dict(collections.Counter(r['status'] for r in sample if r['reader'] == k))
                                          for k in 'abc'},
          {'a': {'UNSOUND': 13, 'WITNESS_ONLY': 23, 'SOURCE_SUPPORTED': 132},
           'b': {'WITNESS_ONLY': 1, 'SOURCE_SUPPORTED': 28},
           'c': {'UNSOUND': 6, 'WITNESS_ONLY': 10, 'SOURCE_SUPPORTED': 16}})

    full = collections.Counter((r['app'], r['stratum']) for r in tags)
    vis = collections.Counter((r['app'], r['stratum']) for r in tags if r['reader'] in VISIBLE)
    check('populations match F73', {(s['app'], s['stratum']): s['population'] for s in strata if s['population']},
          dict(full))
    _, bc, bd, be, bp = census(strata, sample, full)
    check('all rows reproduce F73', (bc, bd, bp, round(be / bp, 12)),
          (2202, 1021, 4652, round(recorded['detection_point_estimate'], 12)))
    seen, vc, vd, ve, vp = census(strata, [r for r in sample if r['reader'] in VISIBLE], vis)
    check('reader-visible rows', vp, 3974)
    check('reader-visible bound', (vc, round(100 * vc / vp, 1)), (1907, 48.0))
    check('reader-visible detection-only bound', (vd, round(100 * vd / vp, 1)), (1007, 25.3))
    check('reader-visible estimate', round(100 * ve / vp, 2), 9.05)
    check('per-stratum rows, sample, losses + unproved, upper count',
          [(s['N'], s['n'], s['k'] + s['u'], s['conf']) for s in seen if s['N']],
          [(81, 32, 8, 33), (1, 1, 0, 0), (488, 36, 5, 151), (28, 28, 1, 1), (1656, 36, 10, 784), (32, 32, 2, 2),
           (1688, 32, 11, 936)])
    check('source-supported rows that leave', sum(1 for r in sample if r['reader'] == 'c' and
                                                  r['status'] == 'SOURCE_SUPPORTED'), 16)
    check('unread sample rows by table', dict(collections.Counter(r['table'] for r in sample if r['reader'] == 'c')),
          {'controller_cache': 18, 'params': 14})
    check('reader-visible share', (round(100 * vp / bp, 1), round(100 * sum(r['reader'] in VISIBLE for r in sample) /
                                                                   len(sample), 1)), (85.4, 86.0))
    shares = [100 * vis[k] / full[k] for k in full if full[k] > 2]
    check('reader-visible share per stratum', (round(min(shares), 1), round(max(shares), 1)), (83.0, 93.3))

    losses = json.loads((F73 / 'losses.json').read_text())['rows']
    unread = sorted((r['census_id'] for r in losses if tag[r['census_id']]['reader'] not in VISIBLE),
                    key=lambda x: (x[0], int(x[1:])))
    check('losing rows', len(losses), 21)
    check('unread losing rows', unread, ['C1855', 'C1856', 'M131', 'M1786', 'M1848', 'M1904'])
    check('reader-visible losing rows', len(losses) - len(unread), 15)

    c = [r for r in tags if r['reader'] == 'c']
    check('unread share', (len(c), round(100 * len(c) / len(tags), 1)), (678, 14.6))
    check('unread by table', dict(collections.Counter(r['table'] for r in c)),
          {'controller_cache': 522, 'params': 126, 'returns': 30})
    ir_spans = {(r['app'], r['span'], r['node']) for r in tags if r['table'] == 'ir' and r['span']}
    twins = [r for r in c if r['table'] == 'controller_cache' and r['span'] and (r['app'], r['span'], r['node']) in ir_spans]
    check('unread controller-cache rows with a narrowed IR twin', len(twins), 509)
    check('M131 is the cache copy of M650', (tag['M131']['span'], tag['M131']['node']) ==
          (tag['M650']['span'], tag['M650']['node']), True)
    check('unread params rows with no analyzer body', sum(1 for r in c if r['table'] == 'params' and
                                                          r['why'].startswith('params: no analyzer body')), 124)
    check('unread includer copies among returns', sum(1 for r in c if r['table'] == 'returns' and
                                                      'includer copy' in r['why']), 13)

    if failures:
        print('\n'.join(failures))
        return 1
    print('sample of 229: 168 read by an analyzed body, 29 only by an emitter, 32 by nothing')
    print(f'unread rows: {len(c)} of {len(tags)} narrowings (14.6%): 522 controller-cache (509 with a narrowed IR '
          f'twin), 126 params, 30 returns')
    print(f'unread losing rows: {" ".join(unread)}')
    print(f'conformance bound, simultaneous 95%: all rows {bc}/{bp} = {100 * bc / bp:.1f}%; '
          f'reader-visible {vc}/{vp} = {100 * vc / vp:.1f}%')
    print(f'detection-only bound: all rows {bd}/{bp} = {100 * bd / bp:.1f}%; reader-visible {vd}/{vp} = '
          f'{100 * vd / vp:.1f}%; weighted estimate {100 * be / bp:.2f}% -> {100 * ve / vp:.2f}%')
    return 0


if __name__ == '__main__':
    sys.exit(main())
