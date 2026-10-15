#!/usr/bin/env python3
"""Record the verified local source identity before the release build."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

D = Path(__file__).resolve().parent
S = D / 'source'
text = (D / 'checks-default.log').read_text()
receipt = json.loads((D / 'checks-default.json').read_text())
focused = dict(re.findall(r'^test (analyze::(?:fixpoint_check|harvest_return)::tests::\S+) \.\.\. (ok|FAILED)',
                         text, re.MULTILINE))
assert focused and all(v == 'ok' for v in focused.values()), focused
assert any('fixpoint_check::tests::' in n for n in focused)
assert any('harvest_return::tests::' in n for n in focused)
result = re.search(r'test result: (\w+)\. (\d+) passed; (\d+) failed; (\d+) ignored;', text)
assert result, 'inspect the default-suite log before committing'
summary = {'default': {'status': result[1], 'passed': int(result[2]), 'failed': int(result[3]),
                       'ignored': int(result[4]), 'exit_code': receipt['exit_code']},
           'relevant_tests': focused, 'log': str(D / 'checks-default.log')}
(D / 'checks-summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
assert subprocess.check_output(['git', 'diff', '--name-only'], cwd=S, text=True).splitlines() == [
    'src/analyze/fixpoint_check.rs']
subprocess.run(['git', 'diff', '--check'], cwd=S, check=True)
env = os.environ.copy()
env.update(GIT_AUTHOR_NAME='bunnykong', GIT_COMMITTER_NAME='bunnykong',
           GIT_AUTHOR_EMAIL='268838774+bunnykong@users.noreply.github.com',
           GIT_COMMITTER_EMAIL='268838774+bunnykong@users.noreply.github.com')
message = ('Expose read-only ownership census sites for provenance diagnostics\n\n'
           'Reuse the advance_prediction ownership and no-stabilize arms from 642217d8.\n'
           'Dump emit-body/site references, provenance bits and type hashes only\n'
           'when RH_REASON_SITE_CENSUS is set alongside the census.\n\n'
           'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n')
msg = D / 'source-commit-message.txt'
msg.write_text(message)
subprocess.run(['git', 'add', '--', 'src/analyze/fixpoint_check.rs'], cwd=S, check=True)
subprocess.run(['git', 'commit', '--file', str(msg)], cwd=S, env=env, check=True)
fields = subprocess.check_output(['git', 'show', '-s', '--format=%H%n%an%n%ae%n%cn%n%ce%n%B'],
                                 cwd=S, text=True).split('\n', 5)
files = subprocess.check_output(['git', 'diff', '--name-only',
    'bf56edf9e74ce2481e43e473de87466aac96283c', 'HEAD'], cwd=S, text=True).splitlines()
candidate = {'commit': fields[0], 'branch': 'writer-ownership',
             'author': {'name': fields[1], 'email': fields[2]},
             'committer': {'name': fields[3], 'email': fields[4]}, 'message': fields[5].strip(),
             'files': {p: hashlib.sha256((S / p).read_bytes()).hexdigest() for p in files},
             'parent': '642217d87f3f02c729d66829b64e182eb48e6539',
             'status': subprocess.check_output(['git', 'status', '--porcelain'], cwd=S, text=True)}
(D / 'candidate-commit.json').write_text(json.dumps(candidate, indent=2) + '\n')
(D / 'source.patch').write_bytes(subprocess.check_output(['git', 'diff',
    'bf56edf9e74ce2481e43e473de87466aac96283c', 'HEAD'], cwd=S))
assert not candidate['status']
print(json.dumps({'commit': candidate['commit'], 'checks': summary['default'],
                  'relevant_tests_passed': len(focused)}, indent=2), flush=True)
