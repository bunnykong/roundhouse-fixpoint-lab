#!/usr/bin/env python3
"""Tests for verdict.py on synthetic obs.py caches (no analyzer). Run: python3 -I -m unittest test_verdict -v
(from this directory) or python3 -I test_verdict.py."""
import contextlib
import copy
import io
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
import verdict as V  # noqa: E402

NIL, STR, INT, BOOL, UNT = ({"kind": k} for k in ("nil", "str", "int", "bool", "untyped"))


def union(*v):
    return {"kind": "union", "variants": list(v)}


def fn(ret):
    return {"kind": "fn", "params": [], "effects": {"effects": []}, "ret": ret,
            "block": {"kind": "class", "id": "ActionController::MimeResponds::Collector", "args": []}}


WIT = json.loads((KIT / "witnesses.json").read_text())["witnesses"]
KEYS = {w["id"]: w.get("keys", []) for w in WIT}
DEFAULTS = dict(V.OBSERVER_DEFAULTS)
PROFILES = {a: json.loads((KIT / "profiles" / f"{a}.json").read_text()) for a in ("C", "T", "CA", "TA")}


def h(x):
    return int(hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:12], 16)


def rows_for(arm, app):
    on, own = arm in ("T", "TA"), arm in ("CA", "TA")
    r = {}
    for key, (off_v, on_v) in V.REGISTRY.items():
        v = on_v if on else off_v
        r[("returns", key)] = fn(v) if key.endswith(".respond_to") else v
    if app == "forem":
        for k in KEYS["F-process"]:
            r[("returns", k)] = union(STR, INT) if on else NIL
        for k in KEYS["F-spliced"]:
            r[("returns", k)] = (union(STR, INT) if on else NIL) if own else UNT
    if app == "mastodon":
        for k in KEYS["M-errors"]:
            r[("returns", k)] = V.RESPOND_RET if on else NIL
        for k in KEYS["M-webfinger"]:
            r[("returns", k)] = BOOL if on else NIL
        for k in KEYS["M-suspension"]:
            module = "Concern#" in k
            r[("returns", k)] = UNT if (module or not own) else (V.RESPOND_RET if on else NIL)
        population = json.loads((KIT / "customization.json").read_text())
        for key in population["keys"]:
            r[("returns", key)] = population["precise"].get(key, UNT)
    r[("returns", "Shown#title")] = STR
    r[("params", "Shown#title[0]")] = INT
    r[("side_table", "slot 1")] = {"kind": "array", "elem": STR}
    r[("ir", "body-1:render")] = STR if on else NIL
    r[("ir", "body-1:other")] = union(STR, INT)
    return r


