#!/usr/bin/env python3
"""Fast, cached quick-test observations and F61 row comparisons (Python 3.9)."""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OBSERVER = ROOT / "tools/observers/obs.py"
DEFAULT_CACHE = OBSERVER.parent / "cache"
APPS = ("campfire", "forem", "chatwoot", "mastodon")
SCHEDULES = ("unset", "1", "2", "repeat")
DEFAULT_SETTINGS = tuple(s + "-v0-a0" for s in SCHEDULES)
TABLES = ("attributes", "block_values", "constants", "controller_bindings", "controller_cache",
          "copies", "ir", "params", "returns", "side_table")
SHORT = dict(zip(TABLES, ("A", "B", "C", "CB", "CC", "CP", "IR", "P", "R", "ST")))
VALUE_TABLES = {"controller_cache", "ir", "params", "returns", "side_table"}
CONDITION = "quick-test-v1 / cached-observers-20261015-source-rebuild / F61"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


@lru_cache(maxsize=1)
def dependencies():
    # Reuse the retained signatures, symbolic-reference resolver, parent identities,
    # and F61 runtime-set relation. Importing these files does not invoke an analyzer.
    obs = module("obs", OBSERVER)
    rows = module("probe_current_return_rows", HERE / "rowdiff.py")
    sets = module("probe_runtime_sets", HERE / "runtime_sets.py")
    sets.VAR_TOP = True
    return obs, rows, sets


def read(path):
    return json.loads(Path(path).read_text())


def csv(value):
    items = [s.strip() for s in value.split(",")]
    if not all(items) or len(set(items)) != len(items):
        raise ValueError("lists must contain distinct, nonempty items")
    return items


def run(args):
    obs, _, _ = dependencies()
    apps = csv(args.apps)
    if any(app not in APPS for app in apps):
        raise ValueError("--apps must select from " + ",".join(APPS))
    settings = [obs.setting(s)["name"] for s in csv(args.settings)]
    if len(set(settings)) != len(settings):
        raise ValueError("duplicate settings after observer-name normalization")
    profile = read(args.profile)
    if not isinstance(profile, dict):
        raise ValueError("--profile must contain a JSON object")
    overrides = [item for group in args.set for item in group]
    effective = dict(profile)
    for item in overrides:
        if "=" not in item:
            raise ValueError("--set requires K=V")
        key, value = item.split("=", 1)
        effective[key] = value
    protected = set(obs.DUMPS) | {"RH_SHUFFLE", "RH_FIXPOINT_VERIFY", "RH_PROVENANCE_AUDIT"}
    if any(not k.startswith("RH_") or k in protected for k in effective):
        raise ValueError("only RH_* overrides are allowed; settings and dump paths belong to obs.py")
    if effective.get("RH_CONTRIBUTOR_VALUES", "1") not in ("1", 1):
        raise ValueError("RH_CONTRIBUTOR_VALUES must be 1 for a quick test")
    obs.label_path(args.cache_root, args.label)  # Validate before any launch.
    status = 0
    for app in apps:
        command = [sys.executable, str(OBSERVER), "run", "--bin", str(args.bin.resolve()),
                   "--flags", str(args.profile.resolve()), "--label", args.label,
                   "--app", app, "--settings", ",".join(settings),
                   "--cache-root", str(args.cache_root.resolve()), "--jobs", str(args.jobs),
                   "--timeout", str(args.timeout)]
        for item in overrides:
            command += ["--flag", item]
        command += ["--flag", "RH_CONTRIBUTOR_VALUES=1"]
        if getattr(args, "fresh", False):
            command.append("--fresh")
        code = subprocess.call(command, cwd=str(ROOT))
        status = max(status, code if code >= 0 else 1)
    return status


def has_reference(value):
    if isinstance(value, dict):
        return value.get("kind") == "rec" or any(has_reference(v) for v in value.values())
    if isinstance(value, list):
        return any(has_reference(v) for v in value)
    return False


