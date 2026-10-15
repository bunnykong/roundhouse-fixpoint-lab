#!/usr/bin/env python3
import json
from pathlib import Path
from audit_rows import CLASSIFY, FRONTIER, HERE, admits, sha

rows = {r['row_id']: r for r in map(json.loads, (CLASSIFY / 'receipts/rows.jsonl').open())}
witness = json.loads((HERE / 'sample-replay.json').read_text())
inputs = FRONTIER / 'agents/ownership-generalization/inputs'
results = []
for sample in witness['samples']:
    row = rows[sample['row_id']]
    value_class = sample['ruby_class']
    main_ok = admits(row['baseline_row']['resolved_ty'], value_class)
    arm_ok = admits(row['arm_row']['resolved_ty'], value_class)
    assert main_ok and not arm_ok, (sample['row_id'], main_ok, arm_ok)
    inner = row['arm_row']
    span = inner.get('span')
    if row['app'] == 'forem':
        path = inputs / 'forem/app/controllers/concerns/listings_toolkit.rb'
    elif row['row_id'] == 'M1973':
        path = inputs / 'mastodon/app/controllers/api/web/embeds_controller.rb'
    elif row['row_id'] == 'M1788':
        path = inputs / 'mastodon/app/helpers/json_ld_helper.rb'
    else:
        path = inputs / 'mastodon/app/controllers/concerns/account_owned_concern.rb'
    source = path.read_bytes()
    if span:
        snippet = source[span['start']:span['end']].decode()
        line = source[:span['start']].count(b'\n') + 1
    else:
        method = row['root_method'].split('#')[1]
        matches = [s for s in witness['sources'] if s['path'] == str(path) and s['method'] == method]
        assert len(matches) == 1, (row['row_id'], matches)
        line = matches[0]['line']
        snippet = source[matches[0]['start']:matches[0]['end']].decode()
    results.append({**sample, 'schedule': row['schedule'], 'part': row['part'],
                    'root_method': row['root_method'], 'main': row['resolved_baseline_value'],
                    'variant': row['resolved_arm_value'], 'main_admits': main_ok, 'variant_admits': arm_ok,
                    'source_path': str(path), 'source_line': line, 'source_snippet': snippet,
                    'source_sha256': sha(path), 'storage_key': row['key']})
output = {'row_condition': 'ownership-runtime-values-20261015-f78d995f',
          'sample_condition': witness['condition'], 'ruby': witness['ruby'],
          'selection': 'Purposive sample across both apps, all schedules, cache/IR/returns, and render/JSON-LD families; includes the inferred embeds row',
          'passing_samples': len(results), 'samples': results}
(HERE / 'sample-admission.json').write_text(json.dumps(output, indent=2) + '\n')
for r in results:
    print(r['row_id'], r['schedule'], r['part'], r['main'], '->', r['variant'],
          r['ruby_class'], 'main admits / variant excludes', str(Path(r['source_path']).relative_to(inputs))+':'+str(r['source_line']))
