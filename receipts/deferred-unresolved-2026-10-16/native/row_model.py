#!/usr/bin/env python3
"""Row model for deferral-protocol: one value per (part, key) from the contributor-values.jsonl row observer.

A row is a component of one of the ten native tables. Typed parts carry a provenance-aware structured type,
`native_ty` (the RETURN_HELPERS branch's `current_returns::describe`), whose `untyped` leaves list their `reasons`; `ty` is the
same type without provenance. Structural parts carry sorted name lists, `names`.

- `ir`, `params`, `returns`, `side_table`, `controller_cache`: keyed as F59 keys them;
- `constants`, `attributes`, `block_values`, `copies`: keyed exactly as their native entries;
- `controller_bindings`: `Controller#action:binding:name`.

`load` returns, per row, (hash, note, detail): the reason-blind type hash the native fingerprint uses, the decision
note of an IR row, and a digest of the provenance-aware content. Values for variance (F59's definition) are
(hash, note). Each native per-entry fingerprint is kept as the row ("fp:<table>", entry), so an aggregate entry
can be checked against its components. Python 3.9, standard library only.
"""
import json
from collections import Counter
import native_hash
from pathlib import Path

TYPED = ("ir", "params", "returns", "side_table", "controller_cache", "constants", "attributes",
         "controller_bindings")
STRUCTURAL = ("block_values", "copies")
PARTS = TYPED + STRUCTURAL
TABLES = ("attributes", "block_values", "constants", "controller_bindings", "controller_cache", "copies", "ir",
          "params", "returns", "side_table")
# A native entry's component rows: the row with the same key, or rows whose key is the entry followed by a separator.
SEPARATOR = {"params": "[", "controller_cache": "#", "controller_bindings": ":"}
# Entries that must have at least one component row; a parameter vector or a binding map may be empty.
COVERED = ("attributes", "block_values", "constants", "controller_cache", "copies", "returns", "side_table")
UNRESOLVED = "Unresolved"
REASONS = "reasons"


def norm(t):
    """A canonical form of a structured type, with the native hash's set semantics: variable ids dropped, union variants
    sorted and deduplicated, a one-variant union collapsed to its variant; provenance reasons kept and sorted."""
    if isinstance(t, list):
        return [norm(x) for x in t]
    if not isinstance(t, dict):
        return t
    if t.get("kind") == "var":
        return {"kind": "var"}
    out = {k: norm(v) for k, v in t.items()}
    if t.get("kind") == "union" and isinstance(out.get("variants"), list):
        arms = {json.dumps(v, sort_keys=True): v for v in out["variants"]}
        out["variants"] = [arms[k] for k in sorted(arms)]
        if len(out["variants"]) == 1:
            return out["variants"][0]
    if t.get("kind") == "untyped" and isinstance(out.get(REASONS), list):
        out[REASONS] = sorted(out[REASONS])
    return out


def validate_type(t):
    """Reject malformed containers and every unavailable provenance leaf, even unchanged leaves."""
    if t is None:
        return
    if not isinstance(t, dict) or not isinstance(t.get("kind"), str):
        raise ValueError("malformed native type")
    kind = t["kind"]
    if kind == "untyped":
        reasons = t.get("reasons")
        if (not isinstance(reasons, list) or not reasons or
                not all(r in ("Gradual", "Unresolved", "Pending") for r in reasons)):
            raise ValueError("untyped leaf lacks valid provenance")
    fields = {"array": ("elem",), "hash": ("key", "value"), "fn": ("ret",)}
    for field in fields.get(kind, ()):
        if field not in t or t[field] is None:
            raise ValueError("missing native type component")
        validate_type(t[field])
    sequence = {"union": "variants", "tuple": "elems", "class": "args"}.get(kind)
    if sequence:
        if not isinstance(t.get(sequence), list) or (kind == "union" and not t[sequence]):
            raise ValueError("malformed native type vector")
        for x in t[sequence]:
            validate_type(x)
    if kind == "record":
        if not isinstance(t.get("row"), dict) or not isinstance(t["row"].get("fields"), dict):
            raise ValueError("malformed record")
        for x in t["row"]["fields"].values():
            validate_type(x)
    if kind == "fn":
        if not isinstance(t.get("params"), list):
            raise ValueError("malformed fn params")
        for x in t["params"]:
            validate_type(x["ty"])
        validate_type(t.get("block"))


def _blind_n(t):
    if isinstance(t, dict):
        return {k: _blind_n(v) for k, v in t.items() if k != "reasons"}
    if isinstance(t, list):
        return [_blind_n(v) for v in t]
    return t


def merge_equal(a, b):
    """Native equal-shape merge: union provenance recursively, without erasing evidence."""
    if isinstance(a, dict):
        return {k: sorted(set(a[k]) | set(b[k])) if k == "reasons" else merge_equal(a[k], b[k]) for k in a}
    if isinstance(a, list):
        return [merge_equal(x, y) for x, y in zip(a, b)]
    return a


