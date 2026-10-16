#!/usr/bin/env python3
"""Pin the source-preserving value probe against research condition and retain its small patch."""
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

D = Path(__file__).resolve().parents[1]
F = D.parents[1]
NATIVE_PROFILE = D.parent / 'strict-producer-reasons'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    freeze = json.loads((NATIVE_PROFILE / 'receipts/source-freeze.json').read_text())
    commit = '2233e2e7e639b9f66ecda41fac34475b2d0f2559'
    assert freeze['commit'] == commit
    changes, patch = {}, []
    for name, expected in freeze['source_files'].items():
        original, probe = NATIVE_PROFILE / 'repo' / name, D / 'source' / name
        assert sha(original) == expected, ('frozen source changed', name)
        actual = sha(probe)
        if actual != expected:
            changes[name] = {'frozen_sha256': expected, 'probe_sha256': actual}
            patch.extend(difflib.unified_diff(original.read_text().splitlines(True),
                                            probe.read_text().splitlines(True),
                                            fromfile='a/' + name, tofile='b/' + name))
    assert set(changes) == {'src/analyze/fixpoint_check.rs', 'src/analyze/fold.rs'}
    (D / 'receipts/value-probe.patch').write_text(''.join(patch))
    reuse = [F / 'agents/ownership-runtime-values/rows.py', F / 'agents/ownership-runtime-values/classify.py',
             F / 'agents/ownership-runtime-values/instrument.py', F / 'agents/ownership-runtime-values/witnesses/ownership.rb',
             F / 'phase2/contributor-ownership/contributor-protocol/verdict.py', F / 'phase2/observers/obs.py']
    result = {
        'base_commit': commit, 'frozen_sources_verified': len(freeze['source_files']),
        'source_changes': changes, 'patch_sha256': sha(D / 'receipts/value-probe.patch'),
        'binary_sha256': sha(D / 'bin/roundhouse'), 'original_binary_sha256': sha(NATIVE_PROFILE / 'bin/roundhouse'),
        'reused_tools': {str(p): sha(p) for p in reuse},
        'instrumentation_adaptation': 'research condition observer with research condition source lookup via App.sources and declaration identity; value transfer/writer/scheduler code unchanged.',
        'rust': subprocess.check_output(['rustc', '+1.98.1', '--version'], text=True).strip(),
        'cargo': subprocess.check_output(['cargo', '+1.98.1', '--version'], text=True).strip(),
        'build': 'cargo +1.98.1 build --locked --offline --release --bin roundhouse; four jobs; owned target; shared heavy lock',
    }
    (D / 'receipts/probe-pins.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
