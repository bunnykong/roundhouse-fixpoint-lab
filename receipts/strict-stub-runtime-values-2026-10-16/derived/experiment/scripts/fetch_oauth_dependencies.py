#!/usr/bin/env python3
"""Fetch only OAuth2's dependency closure at the frozen Chatwoot lockfile versions."""
import hashlib
import json
import re
import urllib.request
from pathlib import Path

D = Path(__file__).resolve().parents[1]
LOCK = D.parent / 'ownership-generalization/inputs/chatwoot/Gemfile.lock'
specs = {}
current = None
for line in LOCK.read_text().splitlines():
    m = re.fullmatch(r'    ([A-Za-z0-9_-]+) \(([^)]+)\)', line)
    if m:
        current = m[1]
        specs[current] = {'version': m[2], 'dependencies': []}
    elif current and re.match(r'^      [A-Za-z0-9_-]+', line):
        specs[current]['dependencies'].append(line.strip().split(' ', 1)[0])
    elif line and not line.startswith(' '):
        current = None
seen = set()


def visit(name):
    if name in seen:
        return
    seen.add(name)
    for dep in specs[name]['dependencies']:
        visit(dep)


visit('oauth2')
downloads = D / 'vendor/downloads'
downloads.mkdir(exist_ok=True)
receipts = []
for name in sorted(seen):
    version = specs[name]['version']
    path = downloads / (name + '-' + version + '.gem')
    url = 'https://rubygems.org/downloads/' + path.name
    if not path.exists():
        with urllib.request.urlopen(url, timeout=30) as response:
            path.write_bytes(response.read())
    receipts.append({'name': name, 'version': version, 'path': str(path), 'url': url,
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    print(path.name, flush=True)
(D / 'receipts/oauth-dependencies.json').write_text(json.dumps({
    'lockfile': str(LOCK), 'lock_sha256': hashlib.sha256(LOCK.read_bytes()).hexdigest(),
    'gems': receipts}, indent=2) + '\n')
