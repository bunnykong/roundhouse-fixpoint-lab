#!/usr/bin/env python3
"""Apply the public shuffled probe and run the literal-dispatch fixture."""
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import support as s

HERE = Path(__file__).resolve().parent


def main():
    args = s.parser('long-name', apps=False).parse_args()
    work, source = s.setup(args)
    condition = json.loads((HERE / 'condition.json').read_text())
    binaries, _ = s.build(source, work, 'probe', condition['base'],
                          patches=[HERE / condition['patch']])
    rows = []
    for seed, verify in [('0', True), ('0', False), ('1', False), ('2', False)]:
        flags = {k: v for k, v in condition['flags'].items() if k != 'RH_FOLD_VERIFY'}
        flags['RH_SHUFFLE'] = seed
        if verify:
            flags['RH_FOLD_VERIFY'] = '1'
        app = s.LAB / 'reproductions/long_name_dispatch'
        result = subprocess.run([binaries['roundhouse'], 'check', '--continue', str(app)],
                                env=s.clean_env(flags), capture_output=True, text=True, timeout=120)
        assert result.returncode in (0, 1)
        lines = [s.scrub(line, [app, work, s.LAB]) for line in result.stderr.splitlines()
                 if line.startswith(('rh-sccq-verify:', 'rh-c1-digest:', 'rh-det-unresolved:'))]
        if verify:
            assert any(line.startswith('rh-sccq-verify:') for line in lines), 'missing extra-round probe'
        assert any(line.startswith('rh-c1-digest:') for line in lines), 'missing digest'
        rows.append(dict(seed=seed, extra_round=verify, exit_code=result.returncode, reports=lines))
    s.write(work / 'observations.json', rows)
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
