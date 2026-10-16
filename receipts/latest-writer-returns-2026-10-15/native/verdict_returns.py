#!/usr/bin/env python3
"""Total, disjoint, evidence-complete verdict for return-protocol (research condition strict replacement).

Reads one evidence bundle per app (JSON; schema in return-protocol.md section 6) and prints a verdict:
INCONCLUSIVE (required evidence absent, malformed, disabled where required, or an incomplete partition),
KILLED (a must-hold failed on well-formed evidence), or CONFIRMED FOR THIS CONDITION.
Order: validate everything, compute the must-hold failures on the well-formed portion, then
gaps win over kills, kills over confirmation. Missing, null, malformed, disabled, zero and empty are
distinguished; nothing absent is ever read as zero. Exit: 0 confirmed, 1 killed, 2 inconclusive, 3 unreadable.
"""
import hashlib
import math
import json
import sys

CONDITION = "latest-writer-returns-20261015-campfire"
SETTINGS = ["unset-v1-a1", "1-v1-a1", "2-v1-a1", "repeat-v1-a1", "unset-v0-a0", "repeat-v0-a0"]
SCHEDULES = ["unset-v1-a1", "1-v1-a1", "2-v1-a1", "repeat-v1-a1"]
REPEAT_PAIRS = [("unset-v1-a1", "repeat-v1-a1"), ("unset-v0-a0", "repeat-v0-a0")]
DIGESTS = ["attributes", "block_values", "constants", "controller_bindings", "controller_cache", "copies", "ir",
           "params", "returns", "side_table"]
LOOPS = ["production", "views_and_tests", "absorb"]
CAPS = ["cap_hits", "cap_osc", "cap_drift", "budget_exhausted", "cuts", "budget_cuts"]
CELL_KEYS = {"valid", "exit", "timed_out", "digests", "loops", "caps", "verify", "audit", "reason_rows_digest",
             "reason_census", "reason_rows", "reason_census_reconciles", "errors_by_kind", "error_identities",
             "diagnostics_by_kind", "diagnostic_kinds", "alias_identity_digest", "performance"}
LEDGER_KEYS = {"available", "resolved", "aggregate_mismatches", "signature_exempt_slots", "route_removals",
               "orphan_destinations", "pending_only_destinations", "route_set_digest", "descents"}
FAMILIES = ["premature_unresolved", "placeholder_flip", "late_unresolved", "shape_refinement", "reference_switch",
            "arm_loss", "other"]
KILL_FAMILIES = ["premature_unresolved", "placeholder_flip"]
INTEGRITY = ["binary_sha256_match", "input_match", "checker_frozen_before_arms", "manifest_frozen_before_K",
             "contributor_observer_parity_with_spine"]
REQUIRED_LAWS = ["current_return_replace_same_writer_replaces", "current_return_replace_second_writer_survives",
                 "current_return_replace_permutations_agree", "current_return_replace_idempotent_associative_pending_identity",
                 "current_return_replace_var_normalizes_to_unresolved", "current_return_replace_host_lend_joins_includers",
                 "current_return_replace_no_route_removal", "current_return_replace_predeclared_slot_reads_pending",
                 "current_return_replace_copies_keep_identity_and_signatures"]
FIX521 = {"config": "Probe::Configuration", "load!": "Probe::Configuration"}
FIX964 = {"mode": "untyped", "c": "untyped", "d": "untyped", "e": "untyped"}
FIXTURE_ARMS = {"issue521": ["K", "K1", "C"], "issue964": ["K", "C"]}
FIXTURE_METHODS = {"issue521": list(FIX521), "issue964": list(FIX964)}


# ---------------------------------------------------------------- validation (gaps, typed view)
def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _is_num(v):
    return (_is_int(v) or isinstance(v, float)) and math.isfinite(v) and v >= 0


