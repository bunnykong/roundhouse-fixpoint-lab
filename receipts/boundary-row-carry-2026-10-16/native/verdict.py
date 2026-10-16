#!/usr/bin/env python3
"""deferral-protocol verdict: every mandatory check, every report-only measurement, and one verdict per outcome.

  verdict.py run --cache-root CACHE --native DIR [--scope campfire|all] [--stage pregate|verdict]
                  [--label variant=LABEL ...] --out FILE
  verdict.py selftest

Reads recorded observer cells only (phase2/observers/obs.py cache, each cell's contributor-values.jsonl row dump, the
stratum-boundary dump contributor-values-boundary.jsonl, and RETURN_HELPERS's current-return-ledger.jsonl); it never runs the analyzer.
A record is pass, fail or unavailable. Order: INCONCLUSIVE when a pre-gate record is not a pass or any mandatory
record is unavailable; else KILLED when any mandatory record fails; else CONFIRMED. Unavailable evidence never
counts as a pass, and a missing or malformed measurement is unavailable, never zero. Every reducer family runs
inside a guard, so even an unexpected input yields a verdict. Python 3.9, standard library plus obs.py, row_model.py
and RETURN_HELPERS's frozen evidence/classifier modules (hash-checked before use).

Families: PG* are the pre-gate. Mandatory records carry a family: A (stratified producer strictness, L9),
N (normalizer dedup) or AN (the two together). R-* records are report-only. The card's verdict covers every
mandatory record; the three family verdicts are reported beside it.

Native receipts are parsed as Cargo prints them under --nocapture: the tagged line may follow the libtest prefix
`test NAME ... ` (the correction protocol's builder made before execution, strict-producer-protocol commit 8468b13).
"""
import argparse
import hashlib
import json
import random
from collections import Counter
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
F = HERE.parents[2]
RETURN_HELPERS = F / "receipts/latest-writer-returns-2026-10-15/native"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(F / "tools/observers"))
import row_model  # noqa: E402

S = ("unset", "1", "2", "repeat")
VA = {"campfire": ("v1-a1", "v1-a0", "v0-a1", "v0-a0"), "forem": ("v1-a1", "v0-a0"), "chatwoot": ("v1-a1", "v0-a0")}
TARGET_APPS = ("forem", "chatwoot")
K_SETTINGS = ("unset-v1-a1", "1-v1-a1", "2-v1-a1", "repeat-v1-a1", "unset-v0-a0", "repeat-v0-a0")
CONDITION = "boundary-row-carry-20261016-campfire"
FLAG_NAMES = ("RH_DEFERRED_CARRY", "RH_DEFERRED_DEFER", "RH_DEFERRED_STRATIFY", "RH_DEFERRED_NDEDUP", "RH_CURRENT_RETURN_REPLACE")
OFF = {"RH_DEFERRED_CARRY": "0", "RH_DEFERRED_DEFER": "0", "RH_DEFERRED_STRATIFY": "0", "RH_DEFERRED_NDEDUP": "0", "RH_CURRENT_RETURN_REPLACE": "0"}
_DS = {"RH_DEFERRED_CARRY": "1", "RH_DEFERRED_DEFER": "all", "RH_DEFERRED_STRATIFY": "1"}
_K = {"RH_CURRENT_RETURN_REPLACE": "1"}
_N = {"RH_DEFERRED_NDEDUP": "1"}
ARM_FLAGS = {"C": {}, "D": {"RH_DEFERRED_DEFER": "all"}, "DS": _DS, "N": _N, "DSN": {**_DS, **_N},
             "P1": {"RH_DEFERRED_DEFER": "stub"}, "K": _K, "KN": {**_K, **_N}, "KDS": {**_K, **_DS},
             "KDSN": {**_K, **_DS, **_N}}
ARMS = tuple(ARM_FLAGS)
SITES = ("register", "union_var", "conv_var", "use_zone", "timeout", "method_missing", "jbuilder", "block_closure",
         "param_seed", "ivar_read", "rs4")
TODAY = {"param_seed": "V", "ivar_read": "V"}  # what a site answers when it does not defer; others answer U
RESTORE = ("seen_none", "seen_pending", "skipped")
TABLES = row_model.TABLES
LOOPS = ("production", "views_and_tests", "absorb")
S1_LOOPS = tuple("stratum1_" + loop for loop in LOOPS)
DEFERRED_TYPES = {"carry": bool, "defer": str, "stratify": bool, "ndedup": bool, "stratum1_pending_minted": int, "boundary_restored": int,
            "stratum2_ran": bool, "stratum2_unresolved": int, "rclosure_kept_pending": int, "settled_pending": int}
FAMILIES = ("premature_unresolved", "placeholder_flip", "late_unresolved", "shape_refinement", "reference_switch",
            "arm_loss", "other")
N_WRITER = ["SetCurrentRequest", "default_url_options", False]
EVIDENCE = ("Gradual", "Unresolved", "LegacyAmbiguousVar")
CARGO_PREFIX = r"(?:test [^\n]+ \.\.\. )?"


def rec(check, scope, status, detail=None, family=None):
    """One record. A family marks it mandatory; report-only records have none."""
    assert status in ("pass", "fail", "unavailable")
    mandatory = family is not None or check.startswith("PG")
    return {"check": check, "scope": scope, "status": status, "mandatory": mandatory, "family": family,
            "detail": detail}


def nat(x):
    return type(x) is int and x >= 0


def norm_flags(flags):
    """The four variant flags of a cell, absent ones as off; None if the flag record is not a mapping."""
    if not isinstance(flags, dict):
        return None
    return {k: str(flags.get(k, OFF[k])) for k in FLAG_NAMES}


def arm_ok(store, arm, app, setting):
    c = store.cell(arm, app, setting)
    return c is not None and norm_flags(c[2]) == {**OFF, **ARM_FLAGS[arm]}


# ---------------------------------------------------------------- stores

def _current_return_modules():
    """RETURN_HELPERS's frozen evidence and classifier modules, after checking their recorded hashes."""
    freeze = {Path(x["file"]).name: x["public_uncompressed_sha256"] for x in json.loads((RETURN_HELPERS.parent / "manifest.json").read_text())["files"] if x["file"].startswith("native/")}
    for name in ("evidence.py", "classifiers.py", "order_a.py", "return_algebra.py", "verdict_returns.py"):
        if hashlib.sha256((RETURN_HELPERS / name).read_bytes()).hexdigest() != freeze[name]:
            raise ValueError("RETURN_HELPERS frozen module changed: " + name)
    sys.path.insert(0, str(RETURN_HELPERS))
    import classifiers
    import evidence
    if tuple(sorted(evidence_families())) != tuple(sorted(FAMILIES)):
        raise ValueError("RETURN_HELPERS descent families changed")
    return evidence, classifiers


def evidence_families():
    sys.path.insert(0, str(RETURN_HELPERS))
    import verdict_returns
    return list(verdict_returns.FAMILIES)


class ObsStore:
    """Recorded cells from an obs.py cache. Every accessor returns None for missing or malformed evidence."""

    def __init__(self, cache, labels):
        import obs
        self.obs, self.cache, self.labels, self.recs, self.memo, self.return_helpers = obs, Path(cache).resolve(), labels, {}, {}, None

    def _records(self, arm):
        if arm not in self.recs:
            try:
                self.recs[arm] = self.obs.label_records(self.obs.load_label(self.cache, self.labels[arm]))
            except Exception:  # noqa: BLE001 - any unreadable label is missing evidence
                self.recs[arm] = None
        return self.recs[arm]

    def _record(self, arm, app, setting):
        r = (self._records(arm) or {}).get(app + "/" + setting)
        return r if isinstance(r, dict) and r.get("valid") is True else None

    def cell(self, arm, app, setting):
        r = self._record(arm, app, setting)
        if r is None:
            return None
        o = r.get("observations")
        d = o.get("value_digests") if isinstance(o, dict) else None
        if not isinstance(d, dict) or set(d) != set(TABLES) or not all(isinstance(v, str) for v in d.values()):
            return None
        flags = (r.get("key") or {}).get("rh_flags") if isinstance(r.get("key"), dict) else None
        return o, r.get("directory"), flags

    def report(self, arm, app, setting):
        c = self.cell(arm, app, setting)
        try:
            got = json.loads((Path(c[1]) / "report.json").read_text()) if c else None
        except (OSError, ValueError, TypeError):
            return None
        return got if isinstance(got, dict) else None

    def reason_rows(self, arm, app, setting):
        r = self._record(arm, app, setting)
        try:
            got = self.obs.observed(r, "reason_rows") if r else None
        except Exception:  # noqa: BLE001
            return None
        return got if isinstance(got, dict) else None

    def rows(self, arm, app, setting, stage="final"):
        key = (arm, app, setting, stage)
        if key not in self.memo:
            self.memo[key] = self._rows(arm, app, setting, stage)
        return self.memo[key]

    def _rows(self, arm, app, setting, stage):
        c = self.cell(arm, app, setting)
        if c is None:
            return None
        name = "contributor-values.jsonl" if stage == "final" else "contributor-values-boundary.jsonl"
        try:
            rows, fingerprint, digests = row_model.load(Path(c[1]) / name, boundary=stage != "final")
        except Exception:  # every malformed cell is unavailable independently
            return None
        if row_model.coverage_gaps(rows, fingerprint):
            return None
        # A final dump whose fingerprint disagrees with the cell's native digests is not evidence.
        if stage == "final" and digests != c[0]["value_digests"]:
            return None
        return rows, fingerprint, digests

    def details(self, arm, app, setting, keys, stage="final"):
        c = self.cell(arm, app, setting)
        name = "contributor-values.jsonl" if stage == "final" else "contributor-values-boundary.jsonl"
        try:
            return row_model.load_details(Path(c[1]) / name, keys) if c else None
        except (OSError, ValueError, TypeError):
            return None

    def census(self, arm, app, setting):
        """RETURN_HELPERS's descent census of one strict-replacement cell: descents by family and the N writer's events."""
        c = self.cell(arm, app, setting)
        if c is None:
            return None
        try:
            if self.return_helpers is None:
                self.return_helpers = _current_return_modules()
            evidence, classifiers = self.return_helpers
            folder = Path(c[1])
            _, _, resolve = evidence.row_data(folder)
            led, state = classifiers.replay({"events": evidence.events(folder / "current-return-ledger.jsonl"),
                                             "resolve": resolve})
            n = sum(1 for e in state["descent_examples"] if e["family"] == "arm_loss"
                    and json.loads(e["writer"])[:3] == N_WRITER)
            events = [json.dumps({"family":e["family"], "writer":e["writer"],
                                  "superseded":row_model.normalize_n(e["superseded"]), "current":row_model.normalize_n(e["current"])},
                                 sort_keys=True) for e in state["descent_examples"]]
            n_signatures = [event for event, e in zip(events, state["descent_examples"])
                            if e["family"] == "arm_loss" and json.loads(e["writer"])[:3] == N_WRITER]
            return {"descents": dict(led["descents"]), "n_events": n, "events": events, "n_signatures": n_signatures}
        except Exception:  # noqa: BLE001 - a ledger the frozen replay rejects is missing evidence
            return None

    def forget(self, app, va):
        for k in [k for k in self.memo if k[1] == app and k[2].endswith(va)]:
            del self.memo[k]


# ---------------------------------------------------------------- measurements (None means unavailable)

