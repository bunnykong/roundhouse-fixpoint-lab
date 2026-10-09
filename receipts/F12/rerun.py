#!/usr/bin/env python3
"""Compare the join-memo fix with the interner-only baseline on pinned public apps."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import support as s
HERE = Path(__file__).resolve().parent
REVISIONS = {'join-base': '060a91d84b55681504374ebb0f9baa7829930b38',
             'memo': '4485e7db7f3e30e15c09800ff807dff29929d223'}


def main():
    args = s.parser('F12').parse_args()
    work, source = s.setup(args)
    s.verify_apps(args.apps, args.app_root.resolve())
    binaries = {}
    for name, revision in REVISIONS.items():
        built, _ = s.build(source, work, name, revision, (HERE / 'leaf-observer.patch',))
        binaries[name] = Path(built['roundhouse'])
    flags = dict(s.S3, RH_FIXPOINT_DIGEST='1', RH_FIXPOINT_STATS='1',
                 RH_PROVENANCE_LEAVES='1', RH_C1_DIGEST='1', **s.seed_hook(work, 1))
    raw, comparisons = {}, {}
    for app in args.apps:
        raw[app] = {}
        for name, binary in binaries.items():
            row = s.run_check(binary, args.app_root.resolve() / app, flags, work / 'runs' / app / name)
            raw[app][name] = dict(fixpoint=row['reports']['rh-fixpoint'][0], diagnostics=row['diagnostics'])
        left, right = raw[app]['join-base'], raw[app]['memo']
        comparisons[app] = dict(digests_equal=left['fixpoint']['digest'] == right['fixpoint']['digest'],
                                loops_equal=left['fixpoint']['loops'] == right['fixpoint']['loops'],
                                tags_equal=left['fixpoint']['provenance_leaves'] == right['fixpoint']['provenance_leaves'],
                                diagnostics_equal=left['diagnostics'] == right['diagnostics'])
        print(app + ': ' + json.dumps(comparisons[app]), flush=True)
        if not all(comparisons[app].values()):
            raise RuntimeError('join-memo difference: ' + app)
    s.verify_apps(args.apps, args.app_root.resolve())
    s.write(work / 'reports.json', raw)
    s.write(work / 'results.json', dict(condition='public-corpus-v1; S3; WTO; native hash seed 1',
                                      comparisons=comparisons, commits=REVISIONS))


if __name__ == '__main__':
    main()