def scan_dump(path, native_digests, expected_sha=None):
    """Stream signatures; keep types out of memory until a row needs classification.

    The row signature and empty-parameter identity are the retained row parser's. Native fingerprint
    rows cover the five tables for which the current dumper has no typed rows.
    """
    _, rows, _ = dependencies()
    signatures, referenced, seen, errors = {}, set(), set(), {}
    raw_hashes = {p: {} for p in ("returns", "side_table")}
    parents = {p: set() for p in ("params", "controller_cache")}
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        first = next(stream, b"")
        hasher.update(first)
        fp = json.loads(first)
        if fp.get("part") != "fingerprint" or fp.get("digests") != native_digests:
            raise ValueError("value dump fingerprint does not match the native ten digests")
        if not isinstance(fp.get("parts"), dict) or not isinstance(fp.get("ir"), list):
            raise ValueError("missing native row fingerprint")
        ir = Counter(tuple(v) for v in fp["ir"])
        for line_number, line in enumerate(stream, 2):
            hasher.update(line)
            row = json.loads(line)
            part, key = row["part"], row["key"]
            if not isinstance(key, str):
                raise ValueError("non-string row identity at line " + str(line_number))
            identity = (part, key)
            if identity in seen:
                raise ValueError("duplicate row identity: " + repr(identity))
            seen.add(identity)
            if part == "aliases":
                continue
            if part not in TABLES:
                raise ValueError("unknown value table: " + str(part))
            if "hash" not in row:
                raise ValueError("row lacks a value hash: " + repr(identity))
            signatures[identity] = rows.stratum2.sig(row)
            if has_reference(row.get("ty")):
                referenced.add(identity)
            if part in raw_hashes:
                raw_hashes[part][key] = row["hash"]
            if part in parents:
                parents[part].add(rows.parent(part, key))
            if part == "ir":
                span = row.get("span") or {}
                ir[(span.get("file"), span.get("start"), span.get("end"),
                    row["hash"], row.get("note"))] -= 1
        if any(ir.values()):
            errors["ir"] = "IR rows do not cover the native fingerprint multiset"
    actual_sha = hasher.hexdigest()
    if expected_sha is not None and actual_sha != expected_sha:
        raise ValueError("value dump SHA-256 differs from the capture receipt")
    for part in TABLES:
        if part == "ir":
            continue
        native = fp["parts"].get(part)
        if not isinstance(native, dict):
            errors[part] = "native table fingerprint missing"
            continue
        if part in raw_hashes and raw_hashes[part] != native:
            errors[part] = "typed rows do not cover native table fingerprint"
        if part in parents and not parents[part].issubset(native):
            errors[part] = "typed rows have parents absent from native fingerprint"
        if part == "params":
            for key, value in native.items():
                if key not in parents[part]:
                    # The row loader retains present empty vectors explicitly.
                    signatures[(part, key + "[empty]")] = (value, None, None)
        if part not in VALUE_TABLES:
            for key, value in native.items():
                signatures.setdefault((part, key), rows.stratum2.sig({"hash": value}))
    return {"path": str(path), "sha256": actual_sha, "fingerprint": fp,
            "signatures": signatures, "referenced": referenced, "errors": errors}


def digest_equality(cells):
    result = {}
    for part in TABLES:
        values = [(cell.get("record") or {}).get("observations", {}).get("value_digests")
                  if cell.get("valid") else None for cell in cells]
        if any(not isinstance(v, dict) or v.get(part) is None for v in values):
            result[part] = None
        else:
            result[part] = len({v[part] for v in values}) == 1
    return {"by_table": result, "equal_tables": [p for p in TABLES if result[p] is True],
            "missing_tables": [p for p in TABLES if result[p] is None]}