def schedule_rows(store, arm, app, va):
    out = {}
    for s in S:
        got = store.rows(arm, app, s + "-" + va)
        if got is None:
            return None
        out[s] = got[0]
    return out


def target_ids(targets, app):
    out = {}
    ids = set(targets[app]["p_sensitive_ids"])
    for r in targets[app]["rows"]:
        if r["id"] in ids:
            part, key = r["part"], r["key"]
            if part == "params" and key.endswith("[empty]"):
                out[("fp:params", key[: -len("[empty]")])] = r["id"]
            else:
                out[(part, key)] = r["id"]
    return out


def reason_counts(store, arm, app, va, s):
    base, other = store.reason_rows(arm, app, "unset-" + va), store.reason_rows(arm, app, s + "-" + va)
    if base is None or other is None:
        return None
    try:
        changes = [k for k in set(base) & set(other) if base[k] != other[k]]
        reason = sum(1 for k in changes if base[k]["type_hash"] == other[k]["type_hash"])
    except (KeyError, TypeError):
        return None
    return {"R": reason, "T": len(changes) - reason, "M": len(set(base) ^ set(other))}


def verify_total(obs):
    """Movement summed over one verification record per loop that ran; None unless every record is complete."""
    loops, records = obs.get("loops"), obs.get("verify")
    if not isinstance(loops, dict) or not isinstance(records, list):
        return None
    ran = {k for k in LOOPS if isinstance(loops.get(k), dict) and loops[k].get("end") in ("settled", "ran_to_cap")}
    seen, total = set(), 0
    for r in records:
        if not isinstance(r, dict) or r.get("loop") not in LOOPS or r["loop"] in seen:
            return None
        moved = r.get("moved")
        if not isinstance(moved, dict) or not all(t in moved for t in TABLES) or not all(nat(v) for v in moved.values()):
            return None
        seen.add(r["loop"])
        total += sum(moved.values())
    return total if seen == ran and ran else None


def caps(report):
    """Worklist caps and the fold budget; None unless every counter is present and a natural number."""
    try:
        e = report["worklist"]["engine"]
        got = {k: e[k] for k in ("cap_hits", "frozen_units", "budget_exhausted")}
        got["fold_budget_cuts"] = report["fold"]["expansion"]["budget_cuts"]
    except (KeyError, TypeError):
        return None
    return got if all(nat(v) for v in got.values()) else None


def pending(obs):
    try:
        v = obs["reason_census"]["untyped_by_provenance"]["pending"]
    except (KeyError, TypeError):
        return None
    return v if nat(v) else None


def deferred_of(report):
    c6 = (report or {}).get("c6") if isinstance(report, dict) else None
    if not isinstance(c6, dict) or any(type(c6.get(k)) is not t for k, t in DEFERRED_TYPES.items()):
        return None
    if any(t is int and c6[k] < 0 for k, t in DEFERRED_TYPES.items()):
        return None
    return c6


def loop_end(obs, loop):
    v = (obs.get("loops") or {}).get(loop) if isinstance(obs.get("loops"), dict) else None
    return v.get("end") if isinstance(v, dict) else None


def evidence_losses(obs):
    laws = obs.get("law_violation_counts") or {}
    entries = [v for k, v in laws.items() if k.startswith("producer_evidence_")] if isinstance(laws, dict) else []
    if not entries:
        return None
    return sum(n for e in entries for k, n in (e.get("parameter_losses_by_kind") or {}).items() if k in EVIDENCE)


def pending_losses(obs):
    laws = obs.get("law_violation_counts") or {}
    entries = [v for k, v in laws.items() if k.startswith("producer_evidence_")] if isinstance(laws, dict) else []
    return sum((e.get("parameter_losses_by_kind") or {}).get("Pending", 0) for e in entries) if entries else None


def digests_of(rows):
    """Native-style digests of a row map: one per table over its fingerprint entries (or rows, for IR)."""
    out = {}
    for t in TABLES:
        items = sorted((k[1], v[0]) for k, v in rows.items() if k[0] == ("ir" if t == "ir" else "fp:" + t))
        out[t] = hashlib.sha256(json.dumps(items).encode()).hexdigest()[:16]
    return out


# ---------------------------------------------------------------- checks

def apps_in(scope):
    return ("campfire",) if scope == "campfire" else tuple(VA)


def pregate(store, pins, kpins, targets, scope):
    out = []
    for app in apps_in(scope):
        for va in VA[app]:
            for s in S:
                name, sc = s + "-" + va, "C/" + app + "/" + s + "-" + va
                c, pin = store.cell("C", app, name), pins["cells"].get(app + "/" + name)
                if c is None or pin is None:
                    out.append(rec("PG1-pinned-digests", sc, "unavailable", "missing cell or pin"))
                    continue
                if not arm_ok(store, "C", app, name):
                    out.append(rec("PG1-pinned-digests", sc, "unavailable", "arm flags differ from C's profile"))
                    continue
                o = c[0]
                out.append(rec("PG1-pinned-digests", sc, "pass" if o["value_digests"] == pin["digests"] else "fail"))
                got = store.rows("C", app, name)
                out.append(rec("PG2-row-dump-integrity", sc, "pass" if got is not None else "unavailable",
                               None if got is not None else "row dump missing, malformed, incomplete or mismatched"))
                rc = caps(store.report("C", app, name))
                delta = ({"R": 0, "T": 0, "M": 0} if store.reason_rows("C", app, name) is not None else None) \
                    if s == "unset" else reason_counts(store, "C", app, va, s)
                moved = verify_total(o) if "-v1-" in name else "not measured"
                measured = {"loops": o.get("loops"), "verify_moved_total": moved, "pending": pending(o),
                            "caps": rc, "reason_delta": delta}
                if rc is None or delta is None or moved is None or measured["pending"] is None:
                    out.append(rec("PG3-pinned-invariants", sc, "unavailable", "missing or malformed measurement"))
                    continue
                expected = {"loops": pin["loops"],
                            "verify_moved_total": pin["verify_moved_total"] if "-v1-" in name else "not measured",
                            "pending": pin["pending"], "caps": dict(pin["caps"], fold_budget_cuts=pin["fold_budget_cuts"]),
                            "reason_delta": pin["reason_delta"]}
                same = measured == expected
                out.append(rec("PG3-pinned-invariants", sc, "pass" if same else "fail",
                               None if same else {"measured": measured, "pinned": expected}))
    for app in [a for a in TARGET_APPS if a in apps_in(scope)]:
        for va in VA[app]:
            rows = schedule_rows(store, "C", app, va)
            if rows is None:
                out.append(rec("PG4-targets-vary", "C/" + app + "/" + va, "unavailable"))
                continue
            vc = row_model.varying(rows)
            live = [i for k, i in target_ids(targets, app).items() if k in vc]
            out.append(rec("PG4-targets-vary", "C/" + app + "/" + va, "pass" if live else "fail",
                           {"targets": len(target_ids(targets, app)), "varying_in_C": len(live)}))
    if "campfire" in apps_in(scope):
        for va in VA["campfire"]:
            rows = schedule_rows(store, "C", "campfire", va)
            out.append(rec("PG5-campfire-closed", "C/campfire/" + va,
                           "unavailable" if rows is None else ("pass" if not row_model.varying(rows) else "fail")))
        for name in K_SETTINGS:
            sc, pin = "K/campfire/" + name, kpins["cells"].get("campfire/" + name)
            c = store.cell("K", "campfire", name)
            got = store.census("K", "campfire", name) if c is not None and store.rows("K", "campfire", name) is not None else None
            if c is None or pin is None or got is None or not arm_ok(store, "K", "campfire", name):
                out.append(rec("PG6-schedule-row-baseline", sc, "unavailable", "missing K cell, pin, flags or replayable ledger"))
                continue
            same = (c[0]["value_digests"] == pin["digests"] and got["descents"] == pin["descents"]
                    and got["n_events"] == pin["n_events"])
            out.append(rec("PG6-schedule-row-baseline", sc, "pass" if same else "fail", None if same else got))
    return out


def tagged(log, ex, tag):
    """One JSON object after a tag, optionally prefixed by Cargo's `test NAME ... `; (value, exit code, error)."""
    try:
        matches = [m.group(1) for line in Path(log).read_text(errors="replace").splitlines()
                   for m in [re.fullmatch(CARGO_PREFIX + re.escape(tag) + r" (.*)", line)] if m]
        if len(matches) != 1:
            raise ValueError("expected exactly one " + tag + " object")
        value, code = json.loads(matches[0]), int(Path(ex).read_text().strip())
        if not isinstance(value, dict):
            raise ValueError("tagged JSON must be an object")
        return value, code, None
    except (OSError, ValueError, TypeError) as error:
        return None, None, str(error)


def native(directory, family=None):
    """H6g: the eleven sites in both strata and SK's restore per DEFER process; the dedup law per NDEDUP process."""
    out, d = [], Path(directory) if directory else None
    for defer in (() if family not in (None, "A") else ("0", "stub", "all")):
        if d is None:
            out.append(rec("H6g-sites", defer, "unavailable", "no native directory", "A"))
            continue
        got, code, error = tagged(d / ("sites-" + defer + ".log"), d / ("sites-" + defer + ".exit"), "DEFERRED-SITES")
        if error:
            out.append(rec("H6g-sites", defer, "unavailable", error, "A"))
            continue
        sites, restore = got.get("sites"), got.get("restore")
        stages = ("after_first_harvest", "after_boundary")
        if (not isinstance(sites, dict) or set(sites) != set(SITES)
                or not all(isinstance(v, dict) and "s1" in v and "stratum2" in v for v in sites.values())
                or not isinstance(restore, dict)
                or not all(isinstance(restore.get(st), dict) and all(k in restore[st] for k in RESTORE) for st in stages)):
            out.append(rec("H6g-sites", defer, "unavailable", "missing or invalid DEFERRED-SITES fields", "A"))
            continue
        if code != 0:
            out.append(rec("H6g-sites", defer, "fail", "test process exited " + str(code), "A"))
            continue
        want = {}
        for site in SITES:
            deferred = defer == "all" or (defer == "stub" and site == "register")
            today = TODAY.get(site, "U")
            want[site] = {"s1": "P" if deferred else today, "stratum2": today}
        want_restore = {"after_first_harvest": dict.fromkeys(RESTORE, "U" if defer == "0" else "P"),
                        "after_boundary": dict.fromkeys(RESTORE, "U")}
        observed = {site: {"s1": v["s1"], "stratum2": v["stratum2"]} for site, v in sites.items()}
        observed_restore = {st: {k: restore[st][k] for k in RESTORE} for st in stages}
        ok = observed == want and observed_restore == want_restore
        out.append(rec("H6g-sites", defer, "pass" if ok else "fail",
                       None if ok else {"observed": [observed, observed_restore], "expected": [want, want_restore]},
                       "A"))
    for flag in (() if family not in (None, "AN") else ("0", "1")):
        if d is None:
            out.append(rec("H6g-ndedup", flag, "unavailable", "no native directory", "AN"))
            continue
        got, code, error = tagged(d / ("ndedup-" + flag + ".log"), d / ("ndedup-" + flag + ".exit"), "DEFERRED-NDEDUP")
        if error or not all(isinstance(got.get(k), int) for k in ("flat_arms", "hash_value_arms")) \
                or not isinstance(got.get("idempotent"), bool):
            out.append(rec("H6g-ndedup", flag, "unavailable", error or "missing or invalid DEFERRED-NDEDUP fields", "AN"))
            continue
        if code != 0:
            out.append(rec("H6g-ndedup", flag, "fail", "test process exited " + str(code), "AN"))
            continue
        arms = 2 if flag == "1" else 4  # String | nil | String | nil: merged under the fix, kept as today without it
        ok = got["flat_arms"] == arms and got["hash_value_arms"] == arms and got["idempotent"] is True
        out.append(rec("H6g-ndedup", flag, "pass" if ok else "fail", None if ok else got, "AN"))
    return out