class Validator:
    """Checks presence and type of every required field; builds a view holding only well-formed values."""

    def __init__(self):
        self.gaps = []

    def gap(self, path, why):
        self.gaps.append("%s: %s" % (path, why))

    def req(self, d, key, path, kind, literals=None):
        """Return the value at d[key] if it has `kind`, else record a gap and return None."""
        if not isinstance(d, dict) or key not in d:
            self.gap(path, "missing")
            return None
        v = d[key]
        ok = {"bool": lambda x: isinstance(x, bool), "int": _is_int, "num": _is_num, "str": lambda x: isinstance(x, str),
              "list": lambda x: isinstance(x, list), "dict": lambda x: isinstance(x, dict)}[kind](v)
        if not ok:
            self.gap(path, "malformed (%s expected, %s found)" % (kind, "null" if v is None else type(v).__name__))
            return None
        if literals is not None and v not in literals:
            self.gap(path, "unexpected value %r" % (v,))
            return None
        return v

    def int_map(self, d, key, path, keys):
        m = self.req(d, key, path, "dict")
        if m is None:
            return None
        out = {}
        if set(m) != set(keys):
            self.gap(path, "out-of-schema count keys")
        for k in keys:
            v = self.req(m, k, path + "." + k, "int")
            if v is not None:
                out[k] = v
        return out if len(out) == len(keys) else None

    def str_list(self, d, key, path):
        v = self.req(d, key, path, "list")
        if v is None:
            return None
        if not all(isinstance(x, str) for x in v):
            self.gap(path, "malformed (list of strings expected)")
            return None
        return v


