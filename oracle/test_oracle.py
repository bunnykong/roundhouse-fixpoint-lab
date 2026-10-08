"""Stdlib tests, including recorder/CLI integration and cyclic proof regressions."""
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from check import Grammar, InputError, Membership, ValueGraph, check_records, load_records

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Symbol:
    name: str


def tagged(value):
    counter, seen = [0], {}

    def visit(v):
        if isinstance(v, (list, dict)) and id(v) in seen:
            return {"ref": seen[id(v)]}
        vid = counter[0]
        counter[0] += 1
        if isinstance(v, (list, dict)):
            seen[id(v)] = vid
        node = {"id": vid}
        if isinstance(v, list):
            node.update(tag="Array", items=[visit(x) for x in v])
        elif isinstance(v, dict):
            node.update(tag="Hash", entries=[{"key": visit(k), "value": visit(x)} for k, x in v.items()])
        elif isinstance(v, Symbol):
            node.update(tag="Symbol", value=v.name)
        elif v is None:
            node["tag"] = "nil"
        elif type(v) is bool:
            node["tag"] = "true" if v else "false"
        elif type(v) is int:
            node.update(tag="Integer", value=v)
        elif type(v) is float:
            node.update(tag="Float", value=v)
        else:
            node.update(tag="String", value=v)
        return node
    return visit(value)


def membership(source, value, alias="root"):
    return Membership(Grammar(source), ValueGraph(tagged(value)), alias)


def report(source, values):
    records = [(i + 1, {"slot": "test:return", "value": tagged(v)}) for i, v in enumerate(values)]
    return check_records(Grammar(source), records, {"test:return": "root"})


class ParserTests(unittest.TestCase):
    def test_grammar_and_forward_references(self):
        grammar = Grammar("""# comment
type root = Hash[String | Symbol, child] | [Integer, child] | { key: child }
type child = Array[child] | (Float | nil | bool | untyped)
""")
        self.assertEqual(set(grammar.aliases), {"root", "child"})
        self.assertEqual(grammar.aliases["root"].kind, "union")
        self.assertEqual(grammar.aliases["root"].args[0].args[0].text(), "String | Symbol")

    def test_empty_containers(self):
        self.assertTrue(membership("type root = [] | {}", []).accepted)
        self.assertTrue(membership("type root = [] | {}", {}).accepted)

    def test_invalid_grammar(self):
        for text in ("", "type x = Unknown", "type x = x", "type x = y type y = x | Integer",
                     "type x = Integer type x = String", "type Integer = nil",
                     "type x = Array[Integer, String]", "type x = Hash[Integer]",
                     "type x = { a: Integer, a: String }", "type x = Integer ?", "type x = [Integer,"):
            with self.subTest(text=text), self.assertRaises(InputError):
                Grammar(text)

    def test_alias_edge_can_be_guarded_elsewhere(self):
        self.assertTrue(membership("type root = child type child = Array[root] | nil", [None]).accepted)


