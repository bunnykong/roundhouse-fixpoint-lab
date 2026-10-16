VAR_TOP = True

def top(t):
    k = t.get("kind") if isinstance(t, dict) else None
    if k == "untyped":
        return True
    if k == "var":
        return VAR_TOP
    if k == "union":
        return any(top(v) for v in t["variants"])
    return False


def empty(t):
    k = t.get("kind")
    if k == "bottom":
        return True
    if k == "var":
        return not VAR_TOP
    if k == "union":
        return all(empty(v) for v in t["variants"])
    return False


def arms(t):
    if t.get("kind") == "union":
        out = []
        for v in t["variants"]:
            out.extend(arms(v))
        return out
    return [t]


def covers(a, b):
    """The values `a` admits include every value `b` admits. Raises KeyError on an unresolved reference."""
    if empty(b) or top(a):
        return True
    if b.get("kind") == "rec" or a.get("kind") == "rec":
        raise KeyError("unresolved reference")
    if b.get("kind") == "union":
        return all(covers(a, v) for v in b["variants"] if not empty(v))
    if top(b):
        return False
    return any(covers1(x, b) for x in arms(a) if not empty(x))


def covers1(a, b):
    ka, kb = a.get("kind"), b.get("kind")
    if top(a):
        return True
    if ka == "rec" or kb == "rec":
        raise KeyError("unresolved reference")
    if ka != kb:
        return False
    if ka == "class":
        aa, ba = a.get("args") or [], b.get("args") or []
        return a.get("id") == b.get("id") and len(aa) == len(ba) and all(covers(x, y) for x, y in zip(aa, ba))
    if ka == "array":
        return covers(a["elem"], b["elem"])
    if ka == "hash":
        return covers(a["key"], b["key"]) and covers(a["value"], b["value"])
    if ka == "tuple":
        ea, eb = a.get("elems") or [], b.get("elems") or []
        return len(ea) == len(eb) and all(covers(x, y) for x, y in zip(ea, eb))
    if ka == "fn":
        return covers(a.get("ret") or {"kind": "untyped"}, b.get("ret") or {"kind": "untyped"})
    if ka in ("nil", "str", "sym", "bool", "int", "float", "date", "time", "self_instance"):
        return True
    return a == b  # records, relations and anything new: only identical shapes cover


def relation(control, join):
    """Relation of the join variant to the control at one row: EQ, WIDEN, NARROW, INCOMP or STRUCT."""
    if control is None or join is None:
        return "STRUCT"
    up, down = covers(join, control), covers(control, join)
    if up and down:
        return "EQ"
    if up:
        return "WIDEN"
    return "NARROW" if down else "INCOMP"