def validate(b):
    """Return (gaps, view). The view contains only values whose presence and type were verified."""
    V = Validator()
    view = {"cells": {"C": {}, "K": {}}, "ledger": {}, "fixtures": {}, "returns": None, "laws": {}}
    if not isinstance(b, dict):
        V.gap("bundle", "not a JSON object")
        return V.gaps, view
    cond = V.req(b, "condition", "condition", "str")
    if cond is not None and cond != CONDITION:
        V.gap("condition", "is %r, the card's condition is %r" % (cond, CONDITION))
    view["app"] = V.req(b, "app", "app", "str", {"campfire", "forem", "chatwoot", "mastodon"})
    view["campfire_first"] = V.req(b, "campfire_first_stage", "campfire_first_stage", "bool")
    if view["campfire_first"] != (view["app"] == "campfire"):
        V.gap("campfire_first_stage", "inconsistent with validated app identity")
    manifest = V.req(b, "target_manifest", "target_manifest", "dict")
    manifest_keys = None
    if manifest is not None:
        mc = V.req(manifest, "condition", "target_manifest.condition", "str", {CONDITION})
        ma = V.req(manifest, "app", "target_manifest.app", "str", {view["app"]})
        manifest_keys = V.str_list(manifest, "keys", "target_manifest.keys")
        mh = V.req(manifest, "sha256", "target_manifest.sha256", "str")
        payload = {"condition": mc, "app": ma, "keys": manifest_keys}
        expected = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if manifest_keys is not None and len(manifest_keys) != len(set(manifest_keys)):
            V.gap("target_manifest.keys", "duplicate identity")
        if mh != expected:
            V.gap("target_manifest.sha256", "manifest digest mismatch")
    integ = V.req(b, "integrity", "integrity", "dict")
    for key in INTEGRITY:
        v = V.req(integ, key, "integrity." + key, "bool") if integ is not None else None
        if v is False:
            V.gap("integrity." + key, "false")
    laws = V.req(b, "native_laws", "native_laws", "dict")
    for name in REQUIRED_LAWS:
        v = V.req(laws, name, "native_laws." + name, "str", {"passed", "failed", "missing", "not_selected"}) if laws is not None else None
        if v in ("missing", "not_selected"):
            V.gap("native_laws." + name, v)
        view["laws"][name] = v
    cells = V.req(b, "cells", "cells", "dict")
    for arm in ("C", "K"):
        arm_cells = V.req(cells, arm, "cells." + arm, "dict") if cells is not None else None
        for s in SETTINGS:
            path = "cells.%s.%s" % (arm, s)
            c = V.req(arm_cells, s, path, "dict") if arm_cells is not None else None
            if c is None:
                continue
            gap_start = len(V.gaps)
            cv = {}
            unknown = sorted(set(c) - CELL_KEYS)
            if unknown:
                V.gap(path, "out-of-schema keys %s" % unknown)
            if V.req(c, "valid", path + ".valid", "bool") is not True:
                V.gap(path + ".valid", "cell invalid")
            if V.req(c, "exit", path + ".exit", "int") not in (0, 1):
                V.gap(path + ".exit", "native exit not 0 or 1")
            if V.req(c, "timed_out", path + ".timed_out", "bool") is True:
                V.gap(path + ".timed_out", "timed out")
            dg = V.req(c, "digests", path + ".digests", "dict")
            if dg is not None:
                if set(dg) != set(DIGESTS) or not all(isinstance(dg[k], str) for k in DIGESTS):
                    V.gap(path + ".digests", "not the exact ten-table schema")
                else:
                    cv["digests"] = dg
            loops = V.req(c, "loops", path + ".loops", "dict")
            if loops is not None:
                lv = {}
                for name in LOOPS:
                    rec = V.req(loops, name, path + ".loops." + name, "dict")
                    if rec is not None:
                        end = V.req(rec, "end", path + ".loops.%s.end" % name, "str")
                        V.req(rec, "round", path + ".loops.%s.round" % name, "int")
                        if end is not None:
                            lv[name] = end
                if len(lv) == len(LOOPS):
                    cv["loops"] = lv
            caps = V.int_map(c, "caps", path + ".caps", CAPS)
            if caps is not None:
                cv["caps"] = caps
            v1 = s.endswith("v1-a1")
            ver = c.get("verify") if "verify" in c else None
            if "verify" not in c:
                V.gap(path + ".verify", "missing")
            elif ver == "disabled":
                if v1:
                    V.gap(path + ".verify", "disabled at a verification-on setting")
                else:
                    cv["verify"] = "disabled"
            elif not v1:
                V.gap(path + ".verify", "must be the explicit state 'disabled' at V0")
            elif not isinstance(ver, dict) or set(ver) != set(LOOPS) or not all(
                    isinstance(ver[l], dict) and all(_is_int(n) for n in ver[l].values()) for l in LOOPS):
                V.gap(path + ".verify", "malformed ({loop: {table: int}} for every loop expected)")
            elif not all(set(DIGESTS) <= set(ver[l]) <= set(DIGESTS) | {"view_seeds"} for l in LOOPS):
                V.gap(path + ".verify", "a loop lacks ten-table coverage or contains an unknown table; view_seeds alone is optional")
            else:
                cv["verify"] = ver
            aud = c.get("audit") if "audit" in c else None
            if "audit" not in c:
                V.gap(path + ".audit", "missing")
            elif aud == "disabled":
                if v1:
                    V.gap(path + ".audit", "disabled at an audit-on setting")
                else:
                    cv["audit"] = "disabled"
            elif not v1:
                V.gap(path + ".audit", "must be the explicit state 'disabled' at A0")
            elif not isinstance(aud, dict):
                V.gap(path + ".audit", "malformed")
            else:
                loss = V.req(aud, "origin_loss_current", path + ".audit.origin_loss_current", "int")
                cov = V.req(aud, "origin_coverage_complete", path + ".audit.origin_coverage_complete", "bool")
                V.req(aud, "permitted_var_to_u", path + ".audit.permitted_var_to_u", "int")
                if cov is False:
                    V.gap(path + ".audit.origin_coverage_complete", "writer coverage incomplete")
                if loss is not None and cov is True:
                    cv["audit"] = {"origin_loss_current": loss}
            rr = V.req(c, "reason_rows_digest", path + ".reason_rows_digest", "str")
            if rr is not None:
                cv["reason_rows_digest"] = rr
            rc = V.req(c, "reason_census", path + ".reason_census", "dict")
            if rc is not None:
                cstart = len(V.gaps)
                for name in ("typed", "missing", "bare_untyped", "untyped_anywhere"):
                    V.req(rc, name, path + ".reason_census." + name, "int")
                V.int_map(rc, "untyped_by_provenance", path + ".reason_census.untyped_by_provenance",
                          ("pending", "gradual", "unresolved"))
                if set(rc) != {"typed", "missing", "bare_untyped", "untyped_anywhere", "untyped_by_provenance"}:
                    V.gap(path + ".reason_census", "out-of-schema census")
                if len(V.gaps) == cstart:
                    cv["reason_census"] = rc
            if "reason_rows" in c:
                rows = V.req(c, "reason_rows", path + ".reason_rows", "dict")
                if rows is not None:
                    for identity, row in rows.items():
                        if not isinstance(row, dict):
                            V.gap(path + ".reason_rows." + identity, "malformed row")
                            continue
                        V.req(row, "untyped_kinds", path + ".reason_rows." + identity + ".untyped_kinds", "int")
                        V.req(row, "type_hash", path + ".reason_rows." + identity + ".type_hash", "str")
                    cv["reason_rows"] = rows
            if V.req(c, "reason_census_reconciles", path + ".reason_census_reconciles", "bool") is False:
                V.gap(path + ".reason_census_reconciles", "rows do not reconcile with the native census")
            ek = V.req(c, "errors_by_kind", path + ".errors_by_kind", "dict")
            if ek is not None:
                if all(isinstance(k, str) and _is_int(n) for k, n in ek.items()):
                    cv["errors_by_kind"] = ek
                else:
                    V.gap(path + ".errors_by_kind", "malformed")
            ids = V.req(c, "error_identities", path + ".error_identities", "list")
            if ids is not None:
                if all(isinstance(i, list) and len(i) == 4 and isinstance(i[0], str) and _is_int(i[1]) and _is_int(i[2])
                       and isinstance(i[3], str) for i in ids):
                    cv["error_identities"] = {tuple(i) for i in ids}
                else:
                    V.gap(path + ".error_identities", "malformed ([file, line, col, kind] expected)")
            dk = V.req(c, "diagnostics_by_kind", path + ".diagnostics_by_kind", "dict")
            dkeys = V.str_list(c, "diagnostic_kinds", path + ".diagnostic_kinds")
            if dk is not None:
                if not all(isinstance(k, str) and _is_int(n) for k, n in dk.items()):
                    V.gap(path + ".diagnostics_by_kind", "nonnegative integer counts required")
                elif dkeys is None or set(dk) != set(dkeys) or len(dkeys) != len(set(dkeys)):
                    V.gap(path + ".diagnostics_by_kind", "diagnostic inventory mismatch")
                else:
                    cv["diagnostics_by_kind"] = dk
            al = V.req(c, "alias_identity_digest", path + ".alias_identity_digest", "str")
            if al is not None:
                cv["alias_identity_digest"] = al
            perf = V.req(c, "performance", path + ".performance", "dict")
            if perf is not None:
                pv = {}
                for k in ("wall_s", "cpu_s", "peak_rss_bytes"):
                    v = V.req(perf, k, path + ".performance." + k, "num")
                    if v is not None:
                        pv[k] = v
                cv["performance"] = pv
            if len(V.gaps) == gap_start:
                view["cells"][arm][s] = cv
            else:
                view.setdefault("untrusted_cells", {})[arm + "/" + s] = {
                    "errors_by_kind": c.get("errors_by_kind"), "valid": c.get("valid"),
                    "timed_out": c.get("timed_out")}

    ledger = V.req(b, "ledger", "ledger", "dict")
    kl = V.req(ledger, "K", "ledger.K", "dict") if ledger is not None else None
    for s in SETTINGS:
        path = "ledger.K." + s
        led = V.req(kl, s, path, "dict") if kl is not None else None
        if led is None:
            continue
        lv = {}
        unknown = sorted(set(led) - LEDGER_KEYS)
        if unknown:
            V.gap(path, "out-of-schema keys %s" % unknown)
        if V.req(led, "available", path + ".available", "bool") is not True:
            V.gap(path + ".available", "ledger unavailable")
        if V.req(led, "resolved", path + ".resolved", "bool") is not True:
            V.gap(path + ".resolved", "descents not computed on resolved storage values")
        for k in ("aggregate_mismatches", "signature_exempt_slots", "route_removals", "orphan_destinations",
                  "pending_only_destinations"):
            v = V.req(led, k, path + "." + k, "int")
            if v is not None:
                lv[k] = v
        rd = V.req(led, "route_set_digest", path + ".route_set_digest", "str")
        if rd is not None:
            lv["route_set_digest"] = rd
        fam = V.int_map(led, "descents", path + ".descents", FAMILIES)
        if fam is not None:
            lv["descents"] = fam
        view["ledger"][s] = lv
    fx = V.req(b, "fixtures", "fixtures", "dict")
    for name, arms in FIXTURE_ARMS.items():
        f = V.req(fx, name, "fixtures." + name, "dict") if fx is not None else None
        for arm in arms:
            fa = V.req(f, arm, "fixtures.%s.%s" % (name, arm), "dict") if f is not None else None
            for s in SCHEDULES:
                path = "fixtures.%s.%s.%s" % (name, arm, s)
                cell = V.req(fa, s, path, "dict") if fa is not None else None
                if cell is None:
                    continue
                if V.req(cell, "valid", path + ".valid", "bool") is not True:
                    V.gap(path + ".valid", "emitter did not complete, or identity, schema or emission check failed")
                    continue
                rets = V.req(cell, "returns", path + ".returns", "dict")
                if rets is None:
                    continue
                rv = {}
                for m in FIXTURE_METHODS[name]:
                    t = V.req(rets, m, path + ".returns." + m, "str")
                    if t is not None:
                        rv[m] = t
                if len(rv) == len(FIXTURE_METHODS[name]):
                    view["fixtures"][(name, arm, s)] = rv
    rk = V.req(V.req(b, "returns", "returns", "dict") or {}, "K", "returns.K", "dict") if isinstance(b.get("returns"), dict) else V.req(b, "returns", "returns", "dict")
    if isinstance(rk, dict):
        rv = {}
        for k in ("stored_var_rows", "nested_var_rows", "new_varying_rows_vs_C"):
            v = V.req(rk, k, "returns.K." + k, "int")
            if v is not None:
                rv[k] = v
        lists = {}
        for k in ("functional_violations", "varying_rows", "machinery_rows", "upstream_rows", "unclassified_rows"):
            v = V.str_list(rk, k, "returns.K." + k)
            if v is not None:
                if len(v) != len(set(v)):
                    V.gap("returns.K." + k, "duplicate row identity")
                lists[k] = v
        rv.update(lists)
        if all(k in lists for k in ("varying_rows", "machinery_rows", "upstream_rows", "unclassified_rows")):
            var, mach, up, un = (set(lists[k]) for k in ("varying_rows", "machinery_rows", "upstream_rows", "unclassified_rows"))
            if mach & up or mach & un or up & un:
                V.gap("returns.K partition", "machinery and upstream overlap")
            if un:
                V.gap("returns.K partition", "%d varying rows unclassified" % len(un))
            if (mach | up | un) != var or len(lists["machinery_rows"]) + len(lists["upstream_rows"]) + len(lists["unclassified_rows"]) != len(lists["varying_rows"]):
                V.gap("returns.K partition", "varying_rows is not the disjoint union of machinery, upstream and unclassified")
        tg = V.req(rk, "targets", "returns.K.targets", "dict")
        if tg is not None:
            tv = {}
            for k in ("total", "present", "invariant"):
                v = V.req(tg, k, "returns.K.targets." + k, "int")
                if v is not None:
                    tv[k] = v
            for k in ("machinery", "upstream", "unclassified"):
                v = V.str_list(tg, k, "returns.K.targets." + k)
                if v is not None:
                    if len(v) != len(set(v)):
                        V.gap("returns.K.targets." + k, "duplicate target identity")
                    if manifest_keys is not None and not set(v) <= set(manifest_keys):
                        V.gap("returns.K.targets." + k, "identity absent from frozen manifest")
                    tv[k] = v
            if all(k in tv for k in ("total", "present", "invariant")):
                if not 0 <= tv["invariant"] <= tv["present"] <= tv["total"]:
                    V.gap("returns.K.targets", "require 0 <= invariant <= present <= total")
                if manifest_keys is None or tv["total"] != len(manifest_keys):
                    V.gap("returns.K.targets.total", "does not match frozen manifest")
            if all(k in tv for k in ("present", "invariant", "machinery", "upstream", "unclassified")):
                groups = [set(tv[k]) for k in ("machinery", "upstream", "unclassified")]
                if any(groups[i] & groups[j] for i in range(3) for j in range(i)):
                    V.gap("returns.K.targets partition", "categories overlap")
                if tv["unclassified"]:
                    V.gap("returns.K.targets partition", "%d varying targets unclassified" % len(tv["unclassified"]))
                if tv["present"] - tv["invariant"] != len(tv["machinery"]) + len(tv["upstream"]) + len(tv["unclassified"]):
                    V.gap("returns.K.targets partition", "present - invariant != machinery + upstream + unclassified")
            rv["targets"] = tv
        view["returns"] = rv
    return V.gaps, view