class World:
    """A synthetic obs cache in which every check passes; tests mutate it before building."""

    def __init__(self, stage="all", discourse=True):
        self.stage = stage
        apps = ["campfire"] if stage == "campfire" else ["campfire", "forem", "chatwoot", "mastodon"]
        self.cells = {}
        for app in apps:
            for s in (V.CAMPFIRE_SETTINGS if app == "campfire" else V.CORE_SETTINGS):
                for arm in ("C", "T"):
                    self.cells[(arm, app, s)] = rows_for(arm, app)
        if stage == "all":
            for app in ("forem", "mastodon"):
                for s in V.H5_SETTINGS:
                    for arm in ("CA", "TA"):
                        self.cells[(arm, app, s)] = rows_for(arm, app)
            if discourse:
                for arm in ("C", "T"):
                    self.cells[(arm, "discourse", "unset-v0-a0")] = rows_for(arm, "discourse")
        self.obs_override = {}
        self.flag_override = {}
        self.binary = {}
        self.ref_override = {}
        self.ref_binary = {}
        self.ref_flag_override = {}
        self.drop_ref = set()
        self.corrupt = {}
        self.header_override = {}
        self.hide_rows = {}
        self.emission = self.good_emission()
        inventory = {"analyze": ["if_branches_union_merge", "good"], "doc:roundhouse": []}
        run = dict(completed=True, complete=True, exit_code=101, inventory=inventory, observed=inventory)
        self.suite = {"off": dict(run, failed=[], passed=4000),
                      "on": dict(run, failed=["analyze::if_branches_union_merge"], passed=3999)}

    @staticmethod
    def good_emission():
        rows = []
        for inp in V.FIXTURES + ["use-app", "tail-app", "void-app", "probe-app", "campfire"]:
            for t in V.TARGETS:
                ex = [1, 0] if inp == "void-app" else [0, 0]
                same = inp != "void-app"
                row = dict(input=inp, target=t, exit=ex, identical_files=same or True, identical_stderr=same,
                           identical=same)
                if inp == "campfire" and t in V.CAMPFIRE_EXPECTED:
                    f = next(iter(V.CAMPFIRE_EXPECTED[t]))
                    row.update(identical_files=False, identical=False, changed_files=[f],
                               changed_lines={f: list(V.CAMPFIRE_LINES)})
                rows.append(row)
        for r in rows:
            if r["input"] == "probe-app":
                r["identical_stderr"], r["identical"] = False, False
        return {"arms": {"off": {}, "on": {"RH_RESPONSE_RETURNS": "1"}}, "binary_sha256": {"off": "B", "on": "B"}, "rows": rows}

    def observations(self, arm, app, s, rows):
        parts = {p: h(sorted((k[1], h(v)) for k, v in rows.items() if k[0] == p)) for p in V.PARTS}
        digests = {n: format(parts.get(n, h([arm in ("T", "TA"), n])) if n in V.PARTS else h(n), "016x")
                   for n in ("attributes", "block_values", "constants", "controller_bindings", "controller_cache",
                             "copies", "ir", "params", "returns", "side_table")}
        obs = {"value_digests": digests, "reason_census": {"untyped_anywhere": 10},
               "diagnostics": {"error/send_dispatch_failed": 5, "warning/gradual_untyped": 7},
               "loops": {"production": {"end": "settled", "round": 3}, "absorb": {"end": "settled", "round": 2}},
               "verify": [{"loop": loop, "moved": {k: (1 if k == "ir" and loop == "production" else 0)
                   for k in list(digests) + ([] if loop == "views_and_tests" else ["view_seeds"])}}
                   for loop in ("production", "views_and_tests", "absorb")] if "-v1-" in s else None, "exit_code": 1}
        obs.update(copy.deepcopy(self.obs_override.get((arm, app, s), {})))
        return obs

    def build(self, root):
        root = Path(root)
        labels = {}
        for (arm, app, s), rows in self.cells.items():
            d = root / "objects" / arm / app / s
            d.mkdir(parents=True, exist_ok=True)
            obs = self.observations(arm, app, s, rows)
            header = {"part": "fingerprint", "digests": obs["value_digests"],
                      "ir": sorted([1, i, i + 1, h(v), None] for i, (k, v) in enumerate(sorted(rows.items())) if k[0] == "ir"),
                      "parts": {p: {k[1]: h(v) for k, v in rows.items() if k[0] == p} for p in ("returns", "side_table")}}
            params = {}
            for k, v in rows.items():
                if k[0] == "params":
                    params.setdefault(k[1].rsplit("[", 1)[0], []).append((k[1], h(v)))
            header["parts"]["params"] = {k: h(sorted(v)) for k, v in params.items()}
            header["parts"]["controller_cache"] = {}
            header.update(self.header_override.get((arm, app, s), {}))
            lines = [json.dumps(header)]
            for i, (k, v) in enumerate(sorted(rows.items())):
                if k in self.hide_rows.get((arm, app, s), set()):
                    continue
                row = {"part": k[0], "key": k[1], "ty": v, "hash": h(v)}
                if k[0] == "ir":
                    row["span"] = {"file": 1, "start": i, "end": i + 1}
                lines.append(json.dumps(row))
            text = "\n".join(lines) + "\n"
            if (arm, app, s) in self.corrupt:
                text = self.corrupt[(arm, app, s)](text)
            (d / "contributor-values.jsonl").write_text(text)
            flags = dict(DEFAULTS, **PROFILES[arm])
            schedule, verify, audit = s.split("-")
            observer = dict(name=s, schedule=schedule, verification=verify == "v1", audit=audit == "a1")
            flags.update(RH_FIXPOINT_VERIFY=verify[1:], RH_PROVENANCE_AUDIT=audit[1:])
            if schedule in ("1", "2"):
                flags["RH_SHUFFLE"] = schedule
            flags.update(self.flag_override.get((arm, app, s), {}))
            flags = {k: v for k, v in flags.items() if v is not None}
            result = {"valid": True, "app": app, "setting": observer, "directory": str(d), "observations": obs,
                      "key": {"binary_sha256": self.binary.get((arm, app, s), "B"), "input_manifest_sha256": "M-" + app,
                              "rh_flags": flags, "schedule": s.split("-")[0]}}
            (d / "result.json").write_text(json.dumps(result))
            labels.setdefault(V.LABELS[arm], {})[f"{app}/{s}"] = {"result": str(d / "result.json"), "valid": True}
            if arm in V.REFS and (arm, app, s) not in self.drop_ref:
                rd = root / "objects" / ("ref-" + arm) / app / s
                rd.mkdir(parents=True, exist_ok=True)
                ref_flags = {k: v for k, v in flags.items() if k not in V.REF_IGNORED_FLAGS}
                ref_flags.update(self.ref_flag_override.get((arm, app, s), {}))
                ref = {"valid": True, "app": app, "setting": observer, "directory": str(rd), "observations": copy.deepcopy(obs),
                       "key": {"binary_sha256": self.ref_binary.get((arm, app, s), V.SPINE_SHA),
                               "input_manifest_sha256": "M-" + app, "rh_flags": ref_flags, "schedule": schedule}}
                for fld, val in self.ref_override.get((arm, app, s), {}).items():
                    ref["observations"][fld] = val
                (rd / "result.json").write_text(json.dumps(ref))
                labels.setdefault(V.REFS[arm], {})[f"{app}/{s}"] = {"result": str(rd / "result.json"), "valid": True}
        for name, cells in labels.items():
            (root / "labels" / name).mkdir(parents=True, exist_ok=True)
            (root / "labels" / name / "label.json").write_text(json.dumps({"cells": cells}))
        (root / "emission.json").write_text(json.dumps(self.emission))
        (root / "suite.json").write_text(json.dumps(self.suite))

    def verdict(self, emission=True, suite=True):
        with tempfile.TemporaryDirectory() as tmp:
            self.build(tmp)
            argv = ["--stage", self.stage, "--cache-root", tmp, "--out", tmp + "/out"]
            if emission:
                argv += ["--emission", tmp + "/emission.json"]
            if suite:
                argv += ["--suite", tmp + "/suite.json"]
            with contextlib.redirect_stdout(io.StringIO()):
                code = V.main(argv)
            out = json.loads(Path(tmp, "out", "verdict.json").read_text())
            return code, out


