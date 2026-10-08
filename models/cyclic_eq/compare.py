"""HKC and antichains for regular's spine-join regular types (Python 3.9+).

Array/Hash choices merge child sets pointwise. Tuple/Record choices retain
correlations and use a greatest-fixed-point AND/OR game when branching.
Observations include constructor heads, so unproductive guarded cycles remain
distinct from bottom, as in fold_model.canonicalize. Bottom is rigid for covers.
No eager powerset construction or recursive Python graph traversal is used.
"""
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from time import perf_counter


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def children(node):
    if node[0] == "leaf":
        return ()
    if node[0] == "array":
        return (node[1],)
    if node[0] == "hash":
        return node[1:]
    if node[0] == "record":
        return tuple(c for _, c in node[1])
    return tuple(node[1])


def head(node):
    kind = node[0]
    if kind == "leaf":
        return (kind, node[1])
    if kind == "tuple":
        return (kind, len(node[1]))
    if kind == "record":
        return (kind, tuple(k for k, _ in node[1]))
    return (kind,)


def remap(node, offset):
    kind = node[0]
    if kind == "leaf":
        return node
    if kind == "array":
        return (kind, node[1] + offset)
    if kind == "hash":
        return (kind, node[1] + offset, node[2] + offset)
    if kind == "record":
        return (kind, tuple((k, c + offset) for k, c in node[1]))
    return (kind, tuple(c + offset for c in node[1]))


@dataclass(frozen=True)
class Automaton:
    """Immutable indexed nodes; root may be any index. Records have exact keys.

    Nodes: ('leaf', tag), ('array', child), ('hash', key, value),
    ('tuple', children), ('record', ((key, child), ...)), ('union', children).
    leaf 'widened' is top; union-only cycles and leaf 'bot' flatten to bottom.
    """
    nodes: tuple
    root: int = 0

    def __post_init__(self):
        normalized = []
        for node in self.nodes:
            if node[0] not in ("leaf", "array", "hash", "tuple", "record", "union"):
                raise ValueError("unsupported node: %r" % (node,))
            kind = node[0]
            if kind == "record":
                fields = tuple(sorted(node[1]))
                if len({k for k, _ in fields}) != len(fields):
                    raise ValueError("duplicate record key")
                node = (kind, fields)
            elif kind in ("tuple", "union"):
                node = (kind, tuple(node[1]))
            else:
                node = tuple(node)
            normalized.append(node)
        object.__setattr__(self, "nodes", tuple(normalized))
        if not 0 <= self.root < len(self.nodes):
            raise ValueError("invalid root")
        for node in self.nodes:
            if any(not isinstance(c, int) or not 0 <= c < len(self.nodes) for c in children(node)):
                raise ValueError("invalid child")
            if node[0] == "leaf":
                hash(node[1])

    @classmethod
    def from_reg(cls, reg):
        return cls(tuple(reg.nodes))


@dataclass
class Comparison:
    holds: object                 # bool, or None when a resource budget is hit
    method: str
    stats: dict
    elapsed_ms: float
    reason: str = ""
    witness: object = None


class Exhausted(Exception):
    pass


class Branching(Exception):
    pass


class Session:
    def __init__(self, left, right, budget, seconds, bottom=()):
        self.started = perf_counter()
        self.deadline = None if seconds is None else self.started + seconds
        self.budget = budget
        self.bottom = frozenset(bottom)
        self.stats = Counter()
        self.nodes = left.nodes + tuple(remap(n, len(left.nodes)) for n in right.nodes)
        self.top = 1 << len(self.nodes)  # a single shared absorbing atom
        self.closures, self.observations = {}, {}
        self.observed_masks = set()
        self.left = self.normalize(1 << left.root)
        self.right = self.normalize(1 << (len(left.nodes) + right.root))
        self.stats["preprocess_ms"] = (perf_counter() - self.started) * 1000

    def check(self, amount=1):
        self.stats["work_units"] += amount
        if self.budget is not None and self.stats["work_units"] > self.budget:
            raise Exhausted("work budget")
        if self.deadline is not None and perf_counter() > self.deadline:
            raise Exhausted("time budget")

    def closure(self, state):
        if state in self.closures:
            return self.closures[state]
        todo, seen, mask = [state], set(), 0
        while todo:
            s = todo.pop()
            if s in seen:
                continue
            seen.add(s)
            self.check()
            self.stats["epsilon_visits"] += 1
            n = self.nodes[s]
            if n[0] == "union":
                todo.extend(n[1])
            elif n == ("leaf", "widened"):
                mask = self.top
                break
            elif n != ("leaf", "bot"):
                mask |= 1 << s
        self.closures[state] = mask
        return mask

    def normalize(self, mask):
        if mask & self.top:
            return self.top
        out = 0
        for s in bits(mask):
            out |= self.closure(s)
            if out & self.top:
                return self.top
        return out

    def observe(self, mask, raw=False):
        key = (mask, raw)
        if key in self.observations:
            return self.observations[key]
        self.check()
        self.stats["observations"] += 1
        groups = defaultdict(list)
        if mask == self.top:
            groups[("leaf", "widened")].append(())
        for s in bits(mask if mask != self.top else 0):
            n = self.nodes[s]
            cs = tuple(self.normalize(1 << c) for c in children(n))
            groups[head(n)].append(cs)
        if not raw:
            for h, alternatives in list(groups.items()):
                if h[0] in ("array", "hash"):
                    merged = []
                    for col in zip(*alternatives):
                        m = 0
                        for c in col:
                            m |= c
                        merged.append(self.top if m & self.top else m)
                    groups[h] = [tuple(merged)]
        out = {h: tuple(sorted(set(alts))) for h, alts in groups.items()}
        self.observations[key] = out
        self.observed_masks.add(mask)
        self.stats["subset_states"] = len(self.observed_masks)
        return out

    def finish(self, holds, method, reason=""):
        return Comparison(holds, method, dict(self.stats), (perf_counter() - self.started) * 1000, reason)

    def ignore_leaf(self, label):
        if label[0] != "leaf":
            return False
        tag = label[1]
        return tag in self.bottom or ("cut" in self.bottom and
                                      (tag == "cut" or isinstance(tag, tuple) and tag[0] == "cut"))


