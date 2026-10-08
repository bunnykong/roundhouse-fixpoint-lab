#!/usr/bin/env python3
"""Membership and witness coverage for a deliberately small recursive RBS grammar.

Membership is the greatest fixed point of finite AND/OR obligations. This is
coinduction without optimistic DFS results leaking out of a failed union arm.
Only guarded recursion is accepted; alias-only cycles are input errors.
"""
import argparse
import base64
import json
import re
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path


class InputError(ValueError):
    pass


ATOMS = frozenset(("Integer", "Float", "String", "Symbol", "nil", "bool", "untyped"))
TAGS = frozenset(("Integer", "Float", "String", "Symbol", "nil", "true", "false", "Array", "Hash"))
TOKEN = re.compile(r"\s+|\#[^\n]*|[A-Za-z_]\w*|[=|\[\]{},:()]")


@dataclass(eq=False)
class Type:
    uid: int
    kind: str
    name: str = ""
    args: tuple = ()
    fields: tuple = ()
    location: str = ""

    def text(self):
        if self.kind in ("atom", "alias"):
            return self.name
        if self.kind == "union":
            return " | ".join(a.text() for a in self.args)
        if self.kind == "tuple":
            return "[" + ", ".join(a.text() for a in self.args) + "]"
        if self.kind == "record":
            return "{ " + ", ".join(k + ": " + t.text() for k, t in self.fields) + " }"
        return self.kind + "[" + ", ".join(a.text() for a in self.args) + "]"


class Grammar:
    def __init__(self, source):
        self.tokens = []
        cursor = 0
        for match in TOKEN.finditer(source):
            if match.start() != cursor:
                raise InputError("unexpected syntax at offset %d" % cursor)
            word = match.group()
            cursor = match.end()
            if word.isspace() or word.startswith("#"):
                continue
            line = source.count("\n", 0, match.start()) + 1
            column = match.start() - source.rfind("\n", 0, match.start())
            self.tokens.append((word, "%d:%d" % (line, column)))
        if cursor != len(source):
            raise InputError("unexpected syntax at offset %d" % cursor)
        self.pos, self.nodes, self.aliases, self.features = 0, [], {}, {}
        while self.peek():
            self.take("type")
            name = self.take_identifier()
            if name in ATOMS or name in ("Array", "Hash", "type") or name in self.aliases:
                raise InputError("reserved or duplicate alias: " + name)
            self.take("=")
            self.aliases[name] = self.union()
        if not self.aliases:
            raise InputError("no type declarations")
        for node in self.nodes:
            if node.kind == "alias" and node.name not in self.aliases:
                raise InputError("unknown alias %s at %s" % (node.name, node.location))
        self._guarded()
        self._features()

    def peek(self):
        return self.tokens[self.pos][0] if self.pos < len(self.tokens) else ""

    def take(self, expected=None):
        if not self.peek():
            raise InputError("unexpected end of type declarations")
        word, location = self.tokens[self.pos]
        if expected is not None and word != expected:
            raise InputError("expected %r, got %r at %s" % (expected, word, location))
        self.pos += 1
        return word

    def take_identifier(self):
        word = self.take()
        if not re.fullmatch(r"[A-Za-z_]\w*", word):
            raise InputError("expected identifier, got " + word)
        return word

    def node(self, kind, name="", args=(), fields=(), location=""):
        node = Type(len(self.nodes), kind, name, tuple(args), tuple(fields), location)
        self.nodes.append(node)
        return node

    def union(self):
        arms = [self.term()]
        while self.peek() == "|":
            self.take()
            arms.append(self.term())
        if len(arms) == 1:
            return arms[0]
        return self.node("union", args=arms, location=arms[0].location)

    def sequence(self, close):
        args = []
        if self.peek() != close:
            args.append(self.union())
            while self.peek() == ",":
                self.take()
                args.append(self.union())
        self.take(close)
        return args

    def term(self):
        location = self.tokens[self.pos][1] if self.peek() else "EOF"
        if self.peek() == "(":
            self.take()
            result = self.union()
            self.take(")")
            return result
        if self.peek() == "[":
            self.take()
            return self.node("tuple", args=self.sequence("]"), location=location)
        if self.peek() == "{":
            self.take()
            fields = []
            while self.peek() != "}":
                key = self.take_identifier()
                if key in [k for k, _ in fields]:
                    raise InputError("duplicate record field " + key)
                self.take(":")
                fields.append((key, self.union()))
                if self.peek() != ",":
                    break
                self.take()
            self.take("}")
            return self.node("record", fields=fields, location=location)
        name = self.take_identifier()
        if name in ("Array", "Hash"):
            self.take("[")
            args = self.sequence("]")
            if len(args) != (1 if name == "Array" else 2):
                raise InputError("wrong arity for " + name)
            return self.node(name, args=args, location=location)
        return self.node("atom" if name in ATOMS else "alias", name=name, location=location)

    def _guarded(self):
        def unguarded(node):
            if node.kind == "alias":
                return {node.name}
            if node.kind == "union":
                return set().union(*(unguarded(a) for a in node.args))
            return set()
        edges = {name: unguarded(body) for name, body in self.aliases.items()}
        done, active = set(), set()

        def visit(name):
            if name in active:
                raise InputError("unguarded alias cycle through " + name)
            if name in done:
                return
            active.add(name)
            for target in sorted(edges[name]):
                visit(target)
            active.remove(name)
            done.add(name)
        for name in self.aliases:
            visit(name)

    def _features(self):
        def walk(node, alias):
            if node.kind == "union":
                for i, arm in enumerate(node.args):
                    key = ("union_arm", node.uid, i)
                    self.features[key] = {"kind": key[0], "alias": alias, "arm": i,
                                          "type": arm.text(), "location": arm.location}
            for child in node.args:
                walk(child, alias)
            for _, child in node.fields:
                walk(child, alias)
        for name, body in self.aliases.items():
            arms = body.args if body.kind == "union" else (body,)
            for i, arm in enumerate(arms):
                key = ("alias_production", name, i)
                self.features[key] = {"kind": key[0], "alias": name, "arm": i,
                                      "type": arm.text(), "location": arm.location}
            walk(body, name)


