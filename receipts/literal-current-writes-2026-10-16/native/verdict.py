#!/usr/bin/env python3
"""Verdict for literal-transfer (literal feedback) on spine v2 `369d963d`. See ../source-equivalence.json.

Reads one bundle JSON (paths only) and recomputes every criterion from primary
files: obs.py label.json files and their result.json cells, the builder's row
files, cargo test logs, the native purity census and runtime witnesses.

Every criterion ends in exactly one state: met, not_met or unavailable.
Missing or malformed evidence is `unavailable`, never a pass.

Outcomes, decided in this order (each bundle gets exactly one):
  KILLED        some decisive criterion is not_met (its own evidence is complete);
  INCONCLUSIVE  otherwise, some decisive criterion is unavailable, or a validity
                criterion is not met or unavailable;
  CONFIRMED     (stage final) or PASSED (stage campfire) otherwise.
Recorded predictions are reported as hit/miss/unavailable and never decide.

Usage: python3 verdict.py BUNDLE.json [--stage campfire|final] [--out REPORT.json]
Exit: 0 confirmed/passed, 1 killed, 2 inconclusive, 3 invalid invocation.
"""
import argparse
import hashlib
import json
import os
import re
import sys

MET, NOT_MET, UNAVAILABLE = 'met', 'not_met', 'unavailable'
SCHEDULES = ('unset', '1', '2', 'repeat')
CASES = tuple('ABCDEFGHIJK')
PREDICTED_LEGACY_FAIL = frozenset('ABEFHIJ')
TABLES = ('attributes', 'block_values', 'constants', 'controller_bindings', 'controller_cache',
          'copies', 'ir', 'params', 'returns', 'side_table')
CELL_FIELDS = ('value_digests', 'diagnostics', 'reason_census', 'reason_rows', 'loops', 'verify',
               'exit_code', 'law_violation_counts')
EXPECTED_LOOPS = frozenset(('production', 'views_and_tests', 'absorb'))
SUITE_BASELINE_PASSED = 1245
CAMPFIRE_SETTINGS = (('on', 'v1-a1'), ('on', 'v0-a0'), ('off', 'v1-a1'))
APP_SETTINGS = {
    'campfire': CAMPFIRE_SETTINGS,
    'chatwoot': (('on', 'v1-a1'), ('on', 'v0-a0')),
    'mastodon': (('on', 'v1-a1'),),
    'forem': (('on', 'v1-a1'),),
}
ROW_APPS = {'chatwoot': ('v1-a1', 'v0-a0'), 'mastodon': ('v1-a1',), 'forem': ('v1-a1',)}
WEBHOOK_INPUTS = {
    'params': ('Webhooks::InstagramController#channel_meta_app_secrets',
               'Webhooks::WhatsappController#channel_meta_app_secrets',
               'Webhooks::InstagramController#provider_config_meta_app_secrets',
               'Webhooks::WhatsappController#provider_config_meta_app_secrets'),
    'returns': ('Webhooks::InstagramController#provider_config_meta_app_secrets',
                'Webhooks::WhatsappController#provider_config_meta_app_secrets'),
}
NIL_PROBE = [{'class': 'NilClass'}]
REQUIRED_FROZEN = ('source-equivalence.json', 'verdict.py', 'test_verdict.py', 'schedule-row-literal-keys.json', 'webhook_secrets.rb',
                   'webhook_secrets.json', 'webhook_map.json', 'featured_tags.rb', 'featured_tags.json',
                   'featured_tags_map.json', 'c-on.json', 'l-on.json', 'c-off.json', 'l-off.json',
                   'campfire-on.json', 'campfire-off.json', 'literal_rows.py', 'literal_transfer_purity.rs')


class Missing(Exception):
    """Evidence is absent or malformed; the criterion is unavailable."""


def crit(name, role, status, detail):
    assert role in ('decisive', 'validity')
    assert status in (MET, NOT_MET, UNAVAILABLE)
    return {'name': name, 'role': role, 'status': status, 'detail': detail}


def decide(criteria, stage):
    """Exactly one outcome for any list of criteria."""
    kills = [c['name'] for c in criteria if c['role'] == 'decisive' and c['status'] == NOT_MET]
    if kills:
        return 'KILLED', kills
    gaps = [c['name'] for c in criteria
            if (c['role'] == 'decisive' and c['status'] == UNAVAILABLE)
            or (c['role'] == 'validity' and c['status'] != MET)]
    if gaps or not criteria:
        return 'INCONCLUSIVE', gaps or ['no criteria evaluated']
    return ('PASSED' if stage == 'campfire' else 'CONFIRMED'), []


# ---------------------------------------------------------------- loading

def resolve(base, path):
    if path is None:
        raise Missing('path not given')
    return path if os.path.isabs(path) else os.path.join(base, path)


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise Missing('%s: %s' % (path, e))


def load_label(path):
    """{cell: observations} for valid cells; invalid cells map to None."""
    label = load_json(path)
    cells = label.get('cells')
    if not isinstance(cells, dict):
        raise Missing('%s: no cells' % path)
    out = {}
    for cell, ref in cells.items():
        if not isinstance(ref, dict) or not ref.get('valid') or not ref.get('result'):
            out[cell] = None
            continue
        result = load_json(resolve(os.path.dirname(path), ref['result']))
        if not result.get('valid', True) or not isinstance(result.get('observations'), dict):
            out[cell] = None
            continue
        out[cell] = result['observations']
    return out


def cell(labels, arm_profile, app, sched, obs):
    """Observations of one cell, or Missing."""
    lab = labels.get(arm_profile)
    if lab is None:
        raise Missing('label %s not loaded' % arm_profile)
    key = '%s/%s-%s' % (app, sched, obs)
    if key not in lab:
        raise Missing('%s: no cell %s' % (arm_profile, key))
    if lab[key] is None:
        raise Missing('%s: invalid cell %s' % (arm_profile, key))
    return lab[key]


