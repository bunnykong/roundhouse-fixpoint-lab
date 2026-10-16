#!/usr/bin/env python3
"""Reconcile complete default Cargo suite logs with independently enumerated test inventory."""
import json
from pathlib import Path
import re
import sys

RUNNING = re.compile(r'^\s*Running (?:unittests )?(\S+)')
DOC = re.compile(r'^\s*Doc-tests (\S+)')
OUTCOME = re.compile(r'^test (\S+) \.\.\. (ok|FAILED|ignored)(?:\b.*)?$')
RESULT = re.compile(r'^test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out(?:;|$)')

def parse(path, inventory=None, process=None):
    path = Path(path)
    if inventory is None:
        inv = path.with_suffix('.inventory.json')
        inventory = json.loads(inv.read_text()) if inv.exists() else {}
    if process is None:
        meta = path.with_suffix('.process.json')
        process = json.loads(meta.read_text()) if meta.exists() else {}
    binary, outcomes, failed, passed, completed, observed, problems = None, {}, set(), 0, 0, {}, []
    with path.open(errors='replace') as source:
        for line in source:
            line = line.rstrip('\n')
            match, doc = RUNNING.match(line), DOC.match(line)
            if match or doc:
                if binary is not None:
                    problems.append('unfinished binary ' + binary)
                if doc:
                    binary = 'doc:' + doc.group(1)
                else:
                    src = match.group(1)
                    binary = 'lib' if src == 'src/lib.rs' else Path(src).stem
                if binary in observed:
                    problems.append('duplicate binary ' + binary)
                outcomes = {}
                continue
            match = OUTCOME.match(line)
            if match and binary is not None:
                name, status = match.groups()
                if name in outcomes:
                    problems.append('duplicate test ' + binary + '::' + name)
                outcomes[name] = status
                if status == 'FAILED':
                    failed.add(binary + '::' + name)
                continue
            match = RESULT.match(line)
            if match:
                if binary is None:
                    problems.append('result without started binary')
                    continue
                counts = list(map(int, match.groups()))
                actual = [sum(v == k for v in outcomes.values()) for k in ('ok', 'FAILED', 'ignored')]
                if counts[:3] != actual or counts[3:] != [0, 0]:
                    problems.append('outcomes do not reconcile for ' + binary)
                if sorted(outcomes) != sorted(inventory.get(binary, [])) or binary not in inventory:
                    problems.append('inventory differs for ' + binary)
                observed[binary] = sorted(outcomes)
                passed += counts[0]
                completed += 1
                binary = None
    if binary is not None:
        problems.append('unfinished binary ' + binary)
    if not inventory or set(inventory) != set(observed):
        problems.append('suite binary inventory incomplete')
    if process.get('completed') is not True or process.get('exit_code') not in (0, 101):
        problems.append('process completion or valid exit status missing')
    if process.get('exit_code') == 0 and failed:
        problems.append('successful process contradicts test failures')
    return dict(failed=sorted(failed), passed=passed, binaries=completed, complete=not problems,
                completed=process.get('completed') is True, exit_code=process.get('exit_code'),
                inventory=inventory, observed=observed, problems=problems)

if __name__ == '__main__':
    print(json.dumps({'off': parse(sys.argv[1]), 'on': parse(sys.argv[2])}, indent=1))