class ValueGraph:
    """One immutable snapshot; ids have scope within this snapshot only."""
    def __init__(self, root):
        self.nodes = {}
        refs = []
        pending = [root]
        while pending:
            node = pending.pop()
            if not isinstance(node, dict):
                raise InputError("tagged value must be an object")
            if "ref" in node:
                if set(node) != {"ref"} or type(node["ref"]) is not int or node["ref"] < 0:
                    raise InputError("invalid reference")
                refs.append(node["ref"])
                continue
            vid, tag = node.get("id"), node.get("tag")
            if type(vid) is not int or vid < 0 or vid in self.nodes or not isinstance(tag, str) or tag not in TAGS:
                raise InputError("invalid/duplicate value id or unsupported tag")
            self.nodes[vid] = node
            if tag == "Array":
                if not isinstance(node.get("items"), list):
                    raise InputError("Array needs items")
                pending.extend(node["items"])
            elif tag == "Hash":
                if not isinstance(node.get("entries"), list):
                    raise InputError("Hash needs entries")
                for entry in node["entries"]:
                    if not isinstance(entry, dict) or set(entry) != {"key", "value"}:
                        raise InputError("Hash entry needs key and value")
                    pending.extend((entry["key"], entry["value"]))
            elif tag == "Integer" and type(node.get("value")) is not int:
                raise InputError("Integer needs an integer payload")
            elif tag == "Float":
                value = node.get("value")
                if type(value) not in (int, float) and value not in ("NaN", "Infinity", "-Infinity"):
                    raise InputError("Float needs a number or tagged nonfinite payload")
            elif tag in ("String", "Symbol"):
                if not isinstance(node.get("value"), str):
                    if tag != "String" or not isinstance(node.get("bytes"), str):
                        raise InputError(tag + " needs a string payload")
                    try:
                        base64.b64decode(node["bytes"], validate=True)
                    except ValueError:
                        raise InputError("invalid String bytes")
        if not self.nodes or any(ref not in self.nodes for ref in refs):
            raise InputError("empty value or dangling reference")
        self.root = self.vid(root)

    @staticmethod
    def vid(node):
        return node["ref"] if "ref" in node else node["id"]

    def value_path(self, key, index):
        node = self.nodes[self.vid(key)]
        if node["tag"] == "String" and "value" in node:
            return "[" + json.dumps(node["value"], ensure_ascii=False) + "]"
        if node["tag"] == "Symbol":
            return "[:" + node["value"] + "]"
        return "[entry:%d]" % index


@dataclass
class Equation:
    vid: int
    ty: Type
    op: str
    deps: list
    constant: bool = True
    reason: str = ""


