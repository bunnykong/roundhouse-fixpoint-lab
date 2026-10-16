#!/usr/bin/env python3
"""Verdict for card Response-return, condition response-return-spine-witnesses-20261016 (phase2/void-top/response-protocol.md).

Reads obs.py cells (labels response-return-spine-response-returns-C, response-return-spine-response-returns-T, response-return-spine-response-returns-CA, response-return-spine-response-returns-TA and the spine references), the row dumps the
RETURN_HELPERS observer writes beside each cell (contributor-values.jsonl), the emission receipt (E1) and the suite receipt (L1).
Invokes no analyzer. Every check yields PASS, KILL, NARROW or UNAVAILABLE; unreadable input makes only the
checks that need it UNAVAILABLE. Three verdict lines, each with exactly one result:

  primary   INCONCLUSIVE(PRE) > KILLED > INCONCLUSIVE > NARROWED > CONFIRMED
  h5        INCONCLUSIVE(PRE) > INCONCLUSIVE > NOT_UNBLOCKED > NARROWED > CHANGED > UNBLOCKED
  discourse NOT RUN | INCONCLUSIVE(PRE) > KILLED > INCONCLUSIVE > NARROWED > CONFIRMED

usage: verdict.py --stage campfire|all [--cache-root DIR] [--emission FILE] [--suite FILE] --out DIR
Exit code: primary CONFIRMED 0, KILLED 1, INCONCLUSIVE 2, NARROWED 3.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

KIT = Path(__file__).resolve().parent
F = KIT.parents[2]  # copied kit lives at agents/<builder>/kit
FLAG = "RH_RESPONSE_RETURNS"
OWN_FLAGS = {"RH_SPLICED_WRITER_OWNERSHIP", "RH_SKIP_RETURN_STABILIZE"}
# v2: stabilization (#521's first-seen stabilize, upstream #964) is off in every variant. In v1 it kept or dropped
# stale pending stubs depending on whether a core was nil-only, which the change alters by design
# (phase2/void-top/response-return-analysis.md). Ownership variants already ran with it off.
OWN_EXPECT = {
    "C": {"RH_SPLICED_WRITER_OWNERSHIP": "0", "RH_SKIP_RETURN_STABILIZE": "1"},
    "T": {"RH_SPLICED_WRITER_OWNERSHIP": "0", "RH_SKIP_RETURN_STABILIZE": "1"},
    "CA": {"RH_SPLICED_WRITER_OWNERSHIP": "1", "RH_SKIP_RETURN_STABILIZE": "1"},
    "TA": {"RH_SPLICED_WRITER_OWNERSHIP": "1", "RH_SKIP_RETURN_STABILIZE": "1"},
}
LABELS = {"C": "response-return-spine-response-returns-C", "T": "response-return-spine-response-returns-T", "CA": "response-return-spine-response-returns-CA", "TA": "response-return-spine-response-returns-TA"}
REFS = {"C": "response-return-spine-response-returns-spine-ownership-off-nostab", "CA": "response-return-spine-response-returns-spine-ownership-on"}
# Both references must come from the unpatched spine binary, with the variant's flags apart from the row observer.
SPINE_SHA = "fb93bd1b1883778a255588e20be4dfae4bb14d5745523d8abd2fa46064ee264d"
REF_IGNORED_FLAGS = {"RH_CONTRIBUTOR_VALUES", "RH_RESPONSE_RETURNS"}
OBSERVER_DEFAULTS = dict(RH_FOLD="1", RH_FOLD_SLOTS="1", RH_FOLD_JOIN="1", RH_FOLD_TAIL="1",
                        RH_BRK_ALLARMS="1", RH_SCHED="sccq", RH_FIXPOINT_DIGEST="1",
                        RH_FIXPOINT_STATS="1", RH_PRECISION_CENSUS="1", RH_PUBLIC_INPUT="1", RH_ERRGATE="1")
PROFILES = {arm: json.loads((KIT / "profiles" / (arm + ".json")).read_text())
            for arm in ("C", "T", "CA", "TA")}
CAMPFIRE_SETTINGS = ["unset-v0-a0", "1-v0-a0", "2-v0-a0", "repeat-v0-a0", "unset-v1-a1"]
CORE_SETTINGS = ["unset-v0-a0", "repeat-v0-a0", "unset-v1-a1"]
H5_SETTINGS = ["unset-v0-a0", "1-v0-a0", "2-v0-a0", "repeat-v0-a0"]
DISCOURSE_SETTINGS = ["unset-v0-a0"]
PARTS = ("returns", "params", "controller_cache", "side_table", "ir")
INERT_FIELDS = ("value_digests", "reason_census", "diagnostics", "loops", "verify", "exit_code")
UNION_STR_INT = {"kind": "union", "variants": [{"kind": "str"}, {"kind": "int"}]}
RESPOND_RET = {"kind": "union", "variants": [{"kind": "str"}, {"kind": "int"}, {"kind": "bool"}, {"kind": "nil"}]}
REGISTRY = {  # key -> (control value, treatment value); respond_to compares the Fn's ret
    "ActionController::Base.render": ({"kind": "nil"}, {"kind": "str"}),
    "ActionController::Base.redirect_to": ({"kind": "nil"}, UNION_STR_INT),
    "ActionController::Base.redirect_back_or_to": ({"kind": "nil"}, UNION_STR_INT),
    "ActionController::Base.head": ({"kind": "nil"}, {"kind": "bool"}),
    "ActionController::Base.respond_to": ({"kind": "nil"}, RESPOND_RET),
}
PRIMARY_EXIT = {"CONFIRMED": 0, "KILLED": 1, "INCONCLUSIVE": 2, "INCONCLUSIVE(PRE)": 2, "NARROWED": 3}
STRING_CLASSES = {"String", "ActiveSupport::SafeBuffer", "ActionView::OutputBuffer"}


class Unavailable(Exception):
    pass


# ---------------------------------------------------------------- types as sets of Ruby values

def canon(t):
    """Canonical JSON: union variants sorted and flattened, so variant order never matters."""
    if isinstance(t, list):
        return [canon(x) for x in t]
    if not isinstance(t, dict):
        return t
    if t.get("kind") == "union":
        flat = []
        for v in t.get("variants") or []:
            v = canon(v)
            flat.extend(v["variants"] if isinstance(v, dict) and v.get("kind") == "union" else [v])
        uniq = {json.dumps(v, sort_keys=True): v for v in flat}
        return {"kind": "union", "variants": [uniq[k] for k in sorted(uniq)]}
    return {k: canon(v) for k, v in t.items()}


def kind(t):
    return t.get("kind") if isinstance(t, dict) and isinstance(t.get("kind"), str) else None


def soft(t):
    """var and unresolved rec: pending placeholders whose reading depends on the mode."""
    return kind(t) in ("var", "rec")


def is_top(t, mode):
    k = kind(t)
    if k == "untyped" or k is None:
        return True
    if soft(t):
        return mode == "primary"
    if k == "union":
        return any(is_top(v, mode) for v in t.get("variants") or [])
    return False


def is_empty(t, mode):
    k = kind(t)
    if k == "bottom":
        return True
    if soft(t):
        return mode != "primary"
    if k == "union":
        return all(is_empty(v, mode) for v in t.get("variants") or [])
    return False


def arms(t):
    if kind(t) == "union":
        out = []
        for v in t.get("variants") or []:
            out.extend(arms(v))
        return out
    return [t]


SCALARS = {"nil", "str", "sym", "bool", "int", "float", "time", "date"}


def covers(a, b, mode="primary"):
    """[[a]] contains [[b]] (class subtyping is not modeled: distinct names are incomparable)."""
    if is_empty(b, mode) or is_top(a, mode):
        return True
    if kind(b) == "union":
        return all(covers(a, v, mode) for v in b.get("variants") or [])
    if is_top(b, mode):
        return False
    return any(covers1(x, b, mode) for x in arms(a) if not is_empty(x, mode))


def covers1(a, b, mode):
    ka, kb = kind(a), kind(b)
    if is_top(a, mode):
        return True
    if ka == "array" and kb == "tuple":
        return all(covers(a.get("elem"), e, mode) for e in b.get("elems") or [])
    if ka != kb:
        return False
    if ka in SCALARS:
        return True
    if ka == "class":
        aa, ba = a.get("args") or [], b.get("args") or []
        return a.get("id") == b.get("id") and len(aa) == len(ba) and all(covers(x, y, mode) for x, y in zip(aa, ba))
    if ka == "array":
        return covers(a.get("elem"), b.get("elem"), mode)
    if ka == "hash":
        return covers(a.get("key"), b.get("key"), mode) and covers(a.get("value"), b.get("value"), mode)
    if ka == "tuple":
        ae, be = a.get("elems") or [], b.get("elems") or []
        return len(ae) == len(be) and all(covers(x, y, mode) for x, y in zip(ae, be))
    if ka == "fn":
        return covers(a.get("ret") or {"kind": None}, b.get("ret") or {"kind": None}, mode)
    return canon(a) == canon(b)  # relation, record, self_instance and anything else: equality


def strip_nil(t):
    """Every nil, at any depth, read as the empty set: what a response call's nil leaves behind."""
    if isinstance(t, list):
        return [strip_nil(x) for x in t]
    if not isinstance(t, dict):
        return t
    if kind(t) == "nil":
        return {"kind": "bottom"}
    return {k: (strip_nil(v) if k != "kind" else v) for k, v in t.items()}