class Congruence:
    """Union-find over subset terms PLUS Horn closure under union contexts.

    Plain UF is insufficient: X=Y must imply X|Z=Y|Z. Each equation
    contributes X -> X|Y and Y -> X|Y. Saturating a queried subset gives
    its largest representative; equal representatives are exactly c(R).
    UF memoizes these equivalences, but is never used without the Horn rules.
    Empty is the semilattice identity. Top is handled by Session.normalize.
    """
    def __init__(self, session):
        self.session = session
        self.parent, self.rank = {}, {}
        self.rules = []
        self.version = 0
        self.cache = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != x:
            nxt = self.parent[x]
            self.parent[x] = root
            x = nxt
        return root

    def union(self, x, y):
        x, y = self.find(x), self.find(y)
        if x == y:
            return
        if self.rank.get(x, 0) < self.rank.get(y, 0):
            x, y = y, x
        self.parent[y] = x
        if self.rank.get(x, 0) == self.rank.get(y, 0):
            self.rank[x] = self.rank.get(x, 0) + 1
        self.session.stats["uf_unions"] += 1

    def normal(self, mask):
        key = (self.version, mask)
        if key in self.cache:
            return self.cache[key]
        out, changed = mask, True
        while changed:
            changed = False
            for premise, consequence in self.rules:
                self.session.check()
                self.session.stats["congruence_rule_checks"] += 1
                if premise & out == premise:
                    new = out | consequence
                    if new != out:
                        out, changed = new, True
        self.union(mask, out)
        self.cache[key] = out
        return out

    def contains(self, left, right):
        self.session.stats["congruence_queries"] += 1
        if self.find(left) == self.find(right):
            return True
        a, b = self.normal(left), self.normal(right)
        return a == b or self.find(a) == self.find(b)

    def add(self, left, right):
        self.rules.extend(((left, left | right), (right, left | right)))
        self.union(left, right)
        self.version += 1
        self.cache.clear()


def hkc(session):
    todo = deque([(session.left, session.right)])
    cc = Congruence(session)
    while todo:
        session.check()
        session.stats["hkc_popped"] += 1
        left, right = todo.popleft()
        if cc.contains(left, right):
            session.stats["hkc_pruned"] += 1
            continue
        a, b = session.observe(left), session.observe(right)
        if set(a) != set(b):
            return False
        for h in sorted(a, key=repr):
            if len(a[h]) > 1 or len(b[h]) > 1:
                raise Branching()
            todo.extend(zip(a[h][0], b[h][0]))
        cc.add(left, right)
        session.stats["hkc_expanded"] += 1
        session.stats["queue_peak"] = max(session.stats["queue_peak"], len(todo))
    return True