class Membership:
    def __init__(self, grammar, graph, alias):
        if alias not in grammar.aliases:
            raise InputError("unknown root alias " + alias)
        self.grammar, self.graph = grammar, graph
        self.equations, self.values, self.covered = {}, {}, set()
        self.root = self._key(graph.root, Type(-1, "alias", name=alias))
        pending = deque([(graph.root, Type(-1, "alias", name=alias))])
        while pending:
            vid, ty = pending.popleft()
            key = self._key(vid, ty)
            if key in self.equations:
                continue
            eq = self._equation(vid, ty)
            self.equations[key] = eq
            pending.extend((child_vid, child_ty) for child_vid, child_ty, _ in eq.deps)
        self._solve()
        self._coverage()

    @staticmethod
    def _key(vid, ty):
        # All references to a given alias use exactly (value id, alias name).
        return (vid, ty.name if ty.kind == "alias" else ty.uid)

    def _equation(self, vid, ty):
        node, kind = self.graph.nodes[vid], ty.kind
        tag = node["tag"]
        deps, op, valid, reason = [], "and", True, ""
        if kind == "alias":
            deps = [(vid, self.grammar.aliases[ty.name], "")]
        elif kind == "union":
            op, deps = "or", [(vid, arm, "") for arm in ty.args]
        elif kind == "atom":
            valid = ty.name == "untyped" or tag == ty.name or (ty.name == "bool" and tag in ("true", "false"))
        elif kind in ("Array", "tuple"):
            valid = tag == "Array"
            if valid and kind == "tuple" and len(node["items"]) != len(ty.args):
                valid, reason = False, "tuple length %d, expected %d" % (len(node["items"]), len(ty.args))
            if valid:
                deps = [(self.graph.vid(v), ty.args[i] if kind == "tuple" else ty.args[0], "[%d]" % i)
                        for i, v in enumerate(node["items"])]
        elif kind in ("Hash", "record"):
            valid = tag == "Hash"
            if valid and kind == "Hash":
                for i, entry in enumerate(node["entries"]):
                    deps.extend(((self.graph.vid(entry["key"]), ty.args[0], ".keys[%d]" % i),
                                 (self.graph.vid(entry["value"]), ty.args[1], self.graph.value_path(entry["key"], i))))
            elif valid:
                fields = {}
                for entry in node["entries"]:
                    key = self.graph.nodes[self.graph.vid(entry["key"])]
                    if key["tag"] == "Symbol":
                        fields[key["value"]] = self.graph.vid(entry["value"])
                missing = [name for name, _ in ty.fields if name not in fields]
                if missing:
                    valid, reason = False, "missing Symbol key :" + missing[0]
                else:
                    deps = [(fields[name], child, "[:" + name + "]") for name, child in ty.fields]
        return Equation(vid, ty, op, deps, valid, reason or "tag %s does not match %s" % (tag, ty.text()))

    def _solve(self):
        # Start at true and remove obligations with a finite refutation.
        # Work is bounded by the finite value/type product, even for cycles.
        parents = {key: set() for key in self.equations}
        failed = deque()
        for key, eq in self.equations.items():
            self.values[key] = eq.constant
            if not eq.constant:
                failed.append(key)
            for vid, ty, _ in eq.deps:
                parents[self._key(vid, ty)].add(key)
        while failed:
            for parent in parents[failed.popleft()]:
                if not self.values[parent]:
                    continue
                eq = self.equations[parent]
                children = [self.values[self._key(vid, ty)] for vid, ty, _ in eq.deps]
                valid = all(children) if eq.op == "and" else any(children)
                if not valid:
                    self.values[parent] = False
                    failed.append(parent)

    @property
    def accepted(self):
        return self.values[self.root]

    def _coverage(self):
        # Every successful obligation is a witness on a value or sub-value.
        # All matching union alternatives count, including overlapping arms.
        for eq in self.equations.values():
            ty = eq.ty
            if ty.kind == "union":
                for i, arm in enumerate(ty.args):
                    if self.values[self._key(eq.vid, arm)]:
                        self.covered.add(("union_arm", ty.uid, i))
            elif ty.kind == "alias":
                body = self.grammar.aliases[ty.name]
                arms = body.args if body.kind == "union" else (body,)
                for i, arm in enumerate(arms):
                    if self.values[self._key(eq.vid, arm)]:
                        self.covered.add(("alias_production", ty.name, i))

    def failure(self):
        def explain(key, active):
            if key in active:
                return None
            eq = self.equations[key]
            choices = []
            for vid, ty, step in eq.deps:
                child = self._key(vid, ty)
                if not self.values[child]:
                    result = explain(child, active | {key})
                    if result is not None:
                        path, expected, actual, reason, depth = result
                        choices.append((step + path, expected, actual, reason, depth + bool(step)))
            if choices:
                best = max(choices, key=lambda r: r[4])
                if eq.ty.kind != "union" or best[4]:
                    return best
            return ("", eq.ty.text(), self.graph.nodes[eq.vid]["tag"],
                    "no union arm matches" if eq.ty.kind == "union" else eq.reason, 0)
        path, expected, actual, reason, _ = explain(self.root, set())
        return {"path": "$" + path, "expected": expected, "actual": actual, "reason": reason}