def relation(c, t):
    """Classify one row: control value c, treatment value t (resolved JSON types or None)."""
    if c is None or t is None:
        return "STRUCT" if (c is None) != (t is None) else "EQ"
    if canon(c) == canon(t):
        return "EQ"
    if covers(t, c):
        return "WIDEN" if not covers(c, t) else "EQ"
    if covers(t, strip_nil(c)):
        return "NIL_DROPPED"
    if covers(t, strip_nil(c), "pending"):
        return "VAR_REC_ONLY"
    return "NARROW_NONNIL"


def admits(t, ruby_class, mode="primary"):
    if is_top(t, mode):
        return True
    if is_empty(t, mode):
        return False
    k = kind(t)
    if k == "union":
        return any(admits(v, ruby_class, mode) for v in t.get("variants") or [])
    if k == "fn":
        return admits(t.get("ret") or {"kind": None}, ruby_class, mode)
    if ruby_class in STRING_CLASSES:
        return k == "str" or (k == "class" and t.get("id") in STRING_CLASSES)
    simple = {"Integer": "int", "NilClass": "nil", "TrueClass": "bool", "FalseClass": "bool",
              "Symbol": "sym", "Float": "float", "Time": "time", "Date": "date"}
    if ruby_class in simple:
        return k == simple[ruby_class]
    if ruby_class == "Array":
        return k in ("array", "tuple")
    if ruby_class == "Hash":
        return k in ("hash", "record")
    return k == "class" and t.get("id") == ruby_class


# ---------------------------------------------------------------- cells and dumps

def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        raise Unavailable(f"unreadable {path}: {e}")


class Store:
    def __init__(self, cache_root):
        self.root = Path(cache_root)
        self.labels = {}
        self.dumps = {}

    def label(self, name):
        if name not in self.labels:
            try:
                self.labels[name] = read_json(self.root / "labels" / name / "label.json").get("cells") or {}
            except Unavailable as e:
                self.labels[name] = e
        if isinstance(self.labels[name], Unavailable):
            raise self.labels[name]
        return self.labels[name]

    def cell(self, label, app, setting):
        cells = self.label(label)
        entry = cells.get(app + "/" + setting)
        if not entry:
            raise Unavailable(f"{label}: no cell {app}/{setting}")
        if not entry.get("valid"):
            raise Unavailable(f"{label}: invalid cell {app}/{setting}")
        result = read_json(entry["result"])
        if not result.get("valid"):
            raise Unavailable(f"{label}: invalid result {app}/{setting}")
        obs = result.get("observations")
        if not isinstance(obs, dict):
            raise Unavailable(f"{label}: no observations {app}/{setting}")
        digests = obs.get("value_digests")
        if not isinstance(digests, dict) or len(digests) != 10:
            raise Unavailable(f"{label}: not ten digests {app}/{setting}")
        if obs.get("exit_code") not in (0, 1):
            raise Unavailable(f"{label}: exit {obs.get('exit_code')} {app}/{setting}")
        return result

    def dump(self, label, app, setting):
        """Signature index of a cell's contributor-values.jsonl, validated against its native report (RETURN_HELPERS's checks)."""
        key = (label, app, setting)
        if key not in self.dumps:
            try:
                self.dumps[key] = scan_dump(self.cell(label, app, setting))
            except Unavailable as e:
                self.dumps[key] = e
        if isinstance(self.dumps[key], Unavailable):
            raise self.dumps[key]
        return self.dumps[key]


