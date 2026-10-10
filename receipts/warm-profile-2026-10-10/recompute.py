#!/usr/bin/env python3
"""Check saved raw outputs and reduce the recorded six profiles; no native runs."""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FP_KEYS = ('fingerprints', 'input_fingerprints', 'value_fingerprints', 'class_fingerprints')


def read(relative):
    return json.loads((ROOT / relative).read_text())


def raw(relative):
    return gzip.decompress((ROOT / relative).read_bytes()).decode()


def reports(text):
    result = collections.defaultdict(list)
    diagnostics = collections.defaultdict(collections.Counter)
    contents, timings, summaries = [], [], []
    for line in text.splitlines():
        if line.startswith('rh-') and ': {' in line:
            prefix, data = line.split(': ', 1)
            result[prefix].append(json.loads(data))
        m = re.match(r'^(?:.*?:\d+:\d+:\s*)?(error|warning|note)\[([a-z_][a-z_0-9]*)\]:', line)
        if m:
            diagnostics[m[1]][m[2]] += 1
            contents.append(line)
        if line.startswith('roundhouse-check: ') and ' — ' in line:
            summaries.append(line.split(' — ', 1)[1])
        m = re.match(r'^roundhouse-timing: (.*): ([0-9.]+)s \(peak rss (\d+) MB\)$', line)
        if m:
            timings.append(dict(phase=m[1], seconds=float(m[2]), peak_rss_mb=int(m[3])))
    return dict(reports=dict(result), diagnostics=dict(diagnostics), timings=timings,
                summaries=summaries, diagnostic_content_sha256=hashlib.sha256(
                    '\n'.join(sorted(contents)).encode()).hexdigest())


def shadow(row):
    r = row['reports']['rh-warm'][0]
    fp = row['reports']['rh-fixpoint']
    assert len(fp) == 2 and row['exit'] in (0, 1)
    assert r['shadow'] == 'pass' and r['first_difference'] is None
    assert fp[0]['entries'] == fp[1]['entries']
    assert fp[0]['digest'] == fp[1]['digest'] == r['warm_digest'] == r['cold_digest']
    return r


def outcomes(text):
    target, pending, data = 'startup', None, {}
    for line in text.splitlines():
        m = re.match(r'^\s*Running (unittests \S+|tests/\S+)', line)
        if m:
            target = m[1]
        if re.match(r'^\s*Doc-tests roundhouse', line):
            target = 'doctests'
        m = re.match(r'^test (.+?) \.\.\. (ok|FAILED|ignored(?:,.*)?)$', line)
        if m:
            name = re.sub(r' \(line \d+\)$', '', m[1]) if target == 'doctests' else m[1]
            data[target, name] = m[2].split(',')[0]
            pending = None
        else:
            m = re.match(r'^test (.+?) \.\.\. ', line)
            if m:
                pending = target, m[1]
            elif pending and line in ('ok', 'FAILED', 'ignored'):
                data[pending] = line
                pending = None
    assert pending is None
    return data