def row_variance(scans):
    """Union of differing exact (table,key) signatures, including row absence."""
    _, rowdiff, _ = dependencies()
    result = {}
    for part in TABLES:
        unavailable = [str(i) for i, scan in enumerate(scans)
                       if scan is None or part in scan["errors"]]
        if unavailable:
            result[part] = {"varying_rows": None, "union_rows": None,
                            "missing": "missing/invalid schedule indexes: " + ",".join(unavailable)}
            continue
        signatures = [{key: sig for (p, key), sig in scan["signatures"].items() if p == part}
                      for scan in scans]
        keys = set().union(*(set(s) for s in signatures))
        changed = {key for key in keys if len({s.get(key) for s in signatures}) > 1}
        # The row parser checks that child differences explain every differing native parent.
        if part in ("params", "controller_cache"):
            native = [scan["fingerprint"]["parts"][part] for scan in scans]
            parents = set().union(*(set(v) for v in native))
            changed_parents = {key for key in parents if len({v.get(key) for v in native}) > 1}
            observed = {rowdiff.parent(part, key) for key in changed}
            if changed_parents != observed:
                result[part] = {"varying_rows": None, "union_rows": len(keys),
                                "missing": "child row differences do not cover native parent differences",
                                "unexplained_parents": sorted(changed_parents - observed),
                                "extra_parents": sorted(observed - changed_parents)}
                continue
        result[part] = {"varying_rows": len(changed), "union_rows": len(keys), "missing": None}
    return result


def value_relation(control, candidate):
    """F61: Untyped and raw Var are top; use F61 runtime-set's recursive container relation."""
    _, _, sets = dependencies()
    sets.VAR_TOP = True
    return sets.relation(control, candidate)


def identity(part, key, row=None, fp=None):
    result = {"table": part, "key": key}
    if row:
        for field in ("root", "path", "span", "node"):
            if field in row:
                result[field] = row[field]
        source = row.get("source")
        if isinstance(source, int) and fp and source > 0:
            sources = fp.get("sources", [])
            source = sources[source - 1] if source <= len(sources) else None
        if source is not None:
            result["source"] = source
    return result


def compare_values(before, after):
    """Compare every unset row, resolving symbolic slots even when its own hash is unchanged."""
    _, rows, _ = dependencies()
    names = ("narrowed", "widened", "unchanged", "incomparable", "missing")
    if before is None or after is None:
        return {"complete": False, "counts": {k: None for k in names}, "by_table": None,
                "narrowings": None, "unclassified": None, "missing": "unset value dump unavailable"}
    a, b = before["signatures"], after["signatures"]
    keys = set(a) | set(b)
    selected = {key for key in keys if a.get(key) != b.get(key)}
    # A stable Rec can denote a changed target. Never skip it on hash equality alone.
    if before["sha256"] != after["sha256"]:
        selected |= before["referenced"] | after["referenced"]
    wanted = {key for key in selected if key[0] in VALUE_TABLES}
    load_error = None
    try:
        left = rows.stratum2.load(Path(before["path"]), wanted)[1] if wanted else {}
        right = rows.stratum2.load(Path(after["path"]), wanted)[1] if wanted else {}
    except (OSError, ValueError, KeyError, AssertionError, RecursionError) as error:
        left, right, load_error = {}, {}, str(error)
    counts, by_table, narrowings, unclassified = Counter(), {}, [], []
    unavailable = {p: before["errors"].get(p) or after["errors"].get(p)
                   for p in TABLES if p in before["errors"] or p in after["errors"]}
    for part in TABLES:
        by_table[part] = {k: None if part in unavailable else 0 for k in names}
    for part, key in sorted(keys):
        if part in unavailable:
            continue
        pair = (part, key)
        detail, relation = None, "EQ"
        if pair not in a or pair not in b:
            detail = "row absent from " + ("control" if pair not in a else "candidate")
        elif pair in selected:
            lrow, rrow = left.get(pair), right.get(pair)
            if load_error:
                detail = "cannot resolve serialized values: " + load_error
            elif part not in VALUE_TABLES:
                detail = "changed fingerprint has no serialized type"
            elif lrow is None or rrow is None:
                detail = "empty parameter vector or serialized value unavailable"
            else:
                try:
                    relation = value_relation(lrow.get("resolved_ty"), rrow.get("resolved_ty"))
                    if relation == "STRUCT":
                        detail = "serialized type absent"
                except (KeyError, TypeError, ValueError, AttributeError, RecursionError) as error:
                    detail = "unresolved value relation: " + str(error)
        if detail:
            category = "missing"
            unclassified.append(dict(identity(part, key), reason=detail))
        else:
            category = {"EQ": "unchanged", "NARROW": "narrowed", "WIDEN": "widened",
                        "INCOMP": "incomparable"}[relation]
            if category == "narrowed":
                lrow, rrow = left[pair], right[pair]
                narrowings.append(dict(identity(part, key, rrow, after["fingerprint"]),
                                       control=lrow["resolved_ty"], candidate=rrow["resolved_ty"],
                                       control_reference_expansions=lrow.get("reference_expansions"),
                                       candidate_reference_expansions=rrow.get("reference_expansions")))
        counts[category] += 1
        by_table[part][category] += 1
    observed = {k: counts[k] for k in names}
    return {"complete": not unavailable and not counts["missing"],
            "counts": {k: None for k in names} if unavailable else observed,
            "classified_counts": observed, "by_table": by_table,
            "narrowings": narrowings, "unclassified": unclassified,
            "unavailable_tables": unavailable, "missing": None}