def scan_dump(result):
    path = Path(result["directory"]) / "contributor-values.jsonl"
    sigs, ir, hashes = {}, [], {"returns": {}, "side_table": {}}
    try:
        with path.open() as f:
            header = json.loads(next(f))
            for n, line in enumerate(f, 2):
                row = json.loads(line)
                k = (row["part"], row["key"])
                if k in sigs:
                    raise Unavailable(f"{path}:{n}: duplicate row {k}")
                sigs[k] = f"{row.get('hash')}|{row.get('note')}|{row.get('module')}"
                if row["part"] == "ir":
                    sp = row["span"]
                    ir.append([sp["file"], sp["start"], sp["end"], row["hash"], row.get("note")])
                elif row["part"] in hashes:
                    hashes[row["part"]][row["key"]] = row["hash"]
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as e:
        raise Unavailable(f"unreadable dump {path}: {e!r}")
    if header.get("part") != "fingerprint":
        raise Unavailable(f"{path}: no fingerprint header")
    if header.get("digests") != result["observations"]["value_digests"]:
        raise Unavailable(f"{path}: fingerprint digests differ from the native report")
    if sorted(ir) != header.get("ir"):
        raise Unavailable(f"{path}: IR rows do not reproduce the native IR multiset")
    for part in hashes:
        if hashes[part] != (header.get("parts") or {}).get(part):
            raise Unavailable(f"{path}: {part} rows do not reproduce the native table")
    return {"path": path, "sigs": sigs, "parts": header.get("parts") or {}}


REC_RET = re.compile(r'Some\(Ret \{ class: ClassId\(Symbol\(("(?:\\.|[^"])*")\)\), method: Symbol\(("(?:\\.|[^"])*")\), class_side: (true|false) \}\)')


def load_rows(path, keys):
    """Rows for `keys`, with fold references resolved as research condition's rows.py resolves them (cycles stay rec)."""
    rows, refs = {}, {}
    try:
        with Path(path).open() as f:
            next(f)
            for line in f:
                v = json.loads(line)
                if v["part"] == "returns":
                    refs["return:" + v["key"]] = v.get("ty")
                elif v["part"] == "side_table":
                    refs[v["key"]] = v.get("ty")
                if (v["part"], v["key"]) in keys:
                    rows[(v["part"], v["key"])] = v
    except (OSError, ValueError, KeyError, StopIteration) as e:
        raise Unavailable(f"unreadable dump {path}: {e!r}")

    def resolve(t, seen):
        if isinstance(t, list):
            return [resolve(x, seen) for x in t]
        if not isinstance(t, dict):
            return t
        if t.get("kind") == "rec":
            slot = t.get("slot")
            lookup = slot
            m = REC_RET.fullmatch(slot or "")
            if m:
                c, meth, side = m.groups()
                lookup = "return:" + json.loads(c) + ("." if side == "true" else "#") + json.loads(meth)
            if lookup not in refs or slot in seen:
                return t
            return resolve(refs[lookup], seen | {slot})
        return {k: resolve(v, seen) for k, v in t.items()}

    return {k: resolve(v.get("ty"), frozenset()) for k, v in rows.items()}


# ---------------------------------------------------------------- checks

class Check:
    """One named check. Three independent facts; the status shown is the strongest."""

    def __init__(self, name):
        self.name, self.details = name, []
        self.killed = self.missing = self.narrowed = False

    def kill(self, msg):
        self.killed = True
        self.details.append("KILL " + msg)

    def narrow(self, msg):
        self.narrowed = True
        self.details.append("NARROW " + msg)

    def unavailable(self, msg):
        self.missing = True
        self.details.append("UNAVAILABLE " + msg)

    def report(self, msg):
        self.details.append(msg)

    @property
    def status(self):
        return "KILL" if self.killed else "UNAVAILABLE" if self.missing else "NARROW" if self.narrowed else "PASS"

    def as_json(self):
        return {"name": self.name, "status": self.status, "killed": self.killed, "missing": self.missing,
                "narrowed": self.narrowed, "details": self.details}


def flags_of(result):
    return {k: v for k, v in (result["key"].get("rh_flags") or {}).items() if "DUMP" not in k}


def observer_custody(chk, result, arm, app, setting, reference=False):
    """Bind the requested cell to its recorded observer, including an independent repeat."""
    schedule, verify, audit = setting.split("-")
    want = dict(name=setting, schedule=schedule, verification=verify == "v1", audit=audit == "a1")
    who = (REFS[arm] if reference else arm) + " " + app + "/" + setting
    for field, expected in (("app", app), ("setting", want)):
        if field not in result:
            chk.unavailable(f"{who}: missing {field} metadata")
        elif result[field] != expected:
            chk.kill(f"{who}: {field}={result[field]!r}, expected {expected!r}")
    key = result.get("key") or {}
    if "schedule" not in key:
        chk.unavailable(f"{who}: missing key.schedule")
    elif key["schedule"] != schedule:
        chk.kill(f"{who}: key.schedule={key['schedule']!r}, expected {schedule!r}")
    expected_flags = dict(OBSERVER_DEFAULTS, **PROFILES[arm])
    expected_flags.update(RH_FIXPOINT_VERIFY=verify[1:], RH_literal_check_3_PROV=audit[1:])
    if schedule in ("1", "2"):
        expected_flags["RH_SHUFFLE"] = schedule
    actual = flags_of(result)
    if reference:
        expected_flags = {k: v for k, v in expected_flags.items() if k not in REF_IGNORED_FLAGS}
        actual = {k: v for k, v in actual.items() if k not in REF_IGNORED_FLAGS}
    if actual != expected_flags:
        chk.kill(f"{who}: effective flags differ by {sorted(set(actual.items()) ^ set(expected_flags.items()))}")
