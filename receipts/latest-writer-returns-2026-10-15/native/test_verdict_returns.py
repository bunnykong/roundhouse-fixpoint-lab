#!/usr/bin/env python3
"""Tests for verdict_returns.py (v2). Missing or malformed evidence is never a pass; every bundle lands in exactly
one class without raising; the checker's seven probes (ck-latest-writer-returns/probe_verdict.py) are frozen here."""
import copy
import hashlib
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verdict_returns as V  # noqa: E402


def cell(setting, arm="C"):
    v1 = setting.endswith("v1-a1")
    return {"valid": True, "exit": 0, "timed_out": False,
            "digests": {k: "d-" + k for k in V.DIGESTS},
            "loops": {l: {"end": "settled", "round": 2} for l in V.LOOPS},
            "caps": {k: 0 for k in V.CAPS},
            "verify": {"production": dict({k: 0 for k in V.DIGESTS}, ir=1), "views_and_tests": {k: 0 for k in V.DIGESTS},
                       "absorb": {k: 0 for k in V.DIGESTS}} if v1 else "disabled",
            "audit": {"origin_loss_current": 0, "origin_coverage_complete": True, "permitted_var_to_u": 3} if v1 else "disabled",
            "reason_rows_digest": "rr-" + arm, "reason_census": {"typed": 20, "missing": 0, "bare_untyped": 3, "untyped_anywhere": 7, "untyped_by_provenance": {"pending": 0, "gradual": 3, "unresolved": 4}},
            "reason_census_reconciles": True,
            "errors_by_kind": {}, "error_identities": [], "diagnostics_by_kind": {"warning/unresolved_type": 10}, "diagnostic_kinds": ["warning/unresolved_type"],
            "alias_identity_digest": "alias-" + arm,
            "performance": {"wall_s": 3.9, "cpu_s": 3.5, "peak_rss_bytes": 250000000}}


def ledger():
    return {"available": True, "resolved": True, "aggregate_mismatches": 0, "signature_exempt_slots": 12,
            "route_removals": 0, "orphan_destinations": 0, "pending_only_destinations": 2, "route_set_digest": "r0",
            "descents": {f: 0 for f in V.FAMILIES}}


def fixture(returns):
    return {"valid": True, "returns": dict(returns)}


def good(app="campfire"):
    manifest = {"condition": V.CONDITION, "app": app, "keys": ["t%d" % i for i in range(1, 11)]}
    manifest["sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"target_manifest": manifest, "condition": V.CONDITION, "app": app, "campfire_first_stage": app == "campfire",
            "integrity": {k: True for k in V.INTEGRITY},
            "native_laws": {n: "passed" for n in V.REQUIRED_LAWS},
            "cells": {a: {s: cell(s, a) for s in V.SETTINGS} for a in ("C", "K")},
            "ledger": {"K": {s: ledger() for s in V.SETTINGS}},
            "fixtures": {"issue521": {"K": {s: fixture(V.FIX521) for s in V.SCHEDULES},
                                      "K1": {s: fixture({"config": "untyped", "load!": "Probe::Configuration"}) for s in V.SCHEDULES},
                                      "C": {s: fixture({"config": "untyped", "load!": "Probe::Configuration" if s == "2-v1-a1" else "untyped"}) for s in V.SCHEDULES}},
                         "issue964": {"K": {s: fixture(V.FIX964) for s in V.SCHEDULES},
                                      "C": {s: fixture(V.FIX964) for s in V.SCHEDULES}}},
            "returns": {"K": {"stored_var_rows": 0, "nested_var_rows": 4, "functional_violations": [],
                              "varying_rows": ["X#a"], "machinery_rows": [], "upstream_rows": ["X#a"], "unclassified_rows": [],
                              "new_varying_rows_vs_C": 1,
                              "targets": {"total": 10, "present": 10, "invariant": 9, "machinery": [], "upstream": ["t1"], "unclassified": []}}}}


def status(b):
    return V.verdict(b)[0]


