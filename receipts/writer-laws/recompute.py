#!/usr/bin/env python3
"""Check the inventory, ignored-test selection and every archived counterexample."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
read = lambda name: json.loads((ROOT / name).read_text())
for file in read('archive.json')['files']:
    assert hashlib.sha256((ROOT / file['path']).read_bytes()).hexdigest() == file['archived_sha256']
with gzip.open(ROOT / 'logs/laws-final.log.gz', 'rt') as stream:
    text = stream.read()
pattern = re.compile(r'WRITER-LAW (.*?) \| (.*?) \| (PASS|FAIL) \| (\d+) checks'
                     r'(?: \| (\d+) nodes \| (.*))?')
actual = []
for line in text.splitlines():
    match = pattern.search(line)
    if match:
        writer, law, status, count, nodes, witness = match.groups()
        actual.append(dict(writer=writer, law=law, result=status, checks=int(count),
                           witness_nodes=int(nodes) if nodes is not None else None, witness=witness))
saved = read('law-results.json')
assert actual == [{k: v for k, v in row.items() if k != 'test'} for row in saved['rows']]
writers = defaultdict(list)
for row in saved['rows']:
    writers[row['writer']].append(row)
failures = {rows[0]['test'].rsplit('::', 1)[-1] for rows in writers.values()
            if any(r['result'] == 'FAIL' for r in rows)}
assert failures == set(read('known-failures.json'))
assert len(writers) == 55 and len(failures) == 41
properties = Counter(r['result'] for r in actual)
assert properties == {'PASS': 199, 'FAIL': 116}
assert sum(r['checks'] for r in actual) == 13256907
assert all(r['witness'] is not None and r['witness_nodes'] is not None for r in actual if r['result'] == 'FAIL')
with gzip.open(ROOT / 'logs/default-suite.log.gz', 'rt') as stream:
    suite = stream.read()
summaries = re.findall(r'^test result: .*? (\d+) passed; (\d+) failed; (\d+) ignored;', suite, re.M)
counts = [sum(int(row[i]) for row in summaries) for i in range(3)]
assert counts == [4941, 3, 277] and len(summaries) == 692
selection = re.findall(r'^test (\S*writer_law_\S*) \.\.\. (.*)$', suite, re.M)
assert len(selection) == 55
ignored = {name.rsplit('::', 1)[-1] for name, status in selection if status.startswith('ignored')}
assert ignored == failures and sum(status == 'ok' for _, status in selection) == 14
controls = read('main-control-results.json')
assert len(controls) == 3 and all(r['exit'] == 101 for r in controls)
print(json.dumps(dict(base=saved['base_sha'], harness=(ROOT / 'COMMIT').read_text().strip(),
                      checks=55, passing_checks=14, known_ignored_checks=41,
                      passing_properties=199, failing_properties=116, comparisons=13256907,
                      default_suite=dict(passed=counts[0], failed=counts[1], ignored=counts[2]),
                      inherited_failures_reproduced=3), indent=2, sort_keys=True))
