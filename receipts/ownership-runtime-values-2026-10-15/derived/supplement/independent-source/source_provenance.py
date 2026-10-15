#!/usr/bin/env python3
"""Bind witness methods to the input manifest and compare the measured/probe source exports."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'frontier/agents'
PIN = 'f78d995f65816dead93dd615dcba370661c50d1f'
manifest = json.loads((BASE / 'ownership-runtime-values/receipts/input-pins.json').read_text())
manifest_index = {app: {f['path']: f for f in record['file_manifest']} for app, record in manifest.items()}
inputs = BASE / 'ownership-generalization/inputs'
witness_files = {}
for packet in ['runtime-replay.json', 'sample-replay.json', 'real-rails-replay.json']:
    for source in json.loads((HERE / packet).read_text())['sources']:
        path = Path(source['path'])
        try:
            relative = path.relative_to(inputs)
        except ValueError:
            continue
        app, app_path = relative.parts[0], '/'.join(relative.parts[1:])
        expected = manifest_index[app][app_path]['sha256']
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected == source['sha256'], str(path)
        witness_files[str(relative)] = {'sha256': actual, 'app_commit': manifest[app]['commit']}

prepared = json.loads((BASE / 'ownership-generalization/evidence/prepared.json').read_text())
assert prepared['source_commit'] == PIN
source_files = {}
for name in ['src/rbs.rs', 'runtime/ruby/action_controller/base.rbs',
             'runtime/ruby/action_controller/base.rb', 'src/analyze/registry/controllers.rs']:
    measured = (BASE / 'ownership-generalization/source' / name).read_bytes()
    probe = (BASE / 'ownership-runtime-values/source' / name).read_bytes()
    assert measured == probe, name
    source_files[name] = {'original_equals_probe': True,
                          'sha256': hashlib.sha256(measured).hexdigest()}
result = {'source_commit_recorded_in_prepared_receipt': PIN,
          'witness_app_files': witness_files, 'main_source_files': source_files}
(HERE / 'source-provenance.json').write_text(json.dumps(result, indent=2) + '\n')
print('Witness app files matching pinned manifest:', len(witness_files))
print('Main source files equal between original export and probe:', len(source_files))