def native_provenance(directory):
    out = []
    for audit in ("0", "1"):
        d = Path(directory) if directory else Path("/nonexistent")
        got, code, error = tagged(d / ("ndedup-1-a"+audit+".log"), d / ("ndedup-1-a"+audit+".exit"), "DEFERRED-NDEDUP")
        if error or type(got.get("mixed_provenance_preserved")) is not bool:
            status = "unavailable"
        else:
            status = "pass" if code == 0 and got["mixed_provenance_preserved"] else "fail"
        out.append(rec("H6g-ndedup-provenance", "a"+audit, status, error or got, "AN"))
    return out


def strict_producer_protocol_native(directory):
    """protocol's six strictness processes and four law processes must still meet protocol's predictions.

    The predictions and field checks are those of the reducer protocol's verdict was computed with
    (agents/strict-producer-reasons/strict-producer-protocol/verdict.py, commit 8468b13), restated here so this script stands alone.
    """
    out, d = [], Path(directory) if directory else None
    if d is None:
        return [rec("H6g-strict-producer-protocol-harness", "native", "unavailable", "no native directory", "A")]
    for f in ("000", "100", "010", "110", "001", "111"):
        stubs, xfer, cong = (int(x) for x in f)
        got, code, error = tagged(d / ("harness-" + f + ".log"), d / ("harness-" + f + ".exit"), "provenance-STRICT")
        if error:
            out.append(rec("H6g-strict-producer-protocol-harness", f, "unavailable", error, "A"))
            continue
        required = {"flags": ("stubs", "xfer", "congruent"), "strictness": ("p1", "p2", "p3", "p4", "p5", "p6", "p7b"),
                    "deferred_var": ("p7",), "identity": ("p8", "p9"), "equality": ("p10_distinguishes",)}
        if any(not isinstance(got.get(k), dict) or not all(n in got[k] for n in names) for k, names in required.items()):
            out.append(rec("H6g-strict-producer-protocol-harness", f, "unavailable", "missing harness fields", "A"))
            continue
        if (any(not nat(got[k][n]) for k in ("flags", "strictness", "deferred_var", "identity") for n in required[k])
                or type(got["equality"]["p10_distinguishes"]) is not bool):
            out.append(rec("H6g-strict-producer-protocol-harness", f, "unavailable", "invalid harness fields", "A"))
            continue
        if code != 0:
            out.append(rec("H6g-strict-producer-protocol-harness", f, "fail", "test process exited " + str(code), "A"))
            continue
        want = {"flags": {"stubs": stubs, "xfer": xfer, "congruent": cong},
                "strictness": dict.fromkeys(("p1", "p2", "p3", "p4", "p5", "p6", "p7b"), 0 if xfer else 1),
                "deferred_var": {"p7": 1}, "identity": {"p8": 0 if xfer else 1, "p9": 0 if (stubs or xfer) else 1},
                "equality": {"p10_distinguishes": bool(cong)}}
        body = {k: {n: got[k][n] for n in required[k]} for k in want}
        out.append(rec("H6g-strict-producer-protocol-harness", f, "pass" if body == want else "fail",
                       None if body == want else {"observed": body, "expected": want}, "A"))
    for x in ("0", "1"):
        for test, tag in (("storage_extended_laws", "STORAGE-EXTENDED"), ("provenance_lineage_factorial", "PENDING-FACTORIAL")):
            scope = x + "/" + test
            got, code, error = tagged(d / ("laws-x" + x + "-" + test + ".log"), d / ("laws-x" + x + "-" + test + ".exit"), tag)
            if error:
                out.append(rec("H6g-strict-producer-protocol-laws", scope, "unavailable", error, "A"))
                continue
            if (not isinstance(got.get("counts"), dict) or type(got.get("seed_ok")) is not bool
                    or type(got.get("no_early_never")) is not bool):
                out.append(rec("H6g-strict-producer-protocol-laws", scope, "unavailable", "missing or invalid law fields", "A"))
                continue
            ok = code == 0 and got["counts"] == {} and got["seed_ok"] and got["no_early_never"]
            out.append(rec("H6g-strict-producer-protocol-laws", scope, "pass" if ok else "fail", None if ok else got, "A"))
    return out


FAMILY_OF = {"DS": "A", "N": "N", "DSN": "AN"}


def variance_checks(store, targets, scope, family=None):
    """H6b no new variance (DS everywhere; N, DSN on Campfire); H6a live targets close at a control value."""
    out = []
    for app in apps_in(scope):
        for va in VA[app]:
            sc = app + "/" + va
            rc = schedule_rows(store, "C", app, va)
            arms = ("DS",) if app != "campfire" else ("DS", "DSN")
            for arm in arms:
                fam = FAMILY_OF[arm]
                if family is not None and fam != family: continue
                ra = schedule_rows(store, arm, app, va)
                if rc is None or ra is None or not all(arm_ok(store, arm, app, s + "-" + va) for s in S):
                    out.append(rec("H6b-no-new-variance", arm + "/" + sc, "unavailable", "row dumps or arm flags", fam))
                    if arm == "DS" and app in TARGET_APPS:
                        out.append(rec("H6a-targets", sc, "unavailable", "row dumps or arm flags", "A"))
                    continue
                vc, va_ = row_model.varying(rc), row_model.varying(ra)
                new = sorted(k for k in va_ if k not in vc)
                out.append(rec("H6b-no-new-variance", arm + "/" + sc, "fail" if new else "pass",
                               {"new_rows": len([k for k in new if not k[0].startswith("fp:")]),
                                "new_native_entries": len([k for k in new if k[0].startswith("fp:")]),
                                "sample": [list(k) for k in new[:5]]}, fam))
                if arm == "DS" and app in TARGET_APPS:
                    live = {k: i for k, i in target_ids(targets, app).items() if k in vc}
                    left = sorted(i for k, i in live.items() if k in va_ or any(k not in ra[s] for s in S))
                    closed = [k for k, i in live.items() if i not in left]
                    new_value = sorted(live[k] for k in closed
                                       if row_model.value(ra["unset"][k]) not in {row_model.value(rc[s].get(k)) for s in S})
                    out.append(rec("H6a-targets", sc, "fail" if (left or new_value) else "pass",
                                   {"targets_varying_in_C": len(live), "still_varying_in_DS": left[:20],
                                    "n": len(left), "closed_to_a_new_value": new_value[:20],
                                    "n_new_value": len(new_value)}, "A"))
                if arm == "DS":
                    out.append(rec("R-varying-tables", sc, "pass",
                                   {"C": sorted({row_model.table_of(k) for k in vc}),
                                    "DS": sorted({row_model.table_of(k) for k in va_})}))
            if app == "campfire":
                rd = schedule_rows(store, "D", app, va)
                if rd is not None and rc is not None:
                    vd = row_model.varying(rd)
                    out.append(rec("R-D-variance", sc, "pass", {"varying": len(vd),
                                                               "new_vs_C": len([k for k in vd if k not in row_model.varying(rc)])}))
            store.forget(app, va)
    return out


def _classify(store, arm, app, name, c_rows, a_rows, keys, stage_a="final"):
    """Classify differing fine-grained rows of `variant` against C in one cell: (violations, unknown, note_only, removals)."""
    lost = [k for k in keys if k in c_rows and k not in a_rows]
    added = [k for k in keys if k in a_rows and k not in c_rows]
    both = [k for k in keys if k in c_rows and k in a_rows]
    da, dc = store.details(arm, app, name, both, stage_a), store.details("C", app, name, both)
    if da is None or dc is None or any(k not in da or k not in dc for k in both):
        return None
    violations, unknown, note_only, removals = list(lost) + list(added), [], [], []
    for k in both:
        if k[0] in row_model.STRUCTURAL:
            if da[k]["names"] != dc[k]["names"]:
                violations.append(k)
            continue
        r = row_model.relation(da[k]["ty"], dc[k]["ty"], ndedup="RH_DEFERRED_NDEDUP" in ARM_FLAGS[arm])
        if r == "violation":
            violations.append(k)
        elif r == "unknown":
            unknown.append(k)
        elif r == "removal":
            removals.append(k)
        elif da[k] != dc[k]:
            if arm == "N" and any(da[k].get(field) != dc[k].get(field) for field in ("diagnostic", "decisions")):
                violations.append(k)
            elif arm == "N" and a_rows[k][1] != c_rows[k][1]:
                violations.append(k)
            else:
                note_only.append(k)
    return violations, unknown, note_only, removals


def restoration(store, scope, family=None):
    """H6c: where stratum 2 changed any row (DS's boundary dump against its final dump), the final value is C's
    value with at most Unresolved removed. Positions inside one row are judged one by one; aggregates are not."""
    out = []
    for app in apps_in(scope):
        for arm in (("DS",) if app != "campfire" else ("DS", "DSN")):
            fam = FAMILY_OF[arm]
            if family is not None and fam != family: continue
            for va in VA[app]:
                rc = schedule_rows(store, "C", app, va)
                vc = row_model.varying(rc) if rc is not None else None
                for s in S:
                    name, sc = s + "-" + va, arm + "/" + app + "/" + s + "-" + va
                    fin, bnd = store.rows(arm, app, name), store.rows(arm, app, name, "boundary")
                    if vc is None or fin is None or bnd is None or not arm_ok(store, arm, app, name):
                        out.append(rec("H6c-restoration", sc, "unavailable", "row dumps, boundary dump or arm flags", fam))
                        continue
                    f, b, c = fin[0], bnd[0], rc[s]
                    changed = [k for k in set(f) | set(b) if not k[0].startswith("fp:") and f.get(k) != b.get(k)]
                    got = _classify(store, arm, app, name, c, f, changed)
                    if got is None:
                        out.append(rec("H6c-restoration", sc, "unavailable", "row details missing", fam))
                        continue
                    violations, unknown, _, _ = got
                    status = "unavailable" if unknown else ("fail" if violations else "pass")
                    out.append(rec("H6c-restoration", sc, status, {"changed_by_stratum_2": len(changed),
                                                                    "violations": len(violations), "unknown": len(unknown),
                                                                    "sample": [list(k) for k in (violations or unknown)[:5]]},
                                   fam))
                store.forget(app, va)
    return out


