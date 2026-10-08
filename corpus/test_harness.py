"""Contract tests: output privacy, honest completion, and independent resource kills."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import LAB_ROOT
from metrics import Reducer
import watchdog
import preflight

SENTINEL = "CORPUS_DIAGNOSTIC_MESSAGE_MUST_NOT_ESCAPE"


class ReductionTest(unittest.TestCase):
    def test_candidate_verification_retains_counters_without_input_data(self):
        r = Reducer()
        r.feed("rh-sccq-verify: " + json.dumps({"phase": "production", "moved_slots": 0,
                 "ir_sites_moved": 3, "name": SENTINEL, "shape": SENTINEL,
                 "engine": {"body_evals": 7, SENTINEL: 4}}))
        r.feed("rh-fold: " + json.dumps({"loop": "absorb", "rounds": 3, "converged": True}))
        data = r.data()
        self.assertNotIn(SENTINEL, json.dumps(data))
        self.assertEqual(data["telemetry"]["rh-sccq-verify"][0]["ir_sites_moved"], 3)
        self.assertTrue(data["telemetry"]["rh-fold"][0]["converged"])
        self.assertIsNone(data["rh_dyn"]["converged"])

    def test_counts_without_messages_or_double_counting(self):
        r = Reducer()
        r.feed("file.rb:1:2: error[unsupported]: " + SENTINEL + " error[ivar_unresolved]: embedded text")
        r.feed("warning[gradual_untyped]: " + SENTINEL)
        r.feed("note[send_dispatch_failed]: " + SENTINEL)
        r.feed("roundhouse-check: secret/input — 0 parse error(s), 1 error(s), 1 warning(s), "
               "1 gap-attributed note(s), 0 survey gap(s)")
        data = r.data()
        self.assertEqual(data["errors_by_kind"], {"unsupported": 1})
        self.assertEqual(data["gradual_untyped"], 1)
        self.assertTrue(data["diagnostics_complete"])
        self.assertNotIn(SENTINEL, json.dumps(data))
        self.assertNotIn("secret/input", json.dumps(data))

    def test_probe_shapes_and_identities_are_dropped(self):
        r = Reducer()
        for phase in ("harvest", "unify"):
            record = {"stage": "production", "round": 11, "phase": phase,
                      "signatures": {"changed": 0, "nodes": 20, "kind_nodes": {"Array": 8, SENTINEL: 9}},
                      "by_slot": {"ret": {"slots": 2}, SENTINEL: {"slots": 4}},
                      "top_slots": [{"shape": SENTINEL, "name": SENTINEL}],
                      "counts": {"harvest_untie_cut": 3, SENTINEL: 20}}
            r.feed("rh-dyn: " + json.dumps(record))
        data = r.data()
        self.assertNotIn(SENTINEL, json.dumps(data))
        self.assertEqual(data["rh_dyn"]["rounds"]["production"], 1)
        self.assertTrue(data["rh_dyn"]["terminal"]["production"]["signatures_stable"])
        self.assertIsNone(data["rh_dyn"]["converged"])

    def test_explicit_convergence_and_incomplete_counts(self):
        r = Reducer()
        r.feed("rh-dyn: " + json.dumps({"stage": "final", "round": 0, "phase": "convergence",
                                      "converged": True}))
        self.assertTrue(r.data()["rh_dyn"]["converged"])
        self.assertFalse(r.data()["diagnostics_complete"])
        r.feed("roundhouse-check: . — 0 parse error(s), 2 error(s), 0 warning(s), "
               "0 gap-attributed note(s), 0 survey gap(s)")
        self.assertFalse(r.data()["counts_agree_with_summary"])


class SupervisorTest(unittest.TestCase):
    def setUp(self):
        temp_root = LAB_ROOT / "corpus/test-tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temp_root)
        self.root = Path(self.temp.name)
        self.app = self.root / "app-input"
        (self.app / "app").mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def run_fake(self, code, limit=1, seconds=30, relative_output=False):
        binary = self.root / "fake-checker"
        binary.write_text("#!" + sys.executable + "\n" + code)
        binary.chmod(0o755)
        capture = io.StringIO()
        output = self.root / "result"
        if relative_output:
            output = Path(os.path.relpath(output, Path.cwd()))
        with contextlib.redirect_stdout(capture):
            result = watchdog.run_check(output, binary, self.app, limit, seconds)
        self.assertNotIn(SENTINEL, capture.getvalue())
        for path in (self.root / "result").rglob("*"):
            if path.is_file():
                self.assertNotIn(SENTINEL, path.read_text(errors="replace"), str(path))
        return result

    def test_exit_one_with_summary_is_completed(self):
        result = self.run_fake(
            "import sys\n"
            "print('error[unsupported]: " + SENTINEL + "', file=sys.stderr)\n"
            "print('warning[gradual_untyped]: " + SENTINEL + "')\n"
            "print('roundhouse-check: . — 0 parse error(s), 1 error(s), 1 warning(s), "
            "0 gap-attributed note(s), 0 survey gap(s)')\n"
            "sys.exit(1)\n")
        self.assertEqual(result["outcome"], "completed")
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(result["errors_by_kind"], {"unsupported": 1})
        self.assertTrue(result["diagnostics_complete"])
        self.assertGreater(result["wait4_peak_rss_bytes"], 0)

    def test_exit_one_without_summary_is_failed(self):
        result = self.run_fake("import sys\nprint('" + SENTINEL + "')\nsys.exit(1)\n")
        self.assertEqual((result["outcome"], result["reason"]), ("failed", "missing_summary"))

    def test_relative_output_preserves_input_tree(self):
        result = self.run_fake(
            "print('roundhouse-check: . — 0 parse error(s), 0 error(s), 0 warning(s), "
            "0 gap-attributed note(s), 0 survey gap(s)')\n", relative_output=True)
        self.assertEqual(result["outcome"], "completed")
        self.assertEqual(sorted(p.name for p in self.app.iterdir()), ["app"])

    def test_deadline_is_independent_of_checker(self):
        result = self.run_fake("import time\ntime.sleep(20)\n", seconds=0.25)
        self.assertEqual((result["outcome"], result["reason"]), ("killed", "wall_limit"))
        self.assertLess(result["wall_seconds"], 3)
        self.assertEqual(result["exit_code"], -9)

    def test_rss_is_independent_of_checker(self):
        result = self.run_fake("import time\nx=bytearray(64*1024*1024)\n"
                               "for i in range(0,len(x),4096): x[i]=1\n"
                               "time.sleep(20)\n", limit=0.03)
        self.assertEqual((result["outcome"], result["reason"]), ("killed", "rss_limit"))
        self.assertGreaterEqual(result["peak_gib"], 0.03)
        self.assertEqual(result["exit_code"], -9)

    def test_ambient_flags_are_removed(self):
        with patch.dict(os.environ, {"RH_BOUND": "1", "RH_DYN_CAP": "2",
                                     "ROUNDHOUSE_INGEST_SURVEY": "1", "RUBYOPT": "-rsecret"}):
            env = watchdog.environment(self.root, {"RH_DYN": "1"})
        self.assertNotIn("RH_BOUND", env)
        self.assertNotIn("RH_DYN_CAP", env)
        self.assertNotIn("ROUNDHOUSE_INGEST_SURVEY", env)
        self.assertNotIn("RUBYOPT", env)
        self.assertEqual(env["RH_DYN"], "1")


class PreflightTest(unittest.TestCase):
    def test_ps_returns_only_aggregate_process_data(self):
        output = ("RSS COMMAND\n1024 /public/roundhouse-x check --continue " + SENTINEL
                  + "\n100 /public/roundhouse-x emit " + SENTINEL
                  + "\n1024 /public/roundhouse-y check .\n")
        with patch.object(preflight.subprocess, "run", return_value=SimpleNamespace(stdout=output)):
            state = preflight.running_checks()
        self.assertEqual(state["processes"], 2)
        self.assertEqual(state["total_gib"], 2048 * 1024 / 1024 ** 3)
        self.assertNotIn(SENTINEL, json.dumps(state))

    def test_ps_unavailable_uses_read_only_fallback(self):
        expected = {"method": "libproc_conservative", "processes": 0, "total_gib": 0}
        with patch.object(preflight.subprocess, "run", side_effect=PermissionError), \
             patch.object(preflight.sys, "platform", "darwin"), \
             patch.object(preflight, "libproc_checks", return_value=expected):
            self.assertEqual(preflight.running_checks(), expected)

    def test_no_visibility_does_not_allow_a_heavy_run(self):
        with patch.object(preflight.subprocess, "run", side_effect=PermissionError), \
             patch.object(preflight.sys, "platform", "darwin"), \
             patch.object(preflight, "libproc_checks", side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                preflight.running_checks()


if __name__ == "__main__":
    unittest.main()
