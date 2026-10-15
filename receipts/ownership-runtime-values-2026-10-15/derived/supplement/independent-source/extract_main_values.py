#!/usr/bin/env python3
"""Extract just the render-family helpers from two recorded main snapshots."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'frontier/agents'
rows = []
for app in ['forem', 'mastodon']:
    coverage = json.loads((BASE / 'ownership-runtime-values/receipts' / app / 'coverage.json').read_text())
    cell = coverage['baseline/unset']
    path = Path(cell['source'])
    pattern = (re.compile(r'(?:Api::V0::)?ListingsController#process_.*') if app == 'forem'
               else re.compile(r'ApplicationController#(?:not_found|forbidden|respond_with_error)'))
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for line_number, line in enumerate(source, 1):
            digest.update(line)
            if b'"part":"returns"' not in line:
                continue
            row = json.loads(line)
            if pattern.fullmatch(row['key']):
                assert row['ty'] == {'kind': 'nil'}, row
                rows.append({'app': app, 'key': row['key'], 'debug': row['debug'],
                             'snapshot': str(path), 'line': line_number})
    assert digest.hexdigest() == cell['sha256'], str(path)
assert len([r for r in rows if r['app'] == 'forem']) == 15
assert len([r for r in rows if r['app'] == 'mastodon']) == 3
source_checks = []
for name in ['src/rbs.rs', 'runtime/ruby/action_controller/base.rbs',
             'runtime/ruby/action_controller/base.rb', 'src/analyze/registry/controllers.rs']:
    measured = BASE / 'ownership-generalization/source' / name
    probe = BASE / 'ownership-runtime-values/source' / name
    assert measured.read_bytes() == probe.read_bytes(), name
    source_checks.append({'path': str(measured), 'probe_equal': True,
                          'sha256': hashlib.sha256(measured.read_bytes()).hexdigest()})
result = {'row_condition': 'ownership-runtime-values-20261015-f78d995f',
          'snapshot_condition': 'ownership-runtime-value-probes-20261015-f78d995f',
          'source_base': 'f78d995f65816dead93dd615dcba370661c50d1f',
          'baseline_schedule': 'unset-v0-a0', 'helpers': rows, 'unchanged_source_files': source_checks}
(HERE / 'main-nil-values.json').write_text(json.dumps(result, indent=2)+'\n')
for row in rows:
    print(row['key'], row['debug'])