class CheckerProbes(unittest.TestCase):
    """The seven counterexamples of the card check, frozen as regressions."""

    def test_all_cell_measurements_and_ledger_counts_missing_is_inconclusive(self):
        b = good()
        for arm in ("C", "K"):
            b["cells"][arm] = {s: {"valid": True} for s in V.SETTINGS}
        b["ledger"]["K"] = {s: {"available": True} for s in V.SETTINGS}
        b["native_laws"] = {V.REQUIRED_LAWS[0]: "passed"}
        s, r, _ = V.verdict(b)
        self.assertEqual(s, "INCONCLUSIVE"); self.assertTrue(any("digests" in x for x in r)); self.assertTrue(any("native_laws" in x for x in r))

    def test_varying_return_in_neither_partition_is_inconclusive(self):
        b = good(); b["returns"]["K"].update(varying_rows=["unclassified#return"], upstream_rows=[], machinery_rows=[])
        s, r, _ = V.verdict(b); self.assertEqual(s, "INCONCLUSIVE"); self.assertTrue(any("partition" in x for x in r))

    def test_exact_reason_repeat_change_kills(self):
        b = good()
        for arm in ("C", "K"):
            for s, c in b["cells"][arm].items():
                c["reason_rows_digest"] = "repeat" if s.startswith("repeat") else "first"
        s, r, _ = V.verdict(b); self.assertEqual(s, "KILLED"); self.assertTrue(any("reason_rows_digest" in x for x in r))

    def test_probe_drift_reasons_in_its_original_field_names_kills(self):
        b = good()
        for arm in ("C", "K"):
            for s, c in b["cells"][arm].items():
                repeat = s.startswith("repeat")
                c["reason_census"] = {"typed": 20, "missing": 0, "bare_untyped": 1, "untyped_anywhere": 1, "untyped_by_provenance": {"pending": 0, "gradual": int(repeat), "unresolved": int(not repeat)}}
                c["reason_rows"] = {"method": {"untyped_kinds": 2 if repeat else 4, "type_hash": "same-value"}}
        s, r, _ = V.verdict(b); self.assertEqual(s, "KILLED"); self.assertTrue(any("reason_census" in x for x in r))

    def test_probe_malformed_movement_in_its_original_field_name_is_out_of_schema(self):
        b = good(); b["cells"]["K"]["unset-v1-a1"]["production_verify_moved"] = [1]
        s, r, _ = V.verdict(b); self.assertEqual(s, "INCONCLUSIVE"); self.assertTrue(any("out-of-schema" in x for x in r))

    def test_unknown_condition_is_inconclusive(self):
        b = good(); b["condition"] = "wrong-condition"
        self.assertEqual(status(b), "INCONCLUSIVE")

    def test_null_stored_var_count_is_inconclusive(self):
        b = good(); b["returns"]["K"]["stored_var_rows"] = None
        self.assertEqual(status(b), "INCONCLUSIVE")

    def test_malformed_movement_type_is_inconclusive_without_raising(self):
        b = good(); b["cells"]["K"]["unset-v1-a1"]["verify"] = [1]
        self.assertEqual(status(b), "INCONCLUSIVE")

    def test_malformed_functional_violations_type_is_inconclusive_without_raising(self):
        b = good(); b["returns"]["K"]["functional_violations"] = 1
        self.assertEqual(status(b), "INCONCLUSIVE")


