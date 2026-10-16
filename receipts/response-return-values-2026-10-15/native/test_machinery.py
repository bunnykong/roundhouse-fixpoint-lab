#!/usr/bin/env python3
"""Binding response-protocol counterprobes. All executions are synthetic; no analyzer is invoked."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
import test_verdict as T


def save(path, value):
    path.write_text(json.dumps(value) + "\n")


class ObserverBinding(unittest.TestCase):
    def verdict_after(self, mutate):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            T.World(stage="campfire").build(root)
            mutate(root)
            with contextlib.redirect_stdout(io.StringIO()):
                T.V.main(["--stage", "campfire", "--cache-root", str(root),
                          "--emission", str(root / "emission.json"), "--suite", str(root / "suite.json"),
                          "--out", str(root / "out")])
            out = json.loads((root / "out/verdict.json").read_text())
            return T.primary(out)

    def change_cell(self, root, setting, mutate, labels=None):
        for label in labels or [T.V.LABELS["C"], T.V.LABELS["T"], T.V.REFS["C"]]:
            p = root / "labels" / label / "label.json"
            entry = json.loads(p.read_text())["cells"]["campfire/" + setting]
            result_path = Path(entry["result"])
            result = json.loads(result_path.read_text())
            mutate(result)
            save(result_path, result)

    def test_repeat_aliases_unset_is_pre(self):
        def mutate(root):
            for name in [T.V.LABELS["C"], T.V.LABELS["T"], T.V.REFS["C"]]:
                p = root / "labels" / name / "label.json"
                label = json.loads(p.read_text())
                label["cells"]["campfire/repeat-v0-a0"] = label["cells"]["campfire/unset-v0-a0"]
                save(p, label)
        self.assertEqual(self.verdict_after(mutate), "INCONCLUSIVE(PRE)")

    def test_crosscheck_audit_off_is_pre(self):
        def mutate(result):
            result["key"]["rh_flags"]["RH_PROVENANCE_AUDIT"] = "0"
            result["setting"].update(name="unset-v1-a0", audit=False)
        self.assertEqual(self.verdict_after(lambda root: self.change_cell(root, "unset-v1-a1", mutate)),
                         "INCONCLUSIVE(PRE)")

    def test_schedule_1_actually_2_is_pre(self):
        def mutate(result):
            result["key"]["schedule"] = "2"
            result["key"]["rh_flags"]["RH_SHUFFLE"] = "2"
            result["setting"].update(name="2-v0-a0", schedule="2")
        self.assertEqual(self.verdict_after(lambda root: self.change_cell(root, "1-v0-a0", mutate)),
                         "INCONCLUSIVE(PRE)")

    def test_rewritten_repeat_metadata_still_needs_separate_execution(self):
        def mutate(root):
            for name in [T.V.LABELS["C"], T.V.LABELS["T"], T.V.REFS["C"]]:
                cells = json.loads((root / "labels" / name / "label.json").read_text())["cells"]
                original = json.loads(Path(cells["campfire/unset-v0-a0"]["result"]).read_text())["directory"]
                self.change_cell(root, "repeat-v0-a0", lambda r: r.update(directory=original), [name])
        self.assertEqual(self.verdict_after(mutate), "INCONCLUSIVE(PRE)")

    def test_wrong_app_or_reference_observer_is_pre(self):
        for label in [T.V.LABELS["C"], T.V.LABELS["T"], T.V.REFS["C"]]:
            with self.subTest(label=label):
                self.assertEqual(self.verdict_after(lambda root: self.change_cell(
                    root, "unset-v0-a0", lambda r: r.update(app="forem"), [label])), "INCONCLUSIVE(PRE)")

    def test_missing_observer_metadata_cannot_confirm(self):
        for field in ("app", "setting"):
            with self.subTest(field=field):
                self.assertEqual(self.verdict_after(lambda root: self.change_cell(
                    root, "unset-v0-a0", lambda r: r.pop(field))), "INCONCLUSIVE")
        self.assertEqual(self.verdict_after(lambda root: self.change_cell(
            root, "unset-v0-a0", lambda r: r["key"].pop("schedule"))), "INCONCLUSIVE")

    def test_shared_wrong_default_flag_is_pre(self):
        self.assertEqual(self.verdict_after(lambda root: self.change_cell(
            root, "unset-v0-a0", lambda r: r["key"]["rh_flags"].update(RH_FOLD_SLOTS="0"))),
                         "INCONCLUSIVE(PRE)")


class ExecutionBinding(unittest.TestCase):
    def test_guard_rejects_executing_a_different_kit(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            (work / "kit").mkdir(parents=True)
            foreign = Path(tmp) / "foreign"
            foreign.mkdir()
            guard = foreign / "verify_freeze.py"
            guard.write_bytes((KIT / "verify_freeze.py").read_bytes())
            proc = subprocess.run([sys.executable, "-B", "-I", str(guard), str(work), "reference"],
                                  capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("executing kit is not the guarded WORK/kit", proc.stderr)
            self.assertFalse((work / "receipts/stage-starts.jsonl").exists())

    def run_stage_body(self, stage, verdict):
        """Run the real shell case with a recording observer and mocked hash check."""
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "verdict-campfire").mkdir()
            save(work / "verdict-campfire/verdict.json", {"primary": {"verdict": verdict}})
            observer = work / "observer.py"
            observer.write_text("import json,sys\nfrom pathlib import Path\n"
                                "with Path(__file__).with_suffix('.jsonl').open('a') as f:\n"
                                " f.write(json.dumps(sys.argv[1:])+'\\n')\n")
            script = (KIT / "run.sh").read_text()
            body = script.split("\n" + stage + ")\n", 1)[1].split("\n  ;;", 1)[0]
            preamble = ('set -euo pipefail\nWORK=$1\nF=$1\nK=$1/kit\nBIN=$1/roundhouse\n'
                        'OBS="python3 $1/observer.py"\nshasum() { cat >/dev/null; }\n')
            proc = subprocess.run(["bash", "-c", preamble + body, "synthetic-stage", str(work)],
                                  capture_output=True, text=True)
            log = observer.with_suffix(".jsonl")
            rows = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
            return proc, rows

    def test_reference_runs_only_campfire(self):
        proc, rows = self.run_stage_body("reference", "INCONCLUSIVE")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][rows[0].index("--app") + 1], "campfire")
        self.assertIn(",".join(T.V.CAMPFIRE_SETTINGS), rows[0])

    def test_rest_references_and_arms_wait_for_campfire(self):
        proc, rows = self.run_stage_body("rest", "NARROWED")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Campfire stop rule", proc.stderr)
        self.assertEqual(rows, [])
        proc, rows = self.run_stage_body("rest", "CONFIRMED")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        references = [r for r in rows if r[r.index("--label") + 1] == T.V.REFS["C"]]
        self.assertEqual([r[r.index("--app") + 1] for r in references],
                         ["forem", "chatwoot", "mastodon", "discourse"])
        count = sum(len(r[r.index("--settings") + 1].split(",")) for r in references)
        self.assertEqual(count, 10)


if __name__ == "__main__":
    unittest.main()