def require_fields(o, setting, where):
    """Note 4: a field absent from both variants must not compare as equal."""
    need = ['value_digests', 'diagnostics', 'reason_census', 'reason_rows', 'loops', 'exit_code']
    if setting.startswith('v1'):
        need.append('verify')
    if setting.endswith('a1'):
        need.append('law_violation_counts')
    missing = [f for f in need if o.get(f) is None]
    vd = o.get('value_digests')
    if isinstance(vd, dict) and any(t not in vd for t in TABLES):
        missing.append('value_digests tables')
    if missing:
        raise Missing('%s lacks %s' % (where, missing))


def field_view(o, name):
    v = o.get(name)
    if name == 'reason_rows' and isinstance(v, dict):
        return {'count': v.get('count'), 'sha256': v.get('sha256')}
    return v


def cell_differences(a, b):
    return [f for f in CELL_FIELDS if field_view(a, f) != field_view(b, f)]


# ---------------------------------------------------------------- types

UNKNOWN_KINDS = ('untyped', 'var')
SCALARS = {'int': 'Integer', 'float': 'Float', 'bool': None, 'str': 'String', 'sym': 'Symbol',
           'nil': 'NilClass', 'date': 'Date', 'time': 'Time'}


def kind(t):
    return t.get('kind') if isinstance(t, dict) else None


def print_ty(t):
    """The RBS-level print: unknown variants print `untyped`; a union with one prints `untyped`."""
    k = kind(t)
    if t is None:
        return '<absent>'
    if k in UNKNOWN_KINDS:
        return 'untyped'
    if k == 'union':
        arms = [print_ty(x) for x in t.get('variants', [])]
        if 'untyped' in arms:
            return 'untyped'
        return '(' + ' | '.join(sorted(set(arms))) + ')'
    if k == 'array':
        return 'Array[%s]' % print_ty(t.get('elem'))
    if k == 'hash':
        return 'Hash[%s, %s]' % (print_ty(t.get('key')), print_ty(t.get('value')))
    if k == 'tuple':
        return '[%s]' % ', '.join(print_ty(x) for x in t.get('elems', []))
    if k == 'class':
        args = t.get('args') or []
        return t.get('id', '?') + ('[%s]' % ', '.join(print_ty(x) for x in args) if args else '')
    if k == 'relation':
        return 'Relation[%s]' % t.get('of')
    if k == 'bottom':
        return 'bot'
    if k == 'rec':
        return 'rec:%s' % t.get('slot')
    if k in SCALARS:
        return k
    if k == 'fn':
        params = ', '.join(print_ty(p.get('ty') if isinstance(p, dict) else p) for p in t.get('params') or [])
        block = '{%s} ' % print_ty(t.get('block')) if t.get('block') else ''
        return '^(%s) %s-> %s' % (params, block, print_ty(t.get('ret')))
    return json.dumps(t, sort_keys=True)


def _and(values):
    values = list(values)
    if any(v is False for v in values):
        return False
    if any(v is None for v in values):
        return None
    return True


def _or(values):
    values = list(values)
    if any(v is True for v in values):
        return True
    if any(v is None for v in values):
        return None
    return False


def covers(a, b):
    """Does type a admit every value type b admits? True, False, or None (cannot tell)."""
    ka, kb = kind(a), kind(b)
    if ka in UNKNOWN_KINDS:
        return True
    if kb == 'bottom':
        return True
    if kb in UNKNOWN_KINDS:
        return False
    if kb == 'union':
        return _and(covers(a, x) for x in b.get('variants', []))
    if ka == 'union':
        return _or(covers(x, b) for x in a.get('variants', []))
    if ka == 'rec' or kb == 'rec':
        return True if a == b else None
    if ka != kb:
        if ka == 'array' and kb == 'tuple':
            return _and(covers(a.get('elem'), x) for x in b.get('elems', []))
        return False
    if ka in SCALARS:
        return True
    if ka == 'array':
        return covers(a.get('elem'), b.get('elem'))
    if ka == 'hash':
        return _and([covers(a.get('key'), b.get('key')), covers(a.get('value'), b.get('value'))])
    if ka == 'tuple':
        ea, eb = a.get('elems', []), b.get('elems', [])
        if len(ea) != len(eb):
            return False
        return _and(covers(x, y) for x, y in zip(ea, eb))
    if ka == 'class':
        if a.get('id') != b.get('id'):
            return False
        aa, ba = a.get('args') or [], b.get('args') or []
        if not aa:
            return True
        if len(aa) != len(ba):
            return False
        return _and(covers(x, y) for x, y in zip(aa, ba))
    if ka == 'relation':
        return a.get('of') == b.get('of')
    if ka == 'fn':
        pa, pb = a.get('params') or [], b.get('params') or []
        same_shape = len(pa) == len(pb) and print_ty(a.get('block')) == print_ty(b.get('block')) and all(
            print_ty(x.get('ty') if isinstance(x, dict) else x) == print_ty(y.get('ty') if isinstance(y, dict) else y)
            for x, y in zip(pa, pb))
        return covers(a.get('ret'), b.get('ret')) if same_shape else None
    return True if a == b else None