def primary(out):
    return out["primary"]["verdict"]


class Relations(unittest.TestCase):
    def test_nil_to_value_is_a_nil_drop(self):
        self.assertEqual(V.relation(NIL, STR), "NIL_DROPPED")
        self.assertEqual(V.relation({"kind": "array", "elem": NIL}, {"kind": "array", "elem": STR}), "NIL_DROPPED")

    def test_losing_a_non_nil_arm_narrows(self):
        self.assertEqual(V.relation(union(STR, INT), STR), "NARROW_NONNIL")

    def test_dropping_an_untyped_arm_narrows(self):
        self.assertEqual(V.relation(union(UNT, NIL), STR), "NARROW_NONNIL")

    def test_var_only_loss(self):
        self.assertEqual(V.relation({"kind": "var", "var": 3}, STR), "VAR_REC_ONLY")

    def test_union_order_is_equality(self):
        self.assertEqual(V.relation(union(STR, INT), union(INT, STR)), "EQ")
        self.assertEqual(V.relation(NIL, union(STR, NIL)), "WIDEN")

    def test_tuple_under_array(self):
        self.assertTrue(V.covers({"kind": "array", "elem": union(STR, INT)}, {"kind": "tuple", "elems": [STR, INT]}))
        self.assertFalse(V.covers({"kind": "tuple", "elems": [STR]}, {"kind": "array", "elem": STR}))

    def test_admits(self):
        self.assertTrue(V.admits(V.RESPOND_RET, "String") and V.admits(V.RESPOND_RET, "NilClass"))
        self.assertTrue(V.admits(fn(V.RESPOND_RET), "TrueClass"))
        self.assertFalse(V.admits(NIL, "String"))
        self.assertTrue(V.admits(UNT, "Account"))
        self.assertFalse(V.admits({"kind": "bottom"}, "NilClass"))