def label_data(cache, name):
    obs, _, _ = dependencies()
    try:
        data = obs.load_label(cache, name)
        if not isinstance(data, dict) or not isinstance(data.get("cells"), dict):
            raise ValueError("label lacks a cell map")
        for key, ref in data["cells"].items():
            app, setting = key.split("/", 1)
            if not app or not isinstance(ref, dict):
                raise ValueError("invalid cell reference")
            obs.setting(setting)
        return data, None
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"cells": {}}, str(error)


def load_cell(label, label_error, app, setting):
    obs, _, _ = dependencies()
    result = {"valid": False, "record": None, "missing": []}
    if label_error:
        result["missing"].append("label unavailable: " + label_error)
        return result
    reference = label.get("cells", {}).get(app + "/" + setting)
    if reference is None:
        result["missing"].append("cell not recorded")
        return result
    try:
        record = obs.checked_result(reference["result"])
        taint = Path(record["directory"]).parents[1] / "inconsistent.json"
        if (not record.get("valid") or not reference.get("valid")
                or reference.get("fresh_match") is False or taint.exists()):
            raise ValueError("invalid or inconsistent observer cell")
        if record.get("app") != app or record.get("setting", {}).get("name") != setting:
            raise ValueError("receipt identity does not match label cell")
        result.update(valid=True, record=record)
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError, RecursionError) as error:
        result["missing"].append(str(error))
    return result


def compatible(cells):
    """Numbers share an input, runtime and observer setting; binaries/repair flags may differ."""
    records = [c["record"] for c in cells if c.get("valid")]
    for field in ("input_manifest_sha256", "runtime"):
        values = [r.get("key", {}).get(field) for r in records]
        if any(v is None for v in values):
            return "missing comparison condition: " + field
        if len({json.dumps(v, sort_keys=True) for v in values}) > 1:
            return "comparison condition differs: " + field
    # Exact source identities in the inherited parser include the public input root.
    if len({r.get("input") for r in records}) > 1:
        return "input roots differ; exact row identities cannot be matched"
    return None