def admits(t, shape):
    """Does type t admit the runtime value shape? True, False, or None (cannot tell)."""
    k = kind(t)
    if k in UNKNOWN_KINDS:
        return True
    if k == 'union':
        return _or(admits(x, shape) for x in t.get('variants', []))
    if k == 'bottom':
        return False
    cls = shape.get('class')
    if k in SCALARS:
        if k == 'bool':
            return cls in ('TrueClass', 'FalseClass')
        return cls == SCALARS[k] or SCALARS[k] in shape.get('ancestors', [])
    if k == 'array':
        if cls != 'Array':
            return False
        return _and(admits(t.get('elem'), e) for e in shape.get('elems', []))
    if k == 'tuple':
        if cls != 'Array':
            return False
        return None  # witness shapes record element classes, not positions
    if k == 'hash':
        if cls != 'Hash':
            return False
        return _and(_and([admits(t.get('key'), kk), admits(t.get('value'), vv)]) for kk, vv in shape.get('pairs', []))
    if k == 'class':
        return cls == t.get('id') or t.get('id') in shape.get('ancestors', [])
    if k == 'fn':
        if cls not in ('Proc', 'Method'):
            return False
        if shape.get('returns') is None:
            return None
        checks = [admits(t.get('ret'), r) for r in shape['returns']]
        params = t.get('params') or []
        for call in shape.get('args') or []:
            for p, a in zip(params, call):
                checks.append(admits(p.get('ty') if isinstance(p, dict) else p, a))
        return _and(checks)
    return None


def admits_probe(t, probe):
    return _and(admits(t, s) for s in probe)


SEVERITY = {'same': 0, 'presence': 1, 'same_print': 1, 'widened': 2, 'narrowed': 3, 'incomparable': 4, 'unknown': 4}


def classify_pair(c, l):
    """Classify one schedule's C value against L's (each a row value dict or None)."""
    sc = None if c is None else (c.get('hash'), c.get('note'))
    sl = None if l is None else (l.get('hash'), l.get('note'))
    if sc == sl:
        return 'same'
    if l is None:
        return 'presence'  # L makes no claim where C had a row
    if c is None:
        # a value only L has: it needs a witness unless it cannot reject anything
        tl = l.get('ty')
        if tl is None:
            return 'presence'
        return 'widened' if print_ty(tl) == 'untyped' else 'unknown'
    tc, tl = c.get('ty'), l.get('ty')
    if tc is None or tl is None:
        return 'unknown' if tc != tl else 'same_print'
    if print_ty(tc) == print_ty(tl):
        return 'same_print'
    up, down = covers(tl, tc), covers(tc, tl)
    if up is True:
        return 'widened'
    if down is True:
        return 'narrowed'
    if up is None or down is None:
        return 'unknown'
    return 'incomparable'


def needs_witness(cls):
    return cls in ('narrowed', 'incomparable', 'unknown')


# ---------------------------------------------------------------- rows

def declaration_of(part, key):
    """The RETURN_HELPERS row observer's convention (agents/schedule-row-attribution/rowdiff.py)."""
    if part == 'returns':
        return key
    if part == 'params':
        return key.rsplit('[', 1)[0]
    if part == 'controller_cache':
        return key.split(':body:', 1)[0].split(':binding:', 1)[0]
    if part == 'ir':
        head = key.rsplit(':occurrence:', 1)[0]
        try:
            return json.loads(head).get('declaration')
        except ValueError:
            return None
    return None


def sig(v):
    return None if v is None else (v.get('hash'), v.get('note'))


def varies(arm_values):
    return len({sig(arm_values[s]) for s in SCHEDULES}) > 1


def valid_type(t):
    if not isinstance(t, dict) or not isinstance(t.get('kind'), str):
        return False
    k = t['kind']
    if k in SCALARS or k in ('untyped', 'bottom', 'self_instance'):
        return True
    if k == 'var':
        return isinstance(t.get('var'), int) and not isinstance(t.get('var'), bool)
    if k == 'rec':
        return isinstance(t.get('slot'), (int, str))
    if k == 'relation':
        return isinstance(t.get('of'), str)
    if k == 'array':
        return valid_type(t.get('elem'))
    if k == 'hash':
        return valid_type(t.get('key')) and valid_type(t.get('value'))
    if k in ('tuple', 'union', 'class'):
        xs = t.get({'tuple': 'elems', 'union': 'variants', 'class': 'args'}[k])
        return (isinstance(xs, list) and all(valid_type(x) for x in xs)
                and (k != 'class' or isinstance(t.get('id'), str)))
    if k == 'record':
        row = t.get('row')
        return (isinstance(row, dict) and isinstance(row.get('fields'), dict)
                and all(valid_type(x) for x in row['fields'].values()))
    if k == 'fn':
        ps = t.get('params')
        return (isinstance(ps, list) and all(isinstance(p, dict) and valid_type(p.get('ty')) for p in ps)
                and valid_type(t.get('ret')) and ('block' in t)
                and (t['block'] is None or valid_type(t['block'])))
    return False


def validate_value(v, part, where):
    if v is None:
        return
    if not isinstance(v, dict):
        raise Missing(where + ': malformed value')
    for f in ('hash', 'note'):
        if not isinstance(v.get(f), (str, int)) or isinstance(v.get(f), bool):
            raise Missing(where + ': missing or malformed ' + f)
    if v.get('empty_vector') is True and part == 'params' and 'ty' in v and v['ty'] is None:
        return
    if not valid_type(v.get('ty')):
        raise Missing(where + ': missing or malformed type payload')


def load_rows(base, entry):
    """Rows of one app/observer: list of dicts, validated, or Missing."""
    if not isinstance(entry, dict):
        raise Missing('row entry absent')
    receipt = load_json(resolve(base, entry.get('reconciled')))
    if receipt.get('complete') is not True:
        raise Missing('row reconciliation not complete')
    cells = receipt.get('cells') or {}
    for arm in ('C', 'L'):
        for s in SCHEDULES:
            c = cells.get('%s/%s' % (arm, s))
            if not isinstance(c, dict) or c.get('fingerprint_matches_native') is not True:
                raise Missing('row reconciliation fails for %s/%s' % (arm, s))
    rows = []
    path = resolve(base, entry.get('file'))
    try:
        with open(path) as f:
            for n, line in enumerate(f, 1):
                if not line.strip():
                    continue
                r = json.loads(line)
                if not isinstance(r, dict):
                    raise Missing('%s:%d is not an object' % (path, n))
                for field in ('part', 'key', 'C', 'L'):
                    if field not in r:
                        raise Missing('%s:%d lacks %s' % (path, n, field))
                for arm in ('C', 'L'):
                    if not isinstance(r[arm], dict) or any(s not in r[arm] for s in SCHEDULES):
                        raise Missing('%s:%d %s lacks a schedule' % (path, n, arm))
                    for schedule in SCHEDULES:
                        validate_value(r[arm][schedule], r['part'], '%s:%d %s/%s' % (path, n, arm, schedule))
                r['declaration'] = r.get('declaration') or declaration_of(r['part'], r['key'])
                rows.append(r)
    except (OSError, ValueError) as e:
        raise Missing('%s: %s' % (path, e))
    return rows