def pregates(store, cells, arms_pairs):
    """P1 custody, P2 completeness, P3 inertness, P4 registry. `cells`: list of (variant, app, setting)."""
    p1, p2, p3, p4 = Check("P1 custody"), Check("P2 completeness"), Check("P3 inertness"), Check("P4 registry")
    results = {}
    for arm, app, setting in cells:
        try:
            results[(arm, app, setting)] = store.cell(LABELS[arm], app, setting)
            store.dump(LABELS[arm], app, setting)
        except Unavailable as e:
            p2.unavailable(str(e))
    shas = {r["key"].get("binary_sha256") for r in results.values()}
    if len(shas) > 1:
        p1.kill(f"cells use {len(shas)} binaries: {sorted(map(str, shas))}")
    for (arm, app, setting), r in results.items():
        observer_custody(p1, r, arm, app, setting)
        f = flags_of(r)
        if f.get("RH_CONTRIBUTOR_VALUES") != "1":
            p1.kill(f"{arm} {app}/{setting}: RH_CONTRIBUTOR_VALUES is not 1")
        if f.get(FLAG) != ("1" if arm in ("T", "TA") else "0"):
            p1.kill(f"{arm} {app}/{setting}: {FLAG}={f.get(FLAG)!r}")
        own = {k: f.get(k) for k in OWN_FLAGS}
        if own != OWN_EXPECT[arm]:
            p1.kill(f"{arm} {app}/{setting}: ownership and stabilization flags {own}, expected {OWN_EXPECT[arm]}")
        if setting.startswith("repeat-"):
            unset = results.get((arm, app, setting.replace("repeat-", "unset-", 1)))
            if unset and (not r.get("directory") or not unset.get("directory")):
                p1.unavailable(f"{arm} {app}/{setting}: missing execution directory")
            elif unset and Path(r["directory"]).resolve() == Path(unset["directory"]).resolve():
                p1.kill(f"{arm} {app}/{setting}: repeat reuses the unset execution")
    for base, treat in arms_pairs:
        for (arm, app, setting), r in results.items():
            if arm != treat or (base, app, setting) not in results:
                continue
            b = results[(base, app, setting)]
            fb, ft = flags_of(b), flags_of(r)
            extra = {k: ft[k] for k in ft if fb.get(k) != ft[k]}
            gone = [k for k in fb if k not in ft]
            if extra != {FLAG: "1"} or gone:
                p1.kill(f"{base}->{treat} {app}/{setting}: flags differ by {extra}, removed {gone}")
            if b["key"].get("input_manifest_sha256") != r["key"].get("input_manifest_sha256"):
                p1.kill(f"{base}->{treat} {app}/{setting}: input manifests differ")
    for (arm, app, setting), r in results.items():
        if arm not in REFS:
            continue
        try:
            ref = store.cell(REFS[arm], app, setting)
        except Unavailable as e:
            p3.unavailable(str(e))
            continue
        observer_custody(p1, ref, arm, app, setting, reference=True)
        if setting.startswith("repeat-"):
            try:
                unset_ref = store.cell(REFS[arm], app, setting.replace("repeat-", "unset-", 1))
                if not ref.get("directory") or not unset_ref.get("directory"):
                    p1.unavailable(f"{REFS[arm]} {app}/{setting}: missing execution directory")
                elif Path(ref["directory"]).resolve() == Path(unset_ref["directory"]).resolve():
                    p1.kill(f"{REFS[arm]} {app}/{setting}: repeat reuses the unset execution")
            except Unavailable as e:
                p1.unavailable(str(e))
        if ref["key"].get("input_manifest_sha256") != r["key"].get("input_manifest_sha256"):
            p1.kill(f"{arm} {app}/{setting}: input differs from {REFS[arm]}")
        if ref["key"].get("binary_sha256") != SPINE_SHA:
            p1.kill(f"{arm} {app}/{setting}: reference {REFS[arm]} was not produced by the pinned spine binary")
        fr = {k: v for k, v in flags_of(ref).items() if k not in REF_IGNORED_FLAGS}
        fa = {k: v for k, v in flags_of(r).items() if k not in REF_IGNORED_FLAGS}
        if fr != fa:
            p1.kill(f"{arm} {app}/{setting}: reference flags differ by {sorted(set(fr.items()) ^ set(fa.items()))}")
        diff = [fld for fld in INERT_FIELDS if ref["observations"].get(fld) != r["observations"].get(fld)]
        if diff:
            p3.kill(f"{arm} {app}/{setting} differs from {REFS[arm]} in {diff}")
    for (arm, app, setting), r in results.items():
        try:
            rows = load_rows(store.dump(LABELS[arm], app, setting)["path"], {("returns", k) for k in REGISTRY})
        except Unavailable as e:
            p4.unavailable(str(e))
            continue
        for key, (off, on) in REGISTRY.items():
            got = rows.get(("returns", key))
            if got is None:
                p4.unavailable(f"{arm} {app}/{setting}: registry row {key} missing")
                continue
            if key.endswith(".respond_to"):
                if kind(got) != "fn" or (got.get("block") or {}).get("id") != "ActionController::MimeResponds::Collector":
                    p4.kill(f"{arm} {app}/{setting}: {key} is not the Collector-yielding Fn")
                    continue
                got = got.get("ret")
            want = on if arm in ("T", "TA") else off
            if canon(got) != canon(want):
                p4.kill(f"{arm} {app}/{setting}: {key} = {json.dumps(got)}, expected {json.dumps(want)}")
    return [p1, p2, p3, p4], results


