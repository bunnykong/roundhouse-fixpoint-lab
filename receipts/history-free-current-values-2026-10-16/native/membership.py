"""Runtime witness admission, with explicit aliases used by this analyzer."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools/probe'))
import probe
_, _, sets = probe.dependencies()

def normalize(t):
    if isinstance(t, list):
        return [normalize(x) for x in t]
    if not isinstance(t, dict):
        return t
    if t.get('kind') == 'class' and t.get('id') == 'Time':
        return {'kind': 'time'}
    if t.get('kind') == 'class' and t.get('id', '').startswith('Arel::Nodes::'):
        return {'kind': 'class', 'id': 'Arel::Node', 'args': []}
    return {k: normalize(v) for k, v in t.items()}

def admits(t, value):
    t, value = normalize(t), normalize(value)
    if sets.top(t) or sets.empty(value):
        return True
    if value['kind'] == 'union':
        return all(admits(t, v) for v in value['variants'])
    if t['kind'] == 'union':
        return any(admits(v, value) for v in t['variants'])
    # This is an analyzer-owned name for actual request values, not a Ruby class.
    if t.get('id') == 'Roundhouse::ParamValue':
        return value['kind'] in ('str', 'int', 'float', 'bool', 'nil', 'array', 'hash') or value.get('id') in (
            'ActionController::Parameters', 'ActionDispatch::Http::UploadedFile')
    if t['kind'] == value['kind'] == 'hash':
        return admits(t['key'], value['key']) and admits(t['value'], value['value'])
    if t['kind'] == value['kind'] == 'array':
        return admits(t['elem'], value['elem'])
    if t['kind'] == value['kind'] == 'class' and t.get('id') == value.get('id'):
        return len(t.get('args', [])) == len(value.get('args', [])) and all(
            admits(a, b) for a, b in zip(t.get('args', []), value.get('args', [])))
    try:
        return sets.covers(t, value)
    except KeyError:
        return None

def observations():
    out = {}
    for app in probe.APPS:
        file = app + '-witnesses.json'
        data = json.loads(Path(file).read_text())
        assert 'ruby 4.0.7' in data['ruby']
        for n, obs in enumerate(data['observations']):
            for id_ in obs['rows']:
                out.setdefault(id_, []).append(dict(obs, receipt=file, observation_index=n))
    return out

if __name__ == '__main__':
    rows = {r['id']: r for r in json.loads(Path('classified-drops.json').read_text())}
    checked = []
    for id_, witnesses in observations().items():
        row = rows[id_]
        for obs in witnesses:
            result = dict(id=id_, observation=obs,
                          control_admits=admits(row['control'], obs['type']),
                          candidate_admits=admits(row['candidate'], obs['type']))
            checked.append(result)
            print(id_, result['control_admits'], result['candidate_admits'], obs['ruby_class'])
    Path('witness-membership.json').write_text(json.dumps({
        'aliases': {
            'Class[Time] and primitive Time': 'src/analyze/body/send.rs:2603; both denote Time values',
            'Arel::Nodes::* -> Arel::Node': 'src/analyze/registry/ar.rs:578-622; analyzer-owned node spelling',
            'Roundhouse::ParamValue': 'src/analyze/body/send.rs:3976; scalar, hash or array request value'
        }, 'checks': checked
    }, indent=2) + '\n')
