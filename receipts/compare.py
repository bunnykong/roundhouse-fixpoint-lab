#!/usr/bin/env python3
"""Check the retained fresh F12/F14/F18 reports against their historical raw inputs."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import matrix
import support as s


def changed(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for key in sorted(a.keys() | b.keys()):
            field = (path + '.' + key).lstrip('.')
            result.extend([field] if key not in a or key not in b else changed(a[key], b[key], field))
        return result
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [path + '.length']
        return [p for i, (left, right) in enumerate(zip(a, b))
                for p in changed(left, right, path + '[' + str(i) + ']')]
    return [] if a == b else [path]


def timing(path):
    key = path.rsplit('.', 1)[-1]
    return key.endswith(('_seconds', '_secs')) or key.startswith(('secs_', 't_'))


def main():
    result = {}
    for fact in ('F12', 'F14', 'F18'):
        root = Path(__file__).resolve().parent / fact
        old_file = 'historical.json' if fact == 'F12' else 'reports.json'
        old = json.loads((root / old_file).read_text())
        new = json.loads((root / 'rerun-reports.json').read_text())
        if fact != 'F12':
            old_census, new_census = matrix.read_inputs(root), matrix.read_inputs(root, 'rerun-')
            assert matrix.reduce(old_census, old)['pooled'] == matrix.reduce(new_census, new)['pooled']
        checks = []
        for app, arms in old.items():
            for arm, left in arms.items():
                right = new[app][arm]
                if fact == 'F12':
                    differences = changed(left['fixpoint'], right['fixpoint'])
                    for severity, name in [('error', 'errors_by_kind'), ('warning', 'warnings_by_kind'),
                                           ('note', 'notes_by_kind')]:
                        assert left[name] == right['diagnostics'].get(severity, {})
                else:
                    differences = changed(left, right)
                    for field in ('diagnostics', 'observations', 'drops'):
                        assert old_census[app][arm][field] == new_census[app][arm][field], (fact, app, arm, field)
                assert all(timing(p) for p in differences), (fact, app, arm, differences)
                checks.append(dict(app=app, arm=arm, all_nontiming_fields_equal=True,
                                   differing_timing_fields=differences))
        result[fact] = checks
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
