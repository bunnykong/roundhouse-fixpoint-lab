"""Unit and fixture integration tests; no native analyzer, network or external packages."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("quick_probe", Path(__file__).with_name("probe.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

U = {"kind": "untyped"}
V = {"kind": "var", "var": 0}
INT = {"kind": "int"}
BOOL = {"kind": "bool"}


def value(part, key, ty=U, h=1, **extra):
    return dict(part=part, key=key, ty=ty, hash=h, **extra)


def dump(path, rows=(), native=None, parts=None):
    native = dict(native or {table: "same" for table in p.TABLES})
    maps = {table: {} for table in p.TABLES if table != "ir"}
    ir = []
    rowdiff = p.dependencies()[1]
    for row in rows:
        part, key = row["part"], row["key"]
        if part == "ir":
            span = row["span"]
            ir.append([span["file"], span["start"], span["end"], row["hash"], row.get("note")])
        elif part in ("params", "controller_cache"):
            maps[part][rowdiff.parent(part, key)] = row["hash"]
        elif part in maps:
            maps[part][key] = row["hash"]
    if parts:
        maps.update(parts)
    fp = {"part": "fingerprint", "parts": maps, "ir": ir, "digests": native, "sources": ["app/test.rb"]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(v) for v in [fp] + list(rows)) + "\n")
    return native


class TempCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.seq = 0

    def scan(self, rows=(), **kwargs):
        self.seq += 1
        path = self.root / (str(self.seq) + ".jsonl")
        native = dump(path, rows, **kwargs)
        return p.scan_dump(path, native)


class RunTests(TempCase):
    def args(self, **kw):
        profile = self.root / "profile.json"
        profile.write_text('{"RH_FOLD":"0"}')
        args = dict(profile=profile, bin=self.root / "roundhouse", set=[], label="test",
                    apps="forem", settings=",".join(p.DEFAULT_SETTINGS), cache_root=self.root / "cache",
                    jobs=1, timeout=1800)
        args.update(kw)
        return argparse.Namespace(**args)

    @patch.object(subprocess, "call", return_value=0)
    def test_run_forwards_profile_overrides_settings_and_mandatory_dump(self, call):
        args = self.args(apps="forem,chatwoot", set=[["RH_NEW=1", "RH_TEXT=x=y"], ["RH_OTHER=0"]])
        self.assertEqual(p.run(args), 0)
        self.assertEqual(call.call_count, 2)
        command = call.call_args_list[0].args[0]
        self.assertEqual(command[:3], [sys.executable, str(p.OBSERVER), "run"])
        self.assertEqual(command[command.index("--settings") + 1], ",".join(p.DEFAULT_SETTINGS))
        self.assertEqual(command[-2:], ["--flag", "RH_CONTRIBUTOR_VALUES=1"])
        for item in ("RH_NEW=1", "RH_TEXT=x=y", "RH_OTHER=0"):
            self.assertIn(item, command)
        self.assertEqual(command[command.index("--flags") + 1], str(args.profile.resolve()))
        self.assertEqual(call.call_args.kwargs["cwd"], str(p.ROOT))

    @patch.object(subprocess, "call", side_effect=[1, 0])
    def test_failed_app_does_not_hide_other_app_or_status(self, call):
        self.assertEqual(p.run(self.args(apps="forem,chatwoot")), 1)
        self.assertEqual(call.call_count, 2)

    @patch.object(subprocess, "call", side_effect=[-15, 0])
    def test_killed_observer_cannot_look_successful(self, call):
        self.assertEqual(p.run(self.args(apps="forem,chatwoot")), 1)

    @patch.object(subprocess, "call", return_value=0)
    def test_explicit_fresh_retry_is_forwarded(self, call):
        p.run(self.args(fresh=True))
        self.assertEqual(call.call_args.args[0][-1], "--fresh")

    @patch.object(subprocess, "call")
    def test_invalid_options_are_rejected_before_launch(self, call):
        for kwargs in ({"set": [["RH_SHUFFLE=1"]]}, {"set": [["RH_CONTRIBUTOR_VALUES=0"]]},
                       {"set": [["NOPE=1"]]}, {"set": [["RH_X"]]}, {"apps": "forem,forem"},
                       {"apps": "unknown"}, {"settings": "unset-v0-a0,unset-v0-a0"},
                       {"settings": "bogus"}, {"label": "../oops"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                p.run(self.args(**kwargs))
        call.assert_not_called()

    def test_profile_must_be_a_map_and_cannot_disable_values(self):
        for content in ('[]', '{"RH_CONTRIBUTOR_VALUES":null}', '{"RH_FIXPOINT_VERIFY":"0"}'):
            args = self.args()
            args.profile.write_text(content)
            with self.assertRaises(ValueError):
                p.run(args)


class DumpTests(TempCase):
    def test_current_return_signature_and_present_empty_vector_are_retained(self):
        s = self.scan([value("returns", "X#m", note=7)], parts={"params": {"X#m": 23}})
        self.assertEqual(s["signatures"][("returns", "X#m")], (1, 7, None))
        self.assertEqual(s["signatures"][("params", "X#m[empty]")], (23, None, None))

    def test_fingerprint_only_rows_are_available_for_variance(self):
        s = self.scan(parts={"attributes": {"X@x": 3}})
        self.assertEqual(s["signatures"][("attributes", "X@x")], (3, None, None))

    def test_native_digest_mismatch_is_rejected(self):
        s = self.scan()
        with self.assertRaisesRegex(ValueError, "ten digests"):
            p.scan_dump(s["path"], {})

    def test_captured_sha_is_verified_including_large_dump_path(self):
        s = self.scan()
        self.assertEqual(p.scan_dump(s["path"], s["fingerprint"]["digests"], s["sha256"])["sha256"], s["sha256"])
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            p.scan_dump(s["path"], s["fingerprint"]["digests"], "wrong")

    def test_duplicate_full_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.scan([value("returns", "X#m"), value("returns", "X#m")])

    def test_missing_return_and_side_rows_are_not_empty_success(self):
        s = self.scan(parts={"returns": {"X#m": 1}, "side_table": {"slot": 2}})
        for part in ("returns", "side_table"):
            self.assertIn(part, s["errors"])
            self.assertIsNone(p.row_variance([s] * 4)[part]["varying_rows"])

    def test_ir_coverage_uses_span_hash_and_note_multiset(self):
        row = value("ir", "root:0", span={"file": 1, "start": 0, "end": 1}, note=7)
        s = self.scan([row])
        data = Path(s["path"]).read_text().splitlines()
        fp = json.loads(data[0])
        fp["ir"][0][-1] = 8
        Path(s["path"]).write_text(json.dumps(fp) + "\n" + data[1] + "\n")
        broken = p.scan_dump(s["path"], fp["digests"])
        self.assertIn("ir", broken["errors"])


class VarianceTests(TempCase):
    def test_union_of_varying_identities_not_pairwise_sum(self):
        a = self.scan([value("returns", "X#a"), value("returns", "X#b")])
        b = self.scan([value("returns", "X#a", h=2)])
        c = self.scan([value("returns", "X#a", h=3), value("returns", "X#b")])
        result = p.row_variance([a, b, c, a])["returns"]
        self.assertEqual(result["varying_rows"], 2)
        self.assertEqual(result["union_rows"], 2)

    def test_note_changes_are_row_differences(self):
        a = self.scan([value("returns", "X#a", note=1)])
        b = self.scan([value("returns", "X#a", note=2)])
        self.assertEqual(p.row_variance([a, b, a, a])["returns"]["varying_rows"], 1)

    def test_missing_schedule_is_null_for_every_table(self):
        a = self.scan()
        for table in p.row_variance([a, None, a, a]).values():
            self.assertIsNone(table["varying_rows"])

    def test_parameter_children_must_explain_native_parents(self):
        a = self.scan([value("params", "X#m[0]")])
        b = self.scan([value("params", "X#m[0]")], parts={"params": {"X#m": 2}})
        result = p.row_variance([a, b, a, a])["params"]
        self.assertIsNone(result["varying_rows"])
        self.assertEqual(result["unexplained_parents"], ["X#m"])

    def test_empty_vector_presence_differs_from_absence(self):
        a = self.scan(parts={"params": {"X#m": 10}})
        b = self.scan()
        self.assertEqual(p.row_variance([a, b, a, a])["params"]["varying_rows"], 1)

    def test_fingerprint_tables_have_actual_row_counts(self):
        a = self.scan(parts={"attributes": {"X@x": 1, "X@y": 2}})
        b = self.scan(parts={"attributes": {"X@x": 3, "X@y": 2}})
        self.assertEqual(p.row_variance([a, b, a, a])["attributes"]["varying_rows"], 1)

    def test_digest_equality_is_independent_of_row_availability(self):
        digest = {table: table for table in p.TABLES}
        a = {"valid": True, "record": {"observations": {"value_digests": digest}}}
        b = {"valid": True, "record": {"observations": {"value_digests": dict(digest, ir="other")}}}
        result = p.digest_equality([a, b, a, a])
        self.assertFalse(result["by_table"]["ir"])
        self.assertEqual(len(result["equal_tables"]), 9)
        result = p.digest_equality([a, {}, a, a])
        self.assertEqual(result["missing_tables"], list(p.TABLES))


class F61Tests(TempCase):
    def test_untyped_and_raw_var_admit_everything(self):
        for top in (U, V, {"kind": "union", "variants": [V, BOOL]}):
            self.assertEqual(p.value_relation(U, top), "EQ")
            self.assertEqual(p.value_relation(top, INT), "NARROW")
            self.assertEqual(p.value_relation(INT, top), "WIDEN")

    def test_recursive_container_checks(self):
        for before, after in (
            ({"kind": "array", "elem": V}, {"kind": "array", "elem": INT}),
            ({"kind": "hash", "key": U, "value": V}, {"kind": "hash", "key": INT, "value": BOOL}),
            ({"kind": "tuple", "elems": [V, INT]}, {"kind": "tuple", "elems": [BOOL, INT]}),
            ({"kind": "class", "id": "Box", "args": [V]}, {"kind": "class", "id": "Box", "args": [BOOL]}),
            ({"kind": "fn", "ret": V}, {"kind": "fn", "ret": BOOL}),
        ):
            with self.subTest(before=before):
                self.assertEqual(p.value_relation(before, after), "NARROW")
                self.assertEqual(p.value_relation(after, before), "WIDEN")
        self.assertEqual(p.value_relation(INT, BOOL), "INCOMP")
        self.assertEqual(p.value_relation(None, INT), "STRUCT")
        with self.assertRaises(KeyError):
            p.value_relation({"kind": "rec", "slot": "missing"}, INT)

    def test_oauth_nested_unknown_is_lost_and_imap_var_is_equal(self):
        before = {"kind": "hash", "key": {"kind": "sym"}, "value": {"kind": "union", "variants": [BOOL, V]}}
        after = {"kind": "hash", "key": {"kind": "sym"}, "value": BOOL}
        a = self.scan([value("params", "OAuth#render[0]", before), value("returns", "Imap#m", U)])
        b = self.scan([value("params", "OAuth#render[0]", after, h=2), value("returns", "Imap#m", V, h=2)])
        result = p.compare_values(a, b)
        self.assertTrue(result["complete"])
        self.assertEqual(result["counts"]["narrowed"], 1)
        self.assertEqual(result["counts"]["unchanged"], 1)
        self.assertEqual(result["narrowings"][0]["key"], "OAuth#render[0]")

    def test_unchanged_reference_hash_can_denote_a_narrowed_target(self):
        slot = 'Some(Ret { class: ClassId(Symbol("Box")), method: Symbol("get"), class_side: false })'
        ref = value("ir", "root:0", {"kind": "rec", "slot": slot}, h=55,
                    span={"file": 1, "start": 0, "end": 1}, note=0)
        a = self.scan([value("returns", "Box#get", U), ref])
        b = self.scan([value("returns", "Box#get", BOOL, h=2), ref])
        result = p.compare_values(a, b)
        self.assertEqual(result["counts"]["narrowed"], 2)
        self.assertEqual({r["key"] for r in result["narrowings"]}, {"Box#get", "root:0"})

    def test_fingerprint_only_change_is_missing_for_f61(self):
        a = self.scan(parts={"attributes": {"Box@x": 1}})
        b = self.scan(parts={"attributes": {"Box@x": 2}})
        result = p.compare_values(a, b)
        self.assertFalse(result["complete"])
        self.assertEqual(result["counts"]["missing"], 1)
        self.assertIn("no serialized type", result["unclassified"][0]["reason"])

    def test_absent_rows_and_unresolved_references_are_missing(self):
        a = self.scan([value("returns", "Box#get", {"kind": "rec", "slot": "missing"})])
        for b in (self.scan(), self.scan([value("returns", "Box#get", INT, h=2)])):
            result = p.compare_values(a, b)
            self.assertFalse(result["complete"])
            self.assertEqual(result["counts"]["missing"], 1)
        result = p.compare_values(a, None)
        self.assertIsNone(result["counts"]["narrowed"])
        self.assertIsNone(result["narrowings"])

    def test_self_comparison_has_zero_narrowings(self):
        a = self.scan([value("returns", "Box#get", V)], parts={"attributes": {"Box@x": 2}})
        result = p.compare_values(a, a)
        self.assertTrue(result["complete"])
        self.assertEqual(result["counts"], {"narrowed": 0, "widened": 0, "unchanged": 2, "incomparable": 0, "missing": 0})


class ReportTests(TempCase):
    def record(self, label, setting, rows=(), diagnostics=None, wall=0.25, manifest="input", valid=True):
        directory = self.root / "objects" / label / setting / "attempts" / "one"
        path = directory / "contributor-values.jsonl"
        native = dump(path, rows)
        record = {"valid": valid, "app": "forem", "input": "public/forem", "directory": str(directory),
                  "setting": {"name": setting}, "cache_key": label + setting,
                  "key": {"input_manifest_sha256": manifest, "runtime": {"ruby": "4.0.7"}, "binary_sha256": label,
                          "rh_flags": {"RH_CONTRIBUTOR_VALUES": "1"}},
                  "observations": {"value_digests": native, "diagnostics": diagnostics},
                  "metrics": {"wall_seconds": wall},
                  "artifacts": {"contributor-values.jsonl": {"bytes": path.stat().st_size,
                                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}}}
        (directory / "result.json").write_text(json.dumps(record))
        label_path = self.root / "labels" / label / "label.json"
        label_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(label_path.read_text()) if label_path.exists() else {"cells": {}}
        data["cells"]["forem/" + setting] = {"result": str(directory / "result.json"), "valid": valid}
        label_path.write_text(json.dumps(data))
        return directory

    def all_cells(self, label="control", **kw):
        for setting in p.DEFAULT_SETTINGS:
            self.record(label, setting, **kw)

    def test_complete_fixture_report_includes_every_required_measure(self):
        self.all_cells(diagnostics={"error/test": 2}, rows=[value("returns", "Box#get", U)])
        self.all_cells("candidate", diagnostics={"error/test": 1}, rows=[value("returns", "Box#get", INT, h=2)])
        result = p.make_report(self.root, "control", "candidate")
        self.assertTrue(result["complete"])
        data = result["apps"]["forem"]["v0-a0"]
        self.assertEqual(data["unset_values"]["counts"]["narrowed"], 1)
        self.assertEqual(data["control"]["cells"]["unset-v0-a0"]["wall_seconds"], 0.25)
        self.assertEqual(data["control"]["cells"]["unset-v0-a0"]["diagnostics"]["total"], 2)
        self.assertIn("error/test 2/2/2/2", p.markdown(result))
        self.assertIn("returns:Box#get", p.markdown(result))
        self.assertLessEqual(len(p.markdown(result).splitlines()), 60)

    def test_missing_cell_field_or_invalid_cell_stays_null(self):
        self.all_cells(diagnostics={})
        self.record("candidate", "unset-v0-a0", diagnostics=None, wall=None)
        self.record("candidate", "1-v0-a0", diagnostics={}, valid=False)
        result = p.make_report(self.root, "control", "candidate")
        self.assertFalse(result["complete"])
        data = result["apps"]["forem"]["v0-a0"]
        for setting in ("unset-v0-a0", "1-v0-a0", "2-v0-a0"):
            cell = data["candidate"]["cells"][setting]
            self.assertIsNone(cell["diagnostics"])
            self.assertIsNone(cell["wall_seconds"])
        self.assertEqual(data["control"]["cells"]["unset-v0-a0"]["diagnostics"]["total"], 0)
        self.assertIsNone(data["candidate"]["varying_rows"]["ir"]["varying_rows"])

    def test_different_inputs_are_not_compared_as_value_changes(self):
        self.all_cells(diagnostics={})
        self.all_cells("candidate", manifest="other", diagnostics={})
        result = p.make_report(self.root, "control", "candidate")
        data = result["apps"]["forem"]["v0-a0"]
        self.assertFalse(result["complete"])
        self.assertIn("input_manifest", data["comparison_missing"])
        self.assertIsNone(data["unset_values"]["counts"]["narrowed"])

    def test_mixed_conditions_are_not_reported_as_schedule_equal(self):
        for field in ("binary_sha256", "rh_flags", "input_manifest_sha256", "runtime"):
            with self.subTest(field=field):
                self.all_cells(diagnostics={})
                path = self.root / "objects/control/1-v0-a0/attempts/one/result.json"
                record = json.loads(path.read_text())
                record["key"][field] = {"different": "1"} if field in ("rh_flags", "runtime") else "different"
                path.write_text(json.dumps(record))
                result = p.make_report(self.root, "control", "control")
                data = result["apps"]["forem"]["v0-a0"]
                self.assertFalse(result["complete"])
                self.assertIsNone(data["control"]["digest_equality"]["by_table"]["returns"])

    def test_unavailable_table_does_not_become_zero_narrowings(self):
        a = self.scan(parts={"returns": {"Box#get": 1}})
        result = p.compare_values(a, a)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["counts"]["narrowed"])
        self.assertIsNone(result["by_table"]["returns"]["narrowed"])

    def test_tainted_cache_is_unavailable(self):
        self.all_cells(diagnostics={})
        directory = self.record("candidate", "unset-v0-a0", diagnostics={})
        (directory.parents[1] / "inconsistent.json").write_text('{}')
        data, error = p.label_data(self.root, "candidate")
        cell = p.load_cell(data, error, "forem", "unset-v0-a0")
        self.assertFalse(cell["valid"])
        self.assertIn("inconsistent", cell["missing"][0])

    def test_uncaptured_dump_is_missing_even_if_a_file_exists(self):
        self.all_cells(diagnostics={})
        path = self.root / "objects/control/unset-v0-a0/attempts/one/result.json"
        record = json.loads(path.read_text())
        record["artifacts"] = {}
        path.write_text(json.dumps(record))
        result = p.make_report(self.root, "control", "control")
        data = result["apps"]["forem"]["v0-a0"]
        self.assertIsNone(data["unset_values"]["counts"]["narrowed"])
        self.assertIn("no captured SHA-256", data["control"]["cells"]["unset-v0-a0"]["missing"][0])

    def test_malformed_receipt_is_missing_instead_of_crashing(self):
        self.all_cells(diagnostics={})
        path = self.root / "objects/control/unset-v0-a0/attempts/one/result.json"
        path.write_text('[]')
        result = p.make_report(self.root, "control", "control")
        self.assertFalse(result["complete"])
        cell = result["apps"]["forem"]["v0-a0"]["control"]["cells"]["unset-v0-a0"]
        self.assertFalse(cell["valid"])
        self.assertIsNone(cell["wall_seconds"])

    def test_missing_labels_generate_missing_report(self):
        result = p.make_report(self.root, "absent-control", "absent-candidate")
        self.assertFalse(result["complete"])
        data = result["apps"]["forem"]["v0-a0"]
        self.assertIsNone(data["unset_values"]["counts"]["narrowed"])
        self.assertIn("missing", p.markdown(result))

    def test_report_cli_writes_both_artifacts_and_exit_status(self):
        self.all_cells(diagnostics={})
        out = self.root / "out"
        code = p.main(["report", "--control", "control", "--candidate", "control",
                       "--cache-root", str(self.root), "--out", str(out)])
        self.assertEqual(code, 0)
        self.assertTrue((out / "report.json").is_file())
        self.assertTrue((out / "report.md").is_file())

    def test_nonfinite_or_negative_timings_are_missing(self):
        for wall in (float("nan"), float("inf"), -1, True):
            with self.subTest(wall=wall):
                self.assertIsNone(p.cell_summary({"valid": True, "missing": [],
                                                 "record": {"metrics": {"wall_seconds": wall}}})["wall_seconds"])

    def test_all_four_apps_and_all_observer_groups_fit_sixty_lines(self):
        self.all_cells(diagnostics={"error/test": 3})
        report = p.make_report(self.root, "control", "control")
        group = report["apps"]["forem"]["v0-a0"]
        report["apps"] = {app: {"v%d-a%d" % (v, a): group for v in (0, 1) for a in (0, 1)} for app in p.APPS}
        text = p.markdown(report)
        self.assertLessEqual(len(text.splitlines()), 60)
        self.assertEqual(text.count("Kinds, candidate:"), 16)


class RetainedPositiveTests(unittest.TestCase):
    def test_actual_sk_oauth_four_and_imap_nine(self):
        path = p.HERE / "fixtures/strict-producer-runtime-rows.jsonl"
        if not path.exists():
            self.skipTest("retained SK observations are not installed")
        with path.open() as stream:
            rows = [json.loads(line) for line in stream if '"unset-v0-a0"' in line]
        self.assertEqual(len(rows), 13)
        narrowed, imap = set(), []
        for row in rows:
            relation = p.value_relation(row["C"]["resolved_ty"], row["SK"]["resolved_ty"])
            if relation == "NARROW":
                narrowed.add(row["key"])
            if "Imap::Authentication" in row["key"]:
                imap.append(relation)
        expected = {"Api::V1::Accounts::" + provider + "::AuthorizationsController#render[0]"
                    for provider in ("Google", "Instagram", "Microsoft", "Notion")}
        self.assertEqual(narrowed, expected)
        self.assertEqual(imap, ["EQ"] * 9)


if __name__ == "__main__":
    unittest.main()