def witness_rows(store, arm, app, setting, keys):
    rows = load_rows(store.dump(LABELS[arm], app, setting)["path"], {("returns", k) for k in keys})
    return {k: rows.get(("returns", k)) for k in keys}


def check_witnesses(store, witnesses, arm, apps, settings, name, control=None):
    """Every listed key present and admitting every class, in every cell. Reports control informativeness."""
    chk = Check(name)
    informative = Counter()
    for w in witnesses:
        if w["app"] not in apps or w.get("role") != "render-family":
            continue
        for setting in settings:
            try:
                got = witness_rows(store, arm, w["app"], setting, w["keys"])
            except Unavailable as e:
                chk.unavailable(f"{w['id']} {arm} {w['app']}/{setting}: {e}")
                continue
            ctl = None
            if control:
                try:
                    ctl = witness_rows(store, control, w["app"], setting, w["keys"])
                except Unavailable as e:
                    chk.unavailable(f"{w['id']} {control} {w['app']}/{setting}: {e}")
            for key, t in got.items():
                if t is None:
                    chk.unavailable(f"{w['id']} {arm} {w['app']}/{setting}: key {key} missing")
                    continue
                for cls in w["classes"]:
                    if not admits(t, cls):
                        chk.kill(f"{w['id']} {arm} {w['app']}/{setting}: {key} = {json.dumps(t)[:160]} excludes {cls}")
                    elif not admits(t, cls, "pending"):
                        chk.report(f"{w['id']} {arm} {w['app']}/{setting}: {key} admits {cls} only through a pending placeholder")
                    if ctl is not None and ctl.get(key) is not None and not admits(ctl[key], cls):
                        informative[(w["app"], setting)] += 1
    return chk, informative


def parent(part, key):
    if part == "params":
        return key.rsplit("[", 1)[0]
    if part == "controller_cache":
        return key.split("#", 1)[0]
    return key


def compare_rows(store, base, treat, app, setting):
    """Classify every row of base vs treat. Raises Unavailable."""
    a, b = store.dump(LABELS[base], app, setting), store.dump(LABELS[treat], app, setting)
    keys = {k for k in set(a["sigs"]) | set(b["sigs"]) if k[0] in PARTS and a["sigs"].get(k) != b["sigs"].get(k)}
    # Every native table entry whose hash differs must be explained by a changed row (research condition rows.py's rule);
    # otherwise a dump is missing rows and the comparison would pass vacuously.
    for part in ("returns", "params", "controller_cache", "side_table"):
        left, right = a["parts"].get(part), b["parts"].get(part)
        if not isinstance(left, dict) or not isinstance(right, dict):
            raise Unavailable(f"{app}/{setting}: native {part} table missing from a dump header")
        native = {k for k in set(left) | set(right) if left.get(k) != right.get(k)}
        observed = {parent(part, k) for p, k in keys if p == part}
        if native != observed:
            raise Unavailable(f"{app}/{setting}: {part} rows do not account for the native changes "
                              f"({len(native ^ observed)} parents differ)")
    ra, rb = load_rows(a["path"], keys), load_rows(b["path"], keys)
    classes, rows = Counter(), []
    pa, pb = a["parts"]["params"], b["parts"]["params"]
    for k in sorted(keys):
        rel = relation(ra.get(k), rb.get(k))
        if rel == "STRUCT" and k[0] == "params" and parent("params", k[1]) in pa and parent("params", k[1]) in pb:
            # A vector's length is the method's arity: an element on one side only is a missing dump row.
            raise Unavailable(f"{app}/{setting}: params row {k[1]} present in one dump only")
        classes[(k[0], rel)] += 1
        if rel in ("NARROW_NONNIL", "VAR_REC_ONLY", "STRUCT"):
            rows.append({"part": k[0], "key": k[1], "relation": rel,
                         base: ra.get(k), treat: rb.get(k)})
    return classes, rows


def check_rows(store, base, treat, apps_settings, name):
    chk = Check(name)
    summary = {}
    for app, setting in apps_settings:
        try:
            classes, rows = compare_rows(store, base, treat, app, setting)
        except Unavailable as e:
            chk.unavailable(f"{app}/{setting}: {e}")
            continue
        summary[f"{app}/{setting}"] = {f"{p}:{r}": c for (p, r), c in sorted(classes.items())}
        for row in rows:
            if row["relation"] == "NARROW_NONNIL":
                chk.narrow(f"{app}/{setting} {row['part']} {row['key']}: {json.dumps(row[base])[:120]} -> {json.dumps(row[treat])[:120]}")
        chk.report({"cell": f"{app}/{setting}", "nonzero": summary[f"{app}/{setting}"],
                    "rows": [r for r in rows if r["relation"] != "NARROW_NONNIL"][:50]})
    return chk