class MembershipTests(unittest.TestCase):
    def test_leaf_distinctions(self):
        for ty, good, bad in (("Integer", 1, True), ("Float", 1.0, 1), ("String", "s", Symbol("s")),
                              ("Symbol", Symbol("s"), "s"), ("nil", None, False), ("bool", False, None)):
            with self.subTest(ty=ty):
                self.assertTrue(membership("type root = " + ty, good).accepted)
                self.assertFalse(membership("type root = " + ty, bad).accepted)
        self.assertTrue(membership("type root = bool", True).accepted)
        self.assertTrue(membership("type root = untyped", {Symbol("s"): [True, 1, None]}).accepted)

    def test_recursive_json_and_failure_path(self):
        source = "type root = Hash[String, root] | Array[root] | Integer | String | nil"
        self.assertTrue(membership(source, {"a": [1, {"b": [None, "s"]}]}).accepted)
        failure = membership(source, {"a": [1, {"b": 1.25}]}).failure()
        self.assertEqual(failure["path"], '$["a"][1]["b"]')
        self.assertEqual(failure["actual"], "Float")
        key_failure = membership(source, {Symbol("a"): 1}).failure()
        self.assertEqual(key_failure["path"], "$.keys[0]")

    def test_mutual_recursion(self):
        source = "type root = Hash[String, other] | Integer type other = Array[root] | String"
        self.assertTrue(membership(source, {"a": [1, {"b": "x"}]}).accepted)
        self.assertFalse(membership(source, {"a": ["x"]}).accepted)

    def test_cyclic_values_are_coinductive(self):
        value = []
        value.append(value)
        self.assertTrue(membership("type root = Array[root]", value).accepted)
        value.append("bad")
        self.assertFalse(membership("type root = Array[root] | Integer", value).accepted)

    def test_no_optimistic_union_cache_leak(self):
        value = []
        value.extend((value, "s"))
        source = "type root = a | b type a = [b, Integer] type b = [a, String]"
        result = membership(source, value)
        self.assertFalse(result.accepted)
        self.assertIn("[1]", result.failure()["path"])

    def test_shared_identity_alias_memo(self):
        source = "type root = [child, child] type child = Hash[String, Integer]"
        shared = {"a": 1}
        result = membership(source, [shared, shared])
        self.assertTrue(result.accepted)
        self.assertEqual(sum(key[1] == "child" for key in result.equations), 1)

    def test_tuples_against_arrays(self):
        self.assertTrue(membership("type root = [Integer, String]", [1, "x"]).accepted)
        for value in ([1], [1, "x", 2], ["x", 1], {0: 1, 1: "x"}):
            self.assertFalse(membership("type root = [Integer, String]", value).accepted)
        self.assertTrue(membership("type root = Array[Integer | String]", [1, "x", 2]).accepted)

    def test_records_require_symbol_keys_allow_extras(self):
        source = "type root = { name: String, child: Array[Integer] }"
        self.assertTrue(membership(source, {Symbol("name"): "x", Symbol("child"): [1], "extra": None}).accepted)
        self.assertFalse(membership(source, {"name": "x", Symbol("child"): [1]}).accepted)
        self.assertFalse(membership(source, {Symbol("name"): "x"}).accepted)
        failed = membership(source, {Symbol("name"): "x", Symbol("child"): [False]})
        self.assertEqual(failed.failure()["path"], "$[:child][0]")

    def test_recursive_keys(self):
        value = {"id": 0, "tag": "Hash", "entries": [
            {"key": {"ref": 0}, "value": {"id": 1, "tag": "nil"}}]}
        grammar = Grammar("type root = Hash[root, root] | nil")
        self.assertTrue(Membership(grammar, ValueGraph(value), "root").accepted)

    def test_malformed_values(self):
        for node in ({"ref": 9}, {"id": 0, "tag": "Object"}, {"id": 0, "tag": "Integer", "value": True},
                     {"id": 0, "tag": "Array", "items": [{"id": 0, "tag": "nil"}]},
                     {"id": 0, "tag": "Hash", "entries": [{"key": tagged(1)}]}):
            with self.subTest(node=node), self.assertRaises(InputError):
                ValueGraph(node)


class TightnessTests(unittest.TestCase):
    def test_recursive_subvalues_exercise_all_arms(self):
        result = report("type root = Hash[String, root] | Array[root] | Integer | String | nil",
                        [{"a": [1, "s", None]}])
        self.assertEqual(result["tightness"]["unexercised"], [])

    def test_surplus_arm_and_unreachable_alias(self):
        result = report("type root = Array[root] | Integer | Symbol type unused = Float", [[1]])
        missing = result["tightness"]["unexercised"]
        self.assertEqual({f["type"] for f in missing}, {"Symbol", "Float"})
        self.assertEqual({f["kind"] for f in missing if f["type"] == "Symbol"}, {"alias_production", "union_arm"})

    def test_empty_array_is_no_evidence_for_element_alias(self):
        result = report("type root = Array[child] type child = Integer | String", [[]])
        self.assertEqual({f["alias"] for f in result["tightness"]["unexercised"]}, {"child"})

    def test_overlapping_union_arms_all_count(self):
        result = report("type root = Integer | untyped", [1])
        self.assertEqual(result["tightness"]["unexercised"], [])

    def test_failed_arm_not_credited(self):
        result = report("type root = [Integer, String] | Array[Integer]", [[1, 2]])
        self.assertEqual({f["type"] for f in result["tightness"]["unexercised"]}, {"[Integer, String]"})

    def test_slot_binding_and_nonvacuity(self):
        grammar = Grammar("type root = Integer")
        for records, slots in (([], {"x": "root"}), ([(1, {"slot": "x", "value": tagged(1)})], {"y": "root"}),
                               ([(1, {"slot": "x", "value": tagged(1)})], {"x": "missing"})):
            with self.assertRaises(InputError):
                check_records(grammar, records, slots)