# ---------------------------------------------------------------- criteria

def c_identity(base, bundle, labels, apps):
    diffs, missing = [], []
    for app in apps:
        for prof, obs in APP_SETTINGS[app]:
            for s in SCHEDULES:
                try:
                    a = cell(labels, 'C_' + prof, app, s, obs)
                    b = cell(labels, 'ref_' + prof, app, s, obs)
                    require_fields(a, obs, 'C %s/%s-%s' % (app, s, obs))
                    require_fields(b, obs, 'ref %s/%s-%s' % (app, s, obs))
                except Missing as e:
                    missing.append(str(e))
                    continue
                d = cell_differences(a, b)
                if d:
                    diffs.append('%s/%s-%s %s: %s' % (app, s, obs, prof, d))
    if missing:
        return crit('V0 control reproduces spine v2', 'validity', UNAVAILABLE, missing[:20])
    if diffs:
        return crit('V0 control reproduces spine v2', 'validity', NOT_MET, diffs[:50])
    return crit('V0 control reproduces spine v2', 'validity', MET, 'every C cell equals its spine v2 cell')


def c_purity(base, bundle):
    name = 'LITERAL_PURITY native purity census'
    try:
        census = load_json(resolve(base, (bundle.get('native') or {}).get('purity')))
        entries = census.get('cases') if isinstance(census, dict) else census
        table = {}
        for e in entries:
            key = (e['case'], e['rule'])
            if e['case'] not in CASES or e['rule'] not in ('legacy', 'law'):
                raise Missing('unknown case or rule %s' % (key,))
            if key in table:
                raise Missing('duplicate census line %s' % (key,))
            table[key] = e['equal']
    except (Missing, KeyError, TypeError, AttributeError) as e:
        return crit(name, 'decisive', UNAVAILABLE, str(e))
    absent = [(c, r) for c in CASES for r in ('legacy', 'law') if (c, r) not in table]
    if absent:
        return crit(name, 'decisive', UNAVAILABLE, 'cases absent: %s' % absent)
    bad = [x for x in table.values() if not isinstance(x, bool)]
    if bad:
        return crit(name, 'decisive', UNAVAILABLE, 'non-boolean results')
    law_fail = sorted(c for c in CASES if table[(c, 'law')] is not True)
    legacy_fail = frozenset(c for c in CASES if table[(c, 'legacy')] is not True)
    problems = []
    if law_fail:
        problems.append('law arm differs from a fresh typing in cases %s' % law_fail)
    if legacy_fail != PREDICTED_LEGACY_FAIL:
        problems.append('legacy failures %s, predicted %s' % (sorted(legacy_fail), sorted(PREDICTED_LEGACY_FAIL)))
    if problems:
        return crit(name, 'decisive', NOT_MET, problems)
    return crit(name, 'decisive', MET, 'law passes all 11; legacy fails exactly %s' % sorted(PREDICTED_LEGACY_FAIL))


RESULT_RE = re.compile(r'test result: \w+\. (\d+) passed; (\d+) failed; (\d+) ignored')


def parse_suite(path):
    try:
        with open(path) as f:
            text = f.read()
    except OSError as e:
        raise Missing('%s: %s' % (path, e))
    found = RESULT_RE.findall(text)
    if not found:
        raise Missing('%s: no cargo result line' % path)
    passed = sum(int(p) for p, _, _ in found)
    failed = sum(int(x) for _, x, _ in found)
    ignored = sum(int(i) for _, _, i in found)
    return passed, failed, ignored


def c_suites(base, bundle):
    native = bundle.get('native') or {}
    out = []
    try:
        off = parse_suite(resolve(base, native.get('suite_off')))
        status = MET if off[1] == 0 and off[0] >= SUITE_BASELINE_PASSED else NOT_MET
        out.append(crit('V2 library suite, flag unset', 'validity', status,
                        'passed %d failed %d ignored %d' % off))
    except Missing as e:
        off = None
        out.append(crit('V2 library suite, flag unset', 'validity', UNAVAILABLE, str(e)))
    try:
        on = parse_suite(resolve(base, native.get('suite_on')))
        if on[1] > 0:
            status = NOT_MET
        elif off is None:
            status = UNAVAILABLE
        elif on[0] != off[0]:
            status = UNAVAILABLE
        else:
            status = MET
        out.append(crit('LIBRARY_GATE library suite, RH_LITERAL_CURRENT_WRITES=1', 'decisive', status,
                        'passed %d failed %d ignored %d' % on))
    except Missing as e:
        out.append(crit('LIBRARY_GATE library suite, RH_LITERAL_CURRENT_WRITES=1', 'decisive', UNAVAILABLE, str(e)))
    return out


def c_campfire(labels):
    name = 'CONTROL_EQUALITY Campfire: L equals C on every field'
    diffs, missing = [], []
    for prof, obs in CAMPFIRE_SETTINGS:
        for s in SCHEDULES:
            try:
                c = cell(labels, 'C_' + prof, 'campfire', s, obs)
                l = cell(labels, 'L_' + prof, 'campfire', s, obs)
                require_fields(c, obs, 'C campfire/%s-%s' % (s, obs))
                require_fields(l, obs, 'L campfire/%s-%s' % (s, obs))
            except Missing as e:
                missing.append(str(e))
                continue
            d = cell_differences(c, l)
            if d:
                diffs.append('%s-%s %s: %s' % (s, obs, prof, d))
    if diffs:
        return crit(name, 'decisive', NOT_MET, diffs)
    if missing:
        return crit(name, 'decisive', UNAVAILABLE, missing)
    return crit(name, 'decisive', MET, '12 cell pairs equal on %s' % list(CELL_FIELDS))