def schedule_condition(cells):
    """Do not turn a mixed-binary/mixed-profile label into a schedule experiment."""
    obs, _, _ = dependencies()
    records = [c["record"] for c in cells if c.get("valid")]
    binaries = [r.get("key", {}).get("binary_sha256") for r in records]
    if any(v is None for v in binaries):
        return "missing schedule condition: binary SHA-256"
    if len(set(binaries)) > 1:
        return "binary differs across schedules"
    flags = [r.get("key", {}).get("rh_flags", r.get("inference_environment")) for r in records]
    if any(not isinstance(v, dict) for v in flags):
        return "missing schedule condition: effective flags"
    ignored = set(obs.DUMPS) | {"RH_SHUFFLE"}
    conditions = [{k: v for k, v in flag.items() if k not in ignored} for flag in flags]
    if len({json.dumps(v, sort_keys=True) for v in conditions}) > 1:
        return "effective profile differs across schedules"
    return None


def cell_summary(cell):
    record = cell.get("record") or {}
    diagnostics = record.get("observations", {}).get("diagnostics") if cell.get("valid") else None
    if isinstance(diagnostics, dict) and all(type(n) is int and n >= 0 for n in diagnostics.values()):
        diagnostics = {"total": sum(diagnostics.values()), "by_kind": diagnostics}
    else:
        diagnostics = None
    wall = record.get("metrics", {}).get("wall_seconds") if cell.get("valid") else None
    if type(wall) not in (int, float) or not math.isfinite(wall) or wall < 0:
        wall = None
    return {"valid": cell["valid"], "missing": cell["missing"], "diagnostics": diagnostics,
            "wall_seconds": wall, "result_directory": record.get("directory"),
            "cache_key": record.get("cache_key"), "binary_sha256": record.get("key", {}).get("binary_sha256"),
            "input_manifest_sha256": record.get("key", {}).get("input_manifest_sha256"),
            "runtime": record.get("key", {}).get("runtime"),
            "effective_flags": record.get("key", {}).get("rh_flags", record.get("inference_environment"))}


def make_report(cache, control, candidate, progress=None):
    labels = {name: label_data(cache, name) for name in {control, candidate}}
    cells = set().union(*(set(data[0].get("cells", {})) for data in labels.values()))
    apps = sorted({c.split("/", 1)[0] for c in cells}) or list(APPS)
    groups = sorted({c.split("/", 1)[1].split("-", 1)[1] for c in cells}) or ["v0-a0"]
    report = {"schema": 1, "condition": CONDITION,
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "control": control, "candidate": candidate,
              "cache_root": str(cache), "schedules": list(SCHEDULES), "apps": {}, "complete": True}
    # Share only the small cell summaries; stream each raw dump once per report.
    for app in apps:
        report["apps"][app] = {}
        app_groups = [g for g in groups if any(c.startswith(app + "/") and c.endswith("-" + g) for c in cells)]
        for group in app_groups or groups:
            settings = [s + "-" + group for s in SCHEDULES]
            roles = {role: [load_cell(*labels[name], app, setting) for setting in settings]
                     for role, name in (("control", control), ("candidate", candidate))}
            all_cells = roles["control"] + roles["candidate"]
            role_conditions = {role: compatible(c) or schedule_condition(c) for role, c in roles.items()}
            mismatch = compatible(all_cells) or next((v for v in role_conditions.values() if v), None)
            scans, role_data = {}, {}
            unset = {}
            for role in ("control", "candidate"):
                role_scans = []
                for setting, cell in zip(settings, roles[role]):
                    scan = None
                    if cell["valid"] and not mismatch:
                        r = cell["record"]
                        key = r["directory"]
                        if key in scans:
                            scan, error = scans[key]
                            if error:
                                cell["missing"].append(error)
                        else:
                            try:
                                if progress:
                                    progress("scan " + role + " " + app + "/" + setting)
                                path = Path(key) / "contributor-values.jsonl"
                                expected_sha = r.get("artifacts", {}).get(path.name, {}).get("sha256")
                                if not isinstance(expected_sha, str):
                                    raise ValueError("value dump has no captured SHA-256 receipt")
                                scan = scan_dump(path, r["observations"].get("value_digests"),
                                                 expected_sha)
                                scans[key] = (scan, None)
                            except (OSError, ValueError, KeyError, AssertionError, TypeError,
                                    AttributeError, RecursionError) as error:
                                cell["missing"].append("row values unavailable: " + str(error))
                                scans[key] = (None, cell["missing"][-1])
                    role_scans.append(scan)
                role_data[role] = {"digest_equality": digest_equality(
                                      roles[role] if not role_conditions[role] else [{}] * 4),
                                   "varying_rows": row_variance(role_scans),
                                   "condition_missing": role_conditions[role],
                                   "cells": {s: cell_summary(c) for s, c in zip(settings, roles[role])}}
                unset[role] = role_scans[0]
            if progress:
                progress("compare unset " + app + "/" + group)
            narrowed = compare_values(unset["control"], unset["candidate"])
            if mismatch:
                narrowed["missing"] = mismatch
            complete = (not mismatch and narrowed["complete"] and
                        all(not d["digest_equality"]["missing_tables"] and
                            all(v["varying_rows"] is not None for v in d["varying_rows"].values()) and
                            all(c["valid"] and not c["missing"] and c["diagnostics"] is not None
                                and c["wall_seconds"] is not None for c in d["cells"].values())
                            for d in role_data.values()))
            report["apps"][app][group] = dict(role_data, settings=settings, unset_values=narrowed,
                                               comparison_missing=mismatch, complete=bool(complete))
            report["complete"] &= bool(complete)
    return report