class RecorderTests(unittest.TestCase):
    def run_record(self, directory, source, *args, output="trace.jsonl"):
        source_path, trace_path = directory / "source.rb", directory / output
        source_path.write_text(source, encoding="utf-8")
        proc = subprocess.run(["ruby", str(HERE / "record.rb"), "--source", str(source_path),
                               "--output", str(trace_path), *args], capture_output=True, text=True)
        return proc, trace_path

    def test_snapshots_tags_cycles_and_parameter_timing(self):
        source = """class Sample < ApplicationController
  def visit(value)
    value << :after
    value
  end
  def index
    cycle = []; cycle << cycle
    visit([1, 2.5, "s", :before, nil, true, false, { :k => "v" }, cycle, "\\xff".b, Float::NAN])
  end
end
"""
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            proc, trace = self.run_record(Path(temp), source, "--entry", "Sample#index", "--returns", "visit", "--params", "visit:value")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            records = load_records(trace)
            before, after = [ValueGraph(r["value"]) for _, r in records]
            self.assertEqual(len(before.nodes[before.root]["items"]), 11)
            self.assertEqual(len(after.nodes[after.root]["items"]), 12)
            self.assertEqual({n["tag"] for n in before.nodes.values()},
                             {"Array", "Hash", "Integer", "Float", "String", "Symbol", "nil", "true", "false"})
            self.assertTrue(any("bytes" in n for n in before.nodes.values()))
            self.assertTrue(any(n.get("value") == "NaN" for n in before.nodes.values()))

    def test_seeded_fuzz_reproducible_and_deep(self):
        source = "class Sample; def visit(value); value; end; end"
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            directory = Path(temp)
            opts = ("--fuzz", "Sample#visit", "--count", "50", "--seed", "7", "--depth", "6", "--returns", "visit")
            a, trace_a = self.run_record(directory, source, *opts, output="a.jsonl")
            b, trace_b = self.run_record(directory, source, *opts, output="b.jsonl")
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertEqual(b.returncode, 0, b.stderr)
            values = [r["value"] for _, r in load_records(trace_a)]
            self.assertEqual(values, [r["value"] for _, r in load_records(trace_b)])
            grammar = Grammar("type root = Hash[String, root] | Array[root] | Integer | Float | String | nil | bool")
            self.assertTrue(all(Membership(grammar, ValueGraph(v), "root").accepted for v in values))
            self.assertGreaterEqual(sum(n["tag"] in ("Array", "Hash") for n in ValueGraph(values[7]).nodes.values()), 6)

    def test_exceptions_and_unsupported_values_invalidate_trace(self):
        for body in ('raise "boom"', "Object.new"):
            with tempfile.TemporaryDirectory(dir=HERE) as temp:
                proc, trace = self.run_record(Path(temp), "class Sample; def visit; " + body + "; end; end",
                                              "--entry", "Sample#visit", "--returns", "visit")
                self.assertEqual(proc.returncode, 2)
                with self.assertRaises(InputError):
                    load_records(trace)

    def test_cli_exit_codes_and_incomplete_trace(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            directory = Path(temp)
            proc, trace = self.run_record(directory, 'module Sample; def visit(value); value; end; end',
                                          "--entry", "Sample#visit", "--args", '[{"a": [1, "x"]}]', "--returns", "visit")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            types = directory / "types.rbs"
            for text, code in (("type root = Hash[String, Array[Integer | String]]", 0),
                               ("type root = Hash[String, Array[Integer]]", 1), ("type root = root", 2)):
                types.write_text(text, encoding="utf-8")
                result = subprocess.run([sys.executable, str(HERE / "check.py"), str(trace), str(types),
                                         "--slot", "Sample#visit:return=root", "--json"], capture_output=True, text=True)
                self.assertEqual(result.returncode, code, result.stderr)
                if code == 1:
                    self.assertEqual(json.loads(result.stdout)["violations"][0]["path"], '$["a"][1]')
            trace.write_text("\n".join(trace.read_text().splitlines()[:-1]) + "\n")
            with self.assertRaises(InputError):
                load_records(trace)


if __name__ == "__main__":
    unittest.main()
