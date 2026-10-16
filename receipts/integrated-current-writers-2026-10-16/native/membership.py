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