def check_runtime(store, base, treat, apps_settings, name):
    """H4 error kinds do not rise; H6 settled loops stay settled; verification movement does not rise."""
    chk = Check(name)
    for app, setting in apps_settings:
        try:
            a = store.cell(LABELS[base], app, setting)["observations"]
            b = store.cell(LABELS[treat], app, setting)["observations"]
        except Unavailable as e:
            chk.unavailable(f"{app}/{setting}: {e}")
            continue
        da, db = a.get("diagnostics"), b.get("diagnostics")
        if not isinstance(da, dict) or not isinstance(db, dict):
            chk.unavailable(f"{app}/{setting}: diagnostics missing")
        else:
            for k in sorted(set(da) | set(db)):
                if k.startswith("error/") and db.get(k, 0) > da.get(k, 0):
                    chk.kill(f"{app}/{setting}: {k} {da.get(k, 0)} -> {db.get(k, 0)}")
            delta = {k: db.get(k, 0) - da.get(k, 0) for k in set(da) | set(db) if db.get(k, 0) != da.get(k, 0)}
            chk.report({"cell": f"{app}/{setting}", "diagnostic_delta": dict(sorted(delta.items())),
                        "census": [a.get("reason_census"), b.get("reason_census")]})
        la, lb = a.get("loops"), b.get("loops")
        if not isinstance(la, dict) or not isinstance(lb, dict):
            chk.unavailable(f"{app}/{setting}: loops missing")
        else:
            for loop, end in la.items():
                if (end or {}).get("end") == "settled" and (lb.get(loop) or {}).get("end") != "settled":
                    chk.kill(f"{app}/{setting}: loop {loop} settled in {base}, {lb.get(loop)} in {treat}")
        if "-v1-" in setting:
            va, vb = a.get("verify"), b.get("verify")
            expected = {"production": set(a["value_digests"]) | {"view_seeds"},
                        "views_and_tests": set(a["value_digests"]),
                        "absorb": set(a["value_digests"]) | {"view_seeds"}}
            def verification(records, arm):
                out = {}
                if not isinstance(records, list):
                    chk.unavailable(f"{app}/{setting}: {arm} verification records missing")
                    return out
                for record in records:
                    if not isinstance(record, dict) or record.get("loop") not in expected:
                        chk.unavailable(f"{app}/{setting}: {arm} invalid verification record")
                        continue
                    loop, moved = record["loop"], record.get("moved")
                    if loop in out:
                        chk.unavailable(f"{app}/{setting}: {arm} duplicate verification loop {loop}")
                    if not isinstance(moved, dict):
                        chk.unavailable(f"{app}/{setting}: {arm}/{loop} counters missing")
                        continue
                    out[loop] = {k: n for k, n in moved.items() if type(n) is int and n >= 0}
                    if set(out[loop]) != expected[loop]:
                        chk.unavailable(f"{app}/{setting}: {arm}/{loop} incomplete verification counters")
                if set(out) != set(expected):
                    chk.unavailable(f"{app}/{setting}: {arm} incomplete verification loops")
                return out
            ma, mb = verification(va, base), verification(vb, treat)
            for loop in ma.keys() & mb.keys():
                for table in ma[loop].keys() & mb[loop].keys():
                    if mb[loop][table] > ma[loop][table]:
                        chk.kill(f"{app}/{setting}: verify {loop}/{table} {ma[loop][table]} -> {mb[loop][table]}")
    return chk


FIXTURES = ["tiny-blog", "tiny-api", "tiny-blog-uuid", "real-blog", "store", "roda-blog", "gem-capabilities-historical-base"]
# Campfire's only emitted difference on main (examples/response-return-witnesses/apps-emit): the RBS sidecar of a test helper
# that maps `ApplicationController.render`, which Rails answers with the rendered String.
CAMPFIRE_EXPECTED = {
    "ruby": {"sig/test/models/action_text_attachment_opengraph_embed_test.rbs"},
    "spinel": {"test/action_text_attachment_opengraph_embed_test.rbs"},
}
CAMPFIRE_LINES = ["-      def render_embeds: (**untyped details) -> Array[nil]",
                  "+      def render_embeds: (**untyped details) -> Array[String]"]
TARGETS = ["crystal", "csharp", "elixir", "go", "kotlin", "python", "rust", "swift", "typescript",
           "typescript-worker", "ruby", "jruby", "spinel"]


def check_emission(path, binary_sha=None, custody=None):
    chk = Check("E1 emission")
    if not path:
        chk.unavailable("no emission receipt")
        return chk
    try:
        rec = read_json(path)
        if not isinstance(rec, dict) or not isinstance(rec.get("rows"), list):
            raise Unavailable("missing emission rows")
        if rec.get("arms") != {"off": {FLAG: "0"}, "on": {FLAG: "1"}}:
            if custody is not None:
                custody.kill("E1 native arm flags differ from the declared off/on settings")
            raise Unavailable("invalid named emission arm flags")
        digests = rec.get("binary_sha256")
        if not isinstance(digests, dict) or set(digests) != {"off", "on"} or not all(digests.values()):
            raise Unavailable("missing named emission binary digests")
        if len(set(digests.values())) != 1 or (binary_sha is not None and set(digests.values()) != {binary_sha}):
            if custody is not None:
                custody.kill("E1 binary digest differs from P1 observer binary")
            raise Unavailable("emission binary custody mismatch")
        if binary_sha is None:
            chk.unavailable("observer binary unavailable for emission binding")
        rows = {}
        for row in rec["rows"]:
            if not isinstance(row, dict) or not isinstance(row.get("input"), str) or not isinstance(row.get("target"), str):
                chk.unavailable("malformed emission row identity")
                continue
            key = (row["input"], row["target"])
            if key in rows:
                chk.unavailable(f"duplicate emission row {key}")
            rows[key] = row
    except (Unavailable, KeyError, TypeError, ValueError) as e:
        chk.unavailable(f"emission receipt: {e}")
        return chk
    for inp in FIXTURES + ["use-app", "tail-app", "void-app", "probe-app", "campfire"]:
        for tgt in TARGETS:
            r = rows.get((inp, tgt))
            if r is None:
                chk.unavailable(f"pair {inp}/{tgt} missing")
                continue
            exits = r.get("exit")
            if not isinstance(exits, list) or len(exits) != 2 or not all(type(n) is int for n in exits) \
                    or any(type(r.get(k)) is not bool for k in ("identical", "identical_files", "identical_stderr")):
                chk.unavailable(f"malformed emission row {inp}/{tgt}")
                continue
            off, on = exits
            if off not in (0, 1) or on not in (0, 1):
                chk.unavailable(f"{inp}/{tgt}: crashed or invalid emission exits {exits}")
                continue
            if inp == "campfire" and tgt in CAMPFIRE_EXPECTED and not r["identical"]:
                files = set(r.get("changed_files") or [])
                lines = r.get("changed_lines") or {}
                if off != on or not r["identical_stderr"] or not files <= CAMPFIRE_EXPECTED[tgt] \
                        or any(lines.get(f) != CAMPFIRE_LINES for f in files):
                    chk.kill(f"campfire/{tgt}: emission differs beyond the render_embeds sidecar line: {sorted(files)}")
                else:
                    chk.report(f"campfire/{tgt}: render_embeds sidecar reads Array[String] (by design)")
                continue
            if inp == "void-app":
                if on != 0:
                    chk.kill(f"{inp}/{tgt}: exit {on} with the flag; the change must unblock this app")
                elif off != 1:
                    chk.unavailable(f"{inp}/{tgt}: exit 0 without the flag, so the false error (the positive control) is absent")
            elif inp == "probe-app":
                if off != on or not r["identical_files"]:
                    chk.kill(f"{inp}/{tgt}: exits {off}/{on}, identical files {r['identical_files']}")
            elif not r["identical"]:
                chk.kill(f"{inp}/{tgt}: output differs (exit {off}/{on}, files {r['identical_files']}, stderr {r['identical_stderr']})")
    return chk