def shown(value):
    return "missing" if value is None else str(value)


def inline(value):
    value = str(value).replace("\n", "\\n").replace("\r", "\\r")
    marker = "`"
    while marker in value:
        marker += "`"
    return marker + " " + value + " " + marker


def markdown(report):
    lines = ["# Quick-test probe", "",
             "Condition: " + report["condition"] + ". Control " + inline(report["control"]) +
             "; candidate " + inline(report["candidate"]) + ".",
             "Vectors: unset / 1 / 2 / repeat, at the named V/A observer. Timings are shared-host measurements.",
             "A=attributes; B=block values; C=constants; CB=controller bindings; CC=controller cache; "
             "CP=copies; IR=expressions; P=params; R=returns; ST=side table.",
             "F61 narrowing is value-set inclusion, not a soundness verdict. Full identities, values, "
             "conditions and missing-data details are in [report.json](report.json).", ""]
    blocks = []
    for app, groups in report["apps"].items():
        for group, data in groups.items():
            text = []
            equal = []
            for role in ("control", "candidate"):
                d = data[role]["digest_equality"]
                value = ",".join(SHORT[p] for p in d["equal_tables"]) or "none"
                if d["missing_tables"]:
                    value += "; missing " + ",".join(SHORT[p] for p in d["missing_tables"])
                equal.append(role + ": " + value)
            text.append("Equal digest tables across four schedules — " + "; ".join(equal) + ".")
            text.append("Varying rows (control → candidate): " + "; ".join(
                SHORT[p] + " " + shown(data["control"]["varying_rows"][p]["varying_rows"]) + "→" +
                shown(data["candidate"]["varying_rows"][p]["varying_rows"]) for p in TABLES) + ".")
            n = data["unset_values"]
            text.append("Unset F61 classified rows: " + "; ".join(k + " " + shown(v) for k, v in n["counts"].items()) +
                        (". Complete." if n["complete"] else ". Incomplete; see missing data in JSON."))
            ids = n["narrowings"]
            text.append("Narrowed identities: " + ("missing" if ids is None else
                        "; ".join(inline(r["table"] + ":" + r["key"]) for r in ids) or "none") + ".")
            kinds = sorted(set().union(*(set(c["diagnostics"]["by_kind"])
                           for role in ("control", "candidate") for c in data[role]["cells"].values()
                           if c["diagnostics"] is not None)))
            def vector(role, field, kind=None):
                values = []
                for setting in data["settings"]:
                    c = data[role]["cells"][setting]
                    if field == "diagnostics":
                        d = c["diagnostics"]
                        v = None if d is None else d["by_kind"].get(kind, 0) if kind else d["total"]
                    else:
                        v = c[field]
                    values.append("%.3f" % v if field == "wall_seconds" and v is not None else shown(v))
                return "/".join(values)
            text.append("Diagnostic totals: control " + vector("control", "diagnostics") +
                        "; candidate " + vector("candidate", "diagnostics") + ".")
            for role in ("control", "candidate"):
                text.append("Kinds, " + role + ": " + ("; ".join(kind + " " + vector(role, "diagnostics", kind)
                            for kind in kinds) or ("none" if all(c["diagnostics"] is not None
                            for c in data[role]["cells"].values()) else "missing")) + ".")
            text.append("Wall seconds (native process, excluding queue/reduction): control " + vector("control", "wall_seconds") +
                        "; candidate " + vector("candidate", "wall_seconds") + ".")
            if not data["complete"]:
                text.append("Missing data: " + (data["comparison_missing"] or n.get("missing") or
                            "one or more cells, row tables, row relations, diagnostics or timings are unavailable") + ".")
            blocks.append(("## " + app + " / " + group, text))
    normal = lines + [line for heading, body in blocks for line in [heading, ""] + body + [""]]
    # A label may contain all sixteen observer settings. Keep the promised line
    # budget without truncating identities or replacing missing values with zeros.
    if len(normal) > 60:
        normal = lines + [line for heading, body in blocks for line in [heading, " ".join(body), ""]]
    assert len(normal) <= 60, "too many app/observer groups for the short report"
    return "\n".join(normal).rstrip() + "\n"