def loops_settled(o):
    loops = o.get('loops')
    if not isinstance(loops, dict) or set(loops) != EXPECTED_LOOPS:
        return None
    if not all(isinstance(v, dict) and v.get('end') in ('settled', 'cap')
               and isinstance(v.get('round'), int) for v in loops.values()):
        return None
    return all(isinstance(v, dict) and v.get('end') == 'settled' for v in loops.values())


def verify_map(o):
    v = o.get('verify')
    if v is None:
        return None
    if not isinstance(v, list) or not all(isinstance(x, dict) and isinstance(x.get('moved'), dict) for x in v):
        raise Missing('malformed verify observation')
    return {x.get('loop'): x['moved'] for x in v}


def c_fixpoint(labels, apps):
    """D6: L settles wherever C settles, and L's repeat equals L's unset. Verification movement outside
    Campfire is recorded (note 1): removing the freeze may unmask movement by design. Campfire's verify
    is decisive through CONTROL_EQUALITY's equality."""
    name = 'D6 L settles wherever C does and repeats agree'
    problems, missing = [], []
    for app in apps:
        for prof, obs in APP_SETTINGS[app]:
            got = {}
            for s in SCHEDULES:
                try:
                    pair = (cell(labels, 'C_' + prof, app, s, obs), cell(labels, 'L_' + prof, app, s, obs))
                    for observation in pair:
                        require_fields(observation, obs, '%s/%s-%s' % (app, s, obs))
                        if obs.startswith('v1'): verify_map(observation)
                    got[s] = pair
                except Missing as e:
                    missing.append(str(e))
            for s, (c, l) in got.items():
                cs, ls = loops_settled(c), loops_settled(l)
                if cs is None or ls is None:
                    missing.append('%s/%s-%s %s: loops absent' % (app, s, obs, prof))
                else:
                    for loop in sorted(EXPECTED_LOOPS):
                        if c['loops'][loop]['end'] == 'settled' and l['loops'][loop]['end'] != 'settled':
                            problems.append('%s/%s-%s %s: L does not settle %s' % (app, s, obs, prof, loop))
            if 'unset' in got and 'repeat' in got:
                lu, lr = got['unset'][1], got['repeat'][1]
                for f in CELL_FIELDS:
                    if (f == 'verify' and not obs.startswith('v1')) or (f == 'law_violation_counts' and not obs.endswith('a1')):
                        continue
                    if lu.get(f) is None or lr.get(f) is None:
                        missing.append('%s-%s %s: %s absent' % (app, obs, prof, f))
                    elif field_view(lu, f) != field_view(lr, f):
                        problems.append('%s-%s %s: L repeat differs from L unset in %s' % (app, obs, prof, f))
    if problems:
        return crit(name, 'decisive', NOT_MET, problems)
    if missing:
        return crit(name, 'decisive', UNAVAILABLE, missing[:20])
    return crit(name, 'decisive', MET, 'loops settle and repeats agree')


def verify_rises(labels, app):
    """Recorded: (rises, complete) of L's verification movement over C's at every V1 cell of app.
    `complete` is False when any V1 cell or its verify observation is missing or malformed."""
    rises, complete = [], True
    for prof, obs in APP_SETTINGS[app]:
        if not obs.startswith('v1'):
            continue
        for s in SCHEDULES:
            try:
                cv = verify_map(cell(labels, 'C_' + prof, app, s, obs))
                lv = verify_map(cell(labels, 'L_' + prof, app, s, obs))
            except Missing:
                complete = False
                continue
            if cv is None or lv is None:
                complete = False
                continue
            for loop, moved in lv.items():
                for table, n in moved.items():
                    base = (cv.get(loop) or {}).get(table, 0)
                    if n > base:
                        rises.append('%s-%s %s.%s %d > %d' % (s, obs, loop, table, n, base))
    return rises, complete


def c_webhook(rows_by, keys):
    """WEBHOOK_ORDER on Chatwoot. At every named observer whose inputs are fixed (P4b), no family row may vary
    under L. Power (P4a): C must vary in the family at one observer at least, or nothing was tested."""
    name = 'WEBHOOK_ORDER Chatwoot webhook family is schedule-equal under L'
    decls = set(keys.get('webhook_declarations') or [])
    if not decls:
        return crit(name, 'decisive', UNAVAILABLE, 'no webhook declarations in the frozen keys')
    details, unavailable, failed, powered = [], [], [], 0
    for obs in ROW_APPS['chatwoot']:
        rows = rows_by.get(('chatwoot', obs))
        if rows is None:
            unavailable.append('chatwoot %s rows unavailable' % obs)
            continue
        fam = [r for r in rows if r['declaration'] in decls]
        c_var = [r for r in fam if varies(r['C'])]
        inputs = [r for r in rows if r['declaration'] in WEBHOOK_INPUTS.get(r['part'], ())
                  and (varies(r['C']) or varies(r['L']))]
        if inputs:
            unavailable.append('%s: P4b fails, webhook inputs vary: %s' % (obs, [r['key'] for r in inputs][:5]))
            continue
        l_var = [r for r in fam if varies(r['L'])]
        surviving = [r for r in c_var if any(r['L'][s] is not None for s in SCHEDULES)]
        disappeared = len(c_var) - len(surviving)
        powered += 1 if surviving else 0
        details.append('%s: %d family rows vary in C, %d in L' % (obs, len(c_var), len(l_var)) + '; %d disappeared, %d surviving targets' % (disappeared, len(surviving)))
        if l_var:
            failed.append('%s: still varying under L: %s' % (obs, [r['key'] for r in l_var][:10]))
    if failed:
        return crit(name, 'decisive', NOT_MET, failed + details)
    if unavailable:
        return crit(name, 'decisive', UNAVAILABLE, unavailable + details)
    if not powered:
        return crit(name, 'decisive', UNAVAILABLE, ['P4a fails: no surviving C-varying family row at any observer'] + details)
    return crit(name, 'decisive', MET, details)