# ---------------------------------------------------------------- must-hold obligations (kills)
def kills_of(view):
    """Failed must-hold obligations, over the well-formed portion of the evidence only."""
    kills, notes = [], {}
    for name, state in view["laws"].items():
        if state == "failed":
            kills.append("native law %s failed" % name)
    cells = view["cells"]
    for arm in ("C", "K"):
        for s, c in cells[arm].items():
            for loop, end in (c.get("loops") or {}).items():
                if end != "settled":
                    kills.append("%s/%s: loop %s ended %r" % (arm, s, loop, end))
            ver = c.get("verify")
            if isinstance(ver, dict) and any(n != 0 for n in ver["absorb"].values()):
                kills.append("%s/%s: final absorb verification moved %s" % (arm, s, ver["absorb"]))
        for a, r in REPEAT_PAIRS:
            ca, cr = cells[arm].get(a, {}), cells[arm].get(r, {})
            for field in ("digests", "reason_rows_digest", "reason_census", "reason_rows", "alias_identity_digest"):
                if field in ca and field in cr and ca[field] != cr[field]:
                    kills.append("%s: %s differ between %s and %s" % (arm, field, a, r))
    for s in SETTINGS:
        c, k = cells["C"].get(s, {}), cells["K"].get(s, {})
        if "caps" in c and "caps" in k:
            for counter in CAPS:
                if k["caps"][counter] > c["caps"][counter]:
                    kills.append("K/%s: %s rose %d -> %d" % (s, counter, c["caps"][counter], k["caps"][counter]))
        if isinstance(c.get("verify"), dict) and isinstance(k.get("verify"), dict):
            for loop in ("production", "views_and_tests"):
                if set(k["verify"][loop]) != set(c["verify"][loop]):
                    kills.append("K/%s: verification table coverage in %s differs from C" % (s, loop))
                for table, n in k["verify"][loop].items():
                    if n > c["verify"][loop].get(table, 0):
                        kills.append("K/%s: verification movement in %s/%s rose %d -> %d" % (s, loop, table, c["verify"][loop].get(table, 0), n))
        if isinstance(k.get("audit"), dict) and k["audit"]["origin_loss_current"] != 0:
            kills.append("K/%s: %d current G/U or ambiguous-Var origin paths lost" % (s, k["audit"]["origin_loss_current"]))
        if "errors_by_kind" in c and "errors_by_kind" in k:
            for kind, n in k["errors_by_kind"].items():
                if n > c["errors_by_kind"].get(kind, 0):
                    kills.append("K/%s: error kind %s rose %d -> %d" % (s, kind, c["errors_by_kind"].get(kind, 0), n))
        if "error_identities" in c and "error_identities" in k and k["error_identities"] - c["error_identities"]:
            kills.append("K/%s: %d new error identities" % (s, len(k["error_identities"] - c["error_identities"])))
    alias = {s: cells["K"][s]["alias_identity_digest"] for s in SCHEDULES if "alias_identity_digest" in cells["K"].get(s, {})}
    if len(set(alias.values())) > 1:
        kills.append("K alias/ownership identities differ across schedules")
    rets = view["returns"] or {}
    if rets.get("stored_var_rows", 0) != 0:
        kills.append("K stores %d top-level legacy Var return rows (RS4 violated)" % rets["stored_var_rows"])
    if rets.get("functional_violations"):
        kills.append("%d inferred return rows violate stored = N(join of current member cells)" % len(rets["functional_violations"]))
    if rets.get("machinery_rows"):
        kills.append("%d varying return rows are machinery (every contributor's body rows identical)" % len(rets["machinery_rows"]))
    tg = rets.get("targets") or {}
    if "present" in tg and "total" in tg and tg["present"] != tg["total"]:
        kills.append("targets deleted: %d of %d present" % (tg["present"], tg["total"]))
    if tg.get("machinery"):
        kills.append("%d targets vary as machinery" % len(tg["machinery"]))
    routes = {}
    for s, led in view["ledger"].items():
        if led.get("aggregate_mismatches", 0) != 0:
            kills.append("K/%s: %d inferred slots whose stored value differs from the aggregate" % (s, led["aggregate_mismatches"]))
        if led.get("route_removals", 0) != 0 or led.get("orphan_destinations", 0) != 0:
            kills.append("K/%s: routes removed or orphan destinations (routes are declared facts)" % s)
        if "route_set_digest" in led:
            routes[s] = led["route_set_digest"]
        for fam in KILL_FAMILIES:
            n = (led.get("descents") or {}).get(fam)
            if n:
                msg = "K/%s: %d %s descents" % (s, n, fam)
                if view.get("app") == "campfire":
                    kills.append(msg + " on Campfire (RS1/RS4 promise)")
                else:
                    notes.setdefault("generalization_descents", []).append(msg)
    if len(set(routes.values())) > 1:
        kills.append("K route set differs across settings: %s" % routes)
    for name, expect in (("issue521", FIX521), ("issue964", FIX964)):
        for s in SCHEDULES:
            got = view["fixtures"].get((name, "K", s))
            if got is not None:
                bad = {m: got[m] for m in expect if got[m] != expect[m]}
                if bad:
                    kills.append("fixture %s K/%s: %s" % (name, s, bad))
    return kills, notes