def direction(store, scope, family=None):
    """H6h (DS, DSN) and H6n (N) on Campfire, every cell: every differing row classified, every changed native entry
    and digest reconciled with a changed component. Unclassifiable evidence is unavailable, never accepted."""
    out = []
    if "campfire" not in apps_in(scope):
        return out
    for arm, check in (("DS", "H6h-campfire-direction"), ("DSN", "H6h-campfire-direction")):
        fam = FAMILY_OF[arm]
        if family is not None and fam != family: continue
        for va in VA["campfire"]:
            for s in S:
                name, sc = s + "-" + va, arm + "/campfire/" + s + "-" + va
                a, c = store.rows(arm, "campfire", name), store.rows("C", "campfire", name)
                if a is None or c is None or not arm_ok(store, arm, "campfire", name):
                    out.append(rec(check, sc, "unavailable", "row dumps or arm flags", fam))
                    continue
                ar, cr, ad, cd = a[0], c[0], a[2], c[2]
                differ = [k for k in set(ar) | set(cr) if not k[0].startswith("fp:") and ar.get(k) != cr.get(k)]
                got = _classify(store, arm, "campfire", name, cr, ar, differ)
                if got is None:
                    out.append(rec(check, sc, "unavailable", "row details missing", fam))
                    continue
                violations, unknown, note_only, removals = got
                if arm == "N":  # N may merge duplicate arms only: under set semantics nothing else may differ
                    violations = violations + removals
                # Reconciliation: a changed native entry or digest must have a changed component.
                unexplained = []
                for t in TABLES:
                    if t == "ir":
                        if ad[t] != cd[t] and not any(k[0] == "ir" for k in differ):
                            unexplained.append(("ir", "<digest>"))
                        continue
                    entries = {k[1] for k in set(ar) | set(cr) if k[0] == "fp:" + t}
                    for e in entries:
                        ka, kc = ("fp:" + t, e) in ar, ("fp:" + t, e) in cr
                        if ka != kc:
                            violations.append(("fp:" + t, e))
                        elif ar[("fp:" + t, e)] != cr[("fp:" + t, e)]:
                            comp = row_model.components(ar, t, e) + row_model.components(cr, t, e)
                            if not any(k in differ for k in comp):
                                unexplained.append(("fp:" + t, e))
                    if ad[t] != cd[t] and not any(k[0] in (t, "fp:" + t) and (k in differ or ar.get(k) != cr.get(k))
                                                  for k in set(ar) | set(cr)):
                        unexplained.append((t, "<digest>"))
                status = "unavailable" if (unknown or unexplained) else ("fail" if violations else "pass")
                out.append(rec(check, sc, status, {"differing_rows": len(differ), "removals": len(removals),
                                                    "note_only": len(note_only), "violations": len(violations),
                                                    "unknown": len(unknown), "unexplained": len(unexplained),
                                                    "sample": [list(k) for k in (violations or unknown or unexplained)[:5]]},
                               fam))
                if arm == "DS":
                    out.append(rec("R-campfire-differences", sc, "pass",
                                   {"rows": len(differ), "removals": len(removals), "note_only": len(note_only),
                                    "by_table": {t: sum(1 for k in differ if k[0] == t) for t in sorted({k[0] for k in differ})}}))
            store.forget("campfire", va)
    return out


def closure(store, scope, family=None):
    """H6f: on Campfire, each candidate variant's digests and diagnostics are equal across the four schedules."""
    out = []
    if "campfire" not in apps_in(scope):
        return out
    for arm in ("DS", "DSN"):
        if family is not None and FAMILY_OF[arm] != family: continue
        for va in VA["campfire"]:
            cells = [store.cell(arm, "campfire", s + "-" + va) for s in S]
            sc = arm + "/campfire/" + va
            if any(c is None or not isinstance(c[0].get("diagnostics"), dict) for c in cells):
                out.append(rec("H6f-campfire-closure", sc, "unavailable", None, FAMILY_OF[arm]))
                continue
            same = all(c[0]["value_digests"] == cells[0][0]["value_digests"]
                       and c[0]["diagnostics"] == cells[0][0]["diagnostics"] for c in cells)
            out.append(rec("H6f-campfire-closure", sc, "pass" if same else "fail", None, FAMILY_OF[arm]))
    return out


def reason_checks(store, scope, family=None):
    out = []
    for app in apps_in(scope):
        for arm in (("DS",) if app != "campfire" else ("DS", "DSN")):
            if family is not None and FAMILY_OF[arm] != family: continue
            for va in VA[app]:
                for s in S[1:]:
                    sc = arm + "/" + app + "/" + s + "-" + va
                    a, c = reason_counts(store, arm, app, va, s), reason_counts(store, "C", app, va, s)
                    if a is None or c is None:
                        out.append(rec("H6e-reason-deltas", sc, "unavailable", None, FAMILY_OF[arm]))
                    elif app == "campfire":
                        out.append(rec("H6e-reason-deltas", sc, "pass" if not any(a.values()) else "fail", a,
                                       FAMILY_OF[arm]))
                    else:
                        ok = all(a[k] <= c[k] for k in ("R", "T", "M"))
                        out.append(rec("H6e-reason-deltas", sc, "pass" if ok else "fail", {arm: a, "C": c},
                                       FAMILY_OF[arm]))
    return out


def settlement(store, scope, family=None):
    """H6d: a bound, not an identity: settlement rewrites in DS (and DSN) are not more than in C, cell by cell."""
    out = []
    for app in apps_in(scope):
        for arm in (("DS",) if app != "campfire" else ("DS", "DSN")):
            if family is not None and FAMILY_OF[arm] != family: continue
            for va in VA[app]:
                for s in S:
                    name, sc = s + "-" + va, arm + "/" + app + "/" + s + "-" + va
                    a, c = deferred_of(store.report(arm, app, name)), deferred_of(store.report("C", app, name))
                    if a is None or c is None:
                        out.append(rec("H6d-settlement-bound", sc, "unavailable", "c6 report missing or malformed",
                                       FAMILY_OF[arm]))
                    else:
                        out.append(rec("H6d-settlement-bound", sc, "pass" if a["settled_pending"] == 0
                                       else "fail", {arm: a["settled_pending"], "C": c["settled_pending"]}, FAMILY_OF[arm]))
                    census = {}
                    for x in ("C", "D", arm):
                        cell = store.cell(x, app, name)
                        try:
                            by = cell[0]["reason_census"]["untyped_by_provenance"] if cell else None
                            census[x] = {k: by.get(k) for k in ("gradual", "unresolved")} if isinstance(by, dict) else None
                        except (KeyError, TypeError):
                            census[x] = None
                    out.append(rec("R-census", sc, "pass", census))
    return out


def invariants(store, scope, family=None):
    """INV: loop ends, stratum-1 loops, caps, verification movement, final Pending and the c6 contract, against C (or,
    for a layered variant, K) in the same cell. Missing evidence makes the record unavailable even when something else
    also fails."""
    out = []
    plan = []
    for app in apps_in(scope):
        for arm in (("DS",) if app != "campfire" else ("DS", "DSN")):
            plan += [(arm, app, s + "-" + va) for va in VA[app] for s in S]
    if "campfire" in apps_in(scope):
        plan += [(arm, "campfire", name) for arm in ("KDS", "KDSN") for name in K_SETTINGS]
    fam_of = {"N": "N", "DS": "A", "DSN": "AN", "KN": "N", "KDS": "A", "KDSN": "AN"}
    for arm, app, name in plan:
        if family is not None and fam_of[arm] != family: continue
        sc = arm + "/" + app + "/" + name
        base = "K" if arm.startswith("K") else "C"  # a layered arm is compared with RETURN_HELPERS's baseline
        d, c = store.cell(arm, app, name), store.cell(base, app, name)
        rd, rc = store.report(arm, app, name), store.report(base, app, name)
        problems, missing = [], []
        if d is None or c is None or rd is None or rc is None:
            out.append(rec("INV", sc, "unavailable", "missing cell or report", fam_of[arm]))
            continue
        if not arm_ok(store, arm, app, name):
            missing.append("arm flags differ from the profile")
        for loop in LOOPS:
            ec, ed = loop_end(c[0], loop), loop_end(d[0], loop)
            if ec is None or ed is None:
                missing.append("loop " + loop)
            elif ec == "settled" and ed != "settled":
                problems.append("loop " + loop)
        c6 = deferred_of(rd)
        stratified = "RH_DEFERRED_STRATIFY" in ARM_FLAGS[arm]
        if c6 is None:
            missing.append("c6 report")
        elif (c6["defer"], c6["stratify"], c6["ndedup"]) != (ARM_FLAGS[arm].get("RH_DEFERRED_DEFER", "0"), stratified,
                                                           "RH_DEFERRED_NDEDUP" in ARM_FLAGS[arm]):
            missing.append("c6 flags differ from the arm")
        elif stratified:
            if c6["stratum1_pending_minted"] == 0:
                missing.append("stratum 1 deferred nothing")
            if c6["stratum2_ran"] is not True:
                problems.append("stratum 2 did not run")
            for loop in S1_LOOPS:
                end = loop_end(d[0], loop)
                if end is None:
                    missing.append(loop)
                elif end != "settled":
                    problems.append(loop + " not settled")
        a, b = caps(rd), caps(rc)
        if a is None or b is None:
            missing.append("caps")
        else:
            problems += [k + " above C" for k in a if a[k] > b[k]]
        if "-v1-" in name:
            m, mc = verify_total(d[0]), verify_total(c[0])
            if m is None or mc is None:
                missing.append("verification records")
            elif m > mc:
                problems.append("verification movement above C")
        pd, pc = pending(d[0]), pending(c[0])
        if pd is None or pc is None:
            missing.append("pending census")
        elif pd > pc:
            problems.append("pending above C")
        status = "unavailable" if missing else ("fail" if problems else "pass")
        out.append(rec("INV", sc, status, {"problems": problems, "missing": missing}, fam_of[arm]))
        if name.endswith("-a1"):
            out.append(rec("R-evidence-losses", sc, "pass", {arm: evidence_losses(d[0]), "C": evidence_losses(c[0]), "pending_kind": {arm: pending_losses(d[0]), base: pending_losses(c[0])}}))
    return out


def layered(store, kpins, scope, family=None):
    out = []
    zero_families = ("premature_unresolved", "late_unresolved", "placeholder_flip", "reference_switch", "shape_refinement")
    for arm, fam in (("KDS", "A"), ("KDSN", "AN")):
        if family is not None and family != fam: continue
        for name in K_SETTINGS:
            sc = arm+"/campfire/"+name
            got, base = store.census(arm,"campfire",name), store.census("K","campfire",name)
            available = (got is not None and base is not None and arm_ok(store,arm,"campfire",name)
                         and isinstance(got.get("descents"),dict)
                         and all(nat(got["descents"].get(x)) for x in FAMILIES)
                         and all(isinstance(x.get("events"),list) for x in (got,base)))
            out.append(rec("H6k-zero-families",sc,"unavailable" if not available else
                           ("pass" if all(got["descents"][x]==0 for x in zero_families) else "fail"),got,fam))
            out.append(rec("H6k-event-subset",sc,"unavailable" if not available else
                           ("pass" if not (Counter(got["events"])-Counter(base["events"])) else "fail"),got,fam))
            out.append(rec("R-descents",sc,"pass",got))
        for va, schedules in (("v1-a1",S),("v0-a0",("unset","repeat"))):
            sc=arm+"/campfire/"+va
            ra={x:store.rows(arm,"campfire",x+"-"+va) for x in schedules}
            rb={x:store.rows("K","campfire",x+"-"+va) for x in schedules}
            ca=[store.cell(arm,"campfire",x+"-"+va) for x in schedules]
            ready=all(x is not None for x in list(ra.values())+list(rb.values())+ca)
            new=[] if not ready else sorted(set(row_model.varying({x:r[0] for x,r in ra.items()}))-
                                           set(row_model.varying({x:r[0] for x,r in rb.items()})))
            out.append(rec("H6b-layered",sc,"unavailable" if not ready else ("fail" if new else "pass"),new,fam))
            closure=ready and all(c[0]["value_digests"]==ca[0][0]["value_digests"] and
                                  c[0].get("diagnostics")==ca[0][0].get("diagnostics") for c in ca)
            out.append(rec("H6f-layered",sc,"unavailable" if not ready else ("pass" if closure else "fail"),None,fam))
    return out


