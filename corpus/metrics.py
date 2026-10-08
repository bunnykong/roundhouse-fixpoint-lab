"""Strict output reduction: kinds, counts, numeric telemetry; never messages."""
from collections import Counter, defaultdict
import json
import math
import re

DIAGNOSTIC = re.compile(r"^(?:.*?:\d+:\d+:\s*)?(error|warning|note)\[([a-z_][a-z_0-9]*)\]:")
SUMMARY = re.compile(
    r"^roundhouse-check: .*? — (\d+) parse error\(s\), (\d+) error\(s\), "
    r"(\d+) warning\(s\)(?:, (\d+) gap-attributed note\(s\))?(?:, (\d+) survey gap\(s\))?\s*$")
STAGES = {"initial", "production", "tests", "absorb", "final"}
PHASES = {"typing", "harvest", "unify", "convergence"}
TYPE_KINDS = {"Int", "Float", "Bool", "Str", "Sym", "Date", "Time", "Nil", "Relation",
              "Array", "Hash", "Tuple", "Record", "Union", "SelfInstance", "Class",
              "Fn", "Var", "Untyped", "Bottom", "Rec"}
AGG_FIELDS = {"slots", "nodes", "max_nodes", "max_depth", "fresh", "changed", "grew",
              "shrank", "same_size", "back_to_seen"}
SLOT_KINDS = {"class_returns", "instance_returns", "returns", "params", "constants",
              "attributes", "typed_constants", "attrs", "typed_consts",
              "ret", "cret", "const", "attr", "param", "tconst"}
COUNTERS = {"harvest_entries", "harvest_changed", "harvest_untie_cut", "unify_rows",
            "unify_changed", "unify_entries", "unify_param_changed", "unify_untie_cut",
            "bound_cut", "bound_calls", "rec_reads", "rec_folds", "backstop_firings"}
REVISIT_FIELDS = {"visits", "distinct_roots", "unchanged_output", "secs", "unchanged_secs"}
TELEMETRY_PREFIXES = {"rh-sccq", "rh-sccq-verify", "rh-fold", "rh-fold-gradual",
                      "rh-ep3", "rh-ep3-round", "rh-arc", "rh-c1-digest"}
TELEMETRY_NUMBERS = {
    "round", "rounds", "stores", "changed", "explained", "folds", "joins", "backstop_firings", "unfolds",
    "interned", "canon_calls", "max_states", "slot_states", "ep3_ms", "t1_checked", "t1_violations",
    "moved", "moved_slots", "moved_params", "side_moved", "state_entries_moved", "ir_sites_moved",
    "side_slots_moved", "ir_sites", "typed_exprs", "bare_untyped", "untyped_arm", "untyped_anywhere",
    "fine_pass_a", "fine_reseed", "ctrl", "class_items", "production_rounds", "test_rounds", "absorb_rounds",
    "body_evals", "body_evaluations", "units", "sccs", "pops", "cap_hits", "frozen", "max_queue",
    "ret", "cret", "param", "ivar", "slots", "states", "nodes", "eq_calls", "eq_hits", "join_calls",
    "join_hits", "hash_calls", "intern_hits", "intern_slots", "view_budget", "sim_calls", "cycles",
}


def safe_telemetry(value):
    if not isinstance(value, dict):
        return None
    out = numeric_fields(value, TELEMETRY_NUMBERS)
    for key in ("phase", "loop", "verify", "when"):
        if value.get(key) in STAGES:
            out[key] = value[key]
    if value.get("arm") in ("sccq", "rounds"):
        out["arm"] = value["arm"]
    for key in ("converged", "capped"):
        if isinstance(value.get(key), bool):
            out[key] = value[key]
    for key in ("engine", "c1", "counts", "by_slot"):
        if isinstance(value.get(key), dict):
            out[key] = numeric_fields(value[key], TELEMETRY_NUMBERS)
    for key in ("digest", "registry", "rows", "side", "ir", "attributes"):
        text = value.get(key)
        if isinstance(text, str) and re.fullmatch(r"[0-9a-f]{16,64}", text):
            out[key] = text
    return out or None


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def numeric_fields(value, keys):
    if not isinstance(value, dict):
        return {}
    return {key: value[key] for key in sorted(keys & value.keys()) if numeric(value[key])}


def aggregate(value):
    out = numeric_fields(value, AGG_FIELDS)
    if isinstance(value, dict):
        kinds = numeric_fields(value.get("kind_nodes"), TYPE_KINDS)
        if kinds:
            out["kind_nodes"] = kinds
    return out


