#!/usr/bin/env python3
"""Retain the final producer/reader values surrounding the lost OAuth parameter arms."""
import json
from pathlib import Path

D = Path(__file__).resolve().parents[1]


def main():
    out = {}
    for arm in ['C', 'SK']:
        label = json.loads((D / 'cache/labels' / ('sk-values-' + arm) / 'label.json').read_text())
        for setting in ['unset-v0-a0', 'unset-v1-a1']:
            result = json.loads(Path(label['cells']['chatwoot/' + setting]['result']).read_text())
            selected = []
            for line in (Path(result['directory']) / 'contributor-values.jsonl').open():
                row = json.loads(line)
                if row['part'] not in ['returns', 'params', 'ir', 'controller_cache']:
                    continue
                take = False
                for provider in ['Google', 'Instagram', 'Microsoft', 'Notion']:
                    owner = 'Api::V1::Accounts::' + provider + '::AuthorizationsController'
                    method = provider.lower() + '_client'
                    if row['part'] == 'returns' and row['key'] in [owner + '#' + method, provider + 'Concern#' + method]:
                        take = True
                    if row['part'] == 'params' and row['key'] == owner + '#render[0]':
                        take = True
                    if row['part'] == 'controller_cache' and row['key'] == owner + '#' + method + ':body:':
                        take = True
                    if row['part'] == 'ir' and (row.get('source') or '').endswith('/' + provider.lower() + '/authorizations_controller.rb'):
                        if row['node'] in ['Hash', 'Var', 'Send', 'Assign'] and row.get('ty', {}).get('kind') in ['untyped', 'hash']:
                            take = True
                if take:
                    selected.append(row)
            out[arm + '/' + setting] = selected
    (D / 'receipts/supporting-values.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print({k: len(v) for k, v in out.items()})


if __name__ == '__main__':
    main()