def named_equalities(store,scope,family=None):
    out=[]
    named=json.loads((HERE/"named-rows.json").read_text())
    for arm,fam in (("DS","A"),("DSN","AN")):
        if family is not None and family!=fam: continue
        for va in VA["campfire"]:
            for schedule in S:
                setting=schedule+"-"+va; keys=[tuple(x["id"]) for x in named]
                a=store.details(arm,"campfire",setting,keys);b=store.details("C","campfire",setting,keys)
                ready=a is not None and b is not None and set(a)==set(keys) and set(b)==set(keys)
                relations=None if not ready else [row_model.relation(a[x]["ty"],b[x]["ty"]) for x in keys]
                status="unavailable" if not ready or "unknown" in relations else ("pass" if all(x=="equal" for x in relations) else "fail")
                out.append(rec("H6h-named-equality",arm+"/campfire/"+setting,status,relations,fam))
    return out

def stratified_plan(scope):
    for app in apps_in(scope):
        for arm in (("DS","DSN") if app=="campfire" else ("DS",)):
            for va in VA[app]:
                for schedule in S: yield arm,app,schedule+"-"+va,FAMILY_OF[arm]
    for arm,fam in (("KDS","A"),("KDSN","AN")):
        for setting in K_SETTINGS: yield arm,"campfire",setting,fam


def carry_checks(store,scope,family=None):
    out=[]
    counters=("boundary_rows_lost","boundary_rows_reinserted","stratum2_answers_outside_set")
    reports=("boundary_placeholders_retracted","never_derived_size")
    for arm,app,name,fam in stratified_plan(scope):
        if family is not None and family!=fam: continue
        sc=arm+"/"+app+"/"+name; report=store.report(arm,app,name)
        c6=report.get("c6") if isinstance(report,dict) else None
        ready=(isinstance(c6,dict) and all(nat(c6.get(x)) for x in counters+reports)
               and type(c6.get("carry")) is bool and c6["carry"] and arm_ok(store,arm,app,name))
        out.append(rec("INV-boundary_carry",sc,"unavailable" if not ready else
                       ("pass" if all(c6[x]==0 for x in counters) else "fail"),c6,fam))
        if arm.startswith("K"):
            settled=c6.get("settled_pending") if isinstance(c6,dict) else None
            out.append(rec("H6d-layered",sc,"unavailable" if not nat(settled) else
                           ("pass" if settled==0 else "fail"),settled,fam))
        # Evidence gates do not mistake a valid semantic violation for unavailable evidence.
        boundary=store.rows(arm,app,name,"boundary")
        out.append(rec("EV-boundary-schema",sc,"pass" if boundary is not None else "unavailable",None,fam))
        base="K" if arm.startswith("K") else "C"
        a,b=store.rows(arm,app,name),store.rows(base,app,name)
        ready=a is not None and b is not None
        unknown=[]
        if ready:
            keys={x for x in set(a[0]) & set(b[0]) if x[0] in row_model.TYPED}
            da=store.details(arm,app,name,keys);db=store.details(base,app,name,keys)
            ready=da is not None and db is not None and set(da)==keys and set(db)==keys
            if ready: unknown=[x for x in keys if row_model.relation(da[x]["ty"],db[x]["ty"])=="unknown"]
        out.append(rec("EV-metadata-compare",sc,"pass" if ready and not unknown else "unavailable",unknown,fam))
    return out


def boundary_native(directory):
    out=[];d=Path(directory) if directory else Path("/nonexistent")
    for carry in ("0","1"):
        path=d/("boundary_carry-boundary-"+carry+".log")
        got,code,error=tagged(path,d/("boundary_carry-boundary-"+carry+".exit"),"BOUNDARY_CARRY-BOUNDARY")
        try: log=path.read_text()
        except OSError: log=""
        selected=re.findall(r"test [^\n ]*boundary_carry_boundary[^\n ]* \.\.\. (?:[^\n]*\n)?ok",log)
        summary=re.search(r"test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed;",log)
        required=("alias_retracted","concrete_reference_survives","mixed_preserved","absent_in_set",
                  "parameter_restored","helper_preserved","derived_not_answered","negative_answer_unresolved")
        ready=(not error and isinstance(got,dict) and all(type(got.get(x)) is bool for x in required)
               and all(nat(got.get(x)) for x in ("retractions","negative_size","boundary_rows_lost",
                                                    "boundary_rows_reinserted","stratum2_answers_outside_set","settled_pending"))
               and summary is not None and int(summary[1])+int(summary[2])>0
               and "boundary_carry_boundary" in log and got.get("selected_tests")==["boundary_carry_boundary"])
        want=2 if carry=="1" else 0
        ok=(ready and code==0 and all(got[x] for x in required) and got["retractions"]==want
            and got["negative_size"]==(4 if carry=="1" else 0)
            and all(got[x]==0 for x in ("boundary_rows_lost","boundary_rows_reinserted",
                                       "stratum2_answers_outside_set","settled_pending")))
        out.append(rec("H6g-boundary_carry-boundary","carry-"+carry,"unavailable" if not ready else
                       ("pass" if ok else "fail"),error or got,"A"))
    return out

def p1_report(store, targets, scope):
    out = []
    for app in [a for a in TARGET_APPS if a in apps_in(scope)]:
        rc, rp = schedule_rows(store, "C", app, "v1-a1"), schedule_rows(store, "P1", app, "v1-a1")
        if rc is None or rp is None:
            out.append(rec("R-P1-replication", app, "unavailable"))
            continue
        vc, vp = row_model.varying(rc), row_model.varying(rp)
        live = {k for k in target_ids(targets, app) if k in vc}
        out.append(rec("R-P1-replication", app, "pass", {"targets_removed": len(live - set(vp)), "targets_live": len(live),
                                                         "new": len([k for k in vp if k not in vc])}))
        store.forget(app, "v1-a1")
    return out


def decide(checks):
    gate = [c for c in checks if c["check"].startswith("PG")]
    mand = [c for c in checks if c["mandatory"]]
    if any(c["status"] != "pass" for c in gate):
        return "INCONCLUSIVE (pre-gate)"
    if any(c["status"] == "unavailable" for c in mand):
        return "INCONCLUSIVE (unavailable mandatory evidence)"
    if any(c["status"] == "fail" for c in mand):
        return "KILLED"
    return "CONFIRMED"


def guarded(name, family, fn, *args):
    """Run one reducer family; any unexpected error becomes an unavailable mandatory record, never a crash."""
    try:
        return fn(*args)
    except Exception as error:  # noqa: BLE001
        return [rec(name, "all", "unavailable", "reducer error: " + repr(error)[:300], family)]


def evidence_checks(store, scope, family):
    out, plan = [], []
    for app in apps_in(scope):
        for arm in (("DS", "DSN") if app == "campfire" else ("DS",)):
            if FAMILY_OF[arm] != family: continue
            plan += [(arm, app, schedule+"-"+va, "C") for va in VA[app] for schedule in S]
    for arm, fam in (("KDS", "A"), ("KDSN", "AN")):
        if family == fam: plan += [(arm, "campfire", setting, "K") for setting in K_SETTINGS]
    for arm, app, setting, baseline in plan:
        sc = arm+"/"+app+"/"+setting
        problems = []
        stages = ((baseline, "final"), (arm, "final"))
        if "RH_DEFERRED_STRATIFY" in ARM_FLAGS[arm]: stages += ((arm, "boundary"),)
        for candidate, stage in stages:
            got = store.rows(candidate, app, setting, stage)
            if got is None:
                problems.append(candidate+"/"+stage+": unavailable dump")
                continue
            keys = [k for k in got[0] if k[0] in row_model.TYPED]
            details = store.details(candidate, app, setting, keys, stage)
            try:
                if details is None or set(details) != set(keys): raise ValueError("missing details")
                for k in keys: row_model.validate_type(details[k]["ty"])
            except (ValueError, KeyError, TypeError) as error:
                problems.append(candidate+"/"+stage+": "+str(error))
        out.append(rec("EV-complete-provenance", sc, "unavailable" if problems else "pass", problems, family))
    return out


def expected_records(scope):
    out=set()
    def add(check,sc,fam): out.add((check,sc,fam))
    for x in ("0","stub","all"): add("H6g-sites",x,"A")
    for x in ("0","1"):
        add("H6g-ndedup",x,"AN");add("H6g-ndedup-provenance","a"+x,"AN")
        add("H6g-boundary_carry-boundary","carry-"+x,"A")
        for test in ("storage_extended_laws","provenance_lineage_factorial"): add("H6g-strict-producer-protocol-laws",x+"/"+test,"A")
    for x in ("000","100","010","110","001","111"): add("H6g-strict-producer-protocol-harness",x,"A")
    for app in apps_in(scope):
        for va in VA[app]:
            for arm in (("DS","DSN") if app=="campfire" else ("DS",)):
                fam=FAMILY_OF[arm]; sc=arm+"/"+app+"/"+va
                add("H6b-no-new-variance",sc,fam)
                add("H6f-campfire-closure",sc,fam) if app=="campfire" else add("H6a-targets",app+"/"+va,fam)
                for schedule in S:
                    sc=arm+"/"+app+"/"+schedule+"-"+va
                    for check in ("INV","EV-complete-provenance","INV-boundary_carry","EV-boundary-schema","EV-metadata-compare",
                                  "H6c-restoration","H6d-settlement-bound"): add(check,sc,fam)
                    if schedule!="unset": add("H6e-reason-deltas",sc,fam)
                    if app=="campfire":
                        add("H6h-campfire-direction",sc,fam);add("H6h-named-equality",sc,fam)
    for arm,fam in (("KDS","A"),("KDSN","AN")):
        for setting in K_SETTINGS:
            sc=arm+"/campfire/"+setting
            for check in ("INV","EV-complete-provenance","INV-boundary_carry","EV-boundary-schema","EV-metadata-compare",
                          "H6d-layered","H6k-zero-families","H6k-event-subset"): add(check,sc,fam)
        for va in ("v1-a1","v0-a0"):
            add("H6b-layered",arm+"/campfire/"+va,fam);add("H6f-layered",arm+"/campfire/"+va,fam)
    return out

def evaluate(store, pins, kpins, targets, native_dir, scope="all", stage="verdict"):
    checks = guarded("PG0-reducer", None, pregate, store, pins, kpins, targets, scope)
    if stage == "verdict":
        checks += guarded("H6g-strict-producer-protocol", "A", strict_producer_protocol_native, native_dir)
        checks += guarded("H6g-ndedup-provenance", "AN", native_provenance, native_dir)
        checks += guarded("H6g-boundary_carry-boundary", "A", boundary_native, native_dir)
        for family in ("A", "AN"):
            checks += guarded("EV-complete-provenance", family, evidence_checks, store, scope, family)
            for name, fn, args in (
                    ("H6g-native", native, (native_dir,)),
                    ("H6ab-variance", variance_checks, (store, targets, scope)),
                    ("H6c-restoration", restoration, (store, scope)),
                    ("H6hn-direction", direction, (store, scope)),
                    ("H6f-closure", closure, (store, scope)),
                    ("H6e-reasons", reason_checks, (store, scope)),
                    ("H6d-settlement", settlement, (store, scope)),
                    ("INV", invariants, (store, scope)),
                    ("INV-boundary_carry", carry_checks, (store,scope)),
                    ("H6h-named-equality", named_equalities, (store,scope)),
                    ("H6k-layered", layered, (store, kpins, scope))):
                checks += guarded(name, family, fn, *args, family)

    if stage == "verdict":
        observed = {(r["check"], r["scope"], r["family"]) for r in checks}
        for check, sc, family in sorted(expected_records(scope) - observed):
            checks.append(rec(check, sc, "unavailable", "mandatory record was not produced", family))
    result = {"condition": CONDITION, "not_evaluated": {"N":"not evaluated (6b KILLED)", "KN":"not evaluated", "narrow_equality_forecasts":"mandatory H6h-named-equality", "residual_exact_counts":"report-only"}, "scope": scope, "stage": stage, "verdict": decide(checks), "checks": checks}
    if stage == "verdict":
        gate = [c for c in checks if c["check"].startswith("PG")]
        result["family_verdicts"] = {f: decide(gate + [c for c in checks if c["family"] == f]) for f in ("A", "AN")}
    return result


