#!/usr/bin/env python3
"""Re-record the public producer witnesses behind the 59 causal annotations."""
import collections
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import support as s
HERE = Path(__file__).resolve().parent


def main():
    args = s.parser('F18-trace').parse_args()
    work, source = s.setup(args)
    s.verify_apps(args.apps, args.app_root.resolve())
    binaries, commit = s.build(source, work, 'trace', '7e4b0d52baec5d119fdae4b74c631de1cd431bfc',
                               (HERE / 'trace-observer.patch',))
    flags = dict(s.S3, RH_FIXPOINT_STATS='1', RH_FIXPOINT_DIGEST='1', RH_C1_DIGEST='1',
                 RH_ERRGATE='1', RH_PRECISION_CENSUS='1', RH_PUBLIC_INPUT='1',
                 RH_PUBLIC_TRACE_FILES=str(HERE / 'trace-files.txt'),
                 RH_PUBLIC_TRACE_SLOTS=str(HERE / 'trace-slots.txt'), **s.seed_hook(work, 7))
    history = {}
    for app in args.apps:
        path = args.app_root.resolve() / app
        for arm, extra in [('s3', {}), ('det', dict(RH_DET='1'))]:
            out = work / 'runs' / app / arm
            s.run_check(Path(binaries['roundhouse']), path, dict(flags, **extra), out)
            rows = []
            for line in (out / 'stderr.log').read_text().splitlines():
                if line.startswith('rh-public-trace: '):
                    rows.extend(json.loads(line[len('rh-public-trace: '):])['history'])
            history[app, arm] = s.scrub(rows, [path])
    targets = json.loads((HERE / 'trace-59.json').read_text())['rows']
    witnessed, differences = [], []
    for target in targets:
        app = target['app']
        if app not in args.apps:
            continue
        evidence = []
        for producer in target['producer_evidence']:
            query = producer['query']
            matched = [r for r in history[app, 's3']
                       if all(r.get(k) == v for k, v in query.items() if k != 'path')
                       and r.get('path', '').endswith(query['path'])]
            if not matched:
                raise RuntimeError('missing producer witness: ' + target['id'] + ' ' + str(query))
            if target['classification'] == 'dispatch-fallback':
                if not any('Var' in r.get('result', r.get('ty', '')) for r in matched):
                    raise RuntimeError('producer no longer returns Var: ' + target['id'])
                expected = {tag for row in producer['observations'] for tag in row.get('fallbacks', [])}
                observed = {tag for row in matched for tag in row.get('fallbacks', [])}
                if expected - observed:
                    raise RuntimeError('producer fallback branch changed: ' + target['id'] + ' ' + str(query))
            old = collections.Counter(json.dumps(r, sort_keys=True) for r in producer['observations'])
            new = collections.Counter(json.dumps(r, sort_keys=True) for r in matched)
            if old != new:
                differences.append(dict(id=target['id'], query=query,
                                        historical_count=sum(old.values()), fresh_count=sum(new.values()),
                                        only_historical=[json.loads(r) for r in sorted((old - new).elements())],
                                        only_fresh=[json.loads(r) for r in sorted((new - old).elements())]))
            evidence.append(dict(query=query, observations=matched,
                                 observations_equal_to_historical=old == new))
        harvest = {arm: [r for r in history[app, arm] if r.get('kind') == 'harvest'
                         and r.get('slot') in target['slots']] for arm in ('s3', 'det')}
        witnessed.append(dict(id=target['id'], app=app, classification=target['classification'],
                              subtype=target['subtype'], producer_evidence=evidence, harvest_evidence=harvest))
    result = dict(commit=commit, rows=witnessed, differing_producer_observations=differences,
                  annotation_counts=dict(collections.Counter(r['classification'] for r in witnessed)),
                  subtype_counts=dict(collections.Counter(r['subtype'] for r in witnessed)),
                  scope='Verifies recorded producer branches; causal chains and other-gap labels remain source annotations.')
    s.write(work / 'results.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
    s.verify_apps(args.apps, args.app_root.resolve())


if __name__ == '__main__':
    main()
