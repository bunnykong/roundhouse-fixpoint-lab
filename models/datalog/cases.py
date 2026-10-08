"""Hand-lowered public sources and the five actual witness-model lambdas.

f2_merge: built-in sort/to_h/map semantics, no monkey patches, generic Hash key
and value summaries; sort order is irrelevant to the inferred read types.
argument-tree: Integer depth is abstract (the literal 3 is intentionally lost).
reembed: ordinary may-flow graph plus explicit nil-[] diagnostic; required records.
"""
from model import Program


def subset_equations(length):
    """Compact equations whose eager determinization has 2**length states."""
    from baselines import m1
    def union(*parts):
        return ("union", parts)
    eqs = {"Q0": lambda s: union(m1.arr(s["Q0"]), m1.hsh(m1.STR, s["Q0"]),
                                 m1.hsh(m1.STR, s["Q1"]))}
    for i in range(1, length):
        eqs["Q%d" % i] = lambda s, j=i + 1: union(m1.arr(s["Q%d" % j]), m1.hsh(m1.STR, s["Q%d" % j]))
    eqs["Q%d" % length] = lambda s: m1.INT
    return eqs
from baselines import m1, extra_equations


def from_equations(name, equations):
    p = Program(name)
    refs = {key: p.slot(key) for key in equations}

    def lower(term, dst, path):
        tag = term[0]
        if tag == "slot":
            p.flow(refs[term[1]], dst)
        elif tag == "union":
            for i, arm in enumerate(term[1]):
                lower(arm, dst, path + "/u%d" % i)
        elif tag in ("array", "hash"):
            fields = ("elem",) if tag == "array" else ("key", "value")
            childslots = {}
            for field, child in zip(fields, term[1:]):
                childslots[field] = p.slot(path + "/" + field)
                lower(child, childslots[field], path + "/" + field)
            p.construct(dst, "site:" + path, tag, childslots)
        else:
            p.literal(dst, {"untyped": "model_u", "var": "model_var"}.get(tag, tag))
    symbolic = {key: ("slot", key) for key in refs}
    for key, fn in equations.items():
        lower(fn(symbolic), refs[key], key)
        p.roots[key.lower()] = key
    return p


def witness(name):
    return from_equations(name, m1.CASES[name][0])


def argument_tree():
    return from_equations("argument_tree", extra_equations("argument_tree")[0])


def chain(length=64):
    return from_equations("chain%d" % length, extra_equations("chain", length)[0])


def reembed(safe=False):
    p = Program("reembed_safe" if safe else "reembed")
    p.literal("R", "nil")
    p.construct("R", "outer", "record_a", {"a": "inner_result"})
    p.construct("inner_result", "inner", "record_b", {"b": "projection"})
    p.fact("Load", "R", "a", p.slot("projection"))
    if safe:
        # Ruby safe navigation, f(n-1)&.[](:a), returns nil on nil.
        p.fact("Filter", "R", "nil", "projection")
    else:
        p.fact("Use", "recursive_index", "R", "[]")
        p.fact("Unsupported", "[]", "nil")
    p.roots = {"r": "R", "b": "inner_result"}
    return p


def f2_merge(mode="mono", heap_context=True):
    p = Program("f2_merge/" + mode + ("" if heap_context else "/shared_heap"))
    heads = ("hash", "array", "str", "int", "nil")
    calls = ("inner_call", "outer_call", "hash_value_call", "array_value_call")
    if mode == "mono":
        contexts = ("all",)
        select = lambda call, head: "all"
    elif mode == "receiver_type":
        contexts = ("TreesController",)
        select = lambda call, head: "TreesController"
    elif mode == "call1":
        contexts = calls
        select = lambda call, head: call
    elif mode == "arg_head":
        contexts = heads
        select = lambda call, head: head
    else:
        raise ValueError(mode)
    for call in calls:
        for head in heads:
            p.fact("Select", call, head, select(call, head))
    for ctx in contexts:
        param, ret = p.slot(ctx + "/P"), p.slot(ctx + "/R")
        p.fact("Formal", ctx, param)
        p.fact("Return", ctx, ret)
        hrecv, arecv = p.slot(ctx + "/hash_recv"), p.slot(ctx + "/array_recv")
        p.fact("Filter", param, "hash", hrecv)
        p.fact("Filter", param, "array", arecv)
        key, val, elem = (p.slot(ctx + "/" + n) for n in ("block_k", "block_v", "block_elem"))
        p.fact("Load", hrecv, "key", key)
        p.fact("Load", hrecv, "value", val)
        p.fact("Load", arecv, "elem", elem)
        hret, aret, strkey = (p.slot(ctx + "/" + n) for n in ("hash_block_ret", "array_block_ret", "strkey"))
        p.fact("ToString", key, strkey)
        p.fact("Invoke", "hash_value_call", val, hret)
        p.fact("Invoke", "array_value_call", elem, aret)
        heap = ctx if heap_context else "shared"
        hs = p.construct(ret, heap + "/to_h", "hash", {"key": strkey, "value": hret}, False)
        ars = p.construct(ret, heap + "/map", "array", {"elem": aret}, False)
        p.fact("Produce", param, "hash", ret, hs)
        p.fact("Produce", param, "array", ret, ars)
        for kind in ("str", "int", "nil"):
            p.fact("Filter", param, kind, ret)

    # canonical({ "b" => [1, "x"] })
    p.literal("keys", "str")
    p.literal("one_and_x", "int")
    p.literal("one_and_x", "str")
    p.literal("two", "int")
    p.literal("nil", "nil")
    p.construct("input_array", "input_array_site", "array", {"elem": "one_and_x"})
    p.construct("input_hash", "input_hash_site", "hash", {"key": "keys", "value": "input_array"})
    p.fact("Invoke", "inner_call", "input_hash", p.slot("inner"))
    # Two fresh merge results. Unknown String keys use weak (union) copying.
    for tag, rhs in (("d", "two"), ("e", "nil")):
        arg = "merge_arg_" + tag
        p.construct(arg, "literal_" + tag, "hash", {"key": "keys", "value": rhs})
        dest, site = p.slot("merged_" + tag), "merge_site_" + tag
        p.site(site, "hash", ("key", "value"))
        p.fact("Merge", "inner", arg, dest, site)
        p.fact("Use", "merge_" + tag, "inner", "merge")
    for kind in heads:
        if kind != "hash":
            p.fact("Unsupported", "merge", kind)
    p.construct("outer_array", "outer_array_site", "array", {"elem": "merged_e"})
    p.flow("merged_d", "outer_values")
    p.flow("outer_array", "outer_values")
    p.construct("outer_hash", "outer_hash_site", "hash", {"key": "keys", "value": "outer_values"})
    p.fact("Invoke", "outer_call", "outer_hash", p.slot("tree"))
    p.roots = {"inner": "inner", "tree": "tree"}
    return p


def acyclic_site_pollution():
    """idbox(x)=[x]; idbox(1); idbox("s"), one shared allocation site.

    A pure input-sensitive equation summary has separate caller instantiations;
    one allocation site without heap contexts admits String at the first call.
    No program recursion is involved.
    """
    p = Program("acyclic_shared_site")
    p.literal("i", "int")
    p.literal("s", "str")
    p.construct("first", "box", "array", {"elem": "i"})
    p.construct("second", "box", "array", {"elem": "s"})
    p.roots = {"first": "first", "second": "second"}
    return p