# ---------------------------------------------------------------- selftest

class FakeStore:
    """Synthetic cells for the self-test, with the same validation contract as ObsStore."""

    def __init__(self):
        self.data, self.raise_reports = {}, False

    def put(self, arm, app, setting, obs, rows, report, boundary=None, census=None, flags=None):
        self.data[(arm, app, setting)] = {"obs": obs, "rows": rows, "report": report, "boundary": boundary,
                                          "census": census, "flags": {**OFF, **ARM_FLAGS[arm]} if flags is None else flags}

    def _get(self, arm, app, setting):
        return self.data.get((arm, app, setting))

    def cell(self, arm, app, setting):
        v = self._get(arm, app, setting)
        if not v or not isinstance(v["obs"], dict):
            return None
        d = v["obs"].get("value_digests")
        if not isinstance(d, dict) or set(d) != set(TABLES):
            return None
        return v["obs"], "/fake", v["flags"]

    def report(self, arm, app, setting):
        if self.raise_reports:
            raise ValueError("malformed report.json")
        v = self._get(arm, app, setting)
        return v["report"] if v and isinstance(v["report"], dict) else None

    def reason_rows(self, arm, app, setting):
        v = self._get(arm, app, setting)
        return v["obs"].get("_reason_rows") if v and isinstance(v["obs"], dict) else None

    def rows(self, arm, app, setting, stage="final"):
        v = self._get(arm, app, setting)
        spec = (v or {}).get("rows" if stage == "final" else "boundary")
        if spec is None:
            return None
        rows, fingerprint = fake_rows(spec)
        if row_model.coverage_gaps(rows, fingerprint):
            return None
        digests = digests_of(rows)
        if stage == "final" and digests != v["obs"].get("value_digests"):
            return None
        return rows, fingerprint, digests

    def details(self, arm, app, setting, keys, stage="final"):
        v = self._get(arm, app, setting)
        spec = (v or {}).get("rows" if stage == "final" else "boundary")
        if spec is None:
            return None
        return {k: spec[k] for k in keys if k in spec}

    def census(self, arm, app, setting):
        v = self._get(arm, app, setting)
        return v["census"] if v else None

    def forget(self, app, va):
        pass


def _blind(t):
    """The reason-blind form the native hash sees: provenance and duplicate variants dropped."""
    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if k != "reasons"}
        if isinstance(x, list):
            return [strip(v) for v in x]
        return x
    return row_model.norm(strip(t))


def _h(obj):
    return int(hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:12], 16)


def fake_rows(spec):
    """Rows, native entries and a fingerprint from a spec {(part, key): detail}; detail has `ty` or `names`."""
    rows, fingerprint = {}, {t: {} for t in TABLES if t != "ir"}
    for (part, key), d in spec.items():
        if part.startswith("fp:"):
            fingerprint[part[3:]][key] = d["value"]
            continue
        h = _h(d["names"]) if part in row_model.STRUCTURAL else _h(_blind(d["ty"]))
        note = d.get("note")
        rows[(part, key)] = (h, note, hash(json.dumps(row_model.detail_of({**d, "native_ty": d.get("ty")}), sort_keys=True)))
    for (part, key), row in list(rows.items()):
        if part == "params":
            entry = key.rsplit("[", 1)[0]
            comps = sorted((k[1], v[0]) for k, v in rows.items() if k[0] == "params" and k[1].startswith(entry + "["))
            fingerprint["params"][entry] = _h(comps)
        elif part in fingerprint and row_model.SEPARATOR.get(part) is None:
            fingerprint[part].setdefault(key, row[0])
    for (part, key), d in spec.items():
        if part.startswith("fp:"):
            fingerprint[part[3:]][key] = d["value"]
    for t, entries in fingerprint.items():
        for e, v in entries.items():
            rows[("fp:" + t, e)] = (v, None, None)
    return rows, fingerprint


U = {"kind": "untyped", "reasons": ["Unresolved"]}
G = {"kind": "untyped", "reasons": ["Gradual"]}
P = {"kind": "untyped", "reasons": ["Pending"]}
USER = {"kind": "class", "id": "User", "args": []}
INT, STR, NIL = {"kind": "int"}, {"kind": "str"}, {"kind": "nil"}


def union(*v):
    return {"kind": "union", "variants": list(v)}


def world(arm, app, s):
    """The predicted row spec of one cell: a never-derived parameter, a premature one, a duplicate-variant union, a
    structural entry, and on Forem and Chatwoot one source-4 target."""
    boundary = arm.endswith("@boundary")
    arm = arm.split("@")[0]
    strict = arm in ("DS", "DSN", "D", "KDS", "KDSN")
    dedup = arm in ("N", "DSN", "KN", "KDSN")
    never = (P if boundary else U) if arm in ("DS", "DSN", "KDS", "KDSN") else (G if arm == "D" else U)
    spec = {("params", "U#u[0]"): {"ty": never},
            ("params", "M#m[0]"): {"ty": USER if strict else union(USER, U)},
            ("params", "Dup#d[0]"): {"ty": union(STR, NIL) if dedup else union(STR, NIL, STR, NIL)},
            ("block_values", "K"): {"names": {"block_value_methods": ["k"]}},
            ("returns", "K#k"): {"ty": INT}}
    if app in TARGET_APPS:
        spec[("params", "T#t[0]")] = {"ty": union(INT, U) if (arm in ("C", "K", "KN") and s == "1") else INT}
    return spec


def fixture():
    """A world in which every prediction holds."""
    store, pins, kpins = FakeStore(), {"cells": {}}, {"cells": {}}
    targets = {app: {"rows": [{"id": app[:2] + "-1", "part": "params", "key": "T#t[0]"}], "p_sensitive_ids": [app[:2] + "-1"]}
               for app in TARGET_APPS}
    k_census = dict(dict.fromkeys(FAMILIES, 0), premature_unresolved=14, arm_loss=5, other=1)
    censuses = {"K": (k_census, 2), "KN": (dict(k_census, arm_loss=3), 0), "KDS": (dict(dict.fromkeys(FAMILIES, 0), arm_loss=2), 2),
                "KDSN": (dict.fromkeys(FAMILIES, 0), 0)}
    for app, vas in VA.items():
        for va in vas:
            for s in S:
                name = s + "-" + va
                v1 = va.startswith("v1")
                verify = [{"loop": loop, "moved": dict.fromkeys(TABLES, 0)} for loop in LOOPS] if v1 else None
                loops = {loop: {"end": "settled", "round": 2} for loop in LOOPS}
                arms = ("C", "DS") + (("D", "N", "DSN") if app == "campfire" else ()) + \
                       (("P1",) if app in TARGET_APPS and va == "v1-a1" else ())
                if app == "campfire" and name in K_SETTINGS:
                    arms += ("K", "KN", "KDS", "KDSN")
                for arm in arms:
                    spec = world(arm, app, s)
                    rows, _ = fake_rows(spec)
                    stratified = arm in ("DS", "DSN", "KDS", "KDSN")
                    obs = {"value_digests": digests_of(rows), "diagnostics": {"warning/x": 1},
                           "loops": dict(loops, **({k: {"end": "settled", "round": 1} for k in S1_LOOPS} if stratified else {})),
                           "verify": verify,
                           "law_violation_counts": {"producer_evidence_0": {"parameter_losses_by_kind": {}}} if va.endswith("a1") else None,
                           "reason_census": {"untyped_by_provenance": {"pending": 0, "gradual": 1, "unresolved": 2}},
                           "_reason_rows": {"site": {"type_hash": "h", "untyped_kinds": 2}}}
                    c6 = {"carry": stratified, "boundary_rows_lost":0,"boundary_rows_reinserted":0,"stratum2_answers_outside_set":0,"boundary_placeholders_retracted":2,"never_derived_size":4,"defer": ARM_FLAGS[arm].get("RH_DEFERRED_DEFER", "0"), "stratify": stratified,
                          "ndedup": "RH_DEFERRED_NDEDUP" in ARM_FLAGS[arm], "stratum1_pending_minted": 3 if arm in ("D", "DS", "DSN", "KDS", "KDSN") else 0,
                          "boundary_restored": 1 if stratified else 0, "stratum2_ran": stratified,
                          "stratum2_unresolved": 2 if stratified else 0, "rclosure_kept_pending": 1 if arm in ("KDS", "KDSN") else 0,
                          "settled_pending": 40 if arm == "D" else 0}
                    report = {"worklist": {"engine": {"cap_hits": 0, "frozen_units": 0, "budget_exhausted": 0}},
                              "fold": {"expansion": {"budget_cuts": 0}}, "c6": c6}
                    boundary = world(arm + "@boundary", app, s) if stratified else None
                    census = None
                    if arm in censuses:
                        counts, nc = censuses[arm]
                        events = [fam+":"+str(i) for fam, n in counts.items() for i in range(n)]
                        n_events = ["arm_loss:"+str(i) for i in range(2)]
                        if arm == "KN": events = [x for x in events if not x.startswith("arm_loss:")] + ["arm_loss:"+str(i) for i in range(2, 5)]
                        census = {"descents": dict(counts), "n_events": nc, "events": events,
                                  "n_signatures": n_events if arm in ("K", "KDS") else []}
                    store.put(arm, app, name, obs, spec, report, boundary, census)
                    if arm == "C":
                        pins["cells"][app + "/" + name] = {
                            "digests": dict(obs["value_digests"]), "loops": dict(loops), "verify_moved_total": 0 if v1 else None,
                            "pending": 0, "caps": {"cap_hits": 0, "frozen_units": 0, "budget_exhausted": 0},
                            "fold_budget_cuts": 0, "reason_delta": {"R": 0, "T": 0, "M": 0}}
                    if arm == "K":
                        kpins["cells"]["campfire/" + name] = {"digests": dict(obs["value_digests"]),
                                                              "descents": dict(k_census), "n_events": 2}
    return store, pins, kpins, targets