class Gaps(unittest.TestCase):
    def test_good_bundle_confirms(self):
        s, r, rep = V.verdict(good()); self.assertEqual(s, "CONFIRMED FOR THIS CONDITION", r)
        self.assertEqual(rep["signature_exempt_slots"]["unset-v1-a1"], 12)

    def test_single_selected_law_does_not_stand_for_the_family(self):
        b = good(); b["native_laws"] = {n: ("passed" if i == 0 else "not_selected") for i, n in enumerate(V.REQUIRED_LAWS)}
        self.assertEqual(status(b), "INCONCLUSIVE")

    def test_failed_law_kills(self):
        b = good(); b["native_laws"][V.REQUIRED_LAWS[4]] = "failed"
        self.assertEqual(status(b), "KILLED")

    def test_verification_disabled_at_v1_is_a_gap_and_a_dict_at_v0_is_a_gap(self):
        b = good(); b["cells"]["K"]["1-v1-a1"]["verify"] = "disabled"; self.assertEqual(status(b), "INCONCLUSIVE")
        b = good(); b["cells"]["K"]["unset-v0-a0"]["verify"] = {l: {} for l in V.LOOPS}; self.assertEqual(status(b), "INCONCLUSIVE")

    def test_audit_coverage_incomplete_is_a_gap_and_loss_kills(self):
        b = good(); b["cells"]["K"]["2-v1-a1"]["audit"]["origin_coverage_complete"] = False; self.assertEqual(status(b), "INCONCLUSIVE")
        b = good(); b["cells"]["K"]["2-v1-a1"]["audit"]["origin_loss_current"] = 1; self.assertEqual(status(b), "KILLED")

    def test_census_not_reconciling_is_a_gap(self):
        b = good(); b["cells"]["C"]["repeat-v0-a0"]["reason_census_reconciles"] = False
        self.assertEqual(status(b), "INCONCLUSIVE")

    def test_ledger_required_at_v0_settings_too(self):
        b = good(); del b["ledger"]["K"]["repeat-v0-a0"]; self.assertEqual(status(b), "INCONCLUSIVE")
        b = good(); b["ledger"]["K"]["unset-v0-a0"]["resolved"] = False; self.assertEqual(status(b), "INCONCLUSIVE")

    def test_missing_report_evidence_is_a_gap_not_a_kill(self):
        b = good(); del b["fixtures"]["issue521"]["K1"]; self.assertEqual(status(b), "INCONCLUSIVE")
        b = good(); b["fixtures"]["issue964"]["C"]["1-v1-a1"]["valid"] = False; self.assertEqual(status(b), "INCONCLUSIVE")
        b = good(); del b["cells"]["K"]["2-v1-a1"]["performance"]; self.assertEqual(status(b), "INCONCLUSIVE")

    def test_invalid_fixture_emission_is_a_gap_even_if_types_look_right(self):
        b = good(); b["fixtures"]["issue521"]["K"]["2-v1-a1"]["valid"] = False
        self.assertEqual(status(b), "INCONCLUSIVE")

    def test_pending_only_destinations_required_even_when_zero_and_never_unavailable(self):
        b = good(); del b["ledger"]["K"]["1-v1-a1"]["pending_only_destinations"]; self.assertEqual(status(b), "INCONCLUSIVE")
        b = good(); b["ledger"]["K"]["1-v1-a1"]["pending_only_destinations"] = 49
        s, _, rep = V.verdict(b); self.assertEqual(s, "CONFIRMED FOR THIS CONDITION"); self.assertEqual(rep["pending_only_destinations"]["1-v1-a1"], 49)

    def test_targets_partition_must_reconcile(self):
        b = good(); b["returns"]["K"]["targets"]["invariant"] = 8
        self.assertEqual(status(b), "INCONCLUSIVE")

    def test_gap_plus_kill_is_inconclusive_with_the_kill_reported(self):
        b = good(); b["returns"]["K"]["machinery_rows"] = ["Z#c"]; b["integrity"]["input_match"] = False
        s, _, rep = V.verdict(b); self.assertEqual(s, "INCONCLUSIVE"); self.assertTrue(rep["observed_counterexamples_despite_gap"])

    def test_every_single_key_deletion_or_null_lands_in_one_class_without_raising(self):
        def paths(o, prefix=()):
            if isinstance(o, dict):
                for k, v in o.items():
                    yield prefix + (k,)
                    yield from paths(v, prefix + (k,))
        base = good()
        for p in list(paths(base)):
            for mode in ("delete", "null", "list"):
                b = copy.deepcopy(base); d = b
                for k in p[:-1]:
                    d = d[k]
                if mode == "delete":
                    del d[p[-1]]
                else:
                    d[p[-1]] = None if mode == "null" else [1]
                s = status(b)
                self.assertIn(s, ("INCONCLUSIVE", "KILLED", "CONFIRMED FOR THIS CONDITION"), p)
                self.assertNotEqual(s, "CONFIRMED FOR THIS CONDITION", (p, mode))

    def test_verification_coverage_must_include_the_ten_tables_and_match_across_arms(self):
        b = good(); del b["cells"]["C"]["unset-v1-a1"]["verify"]["production"]["returns"]; self.assertEqual(status(b), "INCONCLUSIVE")
        b = good(); b["cells"]["K"]["unset-v1-a1"]["verify"]["production"]["view_seeds"] = 0; self.assertEqual(status(b), "KILLED")

    def test_out_of_schema_ledger_key_is_a_gap(self):
        b = good(); b["ledger"]["K"]["1-v1-a1"]["stabilize_events"] = 3; self.assertEqual(status(b), "INCONCLUSIVE")

    def test_non_object_bundle_is_inconclusive(self):
        self.assertEqual(status(None), "INCONCLUSIVE"); self.assertEqual(status([]), "INCONCLUSIVE"); self.assertEqual(status({}), "INCONCLUSIVE")