EXPECTED_NEW_FAILURES = {"analyze::if_branches_union_merge"}


def check_suite(path):
    chk = Check("L1 suite")
    if not path:
        chk.unavailable("no suite receipt")
        return chk
    try:
        rec = read_json(path)
        off, on = rec["off"], rec["on"]
        fo, fn = set(off["failed"]), set(on["failed"])
        if not (off["passed"] > 0 and on["passed"] > 0):
            chk.unavailable("a run passed no tests")
    except (Unavailable, KeyError, TypeError) as e:
        chk.unavailable(f"suite receipt: {e}")
        return chk
    for arm, run in (("off", off), ("on", on)):
        if run.get("completed") is not True or run.get("exit_code") not in (0, 101) or run.get("complete") is not True:
            chk.unavailable(f"{arm}: incomplete suite execution or inventory: {run.get('problems')}")
        inventory = run.get("inventory")
        observed = run.get("observed")
        if not isinstance(inventory, dict) or not inventory or not isinstance(observed, dict) or inventory != observed:
            chk.unavailable(f"{arm}: started/completed tests do not match expected suite inventory")
    if off.get("inventory") != on.get("inventory"):
        chk.unavailable("off/on suite inventories differ")
    new = fn - fo
    chk.report({"failed_off": sorted(fo), "new_with_flag": sorted(new), "passed": [off["passed"], on["passed"]]})
    if EXPECTED_NEW_FAILURES & fo:
        chk.unavailable("the pinned test already fails with the flag off")
    elif new - EXPECTED_NEW_FAILURES:
        chk.kill(f"new failures with the flag: {sorted(new - EXPECTED_NEW_FAILURES)}")
    elif new != EXPECTED_NEW_FAILURES:
        chk.unavailable("the pinned test passes with the flag on: the flag did not reach the in-process analyzer")
    return chk


# ---------------------------------------------------------------- roll-ups

def roll(checks, pre):
    """`pre` holds P1-P4. Affirmative setup errors (P1, P3, P4 killed) invalidate every comparison;
    missing evidence anywhere, P2 included, only blocks confirmation, so valid kills still win."""
    if any(c.killed for c in pre if c.name != "P2 completeness"):
        return "INCONCLUSIVE(PRE)"
    if any(c.killed for c in checks):
        return "KILLED"
    if any(c.missing for c in pre + checks):
        return "INCONCLUSIVE"
    if any(c.narrowed for c in checks):
        return "NARROWED"
    return "CONFIRMED"


def forecasts(store, apps_settings):
    out = {}
    expected = {"returns", "ir", "controller_cache"}
    for app, setting in apps_settings:
        try:
            a = store.cell(LABELS["C"], app, setting)["observations"]
            b = store.cell(LABELS["T"], app, setting)["observations"]
            changed = sorted(k for k in a["value_digests"] if a["value_digests"][k] != b["value_digests"][k])
            out[f"{app}/{setting}"] = {"changed_digests": changed, "digest_forecast_hit": set(changed) == expected,
                "digests": {k: {"changed": k in changed, "forecast_hit": (k in changed) == (k in expected)} for k in a["value_digests"]},
                "diagnostics_equal": a.get("diagnostics") == b.get("diagnostics"),
                "census_equal": a.get("reason_census") == b.get("reason_census")}
        except Unavailable as e:
            out[f"{app}/{setting}"] = {"unavailable": str(e)}
    return out