def game(session, equality=False, raw=False):
    """Greatest fixed point of AND-of-OR-of-AND simulation/bisimulation clauses.

    Build only demanded pairs. Failed candidates propagate via reverse edges;
    no visited-hypothesis leakage from a failed existential Tuple branch.
    Equality matches children by equality, not mutual inclusion.
    """
    root = (session.left, session.right)
    queue, scheduled, formulas = deque([root]), {root}, {}
    while queue:
        session.check()
        pair = queue.popleft()
        session.stats["simulation_pairs" if raw else "game_pairs"] += 1
        left, right = pair
        a, b = session.observe(left, raw), session.observe(right, raw)
        clauses = []
        if left == right or (not equality and right == session.top):
            formulas[pair] = []
            continue
        if not equality:
            a = {h: alts for h, alts in a.items() if not session.ignore_leaf(h)}
            if (left == 0 and "bot" in session.bottom) or (left != 0 and not a):
                formulas[pair] = []
                continue
        if not equality and (left == 0 or right == 0 or left == session.top):
            formulas[pair] = [()]  # rigid bottom; other cases handled above
            continue
        if equality and set(a) != set(b):
            formulas[pair] = [()]
            continue

        def add_direction(src, dst, reverse=False):
            for h in sorted(src, key=repr):
                for arm in src[h]:
                    candidates = []
                    for other in dst.get(h, ()):
                        deps = tuple((y, x) if reverse else (x, y) for x, y in zip(arm, other))
                        candidates.append(deps)
                        for dep in deps:
                            if dep not in scheduled:
                                scheduled.add(dep)
                                queue.append(dep)
                    clauses.append(tuple(candidates))
        add_direction(a, b)
        if equality:
            add_direction(b, a, True)
        formulas[pair] = clauses

    reverse, candidate_counts, clause_counts = defaultdict(list), {}, {}
    pair_fail = deque()
    for pair, clauses in formulas.items():
        for i, candidates in enumerate(clauses):
            clause_counts[(pair, i)] = len(candidates)
            if not candidates:
                pair_fail.append(pair)
            for j, deps in enumerate(candidates):
                ck = (pair, i, j)
                candidate_counts[ck] = 0  # 0 = live, 1 = failed
                for dep in set(deps):
                    reverse[dep].append(ck)
    failed = set()
    while pair_fail:
        session.check()
        pair = pair_fail.popleft()
        if pair in failed:
            continue
        failed.add(pair)
        for ck in reverse[pair]:
            if candidate_counts[ck]:
                continue
            candidate_counts[ck] = 1
            owner, i, _ = ck
            clause_counts[(owner, i)] -= 1
            if clause_counts[(owner, i)] == 0:
                pair_fail.append(owner)
    return root not in failed


def antichain(session):
    """Top-down antichain of structural inclusion obligations for spine joins.

    (L,R0) subsumes (L,R) if R0 subset R. Every constructor
    coordinate is checked. Branching correlated alternatives use the game.
    """
    queue = deque([(session.left, session.right)])
    pending = defaultdict(list)
    retained = 0
    while queue:
        session.check()
        session.stats["antichain_popped"] += 1
        left, right = queue.popleft()
        if left == right or right == session.top:
            session.stats["antichain_pruned"] += 1
            continue
        if left == 0 and "bot" in session.bottom:
            session.stats["antichain_pruned"] += 1
            continue
        a, b = session.observe(left), session.observe(right)
        a = {h: alts for h, alts in a.items() if not session.ignore_leaf(h)}
        if left != 0 and not a:
            session.stats["antichain_pruned"] += 1
            continue
        if left == 0 or right == 0 or left == session.top:
            return False
        if not set(a) <= set(b):
            return False
        if any(len(alts) > 1 for alts in tuple(a.values()) + tuple(b.values())):
            raise Branching()
        previous = pending[left]
        if any(old_r & right == old_r for old_r in previous):
            session.stats["antichain_pruned"] += 1
            continue
        new = [old_r for old_r in previous if not (right & old_r == right)] + [right]
        retained += len(new) - len(previous)
        pending[left] = new
        session.stats["antichain_expanded"] += 1
        session.stats["antichain_peak"] = max(session.stats["antichain_peak"], retained)
        session.stats["antichain_max_width"] = max(session.stats["antichain_max_width"], len(new))
        for h in sorted(a, key=repr):
            queue.extend(zip(a[h][0], b[h][0]))
    return True


def _compare(left, right, equality, fast, budget, seconds, bottom=()):
    session = None
    start = perf_counter()
    try:
        session = Session(left, right, budget, seconds, bottom)
        if fast and game(session, equality, raw=True):
            return session.finish(True, "bisimulation" if equality else "simulation")
        try:
            answer = hkc(session) if equality else antichain(session)
            return session.finish(answer, "HKC" if equality else "antichain")
        except Branching:
            answer = game(session, equality)
            return session.finish(answer, "HKC+choice-game" if equality else "antichain+choice-game")
    except Exhausted as exc:
        if session is not None:
            return session.finish(None, "budget", str(exc))
        return Comparison(None, "budget", {}, (perf_counter() - start) * 1000, str(exc))


def equivalent(left, right, *, fast=True, budget=1_000_000, seconds=None):
    """Bisimulation of normalized workbench choices; see frozen_equal for table equality."""
    return _compare(left, right, True, fast, budget, seconds)


def included(left, right, *, fast=True, budget=1_000_000, seconds=None, bottom=()):
    """Workbench covers(right,left), with default rigid bottom semantics."""
    return _compare(left, right, False, fast, budget, seconds, bottom)


def simulation(left, right, *, equality=False, budget=1_000_000, seconds=None, bottom=()):
    """Sufficient raw simulation (or bisimulation); False is inconclusive."""
    session = None
    start = perf_counter()
    try:
        session = Session(left, right, budget, seconds, bottom)
        return session.finish(game(session, equality, raw=True), "raw-bisimulation" if equality else "raw-simulation")
    except Exhausted as exc:
        if session is not None:
            return session.finish(None, "budget", str(exc))
        return Comparison(None, "budget", {}, (perf_counter() - start) * 1000, str(exc))
