"""Fast unit and cache-contract tests; no native analyzer or heavy-slot acquisition."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location("obs", Path(__file__).with_name("obs.py"))
obs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(obs)


def record(values=None, valid=True, **fields):
    return {"valid": valid, "observations": dict(value_digests=values or {"returns": "abc"}, **fields)}


class KeyTests(unittest.TestCase):
    def test_order_and_only_effective_rh_environment(self):
        a = obs.cache_key("binary", "manifest", {"RH_X": "1", "RH_Y": "0", "PATH": "a"}, "unset")
        b = obs.cache_key("binary", "manifest", {"PATH": "b", "RH_Y": "0", "RH_X": "1"}, "unset")
        self.assertEqual(a, b)

    def test_every_key_dimension_and_absent_versus_zero(self):
        base = obs.cache_key("b", "m", {"RH_X": "1"}, "unset")
        variants = [obs.cache_key("c", "m", {"RH_X": "1"}, "unset"),
                    obs.cache_key("b", "n", {"RH_X": "1"}, "unset"),
                    obs.cache_key("b", "m", {"RH_X": "0"}, "unset"),
                    obs.cache_key("b", "m", {}, "unset"),
                    obs.cache_key("b", "m", {"RH_X": "1", "RH_OTHER": "0"}, "unset"),
                    obs.cache_key("b", "m", {"RH_X": "1"}, "repeat"),
                    obs.cache_key("b", "m", {"RH_X": "1"}, "1"),
                    obs.cache_key("b", "m", {"RH_X": "1"}, "unset", {"ruby": "different"})]
        self.assertTrue(all(v != base for v in variants))
        self.assertEqual(len(set(variants)), len(variants))

    def test_matrix_independent_repeat(self):
        settings = obs.all_settings()
        self.assertEqual(len(settings), 16)
        self.assertEqual(len({x["name"] for x in settings}), 16)
        self.assertEqual(sum(s["schedule"] == "repeat" for s in settings), 4)

    def test_manifest_tracks_bytes_mode_and_external_symlink_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "app"
            root.mkdir()
            source = root / "model.rb"
            source.write_text("one")
            before = obs.inventory(root)
            source.write_text("two")
            self.assertNotEqual(before, obs.inventory(root))
            before = obs.inventory(root)
            source.chmod(0o755)
            self.assertNotEqual(before, obs.inventory(root))
            external = Path(tmp) / "external.rb"
            external.write_text("first")
            (root / "link.rb").symlink_to(external)
            before = obs.inventory(root)[1]
            external.write_text("other")
            self.assertNotEqual(before, obs.inventory(root)[1])


class ClaimTests(unittest.TestCase):
    def setUp(self):
        self.names = ["unset-v1-a1", "1-v1-a1", "2-v1-a1", "repeat-v1-a1"]
        self.claim = {"name": "schedule equality", "apps": ["sample"], "settings": self.names}
        self.records = {"sample/" + n: record() for n in self.names}

    def test_equal_and_mismatch(self):
        self.assertTrue(all(v["passed"] for v in obs.check_claim(self.claim, self.records)))
        self.records["sample/1-v1-a1"] = record({"returns": "changed"})
        verdicts = obs.check_claim(self.claim, self.records)
        self.assertFalse(verdicts[1]["passed"])
        self.assertEqual(verdicts[1]["setting"], "sample/1-v1-a1")

    def test_missing_cell_field_or_invalid_is_never_an_equality(self):
        del self.records["sample/1-v1-a1"]
        self.records["sample/2-v1-a1"]["valid"] = False
        self.records["sample/repeat-v1-a1"]["observations"].clear()
        verdicts = obs.check_claim(self.claim, self.records)
        self.assertEqual([v["passed"] for v in verdicts], [True, False, False, False])

    def test_reject_vacuous_and_unknown_claim(self):
        for change in ({"settings": []}, {"settings": self.names[:1]}, {"apps": []}, {"kind": "typo"}):
            with self.assertRaises(ValueError):
                obs.check_claim(dict(self.claim, **change), self.records)

    def test_exact_expected_values_and_changed_keys(self):
        c = dict(self.claim, kind="equals", expected={"returns": "abc"})
        self.assertTrue(all(v["passed"] for v in obs.check_claim(c, self.records)))
        other = {k: record({"returns": "different"}) for k in self.records}
        c = dict(self.claim, kind="changed_keys", expected=["returns"])
        self.assertTrue(all(v["passed"] for v in obs.check_claim(c, self.records, other)))
        c["expected"] = []
        self.assertFalse(any(v["passed"] for v in obs.check_claim(c, self.records, other)))

    def test_unexposed_laws_cannot_pass_zero(self):
        c = dict(self.claim, kind="zero", field="law_violation_counts")
        self.assertFalse(any(v["passed"] for v in obs.check_claim(c, self.records)))
        for r in self.records.values():
            r["observations"]["law_violation_counts"] = {"native": {}}
        self.assertTrue(all(v["passed"] for v in obs.check_claim(c, self.records)))

    def test_exact_reason_delta_includes_missing_rows_and_type_hash(self):
        a = {obs.canonical({"site": 1}): {"untyped_kinds": 6, "type_hash": "same"}}
        b = {obs.canonical({"site": 1}): {"untyped_kinds": 2, "type_hash": "same"}}
        delta = obs.reason_delta(a, b)
        self.assertEqual(len(delta["changes"]), 1)
        self.assertEqual(delta["changes"][0]["identity"], {"site": 1})
        self.assertFalse(delta["left_only"])
        c = {obs.canonical({"site": 1}): {"untyped_kinds": 2, "type_hash": "other"}}
        self.assertNotEqual(delta, obs.reason_delta(a, c))
        self.assertEqual(len(obs.reason_delta(a, {})["left_only"]), 1)


class CacheContractTests(unittest.TestCase):
    def test_failed_first_result_can_be_retried_without_erasing_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary, app = root / "analyzer", root / "input"
            binary.write_text("fixed executable identity")
            (app / "app").mkdir(parents=True)
            tree, entries = obs.inventory(app)
            manifest = obs.digest({"schema": 1, "tree_sha256": tree, "entries": entries})
            args = argparse.Namespace(bin=binary, app="sample", timeout=2, fresh=False)
            good = [False]

            def fake_launch(command, **kwargs):
                out = Path(obs.read(command[-1])["directory"])
                report = {"digest": {str(i): "fixed" for i in range(10)}}
                (out / "stderr.log").write_text("rh-fixpoint: " + json.dumps(report) if good[0] else "failed")
                obs.save(out / "metrics.json", {"exit_code": 0 if good[0] else 2, "timed_out": False})
                return 0

            with patch.object(obs.subprocess, "call", side_effect=fake_launch) as launched:
                run = lambda: obs.one_cell(args, root / "cache", obs.sha(binary), app, manifest,
                                           tree, {}, {}, {}, obs.setting("unset-v1-a1"))
                failed = run()
                self.assertFalse(failed["valid"])
                warm = run()
                self.assertFalse(warm["valid"])
                self.assertEqual(launched.call_count, 1)
                good[0], args.fresh = True, True
                successful = run()
                self.assertTrue(successful["valid"])
                self.assertIsNone(successful["fresh_match"])
                self.assertFalse(obs.read(failed["result"])["valid"])
                args.fresh = False
                warm = run()
                self.assertTrue(warm["valid"])
                self.assertEqual(warm["analyzer_runs"], 0)
                self.assertEqual(launched.call_count, 2)

    def test_warm_hit_zero_calls_fresh_match_and_fresh_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "roundhouse"
            binary.write_text("fixture binary identity")
            app = root / "app"
            (app / "app").mkdir(parents=True)
            (app / "app/model.rb").write_text("class Model; end")
            tree, entries = obs.inventory(app)
            manifest = obs.digest({"schema": 1, "tree_sha256": tree, "entries": entries})
            args = argparse.Namespace(bin=binary, app="sample", timeout=3, fresh=False)
            calls = []
            values = {str(i): "abc" for i in range(10)}

            def fake_launch(command, **kwargs):
                request = obs.read(command[-1])
                out = Path(request["directory"])
                calls.append(request)
                time.sleep(0.03)
                report = {"digest": dict(values), "census": {"untyped_anywhere": 0,
                    "untyped_by_provenance": {"pending": 0, "gradual": 0, "unresolved": 0}}}
                (out / "stdout.log").write_text("")
                (out / "stderr.log").write_text("rh-fixpoint: " + json.dumps(report) + "\n")
                (out / "census.jsonl").write_text("")
                obs.save(out / "metrics.json", {"exit_code": 0, "timed_out": False})
                return 0

            with patch.object(obs.subprocess, "call", side_effect=fake_launch):
                run = lambda: obs.one_cell(args, root / "cache", obs.sha(binary), app, manifest,
                                           tree, {}, {}, {}, obs.setting("unset-v1-a1"))
                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(lambda _: run(), range(2)))
                first = next(r for r in results if r["analyzer_runs"])
                self.assertTrue(first["valid"])
                self.assertEqual(sorted(r["analyzer_runs"] for r in results), [0, 1])
                second = run()
                self.assertEqual(second["analyzer_runs"], 0)
                self.assertEqual(len(calls), 1)
                with patch.object(obs, "lock", side_effect=AssertionError("cached read took the fresh-run lock")):
                    fast = run()
                self.assertEqual(fast["analyzer_runs"], 0)
                self.assertEqual(len(calls), 1)
                args.fresh = True
                fresh = run()
                self.assertTrue(fresh["fresh_match"])
                self.assertEqual(len(calls), 2)
                values["0"] = "changed"
                fresh = run()
                self.assertFalse(fresh["fresh_match"])
                self.assertFalse(fresh["valid"])
                self.assertEqual(len(calls), 3)
                self.assertEqual(obs.read(second["result"])["observations"]["value_digests"]["0"], "abc")
                args.fresh = False
                tainted = run()
                self.assertEqual(tainted["analyzer_runs"], 0)
                self.assertFalse(tainted["valid"])
                self.assertFalse(tainted["fresh_match"])

    def test_duplicate_census_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            report = {"digest": {str(i): "x" for i in range(10)}, "census": {}}
            (out / "stderr.log").write_text("rh-fixpoint: " + json.dumps(report) + "\n")
            row = {"emit_body": {}, "site": {}, "type_hash": "x", "untyped_kinds": 2}
            (out / "census.jsonl").write_text((json.dumps(row) + "\n") * 2)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                obs.reduce_outputs(out, out, 0)


class MeasurementTests(unittest.TestCase):
    def test_child_status_cpu_rss_and_timeout_are_captured(self):
        old_int, old_term = signal.getsignal(signal.SIGINT), signal.getsignal(signal.SIGTERM)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                binary = root / "analyzer"
                binary.write_text("#!/usr/bin/env python3\nimport sys,time\n"
                                  "time.sleep(3 if 'slow' in sys.argv else 0.02)\nsys.exit(1)\n")
                binary.chmod(0o755)
                with patch.object(obs, "environment", return_value=os.environ.copy()):
                    normal = root / "normal"
                    normal.mkdir()
                    request = {"directory": str(normal), "binary": str(binary), "input": str(root),
                               "timeout": 3, "flags": {}}
                    self.assertEqual(obs.run_child(request), 0)
                    m = obs.read(normal / "metrics.json")
                    self.assertEqual(m["exit_code"], 1)
                    self.assertGreater(m["peak_rss_bytes"], 0)
                    self.assertGreater(m["cpu_seconds"], 0)
                    self.assertGreater(m["wall_seconds"], 0)
                    self.assertFalse(m["timed_out"])
                    binary.write_text("#!/usr/bin/env python3\nimport time\ntime.sleep(5)\n")
                    slow = root / "slow"
                    slow.mkdir()
                    request.update(directory=str(slow), timeout=0.05)
                    self.assertEqual(obs.run_child(request), 0)
                    m = obs.read(slow / "metrics.json")
                    self.assertTrue(m["timed_out"])
                    self.assertLess(m["exit_code"], 0)
                    self.assertLess(m["wall_seconds"], 2)
        finally:
            signal.signal(signal.SIGINT, old_int)
            signal.signal(signal.SIGTERM, old_term)


if __name__ == "__main__":
    unittest.main()
