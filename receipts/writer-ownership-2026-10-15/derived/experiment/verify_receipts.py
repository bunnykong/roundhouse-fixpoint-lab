#!/usr/bin/env python3
"""Check source, frozen inputs and all run provenance under the master heavy lock."""
import hashlib
import json
from pathlib import Path
import subprocess

D = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
frozen = json.loads((D / 'advance_prediction-inputs.json').read_text())
checks = {'frozen_input_hashes': {p: sha(Path(p)) == h for p, h in frozen['files'].items()}}
commit = json.loads((D / 'candidate-commit.json').read_text())
build = json.loads((D / 'build.json').read_text())
index = json.loads((D / 'series-index.json').read_text())
flags = {'a': ['RH_SPLICED_WRITER_OWNERSHIP=1'], 'b': ['RH_SKIP_RETURN_STABILIZE=1'],
         'both': ['RH_SPLICED_WRITER_OWNERSHIP=1', 'RH_SKIP_RETURN_STABILIZE=1'], 'off': []}
checks['source'] = {
    'head_matches_build_and_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
        cwd=D / 'source', text=True).strip() == build['source_commit'] == commit['commit'],
    'branch': subprocess.check_output(['git', 'branch', '--show-current'],
        cwd=D / 'source', text=True).strip() == 'writer-ownership',
    'worktree_clean': not subprocess.check_output(['git', 'status', '--porcelain'], cwd=D / 'source', text=True),
    'no_remotes': not subprocess.check_output(['git', 'remote'], cwd=D / 'source', text=True),
    'arm_A_B_unchanged': not subprocess.check_output(['git', 'diff', frozen['copied_commit'],
        '--', 'src/analyze/mod.rs', 'src/analyze/harvest_return.rs'], cwd=D / 'source', text=True),
    'author': commit['author']['email'] == '268838774+bunnykong@users.noreply.github.com',
    'committer': commit['committer']['email'] == '268838774+bunnykong@users.noreply.github.com',
    'trailer': commit['message'].strip().endswith('Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'),
    'binary': sha(D / 'bin/roundhouse') == build['binary_sha256'],
    'build_success': build['exit_code'] == 0,
    'four_build_workers': build['environment']['CARGO_BUILD_JOBS'] == '4',
    'source_files': all(sha(D / 'source' / p) == h for p, h in commit['files'].items()),
}
checks['runs'] = {}
manifest = json.loads((D / 'workshop/inputs/manifest.json').read_text())
for x, paths in index.items():
    for label, path in paths.items():
        out = Path(path)
        r = json.loads((out / 'command.json').read_text())
        expected = flags.get(x, flags['both'])
        actual = [f for f in r['candidate_flags'] if not f.startswith('RH_REASON_SITE_CENSUS=')]
        checks['runs'][x + '/' + label] = (
            r['condition'] == 'writer-ownership-20261015-bf56edf9-' + x
            and r['source_commit'] == commit['commit'] and r['binary_sha256'] == build['binary_sha256']
            and actual == expected and r['verification'] is False and r['ruby'].startswith('ruby 4.0.7 ')
            and r['input_tree_sha256'] == manifest[r['app']]['tree_sha256']
            and r['analyzer_exit'] in (0, 1)
            and all((out / f).is_file() for f in ('report.json', 'compact.json', 'focus.jsonl',
                                                  'declarations.jsonl', 'structure.jsonl', 'stdout.log', 'stderr.log')))
checks['all_pass'] = all(v for group in ('frozen_input_hashes', 'source', 'runs') for v in checks[group].values())
(D / 'receipt-audit.json').write_text(json.dumps(checks, indent=2, sort_keys=True) + '\n')
print(json.dumps({'all_pass': checks['all_pass'], 'candidate_runs': len(checks['runs']),
                  'source': checks['source']}, indent=2))
assert checks['all_pass'], 'see receipt-audit.json'