def normalize_n(t):
    if isinstance(t, list):
        return [normalize_n(x) for x in t]
    if not isinstance(t, dict):
        return t
    out = {k: normalize_n(v) for k, v in t.items()}
    if out.get("kind") == "union":
        groups = {}
        for arm in out["variants"]:
            key = json.dumps(norm(_blind_n(arm)), sort_keys=True)
            groups[key] = merge_equal(groups[key], arm) if key in groups else arm
        out["variants"] = [groups[k] for k in sorted(groups)]
    return norm(out)


def detail_of(d):
    """The provenance-aware content of one row line, as the reducer compares it."""
    ty = d["native_ty"] if "native_ty" in d else d.get("ty")
    return {"ty": norm(ty), "names": d.get("names"), "diagnostic": d.get("diagnostic"), "decisions": d.get("decisions")}


def _digest(detail):
    return hash(json.dumps(detail, sort_keys=True))


def load(path):
    """({(part, key): (hash, note, detail digest)}, fingerprint parts, digests) for one row dump; ValueError if malformed."""
    rows, fingerprint, digests = {}, None, None
    raw, header = {}, None
    with Path(path).open() as stream:
        for line in stream:
            d = json.loads(line)
            if not isinstance(d, dict):
                raise ValueError("row line is not an object: " + str(path))
            part = d.get("part")
            if part == "fingerprint":
                if fingerprint is not None:
                    raise ValueError("two fingerprint lines: " + str(path))
                fingerprint, digests = d.get("parts"), d.get("digests")
                header = d
                continue
            if part not in PARTS:
                continue
            key, h = d.get("key"), d.get("hash")
            if not isinstance(key, str) or type(h) is not int:
                raise ValueError("malformed row in " + str(path))
            ident = (part, key)
            if ident in rows:
                raise ValueError("duplicate row identity " + repr(ident)[:120])
            if part in TYPED:
                if "native_ty" not in d and not d.get("empty_cache"):
                    raise ValueError("missing native_ty")
                validate_type(d.get("native_ty"))
            elif not isinstance(d.get("names"), dict):
                raise ValueError("missing structural names")
            raw[ident] = d
            note = d.get("note")
            rows[ident] = (h, note if type(note) is int else None, _digest(detail_of(d)))
    if not isinstance(fingerprint, dict):
        raise ValueError("row dump has no fingerprint line: " + str(path))
    if set(fingerprint) != set(TABLES) - {"ir"}:
        raise ValueError("fingerprint table inventory")
    if not isinstance(digests, dict) or set(digests) != set(TABLES):
        raise ValueError("digest inventory")
    ir = sorted([d["span"]["file"], d["span"]["start"], d["span"]["end"], d["hash"], d["note"]]
                for (part, _), d in raw.items() if part == "ir")
    if ir != header.get("ir"):
        raise ValueError("IR multiset incomplete")
    inventory = header.get("components")
    if not isinstance(inventory, dict):
        raise ValueError("missing explicit aggregate component inventory")
    for table in ("params", "controller_bindings", "controller_cache"):
        entries = inventory.get(table)
        if not isinstance(entries, dict) or set(entries) != set(fingerprint[table]):
            raise ValueError("aggregate entry inventory " + table)
        claimed = []
        for entry, keys in entries.items():
            if not isinstance(keys, list) or not all(isinstance(k, str) and is_component(table, entry, k) for k in keys):
                raise ValueError("malformed aggregate components")
            claimed += keys
        if Counter(claimed) != Counter(k for part, k in raw if part == table):
            raise ValueError("aggregate components omitted or extra " + table)
    for table in ("attributes", "constants", "returns", "side_table", "block_values", "copies"):
        if {k: d["hash"] for (part, k), d in raw.items() if part == table} != fingerprint[table]:
            raise ValueError("table coverage/hash mismatch " + table)
    native_hash.reconcile(raw, header)
    for table, entries in fingerprint.items():
        if not isinstance(entries, dict):
            raise ValueError("malformed fingerprint table " + str(table))
        for entry, value in entries.items():
            rows[("fp:" + table, entry)] = (value, None, None)
    return rows, fingerprint, digests


def load_details(path, wanted):
    """{(part, key): detail} for the wanted row identities of one row dump."""
    out, wanted = {}, set(wanted)
    with Path(path).open() as stream:
        for line in stream:
            d = json.loads(line)
            ident = (d.get("part"), d.get("key")) if isinstance(d, dict) else None
            if ident in wanted:
                out[ident] = detail_of(d)
    return out


def value(row):
    """F59's value of a row: (hash, note), or None when absent."""
    return None if row is None else row[:2]