def write_native(directory, broken=None):
    """Receipts as Cargo writes them under --nocapture: each tagged object follows the libtest prefix."""
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)

    def line(test, tag, body):
        return "running 1 test\ntest analyze::" + test + " ... " + tag + " " + json.dumps(body) + "\nok\n"
    for f in ("000", "100", "010", "110", "001", "111"):
        stubs, xfer, cong = (int(x) for x in f)
        body = {"flags": {"stubs": stubs, "xfer": xfer, "congruent": cong},
                "strictness": dict.fromkeys(("p1", "p2", "p3", "p4", "p5", "p6", "p7b"), 0 if xfer else 1),
                "deferred_var": {"p7": 1}, "identity": {"p8": 0 if xfer else 1, "p9": 0 if (stubs or xfer) else 1},
                "equality": {"p10_distinguishes": bool(cong)}}
        (d / ("harness-" + f + ".log")).write_text(line("body::strict_producer_tests::provenance_strict_producer_strictness", "provenance-STRICT", body))
        (d / ("harness-" + f + ".exit")).write_text("0\n")
    for x in ("0", "1"):
        for test, tag in (("storage_extended_laws", "STORAGE-EXTENDED"), ("provenance_lineage_factorial", "PENDING-FACTORIAL")):
            body = {"counts": {}, "seed_ok": True, "no_early_never": True}
            (d / ("laws-x" + x + "-" + test + ".log")).write_text(line("tests::" + test, tag, body))
            (d / ("laws-x" + x + "-" + test + ".exit")).write_text("0\n")
    for defer in ("0", "stub", "all"):
        sites = {}
        for site in SITES:
            deferred = defer == "all" or (defer == "stub" and site == "register")
            today = TODAY.get(site, "U")
            sites[site] = {"s1": "P" if deferred else today, "stratum2": today}
        restore = {"after_first_harvest": dict.fromkeys(RESTORE, "U" if defer == "0" else "P"),
                   "after_boundary": dict.fromkeys(RESTORE, "U")}
        if broken == defer:
            sites["timeout"]["s1"] = "U" if defer == "all" else "P"
        if broken == "restore-" + defer:
            restore["after_first_harvest"]["seen_pending"] = "U"
        if broken == "param-" + defer:
            sites["param_seed"]["stratum2"] = "P"
        (d / ("sites-" + defer + ".log")).write_text(line("deferred_sites", "DEFERRED-SITES", {"sites": sites, "restore": restore}))
        (d / ("sites-" + defer + ".exit")).write_text("0\n")
    for flag in ("0", "1"):
        arms = 2 if flag == "1" else 4
        body = {"flat_arms": arms, "hash_value_arms": arms if broken != "ndedup" else 4, "idempotent": True}
        (d / ("ndedup-" + flag + ".log")).write_text(line("deferred_ndedup", "DEFERRED-NDEDUP", body))
        (d / ("ndedup-" + flag + ".exit")).write_text("0\n")

    for audit in ("0", "1"):
        body = {"flat_arms": 2, "hash_value_arms": 2, "idempotent": True, "mixed_provenance_preserved": True}
        (d / ("ndedup-1-a"+audit+".log")).write_text(line("deferred_ndedup", "DEFERRED-NDEDUP", body))
        (d / ("ndedup-1-a"+audit+".exit")).write_text("0\n")


