#!/usr/bin/env python3
"""Apply F19's frozen selections and oracle to a supplied current source.

Unlike lab/receipts/inference.py rerun, this does NOT check out historical
compiler pins. Run under the workshop shared lock. Python 3.9+.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

D = Path(__file__).resolve().parents[1]
LAB = D / "sources/lab"
S3 = dict(RH_FOLD="1", RH_FOLD_SLOTS="1", RH_FOLD_JOIN="1", RH_FOLD_TAIL="1",
          RH_BRK_ALLARMS="1", RH_SCHED="sccq")
PROGRAMS = ("pend_bot", "pend_rec", "pend_locals", "pend_census")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args], text=True).strip()


def local(path):
    result = path.resolve()
    result.relative_to(D)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=D / "sources/probe-source")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--candidate-env", action="append", default=[], metavar="RH_FLAG=VALUE")
    args = parser.parse_args()
    source, output = local(args.source), local(args.output)
    candidate = {}
    for item in args.candidate_env:
        name, value = item.split("=", 1)
        if not name.startswith("RH_") or not name.replace("_", "").isalnum():
            parser.error("candidate controls must be RH_ environment names")
        # An invented environment variable must not silently produce a no-op comparison.
        if not any(name in p.read_text() for p in (source / "src").rglob("*.rs")):
            parser.error("candidate control is not implemented in this source: " + name)
        candidate[name] = value
    output.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("RH_", "ROUNDHOUSE_", "SOUND_", "PROVENANCE_", "PROBE_BASE"))}
    env.update(CARGO_HOME=str(D / "scratch/cargo-home"), CARGO_BUILD_JOBS="4",
               CARGO_TARGET_DIR=str(D / "scratch/provenance-target"), TMPDIR=str(D / "scratch/tmp"),
               RBENV_VERSION="4.0.7", RUST_MIN_STACK="33554432")
    Path(env["CARGO_HOME"]).mkdir(parents=True, exist_ok=True)
    Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)

    # Keep the original render/membership convention and add a lossless audit sidecar.
    helper = (LAB / "patches/inference-exporter/sound_types.rs").read_text()
    helper = helper.replace("let mut result = BTreeMap::new();",
                            "let mut result = BTreeMap::new(); let mut audit = BTreeMap::new();", 1)
    marker = "result.insert(alias, ty.map(|t| render(t, var)).unwrap_or(missing.into()));"
    if helper.count(marker) != 1:
        raise RuntimeError("exporter changed; review the adapter")
    helper = helper.replace(marker, "audit.insert(alias.clone(), producer_reason_audit(ty));\n                " + marker)
    marker = 'println!("{}", serde_json::to_string_pretty(&result).unwrap());'
    helper = helper.replace(marker, 'std::fs::write(std::env::var("PROVENANCE_AUDIT_PATH").unwrap(), '
                            'serde_json::to_string_pretty(&audit).unwrap()).unwrap();\n            ' + marker, 1)
    helper += "\n" + (D / "experiments/export_audit.rs").read_text()
    example = source / "examples/producer_reason_sound_types.rs"
    example.parent.mkdir(exist_ok=True)
    if example.exists() and example.read_text() != helper:
        raise RuntimeError("refusing to overwrite a different exporter: " + str(example))
    if not example.exists():
        example.write_text(helper)
    build = ["cargo", "+1.98.1", "build", "--locked", "--example", "producer_reason_sound_types"]
    with (output / "build.log").open("w") as log:
        subprocess.run(build, cwd=source, env=env, stdout=log, stderr=log, check=True)
    binary = Path(env["CARGO_TARGET_DIR"]) / "debug/examples/producer_reason_sound_types"
    spec = importlib.util.spec_from_file_location("producer_reason_inference", LAB / "receipts/inference.py")
    inference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inference)
    checker = inference.load_checker()
    (output / "source.diff").write_text(git(source, "diff", "HEAD"))
    inputs = [p for name in PROGRAMS for p in (LAB / "reproductions" / name).rglob("*") if p.is_file()]
    inputs += [LAB / "receipts/F19" / name / "trace.jsonl" for name in PROGRAMS]
    receipt = dict(condition="reflective-evaluated-containers-20261015-fe6b169e/F19", timed_measurement=False, source_head=git(source, "rev-parse", "HEAD"), source_status=git(source, "status", "--porcelain"),
                   source_diff_sha256=sha(output / "source.diff"), binary_sha256=sha(binary),
                   source_files_sha256={str(p.relative_to(source)): sha(p)
                                        for p in sorted((source / "src").rglob("*.rs"))},
                   exporter_sha256=sha(example), cargo_lock_sha256=sha(source / "Cargo.lock"),
                   lab_head=git(LAB, "rev-parse", "HEAD"), build=build,
                   inputs={str(p.relative_to(LAB)): sha(p) for p in inputs}, candidate_env=candidate)
    dump(output / "condition.json", receipt)
    arms = [("s3", {k: "0" for k in candidate})]
    if candidate:
        arms.append(("candidate", candidate))
    summaries = []
    for arm, extra in arms:
        for name in PROGRAMS:
            dest = output / arm / name
            dest.mkdir(parents=True)
            frozen = LAB / "receipts/F19" / name / "baseline"
            for filename in ("selection.json", "slots.json"):
                (dest / filename).write_bytes((frozen / filename).read_bytes())
            command = [str(binary), str(LAB / "reproductions" / name), str(dest / "selection.json")]
            flags = dict(S3, **extra)
            flags.update(SOUND_MISSING="1", RH_FOLD_PRINT="1", RH_FIXPOINT_VERIFY="0",
                         PROVENANCE_AUDIT_PATH=str(dest / "audit.json"), NO_COLOR="1")
            started = time.monotonic()
            result = subprocess.run(command, cwd=source, env=dict(env, **flags),
                                    capture_output=True, text=True, timeout=180)
            (dest / "stderr.log").write_text(result.stderr)
            (dest / "stdout.log").write_text(result.stdout)
            if result.returncode:
                raise RuntimeError("exporter failed: " + str(dest))
            raw = json.loads(result.stdout)
            dump(dest / "raw.json", raw)
            selection = json.loads((dest / "selection.json").read_text())
            if set(raw) != set(selection):
                raise RuntimeError("selected aliases changed")
            final = {a: ("untyped" if t == "__missing__" else
                         t.replace("__var__", "untyped").replace("__bot__", inference.BOT))
                     for a, t in raw.items()}
            (dest / "final.rbs").write_text("".join("type " + a + " = " + t + "\n" for a, t in sorted(final.items())))
            (dest / "graph.rbs").write_text(inference.reduced_grammar(result.stderr, final, selection))
            audit = json.loads((dest / "audit.json").read_text())
            slots = json.loads((dest / "slots.json").read_text())
            coverage = dict(
                selected_slots=len(slots), missing=[a for a, t in raw.items() if t == "__missing__"],
                opaque=[a for a, t in final.items() if "untyped" in t],
                tags={tag: [a for a, row in audit.items() if tag in row["tags"]]
                      for tag in ("Pending", "Unresolved", "Gradual", "Var")},
                unsupported=[a for a, row in audit.items() if row["unsupported_by_exporter"]])
            records = checker.load_records(LAB / "receipts/F19" / name / "trace.jsonl")
            coverage["missing_observations"] = [
                dict(record_line=line, slot=record["slot"], alias=slots[record["slot"]])
                for line, record in records if slots[record["slot"]] in coverage["missing"]]
            for stage in ("final", "graph"):
                report = checker.check_records(checker.Grammar((dest / (stage + ".rbs")).read_text()),
                                               records, slots)
                # Preserve the lab's historical membership counts, but never
                # let its missing-as-untyped convention certify coverage.
                report["legacy_membership_only"] = report.pop("sound")
                report["strict_selected_gate"] = not (
                    report["violations"] or coverage["missing"] or coverage["unsupported"])
                report["coverage"] = coverage
                dump(dest / (stage + "-oracle.json"), report)
                summaries.append(dict(arm=arm, program=name, stage=stage, records=report["records"],
                                      rejected=report["records"] - report["accepted"], coverage=coverage,
                                      strict_selected_gate=report["strict_selected_gate"],
                                      violations=report["violations"], wall_seconds=time.monotonic() - started))
            dump(dest / "command.json", dict(command=command, flags=flags))
    dump(output / "summary.json", summaries)
    print(json.dumps({"output": str(output), "rows": len(summaries),
                      "meaning": "membership and coverage observations; no automatic soundness certificate"}))


if __name__ == "__main__":
    main()