def is_component(table, entry, key):
    sep = SEPARATOR.get(table)
    return key == entry if sep is None else key.startswith(entry + sep)


def components(rows, table, entry):
    return [k for k in rows if k[0] == table and is_component(table, entry, k[1])]


def coverage_gaps(rows, fingerprint):
    """Native entries of covered tables with no component row: the dump cannot classify a change to them."""
    by_table = {}
    for part, key in rows:
        if part in PARTS:
            by_table.setdefault(part, []).append(key)
    gaps = []
    for table in COVERED:
        keys = by_table.get(table, [])
        exact = set(keys)
        for entry in (fingerprint.get(table) or {}):
            sep = SEPARATOR.get(table)
            if (entry not in exact) if sep is None else not any(k.startswith(entry + sep) for k in keys):
                gaps.append((table, entry))
    missing = [t for t in TABLES if t != "ir" and t not in fingerprint]
    return gaps + [(t, "<table missing>") for t in missing]


def relation(ds, c, ndedup=False):
    """How type `ds` stands to type `c`: 'equal', 'removal' (only Unresolved removed), 'violation' or 'unknown'.

    A removal drops a union variant whose provenance is exactly Unresolved, or drops Unresolved from a leaf that keeps
    another reason. Gradual and Pending evidence must stay. A leaf without `reasons` cannot be classified: 'unknown'.
    """
    try:
        validate_type(ds)
        validate_type(c)
    except (ValueError, TypeError, KeyError):
        return "unknown"
    if ndedup:
        ds, c = normalize_n(ds), normalize_n(c)
    ds, c = norm(ds), norm(c)
    if ds == c:
        return "unknown" if _has_untyped_without_reasons(c) else "equal"
    if isinstance(c, dict) and c.get("kind") == "untyped":
        if not isinstance(ds, dict) or ds.get("kind") != "untyped":
            return "violation"
        cw, dw = c.get(REASONS), ds.get(REASONS)
        if not isinstance(cw, list) or not isinstance(dw, list):
            return "unknown"
        if UNRESOLVED in cw and dw and sorted(set(cw) - {UNRESOLVED}) == sorted(dw):
            return "removal"
        return "violation"
    if isinstance(c, dict) and c.get("kind") == "union":
        arms = list(c.get("variants") or [])
        kept = list(ds.get("variants") or []) if isinstance(ds, dict) and ds.get("kind") == "union" else [ds]
        used, results = [False] * len(arms), []
        for d in kept:
            j = next((i for i, a in enumerate(arms) if not used[i] and a == d), None)
            if j is not None:
                results.append("unknown" if _has_untyped_without_reasons(d) else "equal")
            else:
                scored = [(i, relation(d, a)) for i, a in enumerate(arms) if not used[i]]
                j, r = next(((i, r) for i, r in scored if r == "removal"), next(((i, r) for i, r in scored
                                                                                 if r == "unknown"), (None, None)))
                if j is None:
                    return "violation"
                results.append(r)
            used[j] = True
        for i, a in enumerate(arms):
            if used[i]:
                continue
            if not (isinstance(a, dict) and a.get("kind") == "untyped"):
                return "violation"
            if not isinstance(a.get(REASONS), list):
                results.append("unknown")
            elif a[REASONS] == [UNRESOLVED]:
                results.append("removal")
            else:
                return "violation"
        return _combine(results)
    if not (isinstance(ds, dict) and isinstance(c, dict)) or ds.get("kind") != c.get("kind") or set(ds) != set(c):
        return "violation"
    results = []
    for name, b in c.items():
        a = ds[name]
        if isinstance(b, dict):
            results.append(relation(a, b))
        elif isinstance(b, list):
            if not isinstance(a, list) or len(a) != len(b):
                return "violation"
            results += [relation(x, y) if isinstance(y, dict) else ("equal" if x == y else "violation")
                        for x, y in zip(a, b)]
        elif a != b:
            return "violation"
    return _combine(results)


def _combine(results):
    if "unknown" in results:
        return "unknown"
    if "violation" in results:
        return "violation"
    return "removal" if "removal" in results else "equal"


def _has_untyped_without_reasons(t):
    if isinstance(t, dict):
        if t.get("kind") == "untyped" and not isinstance(t.get(REASONS), list):
            return True
        return any(_has_untyped_without_reasons(v) for v in t.values())
    if isinstance(t, list):
        return any(_has_untyped_without_reasons(v) for v in t)
    return False


def varying(cells):
    """Rows whose F59 value (hash, note) or presence differs among the given schedule cells (schedule -> rows)."""
    keys = set().union(*(set(r) for r in cells.values()))
    out = {}
    for k in keys:
        values = [value(r.get(k)) for r in cells.values()]
        if any(v != values[0] for v in values):
            out[k] = values
    return out


def table_of(ident):
    part = ident[0]
    return part[3:] if part.startswith("fp:") else part
