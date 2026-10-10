#!/usr/bin/env python3
"""Reduce retained logical differences and check the recorded receipt, Python 3.9+."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PAIRS = (("unset", "1"), ("unset", "2"), ("1", "2"), ("unset", "repeat-unset"))
ENTITIES = ("route", "slot", "writer")


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def changes(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def build_maps(root):
    apps, summary, condition = {}, {}, None
    for app_dir in sorted((root / "runs").iterdir()):
        if not app_dir.is_dir():
            continue
        app = app_dir.name
        comparisons, schedules = {}, {}
        for schedule in ("unset", "1", "2", "repeat-unset"):
            receipt = read(app_dir / schedule / "receipt.json")
            if condition is None:
                condition = receipt["condition"]
            assert receipt["condition"] == condition, "mixed conditions"
            header = receipt["dump_header"]
            schedules[schedule] = {
                "audit": header["audit"], "counts": header["counts"],
                "dump_bytes": receipt["dump_bytes"], "seconds": receipt["seconds"],
            }
        app_maps = {}
        for left, right in PAIRS:
            pair = left + "--" + right
            diff = read(app_dir / (pair + ".diff.json"))
            path = app_dir / (pair + ".changes.jsonl")
            if not path.exists():
                path = path.with_suffix(path.suffix + ".gz")
            counts, examples = Counter(), defaultdict(list)
            modes = {"left_only": defaultdict(set), "right_only": defaultdict(set)}
            for row in changes(path):
                direction, entity, kind = row[:3]
                assert direction in modes and entity in ENTITIES
                counts[(entity, kind, direction)] += 1
                if len(examples[(entity, kind, direction)]) < 3:
                    examples[(entity, kind, direction)].append(row[3:])
                if entity == "route" and row[-1] in ("inline", "reference"):
                    modes[direction][tuple(row[2:-1])].add(row[-1])
            expected = Counter()
            for row in diff["by_kind"]:
                for direction in modes:
                    n = row[direction]
                    if n:
                        expected[(row["entity"], row["kind"], direction)] = n
                    assert row["samples"][direction] == examples[(row["entity"], row["kind"], direction)]
            assert counts == expected, app + "/" + pair + ": differences disagree"
            totals = {entity: {direction: sum(n for (e, _, d), n in counts.items()
                                              if e == entity and d == direction)
                               for direction in modes} for entity in ENTITIES}
            for entity in ENTITIES:
                for schedule, direction in ((left, "left_only"), (right, "right_only")):
                    n = sum(schedules[schedule]["counts"][entity].values())
                    assert n - totals[entity][direction] == diff["shared"].get(entity, 0)
            replacements = Counter()
            for key in modes["left_only"].keys() & modes["right_only"].keys():
                if modes["left_only"][key] != modes["right_only"][key]:
                    replacements[key[0]] += 1
            a = read(app_dir / left / "report.json")["digest"]
            b = read(app_dir / right / "report.json")["digest"]
            comparisons[pair] = {
                "by_kind": diff["by_kind"], "different": diff["different"], "totals": totals,
                "direct_mode_replacements": dict(sorted(replacements.items())),
                "changed_value_digest_parts": sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k)),
            }
            app_maps[pair] = diff
        apps[app] = app_maps
        summary[app] = {"comparisons": comparisons, "schedules": schedules}
    return {"apps": apps, "condition": condition}, {"apps": summary, "condition": condition}


def check_packet(root):
    actual, summary = build_maps(root)
    assert actual == read(root / "evidence/divergence-map.json")
    assert summary == read(root / "evidence/map-summary.json")
    suite = read(root / "evidence/default-suite.json")
    assert (suite["passed"], suite["failed"], suite["ignored"]) == (4975, 3, 236)
    baseline = read(root / "evidence/baseline-suite.json")
    assert sorted(suite["failures"]) == sorted(baseline["failures"])
    assert suite["tree"] == read(root / "pins.json")["source_tree"]
    for arm in read(root / "evidence/emission-parity.json").values():
        assert arm["pairs"] == 105 and arm["compared_files"] == 11432
        assert arm["byte_different_files"] == 0
        assert not arm["differences"] and not arm["added_files"] and not arm["removed_files"]
    baseline_manifest = read(root / "evidence/baseline-emission-manifest.json")
    baseline_pairs = [json.loads(line) for line in
                      (root.parent / "baseline-2026-10-10/emission/next/pairs.jsonl").read_text().splitlines()]
    for name in ("off", "on"):
        manifest = read(root / "emission" / name / "manifest.json")
        pairs = [json.loads(line) for line in (root / "emission" / name / "pairs.jsonl").read_text().splitlines()]
        assert len(manifest) == 11432 and manifest == baseline_manifest
        assert len(pairs) == 105 and pairs == baseline_pairs
    for name, passed in (("structure-lib-final-v2.json", 3), ("structure-integration-final-v2.json", 2)):
        record = read(root / "evidence" / name)
        assert record["exit"] == 0 and record["passed"] == passed and record["failed"] == 0
    for app, data in summary["apps"].items():
        repeat = data["comparisons"]["unset--repeat-unset"]
        assert repeat["totals"]["slot"] == {"left_only": 0, "right_only": 0}
        assert repeat["totals"]["writer"] == {"left_only": 0, "right_only": 0}
        assert repeat["changed_value_digest_parts"] == []
        assert repeat["different"] == (app != "campfire")
    manifest = root / "files.json"
    if manifest.exists():
        for name, record in read(manifest).items():
            path = root / name
            assert path.stat().st_size == record["bytes"] and sha256(path) == record["sha256"], name
    return {"apps": len(summary["apps"]), "comparisons": sum(len(v) for v in actual["apps"].values()),
            "condition": summary["condition"], "checks": "passed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-runs", type=Path, help="write maps for newly generated runs instead of checking this receipt")
    args = parser.parse_args()
    if args.from_runs:
        a, b = build_maps(args.from_runs)
        write(args.from_runs / "evidence/divergence-map.json", a)
        write(args.from_runs / "evidence/map-summary.json", b)
    else:
        print(json.dumps(check_packet(HERE), sort_keys=True))


if __name__ == "__main__":
    main()
