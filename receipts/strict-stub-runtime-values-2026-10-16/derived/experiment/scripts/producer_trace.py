#!/usr/bin/env python3
"""Reduce research condition's existing V1 producer audit to the four unsound OAuth render rows."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parents[1]
NATIVE_PROFILE = D.parent / 'strict-producer-reasons'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    labels = {a: read(NATIVE_PROFILE / 'cache/labels' / ('strict-producer-' + a) / 'label.json') for a in ['C', 'SK']}
    output = {}
    for setting in ['unset-v1-a1', 'repeat-v1-a1', '1-v1-a1', '2-v1-a1']:
        data, custody = {}, {}
        for arm in ['C', 'SK']:
            ref = labels[arm]['cells']['chatwoot/' + setting]
            result = read(ref['result'])
            path = Path(result['directory']) / 'stderr.log'
            lines = [line[len('rh-provenance-audit: '):] for line in path.open() if line.startswith('rh-provenance-audit: ')]
            assert len(lines) == 1
            data[arm] = json.loads(lines[0])
            custody[arm] = {'path': str(path), 'sha256': sha(path)}
        providers = {}
        for provider in ['Google', 'Instagram', 'Microsoft', 'Notion']:
            owner = 'Api::V1::Accounts::' + provider + '::AuthorizationsController'
            destination = owner + '|render|Instance|param=0'
            per_arm = {}
            for arm in ['C', 'SK']:
                audit = data[arm]
                reason = 'Unresolved' if arm == 'C' else 'Pending'
                events = [e for e in audit['parameter_native_events']
                          if e['destination'] == destination and e['phase'] == 'join'
                          and 'why: ' + reason in e['observed']]
                assert len(events) == 1, (setting, arm, provider, events)
                event = events[0]
                assert event['lost_kinds'] == ([] if arm == 'C' else ['Pending'])
                assert len(event['observed_source_candidates']) == 1
                method = provider.lower() + '_client'
                writers = {k: {'shapes': v, 'origins': audit['writers'][k], 'visits': audit['visits'][k]}
                           for k, v in audit['input_shapes'].items()
                           if k.startswith('owner=' + owner + '|') and '|instance|' + method + '|' in k}
                assert len(writers) == 1
                assert all(v['shapes'] == ['{"kind":"var","var":0}'] for v in writers.values())
                per_arm[arm] = {'native_join': event, 'client_body_producer': writers}
            providers[provider] = per_arm
        output[setting] = {'custody': custody, 'providers': providers}
    (D / 'receipts/producer-attribution.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print('All four providers at all four V1 schedules: C keeps Unresolved; SK removes Pending at render[0].')


if __name__ == '__main__':
    main()
