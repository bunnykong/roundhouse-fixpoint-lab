"""Run and reduce the public S3 / DET / keep-unresolved error and precision census."""
import collections
import csv
import json
from pathlib import Path
import support as s

gate = s.load('receipt_errgate', s.LAB / 'receipts/errgate.py')


def write_inputs(directory, raw):
    """A short CSV row per diagnostic key, with JSON for the type witnesses."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    metadata = {}
    with (directory / 'diagnostics.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['app', 'arm', 'kind', 'site', 'op', 'count'], lineterminator='\n')
        writer.writeheader()
        for app, arms in sorted(raw.items()):
            metadata[app] = {}
            for arm, entry in sorted(arms.items()):
                for row in entry['diagnostics']:
                    writer.writerow(dict(app=app, arm=arm, **row))
                metadata[app][arm] = {k: v for k, v in entry.items() if k != 'diagnostics'}
    s.write(directory / 'census-inputs.json', metadata)


def read_inputs(directory, prefix=''):
    directory = Path(directory)
    raw = json.loads((directory / (prefix + 'census-inputs.json')).read_text())
    for arms in raw.values():
        for entry in arms.values():
            entry['diagnostics'] = []
    with (directory / (prefix + 'diagnostics.csv')).open(newline='') as stream:
        for row in csv.DictReader(stream):
            app, arm = row.pop('app'), row.pop('arm')
            row['count'] = int(row['count'])
            raw[app][arm]['diagnostics'].append(row)
    return raw


def snapshot(dump, selected):
    observations, diagnostics, drops, metadata = dump
    counts = collections.Counter(map(gate.key, diagnostics))
    rows = [dict(kind=k[0], site=k[1], op=k[2], count=n) for k, n in sorted(counts.items())]
    observed = [row for k in sorted(selected) for row in observations.get(k, [])]
    slots = {row.get('recv_slot') for row in observed}
    return dict(diagnostics=rows, observations=observed,
                drops={k: sorted(v) for k, v in drops.items() if k in slots}, metadata=metadata)


def restore(raw):
    observations = collections.defaultdict(list)
    for row in raw['observations']:
        observations[gate.key(row)].append(row)
    diagnostics = []
    for row in raw['diagnostics']:
        diagnostics.extend([{k: row[k] for k in ('kind', 'site', 'op')}] * row['count'])
    return observations, diagnostics, {k: set(v) for k, v in raw['drops'].items()}, raw['metadata']


def select(dumps):
    counters = [collections.Counter(map(gate.key, d[1])) for d in dumps.values()]
    selected = set()
    for left in counters:
        for right in counters:
            selected.update((left - right).keys())
    return selected


def reduce(raw, reports):
    apps, pooled = {}, {}
    arms = next(iter(raw.values())).keys()
    for app, entries in raw.items():
        apps[app] = {}
        for arm in arms:
            restored = restore(entries[arm])
            apps[app][arm] = dict(errors=len(restored[1]), precision=reports[app][arm]['precision'])
            if arm != 's3':
                fresh, summary = gate.compare(restore(entries['s3']), restored)
                apps[app][arm]['against_s3'] = summary
                apps[app][arm]['new_only'] = fresh
        if 'keep' in entries:
            _, summary = gate.compare(restore(entries['det']), restore(entries['keep']))
            apps[app]['keep']['against_det'] = summary
    for arm in arms:
        ps = [a[arm]['precision'] for a in apps.values()]
        totals = {k: sum(p[k] for p in ps) for k in ps[0]}
        totals.update(errors=sum(a[arm]['errors'] for a in apps.values()),
                      fully_typed_percent=100 * totals['fully_typed'] / totals['typed'])
        if arm != 's3':
            cs = [a[arm]['against_s3'] for a in apps.values()]
            totals.update(new_only=sum(c['new_only'] for c in cs), old_only=sum(c['old_only'] for c in cs),
                          new_verdicts=dict(sum((collections.Counter(c['verdicts']) for c in cs), collections.Counter())),
                          vanished=dict(sum((collections.Counter(c['vanished']) for c in cs), collections.Counter())))
        pooled[arm] = totals
    return dict(apps=apps, pooled=pooled)


def rerun(fact, revision, patches=(), keep=False):
    args = s.parser(fact).parse_args()
    work, source = s.setup(args)
    s.verify_apps(args.apps, args.app_root.resolve())
    binaries, commit = s.build(source, work, fact, revision, patches)
    hook = s.seed_hook(work, 7)
    flags = dict(s.S3, RH_FIXPOINT_DIGEST='1', RH_FIXPOINT_STATS='1', RH_C1_DIGEST='1',
                 RH_ERRGATE='1', RH_PUBLIC_INPUT='1', RH_PRECISION_CENSUS='1', **hook)
    raw, reports = {}, {}
    arms = [('s3', {}), ('det', dict(RH_DET='1'))]
    if keep:
        arms.append(('keep', dict(RH_DET='1', RH_DET_KEEP_UNRESOLVED='1')))
    for app in args.apps:
        path = args.app_root.resolve() / app
        dumps, reports[app] = {}, {}
        for arm, extra in arms:
            dest = work / 'runs' / app / arm
            row = s.run_check(Path(binaries['roundhouse']), path, dict(flags, **extra), dest)
            dumps[arm] = gate.read_dump(dest / 'stderr.log')
            reports[app][arm] = row['reports']['rh-fixpoint'][0]
            print(fact + ' ' + app + ' ' + arm + ': ' + str(len(dumps[arm][1])) + ' errors', flush=True)
        selected = select(dumps)
        raw[app] = {arm: s.scrub(snapshot(dump, selected), [path]) for arm, dump in dumps.items()}
    s.verify_apps(args.apps, args.app_root.resolve())
    write_inputs(work, raw)
    s.write(work / 'reports.json', reports)
    result = reduce(raw, reports)
    result.update(commit=commit, native_hash_seed=7 if hook else None,
                  condition='public-corpus-v1; S3; WTO; no extra verification round')
    s.write(work / 'results.json', result)
    print(json.dumps(result['pooled'], indent=2))
