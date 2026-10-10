"""Check retained long-name outputs and the scanner/dispatch witness."""
import json
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
LAB=HERE.parents[1]
source=(LAB/'reproductions/long_name_dispatch/lib/probe.rb').read_text()
name=re.search(r'send\("([^"]+)"\)',source).group(1)
assert len(name.encode('utf-8'))==94 and name.isascii()
assert 'def reader: () -> untyped' in (HERE/'unfixed.rbs').read_text()
assert 'def reader: () -> Hash[String, Array[Integer]]' in (HERE/'repaired.rbs').read_text()
assert 'state_entries_moved=1,ir_sites_moved=1' in (HERE/'verify.txt').read_text()
digests=re.findall(r'[0-9a-f]{16}:[0-9a-f]{16}',(HERE/'shuffles.txt').read_text())
assert len(set(digests))==2
print(json.dumps(dict(literal_bytes=94,old_cutoff_bytes=80,unfixed='untyped',
                     repaired='Hash[String, Array[Integer]]',extra_round_moved=True,
                     distinct_shuffled_answers=2,condition=json.loads((HERE/'condition.json').read_text())),indent=2))