def check_records(grammar, records, slots):
    if not slots or any(alias not in grammar.aliases for alias in slots.values()):
        raise InputError("slot bindings must name declared aliases")
    counts, violations, covered, total = {slot: 0 for slot in slots}, [], set(), 0
    for line, record in records:
        slot = record.get("slot")
        if slot not in slots:
            raise InputError("unbound slot at line %d: %r" % (line, slot))
        graph = ValueGraph(record.get("value"))
        membership = Membership(grammar, graph, slots[slot])
        counts[slot] += 1
        total += 1
        covered.update(membership.covered)
        if not membership.accepted:
            violations.append(dict(membership.failure(), slot=slot, record_line=line))
    if not total or any(count == 0 for count in counts.values()):
        raise InputError("empty trace or unobserved bound slot")
    features = [dict(feature, exercised=key in covered) for key, feature in grammar.features.items()]
    return {"sound": not violations, "records": total, "accepted": total - len(violations),
            "slots": counts, "violations": violations,
            "tightness": {"exercised": sum(f["exercised"] for f in features), "total": len(features),
                          "unexercised": [f for f in features if not f["exercised"]],
                          "meaning": "candidate over-approximations; finite samples cannot prove exactness"}}


def load_records(path):
    records, meta, complete = [], False, False
    with open(path, encoding="utf-8") as stream:
        for line, text in enumerate(stream, 1):
            try:
                record = json.loads(text)
            except ValueError as error:
                raise InputError("bad JSON at line %d: %s" % (line, error))
            if not isinstance(record, dict) or complete:
                raise InputError("invalid record or data after completion at line %d" % line)
            kind = record.get("kind")
            if kind == "meta" and line == 1 and record.get("format") == "shape-oracle/v1":
                meta = True
            elif kind == "value" and meta:
                records.append((line, record))
            elif kind == "complete" and meta:
                if record.get("records") != len(records):
                    raise InputError("completion record count disagrees with trace")
                complete = True
            elif kind == "error":
                raise InputError("recorder failed: " + str(record.get("message")))
            else:
                raise InputError("invalid trace record at line %d" % line)
    if not meta or not complete:
        raise InputError("incomplete trace (needs metadata and completion)")
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    parser.add_argument("types", type=Path)
    parser.add_argument("--slots", type=Path, help="JSON object mapping recorded slot names to aliases")
    parser.add_argument("--slot", action="append", default=[], metavar="SLOT=ALIAS")
    parser.add_argument("--json", action="store_true", help="complete machine-readable report")
    parser.add_argument("--max-errors", type=int, default=20, help="text witness limit (JSON reports all)")
    args = parser.parse_args(argv)
    try:
        grammar = Grammar(args.types.read_text(encoding="utf-8"))
        slots = json.loads(args.slots.read_text(encoding="utf-8")) if args.slots else {}
        if not isinstance(slots, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in slots.items()):
            raise InputError("slots must be a JSON object of strings")
        for binding in args.slot:
            if "=" not in binding:
                raise InputError("slot binding must be SLOT=ALIAS")
            slot, alias = binding.split("=", 1)
            if slot in slots and slots[slot] != alias:
                raise InputError("conflicting binding for " + slot)
            slots[slot] = alias
        report = check_records(grammar, load_records(args.records), slots)
    except (OSError, ValueError, RecursionError) as error:
        print("check: " + str(error), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("%s: %d/%d slot values accepted" % ("SOUND" if report["sound"] else "UNSOUND", report["accepted"], report["records"]))
        for slot, count in report["slots"].items():
            print("  %s: %d values" % (slot, count))
        for violation in report["violations"][:max(0, args.max_errors)]:
            print("  line {record_line} {slot} {path}: {actual}, expected {expected} ({reason})".format(**violation))
        omitted = len(report["violations"]) - max(0, args.max_errors)
        if omitted > 0:
            print("  %d more violations; use --json for all witnesses" % omitted)
        for feature in report["tightness"]["unexercised"]:
            print("  UNEXERCISED {kind}: {alias} arm {arm} = {type} at {location}".format(**feature))
        print("Tightness: %d/%d features exercised; missing features are candidates, not proof." %
              (report["tightness"]["exercised"], report["tightness"]["total"]))
    return 0 if report["sound"] else 1


if __name__ == "__main__":
    sys.exit(main())