def report(args):
    obs, _, _ = dependencies()
    started = time.monotonic()
    for name in (args.control, args.candidate):
        obs.label_path(args.cache_root, name)
    result = make_report(args.cache_root.resolve(), args.control, args.candidate,
                         progress=lambda message: print(message, flush=True))
    result["report_seconds"] = time.monotonic() - started
    out = args.out or HERE / "reports" / (args.control + "--" + args.candidate)
    out.mkdir(parents=True, exist_ok=True)
    obs.save(out / "report.json", result)
    # Atomic replacement keeps readers from seeing a half-written Markdown file.
    temp = out / ("report.md." + str(os.getpid()) + ".tmp")
    try:
        temp.write_text(markdown(result))
        os.replace(str(temp), str(out / "report.md"))
    finally:
        if temp.exists():
            temp.unlink()
    print(str((out / "report.md").resolve()))
    print(str((out / "report.json").resolve()))
    print("complete=" + str(result["complete"]).lower() + " report_seconds=%.3f" % result["report_seconds"])
    return int(not result["complete"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run", help="run missing cells through obs.py, with serialized row values")
    p.add_argument("--bin", type=Path, required=True)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--set", action="append", nargs="+", default=[])
    p.add_argument("--label", required=True)
    p.add_argument("--apps", default=",".join(APPS))
    p.add_argument("--settings", default=",".join(DEFAULT_SETTINGS))
    p.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    p.add_argument("--jobs", type=int, choices=range(1, 7), default=4)
    p.add_argument("--timeout", type=float, default=600)
    p.add_argument("--fresh", action="store_true", help="explicit observer retry; preserves original receipts")
    p.set_defaults(func=run)
    p = sub.add_parser("report", help="compare saved labels; writes report.md (at most 60 lines) and report.json")
    p.add_argument("--control", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    p.add_argument("--out", type=Path, help="output directory; default: phase2/probe/reports/CONTROL--CANDIDATE")
    p.set_defaults(func=report)
    args = parser.parse_args(argv)
    if getattr(args, "timeout", 1) <= 0:
        parser.error("--timeout must be positive")
    try:
        return args.func(args)
    except (OSError, ValueError, KeyError, AssertionError, subprocess.SubprocessError) as error:
        print("probe: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