def run(args):
    store = Store(args.cache_root)
    witnesses = read_json(KIT / "witnesses.json")["witnesses"]
    out = {"condition": "response-return-spine-witnesses-20261016", "stage": args.stage}
    primary_apps = ["campfire"] if args.stage == "campfire" else ["campfire", "forem", "chatwoot", "mastodon"]
    ps = [(app, s) for app in primary_apps for s in (CAMPFIRE_SETTINGS if app == "campfire" else CORE_SETTINGS)]
    cells = [(arm, app, s) for app, s in ps for arm in ("C", "T")]
    pre, results = pregates(store, cells, [("C", "T")])
    checks = [check_rows(store, "C", "T", ps, "H2 no non-nil loss"),
              check_runtime(store, "C", "T", ps, "H4/H6 errors, loops, verification"),
              check_emission(args.emission, next(iter({r["key"].get("binary_sha256") for r in results.values()}), None), pre[0]),
              check_suite(args.suite)]
    if args.stage == "all":
        wapps = ["forem", "mastodon"]
        h1, informative = check_witnesses(store, witnesses, "T", wapps, CORE_SETTINGS, "H1 witnesses", control="C")
        for app in wapps:
            for setting in CORE_SETTINGS:
                if informative[(app, setting)] == 0:
                    h1.unavailable(f"{app}/{setting}: no witness key excludes its class in C")
        h1.report({"control_exclusions": {f"{a}/{s}": n for (a, s), n in informative.items()}})
        checks += [h1]
    out["forecasts"] = forecasts(store, ps + ([("discourse", s) for s in DISCOURSE_SETTINGS] if args.stage == "all" else []))
    verdict = roll(checks, pre)
    out["primary"] = {"verdict": verdict, "checks": [c.as_json() for c in pre + checks]}
    if args.stage == "all":
        out["h5"] = h5(store, witnesses)
        out["discourse"] = discourse(store)
    (Path(args.out) / "verdict.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    lines = [f"# Response-return verdict ({args.stage})", "", f"- primary: **{verdict}**"]
    for k in ("h5", "discourse"):
        if k in out:
            lines.append(f"- {k}: **{out[k]['verdict']}**")
    lines.append("")
    for c in out["primary"]["checks"] + [c for k in ("h5", "discourse") if k in out for c in out[k]["checks"]]:
        lines.append(f"- {c['name']}: {c['status']}" + (" (also missing evidence)" if c["missing"] and c["killed"] else ""))
        for d in c["details"][:12]:
            if isinstance(d, str):
                lines.append(f"  - {d[:300]}")
    (Path(args.out) / "verdict.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:6]))
    return PRIMARY_EXIT[verdict]


def h5(store, witnesses):
    apps = ["forem", "mastodon"]
    cells = [(arm, app, s) for app in apps for s in H5_SETTINGS for arm in ("CA", "TA")]
    pre, _ = pregates(store, cells, [("CA", "TA")])
    adm, _ = check_witnesses(store, witnesses, "TA", apps, H5_SETTINGS, "H5a render-family admitted under ownership")
    inf = Check("H5b defect reproduced")
    spliced = [w for w in witnesses if w["id"] in ("F-spliced", "M-suspension")]
    excluded = Counter()
    for w in spliced:
        hosts = [k for k in w["keys"] if "Concern#" not in k]  # the module contexts hold untyped by design
        for s in H5_SETTINGS:
            try:
                got = witness_rows(store, "CA", w["app"], s, hosts)
            except Unavailable as e:
                inf.unavailable(f"{w['id']} CA {w['app']}/{s}: {e}")
                continue
            for key, t in got.items():
                if t is None:
                    inf.unavailable(f"{w['id']} CA {w['app']}/{s}: key {key} missing")
                elif not all(admits(t, c) for c in w["classes"]):
                    excluded[(w["app"], s)] += 1
    for app in apps:
        for setting in H5_SETTINGS:
            if excluded[(app, setting)] == 0:
                inf.unavailable(f"{app}/{setting}: CA admits String at every spliced slot; defect not reproduced")
    inf.report({"ca_excluded_slots": {f"{a}/{s}": n for (a, s), n in sorted(excluded.items())}})
    narrow = check_rows(store, "CA", "TA", [(a, s) for a in apps for s in H5_SETTINGS], "H5d no non-nil loss under ownership")
    cust = Check("H5c customization kept")
    w = next(x for x in witnesses if x["id"] == "M-customization")
    population = read_json(KIT / "customization.json")
    expected_keys = {("returns", k) for k in population["keys"]}
    for s in H5_SETTINGS:
        try:
            a = store.dump(LABELS["CA"], "mastodon", s)
            keys = {k for k in a["sigs"] if k[0] == "returns" and any(re.fullmatch(p, k[1]) for p in w["key_regex"])}
            b = store.dump(LABELS["TA"], "mastodon", s)
            actual_b = {k for k in b["sigs"] if k[0] == "returns" and any(re.fullmatch(p, k[1]) for p in w["key_regex"])}
            if keys != expected_keys or actual_b != expected_keys:
                cust.unavailable(f"mastodon/{s}: expected all 72 frozen customization keys in CA and TA; got {len(keys)}/{len(actual_b)}")
            keys = expected_keys
            ra, rb = load_rows(a["path"], keys), load_rows(b["path"], keys)
        except Unavailable as e:
            cust.unavailable(f"mastodon/{s}: {e}")
            continue
        cust.report({"cell": s, "rows": len(keys)})
        for k in sorted(keys):
            if ra.get(k) is None or rb.get(k) is None:
                cust.unavailable(f"mastodon/{s}: missing customization key {k[1]}")
                continue
            pinned = population["precise"].get(k[1])
            if pinned is not None and canon(ra[k]) != canon(pinned):
                cust.kill(f"mastodon/{s} {k[1]}: CA lost pinned precise customization type")
            if canon(rb[k]) != canon(ra[k]):
                cust.kill(f"mastodon/{s} {k[1]}: {json.dumps(ra.get(k))[:100]} -> {json.dumps(rb.get(k))[:100]}")
                continue
            cls = next(c for p, c in w["classes_by_regex"].items() if re.fullmatch(p, k[1]))
            for c in cls:
                if not admits(rb[k], c):
                    cust.kill(f"mastodon/{s} {k[1]} excludes {c}")
    if any(c.killed for c in pre if c.name != "P2 completeness"):
        v = "INCONCLUSIVE(PRE)"
    elif any(c.missing for c in pre + [adm, inf, narrow, cust]):
        v = "INCONCLUSIVE"
    elif adm.killed:
        v = "NOT_UNBLOCKED"
    elif narrow.narrowed:
        v = "NARROWED"
    elif cust.killed:
        v = "CHANGED"
    else:
        v = "UNBLOCKED"
    return {"verdict": v, "checks": [c.as_json() for c in pre + [adm, inf, narrow, cust]]}


def discourse(store):
    present = False
    for arm in ("C", "T"):
        try:
            present |= any(k.startswith("discourse/") for k in store.label(LABELS[arm]))
        except Unavailable:
            pass
    if not present:
        return {"verdict": "NOT RUN", "checks": []}
    ps = [("discourse", s) for s in DISCOURSE_SETTINGS]
    pre, _ = pregates(store, [(arm, a, s) for a, s in ps for arm in ("C", "T")], [("C", "T")])
    checks = [check_rows(store, "C", "T", ps, "D-H2 no non-nil loss"), check_runtime(store, "C", "T", ps, "D-H4/H6")]
    return {"verdict": roll(checks, pre), "checks": [c.as_json() for c in pre + checks]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["campfire", "all"], required=True)
    ap.add_argument("--cache-root", default=str(F / "phase2/observers/cache"))
    ap.add_argument("--emission")
    ap.add_argument("--suite")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