def load_witnesses(base, bundle):
    """[(map, witness doc)] or Missing."""
    out = []
    for m in bundle.get('witness_maps') or []:
        wmap = load_json(resolve(base, m))
        wdoc = load_json(resolve(os.path.dirname(resolve(base, m)), wmap['witness']))
        if not str(wdoc.get('ruby', '')).startswith('ruby 4.0.7 '):
            raise Missing('witness %s not run on CRuby 4.0.7' % wmap['witness'])
        out.append((wmap, wdoc))
    if not out:
        raise Missing('no witness maps')
    return out


def probe_for(row, witnesses):
    """The concatenated probe list mapped to a row, or None."""
    for wmap, wdoc in witnesses:
        if wmap.get('app') != row.get('app') or row['declaration'] not in wmap.get('declarations', []):
            continue
        names = None
        if row['part'] == 'returns':
            names = (wmap.get('returns') or {}).get('probes')
        else:
            span = row.get('span') or {}
            path = row['key'].rsplit(':occurrence:', 1)[-1].split(':', 1)[-1] if ':occurrence:' in row['key'] else None
            for entry in wmap.get('by_span', []):
                if [span.get('start'), span.get('end')] == entry['span'] and entry.get('path', path) == path:
                    names = entry['probes']
        if names:
            shapes = []
            for n in names:
                if n != 'nil' and n not in (wdoc.get('probes') or {}):
                    raise Missing('witness %s lacks probe %s' % (wmap.get('witness'), n))
                shapes += NIL_PROBE if n == 'nil' else wdoc['probes'][n]
            return shapes
    return None


def c_soundness(rows_by, witnesses, apps):
    name = 'RUNTIME_ADMISSION every changed value is sound'
    kills, unwitnessed, unknown, preexisting, counts = [], [], [], [], {}
    for (app, obs), rows in sorted(rows_by.items()):
        if app not in apps or rows is None:
            continue
        tally = {}
        for r in rows:
            r['app'] = app
            classes = [classify_pair(r['C'][s], r['L'][s]) for s in SCHEDULES]
            worst = max(classes, key=lambda x: SEVERITY[x])
            tally[worst] = tally.get(worst, 0) + 1
            probe = probe_for(r, witnesses) if witnesses is not None else None
            if probe is not None:
                for s, cls in zip(SCHEDULES, classes):
                    lv, cv = r['L'][s], r['C'][s]
                    if lv is None or lv.get('ty') is None:
                        continue
                    al = admits_probe(lv['ty'], probe)
                    ac = None if cv is None or cv.get('ty') is None else admits_probe(cv['ty'], probe)
                    where = '%s %s %s %s' % (app, obs, s, r['key'])
                    if al is False and ac is True:
                        kills.append(where + ': L rejects a runtime value C admits')
                    elif al is False and needs_witness(cls):
                        kills.append(where + ': L changed the value (%s) to one that rejects a runtime value' % cls)
                    elif al is False:
                        preexisting.append(where)
                    elif al is None and needs_witness(cls):
                        unknown.append(where)
            elif needs_witness(worst):
                unwitnessed.append('%s %s %s (%s)' % (app, obs, r['key'], worst))
        counts['%s %s' % (app, obs)] = tally
    if kills:
        return crit(name, 'decisive', NOT_MET, {'regressions': kills, 'counts': counts})
    if witnesses is None:
        return crit(name, 'decisive', UNAVAILABLE, {'reason': 'witnesses unavailable', 'counts': counts})
    missing_apps = [a for a in apps for o in ROW_APPS.get(a, ()) if rows_by.get((a, o)) is None]
    if unwitnessed or unknown or missing_apps:
        return crit(name, 'decisive', UNAVAILABLE, {'unwitnessed': unwitnessed[:50], 'undecided': unknown[:50],
                                                    'rows unavailable': missing_apps, 'counts': counts,
                                                    'preexisting_unsound': preexisting[:20]})
    return crit(name, 'decisive', MET, {'counts': counts, 'preexisting_unsound': preexisting[:20]})


def c_frozen(base, bundle):
    """V3: the advance prediction inputs still hash to the list recorded before any variant ran."""
    name = 'V3 advance prediction inputs unchanged'
    frozen = bundle.get('frozen') or {}
    try:
        listing = resolve(base, frozen.get('list'))
        root = resolve(base, frozen.get('root'))
        with open(listing) as f:
            entries = [line.split(None, 1) for line in f if line.strip()]
    except (Missing, OSError) as e:
        return crit(name, 'validity', UNAVAILABLE, str(e))
    seen, bad = set(), []
    for entry in entries:
        if len(entry) != 2:
            return crit(name, 'validity', UNAVAILABLE, 'malformed line in %s' % listing)
        digest, path = entry[0].strip(), entry[1].strip()
        full = path if os.path.isabs(path) else os.path.join(root, path)
        try:
            with open(full, 'rb') as f:
                actual = hashlib.sha256(f.read()).hexdigest()
        except OSError:
            bad.append('missing ' + path)
            continue
        if actual != digest:
            bad.append('changed ' + path)
        seen.add(os.path.basename(path))
    absent = [b for b in REQUIRED_FROZEN if b not in seen]
    if bad:
        return crit(name, 'validity', NOT_MET, bad)
    if absent:
        return crit(name, 'validity', UNAVAILABLE, 'not frozen: %s' % absent)
    return crit(name, 'validity', MET, '%d files match' % len(entries))