def safe_probe(value):
    """Reject unknown fields and identities, including the probe's type shapes."""
    if not isinstance(value, dict):
        return None
    stage, phase, round_number = value.get("stage"), value.get("phase"), value.get("round")
    if stage not in STAGES or phase not in PHASES or not isinstance(round_number, int) or isinstance(round_number, bool):
        return None
    if round_number < 0:
        return None
    out = {"stage": stage, "phase": phase, "round": round_number}
    for name in ("signatures", "ir"):
        if isinstance(value.get(name), dict):
            out[name] = aggregate(value[name])
    if isinstance(value.get("by_slot"), dict):
        out["by_slot"] = {key: aggregate(val) for key, val in value["by_slot"].items()
                          if key in SLOT_KINDS and isinstance(val, dict)}
    for name, keys in (("counts", COUNTERS), ("revisits", REVISIT_FIELDS)):
        clean = numeric_fields(value.get(name), keys)
        if clean:
            out[name] = clean
    out.update(numeric_fields(value, {"probe_secs", "secs_since_last_probe"}))
    # A candidate may supply an explicit convergence observation.
    if isinstance(value.get("converged"), bool):
        out["converged"] = value["converged"]
    return out


class Reducer:
    def __init__(self):
        self.counts = Counter()
        self.summary = None
        self.probes = []
        self.ignored_probe_records = 0
        self.truncated_lines = 0
        self.telemetry = defaultdict(list)

    def feed(self, line):
        match = DIAGNOSTIC.match(line)
        if match:
            severity, kind = match.groups()
            self.counts[severity + ":" + kind] += 1
            return
        match = SUMMARY.fullmatch(line.rstrip("\r\n"))
        if match:
            values = [int(n) if n is not None else 0 for n in match.groups()]
            self.summary = dict(zip(("parse_errors", "errors", "warnings", "notes", "survey_gaps"), values))
            return
        prefix, separator, payload = line.partition(": ")
        if separator and prefix in TELEMETRY_PREFIXES:
            try:
                clean = safe_telemetry(json.loads(payload))
            except (ValueError, TypeError):
                clean = None
            if clean is not None and len(self.telemetry[prefix]) < 10000:
                self.telemetry[prefix].append(clean)
            else:
                self.ignored_probe_records += 1
            return
        if line.startswith("rh-dyn: "):
            try:
                clean = safe_probe(json.loads(line[len("rh-dyn: "):]))
            except (ValueError, TypeError):
                clean = None
            if clean is None:
                self.ignored_probe_records += 1
            else:
                self.probes.append(clean)

    def data(self):
        by_severity = {}
        for severity in ("error", "warning", "note"):
            by_severity[severity] = {key.split(":", 1)[1]: count for key, count in sorted(self.counts.items())
                                     if key.startswith(severity + ":")}
        observed_errors = sum(by_severity["error"].values())
        observed_warnings = sum(by_severity["warning"].values())
        agrees = None
        if self.summary is not None:
            agrees = (observed_errors == self.summary["errors"] + self.summary["parse_errors"]
                      and observed_warnings == self.summary["warnings"])
        return {"errors_by_kind": by_severity["error"], "warnings_by_kind": by_severity["warning"],
                "notes_by_kind": by_severity["note"],
                "gradual_untyped": by_severity["warning"].get("gradual_untyped", 0),
                "summary_counts": self.summary, "counts_agree_with_summary": agrees,
                "diagnostics_complete": self.summary is not None and self.truncated_lines == 0 and agrees,
                "rh_dyn": probe_summary(self.probes), "probe_records": self.probes,
                "telemetry": dict(self.telemetry),
                "ignored_probe_records": self.ignored_probe_records,
                "truncated_lines": self.truncated_lines}


def probe_summary(records):
    if not records:
        return {"present": False, "records": 0, "rounds": {}, "converged": None,
                "convergence_basis": "no_probe"}
    stages = defaultdict(list)
    for record in records:
        stages[record["stage"]].append(record)
    rounds = {}
    terminal = {}
    for stage in ("production", "tests", "absorb"):
        rs = stages.get(stage, [])
        if not rs:
            continue
        last = max(r["round"] for r in rs)
        rounds[stage] = len({r["round"] for r in rs})
        changes = {}
        for r in rs:
            if r["round"] == last and r["phase"] in ("harvest", "unify"):
                changed = r.get("signatures", {}).get("changed")
                if changed is not None:
                    changes[r["phase"]] = changed
        terminal[stage] = {"last_round_index": last, "signature_changes": changes,
                           "signatures_stable": (all(v == 0 for v in changes.values())
                                                 if set(changes) == {"harvest", "unify"} else None)}
    explicit = [r["converged"] for r in records if "converged" in r]
    counts = Counter()
    for record in records:
        counts.update(record.get("counts", {}))
    # Probe signatures omit block-value sets. Zero changes alone are not a fixpoint certificate.
    return {"present": True, "records": len(records), "rounds": rounds,
            "terminal": terminal, "event_counts": dict(sorted(counts.items())),
            "converged": explicit[-1] if explicit else None,
            "convergence_basis": "explicit_probe" if explicit else "not_observed"}