class Kills(unittest.TestCase):
    def test_stored_var_kills_but_nested_var_is_reported(self):
        b = good(); b["returns"]["K"]["stored_var_rows"] = 1; self.assertEqual(status(b), "KILLED")
        b = good(); b["returns"]["K"]["nested_var_rows"] = 900
        s, _, rep = V.verdict(b); self.assertEqual(s, "CONFIRMED FOR THIS CONDITION"); self.assertEqual(rep["nested_var_rows"], 900)

    def test_signature_exempt_slots_do_not_kill_but_aggregate_mismatch_does(self):
        b = good(); b["ledger"]["K"]["unset-v1-a1"]["signature_exempt_slots"] = 300; self.assertEqual(status(b), "CONFIRMED FOR THIS CONDITION")
        b = good(); b["ledger"]["K"]["unset-v0-a0"]["aggregate_mismatches"] = 1; self.assertEqual(status(b), "KILLED")

    def test_machinery_row_and_machinery_target_kill(self):
        b = good(); b["returns"]["K"].update(varying_rows=["X#a", "Z#c"], machinery_rows=["Z#c"]); self.assertEqual(status(b), "KILLED")
        b = good(); b["returns"]["K"]["targets"].update(invariant=8, machinery=["t2"]); self.assertEqual(status(b), "KILLED")

    def test_upstream_new_variance_does_not_kill(self):
        b = good(); b["returns"]["K"].update(varying_rows=["X#a", "Y#b"], upstream_rows=["X#a", "Y#b"], new_varying_rows_vs_C=2)
        self.assertEqual(status(b), "CONFIRMED FOR THIS CONDITION")

    def test_deleted_target_kills(self):
        b = good(); b["returns"]["K"]["targets"].update(present=9, invariant=8); self.assertEqual(status(b), "KILLED")

    def test_fixture_gates(self):
        b = good(); b["fixtures"]["issue521"]["K"]["2-v1-a1"]["returns"]["config"] = "untyped"; self.assertEqual(status(b), "KILLED")
        b = good(); b["fixtures"]["issue964"]["K"]["unset-v1-a1"]["returns"]["d"] = "Symbol"; self.assertEqual(status(b), "KILLED")
        b = good(); b["fixtures"]["issue521"]["K1"]["unset-v1-a1"]["returns"]["config"] = "Probe::Configuration"
        self.assertEqual(status(b), "CONFIRMED FOR THIS CONDITION")

    def test_errors_and_identities(self):
        b = good(); b["cells"]["K"]["unset-v1-a1"]["errors_by_kind"] = {"error/send_dispatch_failed": 3}
        b["cells"]["K"]["unset-v1-a1"]["error_identities"] = [["a.rb", 8, 15, "send_dispatch_failed"]]
        self.assertEqual(status(b), "KILLED")
        b = good(); b["cells"]["K"]["unset-v1-a1"]["diagnostics_by_kind"] = {"warning/unresolved_type": 19}
        self.assertEqual(status(b), "CONFIRMED FOR THIS CONDITION")

    def test_repeat_mismatches_kill_for_digests_reasons_and_aliases(self):
        for field, val in (("digests", {k: "x" for k in V.DIGESTS}), ("reason_rows_digest", "z"), ("alias_identity_digest", "z")):
            b = good(); b["cells"]["C"]["repeat-v0-a0"][field] = val
            self.assertEqual(status(b), "KILLED", field)

    def test_alias_identities_must_agree_across_k_schedules(self):
        b = good(); b["cells"]["K"]["2-v1-a1"]["alias_identity_digest"] = "other"; self.assertEqual(status(b), "KILLED")

    def test_verification_per_loop_and_table_and_final_absorb(self):
        b = good(); b["cells"]["K"]["1-v1-a1"]["verify"]["production"]["ir"] = 2; self.assertEqual(status(b), "KILLED")
        b = good(); b["cells"]["K"]["1-v1-a1"]["verify"]["views_and_tests"]["ir"] = 1; self.assertEqual(status(b), "KILLED")
        b = good(); b["cells"]["K"]["1-v1-a1"]["verify"]["production"]["ir"] = 0; self.assertEqual(status(b), "CONFIRMED FOR THIS CONDITION")
        b = good(); b["cells"]["C"]["repeat-v1-a1"]["verify"]["absorb"]["ir"] = 1; self.assertEqual(status(b), "KILLED")

    def test_each_cap_counter_individually(self):
        for counter in V.CAPS:
            b = good(); b["cells"]["K"]["unset-v0-a0"]["caps"][counter] = 1
            self.assertEqual(status(b), "KILLED", counter)

    def test_loop_not_settled_kills(self):
        b = good(); b["cells"]["K"]["unset-v1-a1"]["loops"]["absorb"]["end"] = "cap"; self.assertEqual(status(b), "KILLED")

    def test_routes(self):
        b = good(); b["ledger"]["K"]["unset-v1-a1"]["route_removals"] = 2; self.assertEqual(status(b), "KILLED")
        b = good(); b["ledger"]["K"]["repeat-v0-a0"]["route_set_digest"] = "r9"; self.assertEqual(status(b), "KILLED")

    def test_descent_families_kill_on_campfire_report_elsewhere_and_report_families_never_decide(self):
        b = good(); b["ledger"]["K"]["unset-v1-a1"]["descents"]["premature_unresolved"] = 4; self.assertEqual(status(b), "KILLED")
        b = good("forem"); b["ledger"]["K"]["unset-v1-a1"]["descents"]["placeholder_flip"] = 4
        s, _, rep = V.verdict(b); self.assertEqual(s, "CONFIRMED FOR THIS CONDITION"); self.assertTrue(rep["generalization_descents"])
        b = good(); b["ledger"]["K"]["unset-v1-a1"]["descents"].update(arm_loss=500, late_unresolved=106)
        self.assertEqual(status(b), "CONFIRMED FOR THIS CONDITION")


if __name__ == "__main__":
    unittest.main()
