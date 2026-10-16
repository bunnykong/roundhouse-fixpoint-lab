#!/usr/bin/env python3
"""Fill absent serialized value observations with the research condition read-only probe, through obs.py."""
import json
import subprocess
import sys
from pathlib import Path

D = Path(__file__).resolve().parents[1]
F = D.parents[1]
NATIVE_PROFILE = F / 'agents/strict-producer-reasons'


def main():
    for arm in ['C', 'SK']:
        flags = json.loads((NATIVE_PROFILE / 'strict-producer-protocol/profiles' / (arm + '.json')).read_text())
        flags['RH_CONTRIBUTOR_VALUES'] = '1'
        (D / ('flags-' + arm + '.json')).write_text(json.dumps(flags, indent=2) + '\n')
    for schedule in ['unset', 'repeat', '1', '2']:
        for va in ['v0-a0', 'v1-a1']:
            setting = schedule + '-' + va
            for arm in ['C', 'SK']:
                command = [sys.executable, str(F / 'phase2/observers/obs.py'), 'run',
                           '--bin', str(D / 'bin/roundhouse'), '--app', 'chatwoot',
                           '--settings', setting, '--label', 'sk-values-' + arm,
                           '--flags', str(D / ('flags-' + arm + '.json')), '--jobs', '1',
                           '--cache-root', str(D / 'cache')]
                print(arm, setting, flush=True)
                result = subprocess.run(command, cwd=F)
                if result.returncode:
                    raise SystemExit(result.returncode)
                label = json.loads((D / 'cache/labels' / ('sk-values-' + arm) / 'label.json').read_text())
                ref = label['cells']['chatwoot/' + setting]
                captured = json.loads(Path(ref['result']).read_text())
                original_label = json.loads((NATIVE_PROFILE / 'cache/labels' / ('strict-producer-' + arm) / 'label.json').read_text())
                original_ref = original_label['cells']['chatwoot/' + setting]
                original = json.loads(Path(original_ref['result']).read_text())
                assert captured['valid'] and original['valid']
                assert captured['observations']['value_digests'] == original['observations']['value_digests'], (arm, setting, 'digest mismatch')
                assert captured['input_tree_sha256'] == original['input_tree_sha256']
                assert (Path(captured['directory']) / 'contributor-values.jsonl').is_file()
                print('all ten research condition digests reproduced', arm, setting, flush=True)


if __name__ == '__main__':
    main()