# ---------------------------------------------------------------- recorded predictions

def recorded(rows_by, keys, labels):
    out = []

    def rec(name, prediction, observed, hit):
        out.append({'name': name, 'prediction': prediction, 'observed': observed,
                    'result': 'unavailable' if hit is None else ('hit' if hit else 'miss')})

    def matched(app, obs):
        rows = rows_by.get((app, obs))
        if rows is None:
            return None
        want = {(r['part'], r['key']) for r in (keys.get('apps', {}).get(app, {}).get('rows') or [])}
        return [r for r in rows if (r['part'], r['key']) in want and varies(r['C'])]

    for app, threshold in (('chatwoot', 0.95), ('mastodon', 0.9)):
        m = matched(app, 'v1-a1')
        if m is None:
            rec('%s matched RETURN_HELPERS keys removed' % app, '>= %d%%' % (threshold * 100), None, None)
        else:
            removed = sum(1 for r in m if not varies(r['L']) and any(r['L'][s] is not None for s in SCHEDULES))
            disappeared = sum(1 for r in m if all(r['L'][s] is None for s in SCHEDULES))
            rec('%s matched RETURN_HELPERS keys disappeared' % app, 'record separately', disappeared, disappeared == 0)
            frac = removed / len(m) if m else None
            rec('%s matched RETURN_HELPERS keys removed' % app, '>= %d%%' % (threshold * 100),
                '%d of %d still-varying RETURN_HELPERS keys' % (removed, len(m)), None if frac is None else frac >= threshold)
    for app, bound in (('chatwoot', 0), ('mastodon', 10), ('forem', 0)):
        rows = rows_by.get((app, 'v1-a1'))
        if rows is None:
            rec('%s new varying rows under L' % app, '<= %d' % bound, None, None)
            continue
        new = [r for r in rows if varies(r['L']) and not varies(r['C'])]
        c_var_decls = {r['declaration'] for r in rows if varies(r['C'])}
        exposed = [r for r in new if r['declaration'] in c_var_decls]
        rec('%s new varying rows under L' % app, '<= %d, each in a declaration with a C-varying row' % bound,
            '%d new, %d exposed' % (len(new), len(exposed)), len(new) <= bound and len(exposed) == len(new))
    rows = rows_by.get(('forem', 'v1-a1'))
    if rows is None:
        rec('forem varying rows removed', '0', None, None)
    else:
        removed = [r for r in rows if varies(r['C']) and not varies(r['L'])
                   and any(r['L'][s] is not None for s in SCHEDULES)]
        rec('forem varying rows removed', '0', len(removed), len(removed) == 0)
    for app, allowed in (('chatwoot', {'controller_bindings', 'controller_cache', 'ir', 'params', 'returns', 'side_table'}),
                         ('mastodon', {'controller_bindings', 'controller_cache', 'ir', 'params', 'returns'})):
        try:
            c = cell(labels, 'C_on', app, 'unset', 'v1-a1')
            l = cell(labels, 'L_on', app, 'unset', 'v1-a1')
            changed = sorted(t for t in TABLES if (c.get('value_digests') or {}).get(t) != (l.get('value_digests') or {}).get(t))
            rec('%s changed tables at unset V1A1' % app, 'subset of %s' % sorted(allowed), changed, set(changed) <= allowed)
            dc, dl = c.get('diagnostics') or {}, l.get('diagnostics') or {}
            delta = {k: dl.get(k, 0) - dc.get(k, 0) for k in set(dc) | set(dl) if dl.get(k, 0) != dc.get(k, 0)}
            rec('%s diagnostics change at unset V1A1' % app, '|delta| <= 5 per kind', delta,
                all(abs(v) <= 5 for v in delta.values()))
            uc = (c.get('reason_census') or {}).get('untyped_anywhere')
            ul = (l.get('reason_census') or {}).get('untyped_anywhere')
            rec('%s census untyped_anywhere at unset V1A1' % app, 'L <= C (a relabel, not a precision gain)',
                {'C': uc, 'L': ul}, None if uc is None or ul is None else ul <= uc)
        except Missing:
            rec('%s changed tables at unset V1A1' % app, 'subset of %s' % sorted(allowed), None, None)
            rec('%s diagnostics change at unset V1A1' % app, '|delta| <= 5 per kind', None, None)
            rec('%s census untyped_anywhere at unset V1A1' % app, 'L <= C (a relabel, not a precision gain)', None, None)
    rows = rows_by.get(('chatwoot', 'v1-a1'))
    if rows is None:
        rec('webhook literal prints Array[untyped] under L', 'all four schedules, both copies', None, None)
    else:
        lits = [r for r in rows if r['declaration'] in set(keys.get('webhook_declarations') or [])
                and r['part'] == 'ir' and [((r.get('span') or {}).get('start')), ((r.get('span') or {}).get('end'))] == [1629, 1631]]
        prints = sorted({print_ty((r['L'][s] or {}).get('ty')) for r in lits for s in SCHEDULES})
        rec('webhook literal prints Array[untyped] under L', 'all four schedules, both copies', prints,
            None if not lits else prints == ['Array[untyped]'])
    for app in ('chatwoot', 'mastodon', 'forem'):
        rows = rows_by.get((app, 'v1-a1'))
        if rows is None:
            rec('%s presence changes' % app, '0', None, None)
            continue
        pres = sum(1 for r in rows if any((r['C'][s] is None) != (r['L'][s] is None) for s in SCHEDULES))
        rec('%s presence changes' % app, '0', pres, pres == 0)
    for app in ('chatwoot', 'mastodon', 'forem'):
        rises, complete = verify_rises(labels, app)
        rec('%s verification movement under L' % app, 'L <= C per loop and table at every V1 cell',
            rises if complete else None, None if not complete else not rises)
    try:
        lv = verify_map(cell(labels, 'L_on', 'mastodon', 'unset', 'v1-a1')) or {}
        cv = verify_map(cell(labels, 'C_on', 'mastodon', 'unset', 'v1-a1')) or {}
        pl, pc = (lv.get('production') or {}).get('ir'), (cv.get('production') or {}).get('ir')
        rec('mastodon production verify ir movement', 'L < C (E: 1 -> 0)', {'C': pc, 'L': pl},
            None if pl is None or pc is None else pl < pc)
    except Missing:
        rec('mastodon production verify ir movement', 'L < C (E: 1 -> 0)', None, None)
    return out


