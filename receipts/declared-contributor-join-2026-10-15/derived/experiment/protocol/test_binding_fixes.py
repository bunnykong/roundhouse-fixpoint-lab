"""Binding CHECK.md counterexamples; synthetic only, no analyzer invocation."""
import json
import unittest
from pathlib import Path

import test_verdict as T

V = T.V
EMPTY = {"targets": [], "excluded_declared": [], "modules": [], "classes": []}
SUMMARY = ["rh-contributor-summary: " + json.dumps({"targets": 0, "own_present": 0, "module_present": 0,
                                         "replay_failures": 0, "perm_failures": 0})]


class BindingFixes(unittest.TestCase):
    def setUp(self):
        self.lab = None

    def tearDown(self):
        if self.lab:
            self.lab.close()

    def mutate_join_stderr(self, fn):
        for r in V.records(self.lab.root, "contributor-join-join").values():
            path = Path(r["directory"]) / "stderr.log"
            lines = []
            for line in path.read_text().splitlines():
                tag, raw = line.split(": ", 1)
                obj = json.loads(raw)
                fn(tag, obj)
                lines.append(tag + ": " + json.dumps(obj))
            path.write_text("\n".join(lines) + "\n")

    def test_overlapping_tuple_floor_kills(self):
        self.lab = T.Lab()
        a = {"kind": "tuple", "elems": [T.union(T.STR, T.NIL)]}
        b = {"kind": "tuple", "elems": [T.union(T.STR, T.BOOL)]}
        self.assertEqual(V.meet(a, b), {"kind": "tuple", "elems": [T.STR]})
        for i, n in enumerate(V.V0):
            self.lab.cell("c", "forem", n, rows={T.RET: a if i % 2 == 0 else b})
            self.lab.cell("j", "forem", n, rows={T.RET: T.NIL})
        checks, _ = V.check_floor_and_scope(V.records(self.lab.root, "c"), V.records(self.lab.root, "j"),
                                            "forem", V.V0, False)
        self.assertTrue(all(c["status"] == "fail" for c in checks if c["check"] == "K1-floor"))

    def test_unsupported_intersections_unavailable(self):
        for a, b in [(T.cls("Account"), T.cls("User")),
                     ({"kind": "record", "row": {"fields": {"x": T.STR}}},
                      {"kind": "record", "row": {"fields": {"y": T.STR}}})]:
            with self.assertRaises(KeyError):
                V.meet(a, b)

    def test_discourse_second_schedule_is_mandatory(self):
        self.lab = T.Lab()
        for n, cty, jty in zip(V.DISCOURSE, [T.STR, T.U], [T.STR, T.NIL]):
            for label, ty in [("c", cty), ("j", jty)]:
                self.lab.cell(label, "discourse", n, rows={T.RET: ty}, digests={"returns": T.digest_of(ty)},
                              closure=EMPTY, stderr=SUMMARY if label == "j" else ())
        args = V.argparse.Namespace(cache_root=self.lab.root, label=["C=c", "J=j"])
        result = V.mode_discourse(args)
        self.assertEqual(result["verdict"], "KILLED")
        self.assertTrue(any(c["check"] == "K1-floor" and c["scope"].endswith("1-v0-a0") and
                            c["status"] == "fail" for c in result["checks"]))

    def test_header_only_dumps_are_inconclusive(self):
        self.lab = T.campfire_lab()
        for label in ("contributor-join-control", "contributor-join-join"):
            for r in V.records(self.lab.root, label).values():
                p = Path(r["directory"]) / "contributor-values.jsonl"
                p.write_text(p.read_text().splitlines()[0] + "\n")
        self.assertEqual(T.run_campfire(self.lab)["verdict"], "INCONCLUSIVE")

    def test_alias_inventory_catches_deleted_alias(self):
        self.lab = T.campfire_lab()
        for r in V.records(self.lab.root, "contributor-join-join").values():
            p = Path(r["directory"]) / "contributor-values.jsonl"
            p.write_text("\n".join(line for line in p.read_text().splitlines()
                                   if json.loads(line).get("part") != "aliases") + "\n")
        self.assertEqual(T.run_campfire(self.lab)["verdict"], "INCONCLUSIVE")

    def test_missing_hashes_unavailable(self):
        self.lab = T.campfire_lab()
        def mutate(tag, obj):
            if tag == "rh-contributor-cell":
                obj.pop("stored_hash")
                obj.pop("aggregate_hash")
        self.mutate_join_stderr(mutate)
        self.assertEqual(T.run_campfire(self.lab)["verdict"], "INCONCLUSIVE")

    def test_each_summary_counter_reconciles(self):
        for field in ("own_present", "module_present", "perm_failures", "replay_failures", "targets"):
            with self.subTest(field=field):
                self.lab = T.campfire_lab()
                self.mutate_join_stderr(lambda tag, obj: obj.update({field: 999}) if tag == "rh-contributor-summary" else None)
                self.assertEqual(T.run_campfire(self.lab)["verdict"], "KILLED")
                self.lab.close()
                self.lab = None

    def test_permutation_and_replay_failures_are_separate(self):
        self.lab = T.campfire_lab()
        def mutate(tag, obj):
            if tag == "rh-contributor-cell":
                obj["perm_equal"] = False
            if tag == "rh-contributor-summary":
                obj["perm_failures"] = 1
        self.mutate_join_stderr(mutate)
        checks = V.check_replay(V.records(self.lab.root, "contributor-join-control"), V.records(self.lab.root, "contributor-join-join"),
                                "campfire", V.CAMPFIRE)
        self.assertTrue(all(c["status"] == "fail" for c in checks))
        self.assertTrue(all(c["detail"]["unavailable"] == [] for c in checks))
        self.assertTrue(all(not any("summary" in p for p in c["detail"]["problems"]) for c in checks))

    def test_missing_budget_and_verification_observations_unavailable(self):
        self.lab = T.Lab()
        n = "unset-v1-a1"
        self.lab.cell("c", "forem", n, verify=T.VERIFY0)
        self.lab.cell("j", "forem", n, verify=[])
        c, j = V.records(self.lab.root, "c"), V.records(self.lab.root, "j")
        p = Path(j["forem/" + n]["directory"]) / "report.json"
        report = json.loads(p.read_text())
        report["worklist"] = {"engine": {}}
        report.pop("fold")
        p.write_text(json.dumps(report))
        checks = V.check_invariants(c, j, "forem", [n])
        self.assertEqual(checks[0]["status"], "unavailable")
        self.assertEqual(len(checks[0]["detail"]["unavailable"]), 2)

    def test_malformed_empty_duplicate_dumps_preserve_valid_failure(self):
        for kind in ("json", "empty", "duplicate", "bad_record"):
            with self.subTest(kind=kind):
                self.lab = T.campfire_lab(replay_ok=False)
                r = V.records(self.lab.root, "contributor-join-join")["campfire/unset-v0-a0"]
                p = Path(r["directory"]) / "contributor-values.jsonl"
                lines = p.read_text().splitlines()
                data = {"json": "{\n", "empty": "", "duplicate": "\n".join(lines[:-1] + [lines[1], lines[-1]]),
                        "bad_record": "\n".join([lines[0], "[]", lines[-1]])}[kind]
                p.write_text(data)
                result = T.run_campfire(self.lab)
                self.assertEqual(result["verdict"], "KILLED")
                self.assertTrue(any(c["check"] == "K1-floor" and c["status"] == "unavailable"
                                    for c in result["checks"]))
                self.lab.close()
                self.lab = None

    def test_malformed_stderr_is_unavailable(self):
        self.lab = T.campfire_lab()
        r = V.records(self.lab.root, "contributor-join-join")["campfire/unset-v0-a0"]
        (Path(r["directory"]) / "stderr.log").write_text("rh-contributor-cell: {\n")
        self.assertEqual(T.run_campfire(self.lab)["verdict"], "INCONCLUSIVE")

    def test_partial_witness_coverage_unavailable_but_loss_wins(self):
        self.lab = T.Lab()
        row = ("returns", "ListingsController#create_draft")
        for label, ty in (("c", T.U), ("j", T.U), ("bad", T.NIL)):
            self.lab.cell(label, "forem", "unset-v0-a0", rows={row: ty})
        wmap = json.loads((T.HERE / "witness-map.json").read_text())
        c, j, bad = [V.records(self.lab.root, label) for label in ("c", "j", "bad")]
        good = V.check_witnesses(c, j, "forem", ["unset-v0-a0"], wmap)[0]
        loss = V.check_witnesses(c, bad, "forem", ["unset-v0-a0"], wmap)[0]
        self.assertEqual(good["status"], "unavailable")
        self.assertEqual(len(good["detail"]["coverage"]), 12)
        self.assertEqual(loss["status"], "fail")

    def test_each_explicit_witness_target_requires_coverage(self):
        self.lab = T.Lab()
        row = ("returns", "First#value?")
        for label in ("c", "j"):
            self.lab.cell(label, "mastodon", "unset-v0-a0", rows={row: T.U})
        wmap = {"witnesses": [{"app": "mastodon", "key_regex": r"(First|Second)#value\?",
                                "ruby_class": "String", "label": "both-targets"}]}
        result = V.check_witnesses(V.records(self.lab.root, "c"), V.records(self.lab.root, "j"),
                                   "mastodon", ["unset-v0-a0"], wmap)[0]
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["detail"]["coverage"][0]["missing_targets"], ["Second#value?"])


if __name__ == "__main__":
    unittest.main()