def main():
    for row in read('recorded-files.json')['files']:
        payload = (ROOT / row['file']).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == row['file_sha256'], row['file']
        if row['gzip']:
            payload = gzip.decompress(payload)
        assert hashlib.sha256(payload).hexdigest() == row['public_uncompressed_sha256'], row['file']
    recorded = read('profiles/results.json')
    pins = read('pins.json')
    runs = {row['label']: row for row in read('profiles/runs.json')}
    public_hashes = read('public-diagnostic-hashes.json')
    assert len(runs) == 20
    for label, row in runs.items():
        assert row['condition'] == recorded['condition'] == pins['condition']
        assert row['binary_sha256'] == recorded['binary_sha256'] == pins['binary_sha256']
        individual = read('profiles/runs/' + label + '/run.json')
        assert individual == {k: v for k, v in row.items() if k != 'label'}
        parsed = reports(raw('profiles/runs/' + label + '/stderr.log.gz'))
        for key, value in parsed.items():
            if key == 'diagnostic_content_sha256':
                assert row[key] == public_hashes[label]['recorded']
                assert value == public_hashes[label]['public']
            else:
                assert row[key] == value, (label, key)
        if not label.endswith('-cold'):
            shadow(row)
    assert read('edits.json')['cases'] == read('profiles/inputs.json')['cases']
    assert read('edits.json')['cases'] == json.loads((ROOT.parent / 'F15/edits.json').read_text())['cases']
    reduced = []
    for pair in recorded['pairs']:
        label = pair['app'] + '-' + pair['edit']
        cold, warm, correctness = [runs[label + '-' + suffix] for suffix in ('cold', 'warm', 'correctness')]
        report = shadow(warm)
        shadow(correctness)
        assert cold['exit'] == warm['exit'] == correctness['exit']
        assert report['warm_digest'] == cold['reports']['rh-fixpoint'][0]['digest']
        assert report['warm_digest'] == correctness['reports']['rh-warm'][0]['warm_digest']
        for key in ('diagnostics', 'diagnostic_content_sha256', 'summaries'):
            assert cold[key] == warm[key] == correctness[key], (label, key)
        assert public_hashes[label + '-cold']['public'] == public_hashes[label + '-warm']['public']
        assert public_hashes[label + '-cold']['public'] == public_hashes[label + '-correctness']['public']
        assert cold['reports']['rh-fixpoint'][0]['entries'] == warm['reports']['rh-fixpoint'][0]['entries']
        for part in ('returns', 'ir', 'sccq_dependencies', 'sccq_contexts', 'sccq_entry_contexts'):
            assert warm['reports']['rh-fixpoint'][0]['entries'][part] > 0
        assert pair['shadow_matches'] and pair['diagnostic_contents_equal'] and pair['loaded'] > 0
        assert pair['phases'] == report['phases'] and pair['evaluations'] == report['evaluations']
        phases = report['phases']['seconds']
        assert all(value >= 0 for value in phases.values())
        assert abs(sum(phases.values()) - report['phases']['total_seconds']) < 1e-7
        direct = dict(ingest_seconds='ingest_seconds', shadow_clone_seconds='shadow_clone_seconds',
                      warm_analysis_seconds='warm_analyze_seconds', shadow_analysis_seconds='cold_analyze_seconds',
                      shadow_seconds='shadow_seconds')
        for key, source in direct.items():
            assert pair[key] == report[source], (label, key)
        assert pair['cold_wall_seconds'] == cold['wall_seconds']
        assert pair['full_warm_wall_seconds'] == warm['wall_seconds']
        assert pair['warm_excluding_shadow_seconds'] == warm['reports']['rh-warm-wall'][0]['check_excluding_shadow_seconds']
        assert pair['save_seconds'] == warm['reports']['rh-warm-save'][0]['seconds']
        assert pair['published_trace_cleanup_seconds'] == warm['reports']['rh-warm-cleanup'][0]['published_records_drop_seconds']
        assert pair['cold_analysis_seconds'] == next(t['seconds'] for t in cold['timings'] if t['phase'] == 'analyze')
        reduced.append(dict(app=pair['app'], edit=pair['edit'], parity='match',
                            total_fingerprints=sum(phases[k] for k in FP_KEYS),
                            input_fingerprints=phases['input_fingerprints'],
                            cold_analysis=pair['cold_analysis_seconds'],
                            whole_warm=pair['full_warm_wall_seconds'],
                            warm_excluding_shadow=pair['warm_excluding_shadow_seconds'],
                            ratio=pair['warm_excluding_shadow_seconds'] / pair['cold_wall_seconds']))
    assert len(reduced) == 6 and {(x['app'], x['edit']) for x in reduced} == {
        (a, e) for a in ('mastodon', 'discourse') for e in ('boolean', 'return-type', 'withdraw-read')}
    before, after = [outcomes(raw('logs/' + name + '.log.gz')) for name in ('next-suite', 'suite')]
    common = before.keys() & after.keys()
    assert len(common) == 5209 and all(before[k] == after[k] for k in common)
    assert not before.keys() - after.keys()
    added = after.keys() - before.keys()
    assert len(added) == 14 and all(k[0] == 'tests/warm_check.rs' and after[k] == 'ok' for k in added)
    expected = [(4970, 3, 236), (4984, 3, 236)]
    for table, counts in zip((before, after), expected):
        assert tuple(sum(v == state for v in table.values()) for state in ('ok', 'FAILED', 'ignored')) == counts
    suite = read('evidence/suite-comparison.json')
    assert suite['shared_tests'] == len(common) and not suite['different'] and not suite['missing']
    assert suite['equal_failures']
    emission = read('evidence/emission.json')
    assert emission['pairs'] == 105 and emission['byte_compared'] == 11432
    assert not emission['different'] and not emission['byte_differences'] and emission['same_pair_inventory']
    total_input = sum(p['input_fingerprints'] for p in reduced)
    denominator = sum(p['warm_excluding_shadow'] for p in reduced)
    print(json.dumps(dict(condition=recorded['condition'], raw_runs_checked=len(runs), profiles=reduced,
                          flags_off_shared_outcomes=len(common), added_passes=len(added),
                          input_fingerprints_total_seconds=total_input,
                          input_fingerprints_share_of_summed_warm_excluding_shadow=total_input / denominator,
                          emission_record=dict(pairs=105, files=11432),
                          native_runs_performed=0), indent=2))


if __name__ == '__main__':
    main()