# ---------------------------------------------------------------- main

def guard(name, role, fn, *args):
    """Run one criterion; any unexpected exception makes it unavailable, never a kill (note 3)."""
    try:
        return fn(*args)
    except Missing as e:
        return crit(name, role, UNAVAILABLE, str(e))
    except Exception as e:
        return crit(name, role, UNAVAILABLE, 'verdict machinery error: %s: %s' % (type(e).__name__, e))


def guard_many(names_roles, fn, *args):
    try:
        return fn(*args)
    except Exception as e:
        return [crit(n, r, UNAVAILABLE, 'verdict machinery error: %s: %s' % (type(e).__name__, e)) for n, r in names_roles]


def evaluate(bundle_path, stage):
    base = os.path.dirname(os.path.abspath(bundle_path))
    bundle = load_json(bundle_path)
    apps = ('campfire',) if stage == 'campfire' else ('campfire', 'chatwoot', 'mastodon', 'forem')
    labels = {}
    for name in ('ref_on', 'ref_off', 'C_on', 'L_on', 'C_off', 'L_off'):
        try:
            labels[name] = load_label(resolve(base, (bundle.get('labels') or {}).get(name)))
        except Missing:
            labels[name] = None
    criteria = [guard('V3 advance prediction inputs unchanged', 'validity', c_frozen, base, bundle),
                guard('V0 control reproduces spine v2', 'validity', c_identity, base, bundle, labels, apps),
                guard('LITERAL_PURITY native purity census', 'decisive', c_purity, base, bundle)]
    criteria += guard_many((('V2 library suite, flag unset', 'validity'), ('LIBRARY_GATE library suite, RH_LITERAL_CURRENT_WRITES=1', 'decisive')),
                           c_suites, base, bundle)
    criteria.append(guard('CONTROL_EQUALITY Campfire: L equals C on every field', 'decisive', c_campfire, labels))
    criteria.append(guard('D6 L settles wherever C does and repeats agree', 'decisive', c_fixpoint, labels, apps))
    rows_by = {}
    rec_list = []
    if stage == 'final':
        keys = {}
        try:
            keys = load_json(resolve(base, bundle.get('keys')))
        except Missing:
            keys = {}
        row_errors = []
        for app, observers in ROW_APPS.items():
            for obs in observers:
                try:
                    rows_by[(app, obs)] = load_rows(base, ((bundle.get('rows') or {}).get(app) or {}).get(obs))
                except Missing as e:
                    rows_by[(app, obs)] = None
                    row_errors.append('%s %s: %s' % (app, obs, e))
        criteria.append(crit('V1 row dumps reconcile with native digests', 'validity',
                             UNAVAILABLE if row_errors else MET, row_errors or 'all row files reconcile'))
        literal_check_4 = 'WEBHOOK_ORDER Chatwoot webhook family is schedule-equal under L'
        criteria.append(guard(literal_check_4, 'decisive', c_webhook, rows_by, keys) if keys else
                        crit(literal_check_4, 'decisive', UNAVAILABLE, 'keys missing'))
        try:
            witnesses = load_witnesses(base, bundle)
        except (Missing, KeyError, TypeError, AttributeError):
            witnesses = None
        criteria.append(guard('RUNTIME_ADMISSION every changed value is sound', 'decisive', c_soundness, rows_by, witnesses,
                              ('chatwoot', 'mastodon', 'forem')))
        try:
            rec_list = recorded(rows_by, keys, labels)
        except Exception as e:  # recorded predictions never decide
            rec_list = [{'name': 'recorded predictions', 'prediction': None, 'observed': repr(e), 'result': 'unavailable'}]
    outcome, reasons = decide(criteria, stage)
    return {'condition': bundle.get('condition'), 'stage': stage, 'outcome': outcome, 'reasons': reasons,
            'criteria': criteria, 'recorded_predictions': rec_list}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('bundle')
    ap.add_argument('--stage', choices=('campfire', 'final'), default='final')
    ap.add_argument('--out')
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 3
    try:
        report = evaluate(a.bundle, a.stage)
    except Missing as e:
        report = {'stage': a.stage, 'outcome': 'INCONCLUSIVE', 'reasons': ['bundle unreadable: %s' % e],
                  'criteria': [], 'recorded_predictions': []}
    except Exception as e:  # note 3: a machinery failure is never a kill
        import traceback
        report = {'stage': a.stage, 'outcome': 'INCONCLUSIVE',
                  'reasons': ['verdict machinery error: %s: %s' % (type(e).__name__, e)],
                  'traceback': traceback.format_exc(), 'criteria': [], 'recorded_predictions': []}
    text = json.dumps(report, indent=1, sort_keys=True, default=str)
    if a.out:
        with open(a.out, 'w') as f:
            f.write(text + '\n')
    print(report['outcome'], '-', '; '.join(map(str, report['reasons'])) or 'all criteria met')
    for c in report['criteria']:
        print('  [%s] %s (%s)' % (c['status'], c['name'], c['role']))
    for r in report['recorded_predictions']:
        print('  recorded %-8s %s: predicted %s, observed %s' % (r['result'], r['name'], r['prediction'], r['observed']))
    return {'CONFIRMED': 0, 'PASSED': 0, 'KILLED': 1, 'INCONCLUSIVE': 2}[report['outcome']]


if __name__ == '__main__':
    sys.exit(main())
