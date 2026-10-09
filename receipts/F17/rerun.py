#!/usr/bin/env python3
"""Recheck the published settling witness on a pinned or newly fetched upstream main."""
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import support as s

HERE = Path(__file__).resolve().parent
MAIN = '1ce9969564303ebe1bf5b8ca3304f982272079c1'
SOUND = '96cdea9a1e6e6bb32a267a247d72f99b98a50b70'


def main():
    p = s.parser('F17', apps=False)
    p.add_argument('--main-sha', default=MAIN)
    p.add_argument('--latest-main', action='store_true', help='Fetch rubys/roundhouse main instead of the receipt pin.')
    args = p.parse_args()
    work, source = s.setup(args)
    main_sha = args.main_sha
    subprocess.run(['git', '-C', str(source), 'fetch', 'https://github.com/rubys/roundhouse.git',
                    'main' if args.latest_main else main_sha], check=True)
    if args.latest_main:
        main_sha = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'FETCH_HEAD'], text=True).strip()
    reproduction = s.LAB / 'reproductions/settle_sound'
    binaries, commits = {}, {}
    for name, revision, patches in [('main', main_sha, ()),
                                     ('main-flowfix', main_sha, (HERE / 'flow-fix-current.patch',)),
                                     ('sound', SOUND, ())]:
        binaries[name], commits[name] = s.build(source, work, name, revision, patches,
                                               reproduction / 'settle_probe.rs')
    supplied = work / 'binaries.json'
    s.write(supplied, dict(binaries=binaries, commits=commits))
    runner = s.load('receipt_settle_runner', reproduction / 'run.py')
    runner.ARMS = [('main', main_sha, False), ('main-flowfix', main_sha, False), ('sound', SOUND, True)]
    output = work / 'measurement'
    saved_argv = sys.argv
    sys.argv = [str(reproduction / 'run.py'), '--binaries', str(supplied), '--output', str(output)]
    try:
        runner.main()
    finally:
        sys.argv = saved_argv
    raw = json.loads((output / 'results.json').read_text())
    raw.update(main_sha=commits['main'], flow_fix_sha256=s.sha(HERE / 'flow-fix-current.patch'),
               runner_sha256=s.sha(reproduction / 'run.py'),
               exporter_sha256=s.sha(reproduction / 'settle_probe.rs'))
    s.write(work / 'results.json', s.scrub(raw, [reproduction, work]))
    print(json.dumps(dict(main_sha=commits['main'],
                         rows=[{k:r[k] for k in ('arm','loops','records','rejected')} for r in raw['rows']]), indent=2))


if __name__ == '__main__':
    main()