def report_of(view, kills, notes):
    cells = view["cells"]
    rets = view["returns"] or {}
    rep = {"app": view.get("app"),
           "varying_return_rows": len(rets.get("varying_rows") or []),
           "upstream_return_rows": len(rets.get("upstream_rows") or []),
           "new_varying_rows_vs_C": rets.get("new_varying_rows_vs_C"),
           "nested_var_rows": rets.get("nested_var_rows"),
           "targets": {k: (rets.get("targets") or {}).get(k) for k in ("total", "present", "invariant")},
           "pending_only_destinations": {s: view["ledger"].get(s, {}).get("pending_only_destinations") for s in SETTINGS},
           "signature_exempt_slots": {s: view["ledger"].get(s, {}).get("signature_exempt_slots") for s in SETTINGS},
           "descents": {s: view["ledger"].get(s, {}).get("descents") for s in SETTINGS},
           "fixture_ablation_K1": {s: view["fixtures"].get(("issue521", "K1", s)) for s in SCHEDULES},
           "fixture_control_C": {n: {s: view["fixtures"].get((n, "C", s)) for s in SCHEDULES} for n in FIXTURE_ARMS},
           "diagnostics_by_kind": {s: {a: cells[a].get(s, {}).get("diagnostics_by_kind") for a in ("C", "K")} for s in SETTINGS},
           "performance": {s: {a: cells[a].get(s, {}).get("performance") for a in ("C", "K")} for s in SETTINGS},
           "control_origin_losses_report_only": {s: c.get("audit") for s, c in cells["C"].items()},
           "untrusted_observations": view.get("untrusted_cells", {}),
           "observed_counterexamples_despite_gap": list(kills)}
    rep.update(notes)
    return rep


def verdict(b):
    """Return (status, reasons, report): gaps, then kills, then confirmation; exactly one outcome."""
    gaps, view = validate(b)
    kills, notes = kills_of(view)
    rep = report_of(view, kills, notes)
    if gaps:
        return "INCONCLUSIVE", gaps, rep
    rep["observed_counterexamples_despite_gap"] = []
    if kills:
        return "KILLED", kills, rep
    return "CONFIRMED FOR THIS CONDITION", [], rep


def main(argv):
    if len(argv) != 2:
        print("usage: verdict_returns.py BUNDLE.json", file=sys.stderr)
        return 3
    try:
        with open(argv[1]) as f:
            bundle = json.load(f)
    except (OSError, ValueError) as e:
        print("unreadable bundle: %s" % e, file=sys.stderr)
        return 3
    status, reasons, report = verdict(bundle)
    print(json.dumps({"status": status, "reasons": reasons, "report": report}, indent=1, sort_keys=True, default=str))
    return {"CONFIRMED FOR THIS CONDITION": 0, "KILLED": 1, "INCONCLUSIVE": 2}[status]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