def selftest():
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="deferred_unresolved-selftest-"))
    good = tmp / "native-good"
    write_native(good)
    for name, broken in (("native-param", "param-all"), ("native-restore", "restore-all"), ("native-ndedup", "ndedup")):
        write_native(tmp / name, broken)
    results = []
    # ObsStore turns a malformed report.json into missing evidence instead of an exception (check probe 9).
    bad = tmp / "malformed-cell"
    bad.mkdir()
    (bad / "report.json").write_text("{malformed\n")
    probe = object.__new__(ObsStore)
    probe.cell = lambda *_: ({}, str(bad), {})
    assert probe.report("DS", "forem", "unset-v1-a1") is None
    results.append(("check: ObsStore reads a malformed report.json as missing", "unavailable", []))

    def run(name, mutate, expect, native_dir=good, why=None, scope="all", family=None):
        store, pins, kpins, targets = fixture()
        mutate(store, pins, kpins)
        result = evaluate(store, pins, kpins, targets, native_dir, scope)
        verdict = result["verdict"] if family is None else result["family_verdicts"][family]
        gate = sorted({c["check"] for c in result["checks"] if c["check"].startswith("PG") and c["status"] != "pass"})
        unav = sorted({c["check"] for c in result["checks"] if c["mandatory"] and c["status"] == "unavailable"})
        fail = sorted({c["check"] for c in result["checks"] if c["mandatory"] and c["status"] == "fail"})
        deciding = gate or unav or fail
        label = name + ("" if family is None else " [" + family + "]") + ("" if scope == "all" else " (" + scope + ")")
        results.append((label, verdict, deciding))
        assert verdict.startswith(expect), (name, verdict, expect, deciding)
        assert why is None or deciding == sorted(why), (name, deciding, why)

    def noop(store, pins, kpins):
        pass

    def respec(store, arm, app, setting, update=None, boundary=None):
        """Replace rows of one cell and recompute its digests, as a real dump would carry them."""
        v = store.data[(arm, app, setting)]
        spec = {**v["rows"], **(update or {})}
        spec = {k: x for k, x in spec.items() if x is not None}
        rows, _ = fake_rows(spec)
        v["obs"] = dict(v["obs"], value_digests=digests_of(rows))
        v["rows"] = spec
        if boundary is not None:
            v["boundary"] = {k: x for k, x in {**v["boundary"], **boundary}.items() if x is not None}

    def every(store, arms, app, va, update, boundary=None, pins=None):
        for s in S:
            for arm in arms:
                respec(store, arm, app, s + "-" + va, update, boundary if arm in ("DS", "DSN") else None)
                if arm == "C" and pins is not None:
                    pins["cells"][app + "/" + s + "-" + va]["digests"] = store.data[(arm, app, s + "-" + va)]["obs"]["value_digests"]

    # The check's counterexamples (ck-deferred-unresolved/check_probes.py), as regression tests.
    def mixed_vector(store, pins, kpins):
        every(store, ("C",), "campfire", "v1-a1", {("params", "Mixed#m[0]"): {"ty": union(INT, U)},
                                                    ("params", "Mixed#m[1]"): {"ty": U}}, pins=pins)
        every(store, ("D",), "campfire", "v1-a1", {("params", "Mixed#m[0]"): {"ty": INT},
                                                    ("params", "Mixed#m[1]"): {"ty": {"kind": "var", "var": 0}}})
        every(store, ("DS", "DSN"), "campfire", "v1-a1", {("params", "Mixed#m[0]"): {"ty": INT},
                                                           ("params", "Mixed#m[1]"): {"ty": U}},
              boundary={("params", "Mixed#m[0]"): {"ty": INT}, ("params", "Mixed#m[1]"): {"ty": P}})
        every(store, ("N",), "campfire", "v1-a1", {("params", "Mixed#m[0]"): {"ty": union(INT, U)},
                                                    ("params", "Mixed#m[1]"): {"ty": U}})

    def concrete_row_lost(store, pins, kpins):
        every(store, ("DS", "D"), "campfire", "v1-a1", {("returns", "K#k"): None}, boundary={("returns", "K#k"): None})

    def native_entry_without_component(store, pins, kpins):
        for arm, value in (("C", 10), ("D", 11), ("DS", 11)):
            every(store, (arm,), "campfire", "v1-a1", {("fp:constants", "A::VALUE"): {"value": value}},
                  pins=pins if arm == "C" else None)

    def native_constant_changes(store, pins, kpins):
        every(store, ("C", "N", "DSN"), "campfire", "v1-a1", {("constants", "A::VALUE"): {"ty": INT}}, pins=pins)
        every(store, ("DS", "D"), "campfire", "v1-a1", {("constants", "A::VALUE"): {"ty": STR}},
              boundary={("constants", "A::VALUE"): {"ty": STR}})

    def gradual_arm_removed(store, pins, kpins):
        every(store, ("C", "N"), "campfire", "v1-a1", {("params", "Gr#g[0]"): {"ty": union(INT, G)}}, pins=pins)
        every(store, ("DS", "D", "DSN"), "campfire", "v1-a1", {("params", "Gr#g[0]"): {"ty": INT}},
              boundary={("params", "Gr#g[0]"): {"ty": INT}})

    def empty_verify(store, pins, kpins):
        store.data[("DS", "forem", "unset-v1-a1")]["obs"]["verify"] = []

    def absent_caps(store, pins, kpins):
        v = store.data[("DS", "forem", "unset-v1-a1")]
        v["report"] = dict(v["report"], worklist={"engine": {}})
        v["report"].pop("fold")

    def missing_and_failed(store, pins, kpins):
        v = store.data[("DS", "forem", "unset-v1-a1")]
        loops = {k: x for k, x in v["obs"]["loops"].items() if k != "stratum1_absorb"}
        loops["production"] = {"end": "ran_to_cap"}
        v["obs"] = dict(v["obs"], loops=loops)

    def malformed_reports(store, pins, kpins):
        store.raise_reports = True

    # deferral-protocol's own failure modes.
    def relabel_gradual(store, pins, kpins):
        every(store, ("DS",), "campfire", "v1-a1", {("params", "U#u[0]"): {"ty": G}})

    def stratum2_wrong_on_forem(store, pins, kpins):
        every(store, ("DS",), "forem", "v0-a0", {("params", "U#u[0]"): {"ty": STR}})

    def no_boundary(store, pins, kpins):
        store.data[("DS", "chatwoot", "2-v1-a1")]["boundary"] = None

    def structural_change(store, pins, kpins):
        every(store, ("DS", "D"), "campfire", "v0-a1", {("block_values", "K"): {"names": {"block_value_methods": ["j"]}}},
              boundary={("block_values", "K"): {"names": {"block_value_methods": ["j"]}}})

    def no_provenance(store, pins, kpins):
        every(store, ("C", "N"), "campfire", "v1-a0", {("params", "Q#q[0]"): {"ty": union(INT, {"kind": "untyped"})}},
              pins=pins)
        every(store, ("DS", "D", "DSN"), "campfire", "v1-a0", {("params", "Q#q[0]"): {"ty": INT}},
              boundary={("params", "Q#q[0]"): {"ty": INT}})

    def target_left(store, pins, kpins):
        respec(store, "DS", "forem", "1-v1-a1", {("params", "T#t[0]"): {"ty": union(INT, U)}})

    def new_target_value(store, pins, kpins):
        every(store, ("DS",), "forem", "v0-a0", {("params", "T#t[0]"): {"ty": STR}})

    def new_variance(store, pins, kpins):
        respec(store, "DS", "chatwoot", "2-v0-a0", {("returns", "X#x"): {"ty": INT}})

    def settlement_up(store, pins, kpins):
        v = store.data[("DS", "chatwoot", "repeat-v0-a0")]
        v["report"] = dict(v["report"], c6=dict(v["report"]["c6"], settled_pending=9))

    def reason_up(store, pins, kpins):
        store.data[("DS", "forem", "2-v0-a0")]["obs"]["_reason_rows"] = {"site": {"type_hash": "h", "untyped_kinds": 6}}

    def contributor_capped(store, pins, kpins):
        v = store.data[("DS", "forem", "unset-v1-a1")]
        v["obs"] = dict(v["obs"], loops=dict(v["obs"]["loops"], production={"end": "ran_to_cap"}))

    def s1_capped(store, pins, kpins):
        v = store.data[("DSN", "campfire", "2-v0-a0")]
        v["obs"] = dict(v["obs"], loops=dict(v["obs"]["loops"], stratum1_absorb={"end": "ran_to_cap"}))

    def contributor_not_run(store, pins, kpins):
        v = store.data[("DS", "campfire", "1-v0-a1")]
        v["report"] = dict(v["report"], c6=dict(v["report"]["c6"], stratum2_ran=False))

    def wrong_flags(store, pins, kpins):
        store.data[("DS", "forem", "1-v0-a0")]["flags"] = {**OFF, "RH_DEFERRED_DEFER": "all"}

    def never_fired(store, pins, kpins):
        v = store.data[("DS", "campfire", "2-v1-a0")]
        v["report"] = dict(v["report"], c6=dict(v["report"]["c6"], stratum1_pending_minted=0))

    def kds_premature(store, pins, kpins):
        store.data[("KDS", "campfire", "unset-v1-a1")]["census"]["descents"]["premature_unresolved"] = 1

    def kdsn_n_event(store, pins, kpins):
        v = store.data[("KDSN", "campfire", "repeat-v0-a0")]["census"]
        v["descents"]["arm_loss"], v["n_events"] = 2, 2

    def kn_extra(store, pins, kpins):
        store.data[("KN", "campfire", "1-v1-a1")]["census"]["descents"]["arm_loss"] = 5

    def kdsn_capped(store, pins, kpins):
        v = store.data[("KDSN", "campfire", "unset-v0-a0")]
        v["report"] = dict(v["report"], worklist={"engine": {"cap_hits": 1, "frozen_units": 1, "budget_exhausted": 0}})

    def kdsn_unreplayable(store, pins, kpins):
        store.data[("KDSN", "campfire", "2-v1-a1")]["census"] = None

    def k_baseline_moved(store, pins, kpins):
        store.data[("K", "campfire", "unset-v0-a0")]["census"]["descents"]["premature_unresolved"] = 13

    def n_changes_more(store, pins, kpins):
        every(store, ("N",), "campfire", "v0-a0", {("params", "M#m[0]"): {"ty": USER}})

    def pin_mismatch(store, pins, kpins):
        pins["cells"]["forem/unset-v1-a1"]["digests"]["returns"] = "other"

    def fold_pin(store, pins, kpins):
        pins["cells"]["chatwoot/2-v1-a1"]["fold_budget_cuts"] = 1

    def control_reasons(store, pins, kpins):
        pins["cells"]["chatwoot/2-v1-a1"]["reason_delta"] = {"R": 26, "T": 114, "M": 135}

    def targets_gone(store, pins, kpins):
        every(store, ("C",), "forem", "v0-a0", {("params", "T#t[0]"): {"ty": INT}}, pins=pins)

    def missing_ds_cell(store, pins, kpins):
        del store.data[("DS", "forem", "repeat-v0-a0")]

    def p1_missing(store, pins, kpins):
        del store.data[("P1", "forem", "2-v1-a1")]

    def campfire_only(store, pins, kpins):
        for k in [k for k in store.data if k[1] != "campfire"]:
            del store.data[k]

    run("all predictions hold", noop, "CONFIRMED", why=[])
    run("report-only P1 cell missing", p1_missing, "CONFIRMED", why=[])
    run("check: mixed restoration and removal in one entry", mixed_vector, "CONFIRMED", why=[])
    run("check: concrete Campfire row lost", concrete_row_lost, "KILLED", why=["H6h-campfire-direction"])
    run("check: native entry without component evidence", native_entry_without_component, "INCONCLUSIVE (pre-gate)",
        why=["PG2-row-dump-integrity", "PG5-campfire-closed"])
    run("check: native constant changes beyond Unresolved", native_constant_changes, "KILLED",
        why=["H6h-campfire-direction"])
    run("check: Gradual arm removed on Campfire", gradual_arm_removed, "KILLED", why=["H6h-campfire-direction"])
    run("check: empty V1 verification list", empty_verify, "INCONCLUSIVE (unavailable", why=["INV"])
    run("check: missing cap and fold counters", absent_caps, "INCONCLUSIVE (unavailable", why=["INV"])
    run("check: missing loop beside a failed loop", missing_and_failed, "INCONCLUSIVE (unavailable", why=["INV"])
    run("check: malformed report.json", malformed_reports, "INCONCLUSIVE (pre-gate)", why=["PG0-reducer"])
    run("Unresolved relabeled Gradual on Campfire", relabel_gradual, "KILLED",
        why=["H6c-restoration", "H6h-campfire-direction"])
    run("stratum 2 changes a C-stable Forem row", stratum2_wrong_on_forem, "KILLED", why=["H6c-restoration"])
    run("boundary dump missing", no_boundary, "INCONCLUSIVE (unavailable", why=["EV-complete-provenance", "H6c-restoration"])
    run("structural entry changes on Campfire", structural_change, "KILLED", why=["H6h-campfire-direction"])
    run("untyped leaf without provenance", no_provenance, "INCONCLUSIVE (unavailable", why=["EV-complete-provenance", "H6h-campfire-direction"])
    run("a target still varies", target_left, "KILLED", why=["H6a-targets"])
    run("a target closes to a new value", new_target_value, "KILLED", why=["H6a-targets", "H6c-restoration"])
    run("new variance", new_variance, "KILLED", why=["H6b-no-new-variance", "H6c-restoration"])
    run("settlement rewrites above C", settlement_up, "KILLED", why=["H6d-settlement-bound"])
    run("reason delta grows", reason_up, "KILLED", why=["H6e-reason-deltas"])
    run("stratum 2 runs to its cap", contributor_capped, "KILLED", why=["INV"])
    run("stratum 1 runs to its cap (DSN)", s1_capped, "KILLED", why=["INV"])
    run("stratum 2 did not run", contributor_not_run, "KILLED", why=["INV"])
    run("DS cell run with the wrong flags", wrong_flags, "INCONCLUSIVE (unavailable",
        why=["H6a-targets", "H6b-no-new-variance", "H6c-restoration", "INV"])
    run("deferral never fired", never_fired, "INCONCLUSIVE (unavailable", why=["INV"])
    run("KDS keeps a premature descent", kds_premature, "KILLED", why=["H6k-strictness-descents"])
    run("KDS keeps a premature descent", kds_premature, "KILLED", why=["H6k-strictness-descents"], family="A")
    run("KDS keeps a premature descent", kds_premature, "CONFIRMED", why=["H6k-strictness-descents"], family="N")
    run("KDSN keeps the normalizer events", kdsn_n_event, "KILLED", why=["H6k-combined-descents"])
    run("KN removes more than the normalizer events", kn_extra, "KILLED", why=["H6k-dedup-descents"], family="N")
    run("KDSN hits a worklist cap that K does not", kdsn_capped, "KILLED", why=["INV"])
    run("KDSN ledger not replayable", kdsn_unreplayable, "INCONCLUSIVE (unavailable", why=["H6k-combined-descents"])
    run("RETURN_HELPERS baseline not reproduced", k_baseline_moved, "INCONCLUSIVE (pre-gate)", why=["PG6-schedule-row-baseline"])
    run("N changes more than duplicate arms", n_changes_more, "KILLED", why=["H6n-dedup-only"])
    run("native site answers Pending in stratum 2", noop, "KILLED", native_dir=tmp / "native-param",
        why=["H6g-sites"])
    run("restore undoes the deferral", noop, "KILLED", native_dir=tmp / "native-restore", why=["H6g-sites"])
    run("dedup law fails on a Hash value", noop, "KILLED", native_dir=tmp / "native-ndedup", why=["H6g-ndedup"])
    run("no native receipts", noop, "INCONCLUSIVE (unavailable", native_dir=tmp / "absent",
        why=["H6g-strict-producer-protocol-harness", "H6g-strict-producer-protocol-laws", "H6g-ndedup", "H6g-ndedup-provenance", "H6g-sites"])
    run("pinned digest differs", pin_mismatch, "INCONCLUSIVE (pre-gate)", why=["PG1-pinned-digests"])
    run("pinned fold budget differs", fold_pin, "INCONCLUSIVE (pre-gate)", why=["PG3-pinned-invariants"])
    run("control reason delta differs from pin", control_reasons, "INCONCLUSIVE (pre-gate)", why=["PG3-pinned-invariants"])
    run("targets no longer vary in C", targets_gone, "INCONCLUSIVE (pre-gate)", why=["PG4-targets-vary"])
    run("missing DS cell", missing_ds_cell, "INCONCLUSIVE (unavailable",
        why=["EV-complete-provenance", "H6a-targets", "H6b-no-new-variance", "H6c-restoration", "H6d-settlement-bound", "H6e-reason-deltas", "INV"])
    run("Campfire scope without the other apps", campfire_only, "CONFIRMED", why=[], scope="campfire")
    run("full scope without the other apps", campfire_only, "INCONCLUSIVE (pre-gate)",
        why=["PG1-pinned-digests", "PG4-targets-vary"])
    # Totality and disjointness over random status assignments.
    rng = random.Random(6)
    for _ in range(2000):
        checks = [rec(rng.choice(["PG1", "H6a", "H6b", "INV", "R-x"]), "s", rng.choice(["pass", "fail", "unavailable"]),
                      None, rng.choice(["A", "N", "AN", None])) for _ in range(rng.randint(1, 8))]
        v = decide(checks)
        assert v in ("INCONCLUSIVE (pre-gate)", "INCONCLUSIVE (unavailable mandatory evidence)", "KILLED", "CONFIRMED")
        if v == "CONFIRMED":
            assert all(c["status"] == "pass" for c in checks if c["mandatory"])
        if any(c["status"] != "pass" for c in checks if c["check"].startswith("PG")):
            assert v == "INCONCLUSIVE (pre-gate)"
    for name, verdict, deciding in results:
        print("ok  %-58s %-46s %s" % (name, verdict, ", ".join(deciding) or "-"))
    print("ok  2000 random status assignments: exactly one verdict each; CONFIRMED only when every mandatory record passed")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="mode", required=True)
    r = sub.add_parser("run")
    r.add_argument("--condition", required=True, choices=(CONDITION,))
    r.add_argument("--cache-root", type=Path, required=True)
    r.add_argument("--native", type=Path, required=True)
    r.add_argument("--scope", choices=("campfire", "all"), default="all")
    r.add_argument("--stage", choices=("pregate", "verdict"), default="verdict")
    r.add_argument("--label", action="append", default=[], help="ARM=LABEL override")
    r.add_argument("--pins", type=Path, default=HERE / "pins/fixpoint-spine-control.json")
    r.add_argument("--kpins", type=Path, default=HERE / "pins/schedule-row-K.json")
    r.add_argument("--out", type=Path, required=True)
    sub.add_parser("selftest")
    args = p.parse_args(argv)
    if args.mode == "selftest":
        from regressions import selftest
        return selftest()
    labels = {arm: "boundary_carry-" + arm for arm in ARMS}
    labels.update(dict(x.split("=", 1) for x in args.label))
    targets = {app: json.loads((HERE / "targets" / (app + ".json")).read_text()) for app in TARGET_APPS}
    result = evaluate(ObsStore(args.cache_root, labels), json.loads(args.pins.read_text()),
                      json.loads(args.kpins.read_text()), targets, args.native, args.scope, args.stage)
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True, default=list) + "\n")
    if args.stage == "pregate":
        ok = result["verdict"] != "INCONCLUSIVE (pre-gate)"
        print("PRE-GATE PASS" if ok else "PRE-GATE NOT PASSED")
        return 0 if ok else 1
    print(result["verdict"], json.dumps(result.get("family_verdicts", {}), sort_keys=True))
    return 0 if result["verdict"] == "CONFIRMED" else 1


if __name__ == "__main__":
    sys.exit(main())
