#!/usr/bin/env python3
"""Recompute saved-value membership from the retained type grammars and lab trace."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import support as s
HERE = Path(__file__).resolve().parent
reproduction = s.LAB / 'reproductions/settle_sound'
checker = s.load('settle_receipt_checker', s.LAB / 'oracle/check.py')
slots = json.loads((reproduction / 'slots.json').read_text())
records = checker.load_records(reproduction / 'trace.jsonl')
rows = []
for source, prefix in [('historical.json', 'historical-'), ('rerun.json', 'rerun-')]:
    result = json.loads((HERE / source).read_text())
    assert s.sha(reproduction / 'trace.jsonl') == result['trace_sha256']
    assert s.sha(reproduction / 'app/controllers/trees_controller.rb') == result['input_sha256']
    for row in result['rows']:
        grammar = (HERE / (prefix + row['arm'] + '.rbs')).read_text()
        oracle = checker.check_records(checker.Grammar(grammar), records, slots)
        rejected = oracle['records'] - oracle['accepted']
        assert rejected == row['rejected'] and oracle['records'] == row['records']
        rows.append(dict(receipt=source, arm=row['arm'], commit=row['commit'], loops=row['loops'],
                         rejected=rejected, records=oracle['records']))
print(json.dumps(rows, indent=2, sort_keys=True))