class Verdicts(unittest.TestCase):
    def test_good_world_confirms(self):
        code, out = World().verdict()
        self.assertEqual(primary(out), "CONFIRMED", json.dumps(out)[:3000])
        self.assertEqual(code, 0)
        self.assertEqual(out["h5"]["verdict"], "UNBLOCKED")
        self.assertEqual(out["discourse"]["verdict"], "CONFIRMED")

    def test_campfire_stage_requires_suite(self):
        code, out = World(stage="campfire").verdict(suite=False)
        self.assertEqual(primary(out), "INCONCLUSIVE")
        self.assertNotIn("h5", out)

    def test_missing_treatment_cell_is_inconclusive(self):
        w = World()
        del w.cells[("T", "forem", "repeat-v0-a0")]
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")

    def test_witness_exclusion_kills(self):
        w = World()
        w.cells[("T", "forem", "unset-v1-a1")][("returns", "ListingsController#process_successful_draft")] = NIL
        code, out = w.verdict()
        self.assertEqual(primary(out), "KILLED")
        self.assertEqual(code, 1)

    def test_missing_witness_key_is_not_a_pass(self):
        w = World()
        del w.cells[("T", "mastodon", "unset-v0-a0")][("returns", "ErrorResponses#gone")]
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")

    def test_uninformative_witnesses_are_inconclusive(self):
        w = World()
        for k, cell in w.cells.items():
            if k[0] == "C" and k[1] == "forem":
                for key in KEYS["F-process"]:
                    cell[("returns", key)] = UNT
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")

    def test_non_nil_loss_narrows(self):
        w = World()
        w.cells[("T", "chatwoot", "unset-v0-a0")][("ir", "body-1:other")] = STR
        code, out = w.verdict()
        self.assertEqual(primary(out), "NARROWED")
        self.assertEqual(code, 3)

    def test_nil_drops_and_var_only_losses_confirm(self):
        w = World()
        for k in [("C", "campfire", "unset-v0-a0"), ("T", "campfire", "unset-v0-a0")]:
            w.cells[k][("params", "Shown#title[1]")] = {"kind": "var", "var": 1} if k[0] == "C" else STR
            w.cells[k][("side_table", "slot 2")] = {"kind": "array", "elem": NIL} if k[0] == "C" else {"kind": "array", "elem": STR}
        self.assertEqual(primary(w.verdict()[1]), "CONFIRMED")

    def test_error_increase_kills(self):
        w = World()
        w.obs_override[("T", "mastodon", "repeat-v0-a0")] = {"diagnostics": {"error/send_dispatch_failed": 6, "warning/gradual_untyped": 7}}
        self.assertEqual(primary(w.verdict()[1]), "KILLED")

    def test_warning_change_alone_does_not_kill(self):
        w = World()
        w.obs_override[("T", "mastodon", "repeat-v0-a0")] = {"diagnostics": {"error/send_dispatch_failed": 5, "warning/gradual_untyped": 9}}
        self.assertEqual(primary(w.verdict()[1]), "CONFIRMED")

    def test_settled_loop_to_cap_kills(self):
        w = World()
        w.obs_override[("T", "campfire", "2-v0-a0")] = {"loops": {"production": {"end": "ran_to_cap"}, "absorb": {"end": "settled", "round": 2}}}
        self.assertEqual(primary(w.verdict()[1]), "KILLED")

    def test_verification_rise_kills_and_missing_is_unavailable(self):
        w = World()
        w.obs_override[("T", "forem", "unset-v1-a1")] = {"verify": [{"loop": "production", "moved": {"ir": 4}}]}
        self.assertEqual(primary(w.verdict()[1]), "KILLED")
        w = World()
        w.obs_override[("T", "forem", "unset-v1-a1")] = {"verify": None}
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")

    def test_truncated_dump_is_inconclusive(self):
        w = World()
        w.corrupt[("T", "chatwoot", "unset-v0-a0")] = lambda text: text.splitlines()[0] + "\n"
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")

    def test_malformed_dump_still_lets_a_valid_kill_win(self):
        w = World()
        w.corrupt[("T", "chatwoot", "unset-v0-a0")] = lambda text: text + "{not json\n"
        w.cells[("T", "forem", "unset-v1-a1")][("returns", "ListingsController#process_successful_draft")] = NIL
        self.assertEqual(primary(w.verdict()[1]), "KILLED")

    def test_header_digest_mismatch_is_inconclusive(self):
        w = World()
        w.header_override[("C", "campfire", "1-v0-a0")] = {"digests": {"returns": "x"}}
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")

    def test_flag_missing_in_treatment_is_pre(self):
        w = World()
        w.flag_override[("T", "campfire", "unset-v0-a0")] = {"RH_RESPONSE_RETURNS": None}
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE(PRE)")

    def test_extra_flag_difference_is_pre(self):
        w = World()
        w.flag_override[("T", "forem", "unset-v0-a0")] = {"RH_FOLD": "0"}
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE(PRE)")

    def test_two_binaries_is_pre(self):
        w = World()
        w.binary[("T", "mastodon", "unset-v0-a0")] = "OTHER"
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE(PRE)")

    def test_inertness_failure_is_pre_even_with_a_kill(self):
        w = World()
        w.ref_override[("C", "campfire", "unset-v0-a0")] = {"diagnostics": {"error/x": 1}}
        w.cells[("T", "forem", "unset-v1-a1")][("returns", "ListingsController#process_successful_draft")] = NIL
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE(PRE)")

    def test_missing_reference_is_inconclusive(self):
        w = World()
        w.drop_ref.add(("C", "forem", "repeat-v0-a0"))
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")

    def test_registry_not_switched_is_pre(self):
        w = World()
        w.cells[("T", "campfire", "unset-v0-a0")][("returns", "ActionController::Base.render")] = NIL
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE(PRE)")

    def test_registry_union_order_is_free(self):
        w = World()
        for k, cell in w.cells.items():
            if k[0] in ("T", "TA"):
                cell[("returns", "ActionController::Base.redirect_to")] = union(INT, STR)
        self.assertEqual(primary(w.verdict()[1]), "CONFIRMED")

    def test_emission(self):
        w = World()
        w.emission["rows"][0]["identical"] = False
        self.assertEqual(primary(w.verdict()[1]), "KILLED")
        w = World()
        w.emission["rows"].pop()
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")
        w = World()
        r = next(r for r in w.emission["rows"] if r["input"] == "void-app")
        r["exit"] = [1, 1]
        self.assertEqual(primary(w.verdict()[1]), "KILLED")
        w = World()
        r = next(r for r in w.emission["rows"] if r["input"] == "void-app")
        r["exit"] = [0, 0]
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")
        self.assertEqual(primary(World().verdict(emission=False)[1]), "INCONCLUSIVE")
        w = World()
        r = next(r for r in w.emission["rows"] if r["input"] == "campfire" and r["target"] == "ruby")
        r["changed_lines"] = {r["changed_files"][0]: ["-  def x: () -> nil", "+  def x: () -> String"]}
        self.assertEqual(primary(w.verdict()[1]), "KILLED")
        w = World()
        r = next(r for r in w.emission["rows"] if r["input"] == "campfire" and r["target"] == "spinel")
        r["changed_files"] = r["changed_files"] + ["app/other.rbs"]
        self.assertEqual(primary(w.verdict()[1]), "KILLED")

    def test_suite(self):
        w = World()
        w.suite["on"]["failed"].append("lib::other")
        self.assertEqual(primary(w.verdict()[1]), "KILLED")
        w = World()
        w.suite["on"]["failed"] = []
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")
        self.assertEqual(primary(World().verdict(suite=False)[1]), "INCONCLUSIVE")

    def test_h5_outcomes(self):
        w = World()
        for k, cell in w.cells.items():
            if k[0] == "CA":
                for key in KEYS["F-spliced"] + KEYS["M-suspension"] + KEYS["F-process"] + KEYS["M-errors"] + KEYS["M-webfinger"]:
                    if ("returns", key) in cell:
                        cell[("returns", key)] = UNT
        self.assertEqual(w.verdict()[1]["h5"]["verdict"], "INCONCLUSIVE")
        w = World()
        w.cells[("TA", "forem", "1-v0-a0")][("returns", "ListingsController#create_draft")] = NIL
        self.assertEqual(w.verdict()[1]["h5"]["verdict"], "NOT_UNBLOCKED")
        w = World()
        w.cells[("TA", "mastodon", "2-v0-a0")][("returns", "Api::V1::Admin::AccountsController#log_action")] = UNT
        self.assertEqual(w.verdict()[1]["h5"]["verdict"], "CHANGED")
        w = World()
        w.cells[("TA", "mastodon", "2-v0-a0")][("ir", "body-1:other")] = INT
        self.assertEqual(w.verdict()[1]["h5"]["verdict"], "NARROWED")

    def test_struct_rows_report_only(self):
        w = World()
        w.cells[("T", "campfire", "unset-v0-a0")][("ir", "body-2:new")] = STR
        self.assertEqual(primary(w.verdict()[1]), "CONFIRMED")

    def test_kill_beats_narrow(self):
        w = World()
        w.cells[("T", "chatwoot", "unset-v0-a0")][("ir", "body-1:other")] = STR
        w.obs_override[("T", "campfire", "1-v0-a0")] = {"diagnostics": {"error/send_dispatch_failed": 6, "warning/gradual_untyped": 7}}
        self.assertEqual(primary(w.verdict()[1]), "KILLED")

    def test_missing_label_is_inconclusive(self):
        w = World()
        for k in [k for k in w.cells if k[0] == "T"]:
            del w.cells[k]
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")

    def test_admitted_only_by_var_is_reported(self):
        w = World()
        w.cells[("T", "forem", "unset-v0-a0")][("returns", "ListingsController#process_successful_draft")] = {"kind": "var", "var": 9}
        out = w.verdict()[1]
        self.assertEqual(primary(out), "CONFIRMED")
        h1 = next(c for c in out["primary"]["checks"] if c["name"] == "H1 witnesses")
        self.assertTrue(any("pending placeholder" in d for d in h1["details"] if isinstance(d, str)))

    def test_dump_missing_a_changed_param_row_is_inconclusive(self):
        w = World()
        for arm in ("C", "T"):
            w.cells[(arm, "chatwoot", "unset-v0-a0")][("params", "Shown#title[1]")] = NIL if arm == "C" else STR
        w.hide_rows[("T", "chatwoot", "unset-v0-a0")] = {("params", "Shown#title[1]")}
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE")

    def test_changed_param_rows_with_coverage_confirm(self):
        w = World()
        for arm in ("C", "T"):
            w.cells[(arm, "chatwoot", "unset-v0-a0")][("params", "Shown#title[1]")] = NIL if arm == "C" else STR
        self.assertEqual(primary(w.verdict()[1]), "CONFIRMED")

    def test_h5b_needs_the_spliced_slots_themselves(self):
        w = World()
        for k, cell in w.cells.items():
            if k[0] == "CA":
                for key in KEYS["F-spliced"] + KEYS["M-suspension"]:
                    cell[("returns", key)] = UNT
        out = w.verdict()[1]
        self.assertEqual(out["h5"]["verdict"], "INCONCLUSIVE")
        h5b = next(c for c in out["h5"]["checks"] if c["name"] == "H5b defect reproduced")
        self.assertTrue(h5b["missing"])

    def test_v2_stabilization_must_be_off_in_every_arm(self):
        w = World()
        w.flag_override[("C", "campfire", "unset-v0-a0")] = {"RH_SKIP_RETURN_STABILIZE": "0"}
        w.flag_override[("T", "campfire", "unset-v0-a0")] = {"RH_SKIP_RETURN_STABILIZE": "0"}
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE(PRE)")

    def test_v2_reference_must_be_the_spine_with_the_arm_flags(self):
        w = World()
        w.ref_binary[("C", "forem", "unset-v0-a0")] = "8772885266ecc4039707c5fc964842336410661f5cbc74f85cee863b0cb020cd"
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE(PRE)")
        w = World()
        w.ref_flag_override[("C", "campfire", "1-v0-a0")] = {"RH_SKIP_RETURN_STABILIZE": "0"}
        self.assertEqual(primary(w.verdict()[1]), "INCONCLUSIVE(PRE)")
        w = World()
        w.ref_flag_override[("CA", "mastodon", "2-v0-a0")] = {"RH_CONTRIBUTOR_VALUES": "1"}
        self.assertEqual(primary(w.verdict()[1]), "CONFIRMED")

    def test_v2_keeps_h2_strict_for_the_v1_stub_shape(self):
        w = World()
        for arm in ("C", "T"):
            w.cells[(arm, "campfire", "1-v0-a0")][("returns", "SessionsController#create")] = (
                union(UNT, NIL) if arm == "C" else union(INT, STR))
        self.assertEqual(primary(w.verdict()[1]), "NARROWED")

    def test_discourse_is_separate(self):
        code, out = World(discourse=False).verdict()
        self.assertEqual(out["discourse"]["verdict"], "NOT RUN")
        self.assertEqual(primary(out), "CONFIRMED")
        w = World()
        w.obs_override[("T", "discourse", "unset-v0-a0")] = {"diagnostics": {"error/send_dispatch_failed": 9, "warning/gradual_untyped": 7}}
        out = w.verdict()[1]
        self.assertEqual(out["discourse"]["verdict"], "KILLED")
        self.assertEqual(primary(out), "CONFIRMED")


if __name__ == "__main__":
    unittest.main()
