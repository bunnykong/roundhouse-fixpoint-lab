#!/usr/bin/env python3
"""Assign every NARROW row (runtime_sets.py, primary reading) to a family and a soundness verdict.

Recorded data only. Inputs: evidence/runtime-rows.tsv (from runtime_sets.py) and the contributor-classify rows.jsonl
(for source spans). Verdicts, relative to main (the baseline of ownership-runtime-values-20261015-f78d995f):

  UNSOUND_W    the arm excludes a value CRuby produced for this slot or for the expression's source slot
               (runtime-witnesses-v3.json, condition ownership-ruby-boundary-witnesses-20261015), which main admitted
  SOUND_W      the arm narrows, and every CRuby value recorded for the source slot is admitted (contract-relative)
  SOUND_GUARD  the expression is read inside an is_a? guard that implies the arm type (Ruby semantics; source span checked)
  BOUNDARY     a CRuby value outside the arm exists only at the method boundary (unset ivar); every request-path
               reader found by source inspection runs after the assignment
  UNWITNESSED  the arm narrows and no witness covers the excluded values
Families: R render/redirect/respond_to contract; C customization with a modeled contract; G guarded read;
J JSON-LD return; P parameter lost unknown call-site arms; V Var-only loss; B boundary ivar.
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROWS = HERE.parents[0] / "ownership-runtime-values/receipts/rows.jsonl"
GUARDED = {449, 933, 969, 1456, 1464, 1465, 1539, 1586, 1759, 7883, 7908, 11952}
PARAM_LOSS = {12079, 12140}
RENDER = {"check_account_suspension", "permanent_unavailability_response", "temporary_suspension_response"}


def family(r, span):
    app, root, arm = r["app"], r["root_method"], r["arm"]
    meth = root.split("#", 1)[1] if "#" in root else root
    if app == "forem":
        return "R", "UNSOUND_W"
    if meth in RENDER or root == "Api::Web::EmbedsController#show":
        return "R", "UNSOUND_W"
    if "Admin::ActionLog" in arm:
        return "C-log_action", "SOUND_W"
    if meth == "pundit_user":
        return "C-pundit_user", "SOUND_W"
    if meth == "webauthn_enabled?" or "auth/sessions/two_factor" in root:
        return "B", "BOUNDARY"
    if meth == "first_lang_string" and r["part"] == "returns":
        return "J", "UNSOUND_W"
    if (span and span.get("file") == 966 and span.get("start") in GUARDED) or root.startswith("Some(Narrow"):
        return "G", "SOUND_GUARD"
    if (span and span.get("file") == 966 and span.get("start") in PARAM_LOSS) or meth == "non_matching_uri_hosts?":
        return "P", "UNWITNESSED"
    if r["baseline"] == "String | Var" and arm == "String":
        return "V", "UNWITNESSED"
    return "?", "UNCLASSIFIED"


def main():
    spans = {}
    for line in ROWS.open():
        j = json.loads(line)
        row = j.get("arm_row") or j.get("baseline_row") or {}
        spans[j["row_id"]] = row.get("span")
    out = Counter()
    fam = defaultdict(Counter)
    classification_counts = defaultdict(Counter)
    lines = []
    with (HERE / "evidence/runtime-rows.tsv").open() as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["relation"] != "NARROW":
                classification_counts[(r["classification_label"], r["relation"])]["-"] += 1
                continue
            f, v = family(r, spans.get(r["row_id"]))
            out[v] += 1
            fam[(r["app"], f, v)][r["part"]] += 1
            classification_counts[(r["classification_label"], "NARROW")][v] += 1
            lines.append("\t".join([r["row_id"], r["app"], r["schedule"], r["part"], r["root_method"][:90], f, v,
                                    r["baseline"], r["arm"]]))
    (HERE / "evidence/narrow-verdicts.tsv").write_text(
        "row_id\tapp\tschedule\tpart\troot_method\tfamily\tverdict\tbaseline\tarm\n" + "\n".join(lines) + "\n")
    print("NARROW verdicts:", dict(out))
    for k in sorted(fam):
        print("  %-9s %-14s %-12s n=%-4d %s" % (k[0], k[1], k[2], sum(fam[k].values()), dict(fam[k])))
    print("prior classifier class x relation x verdict:")
    for k in sorted(classification_counts):
        print("  %-12s %-7s %s" % (k[0], k[1], dict(classification_counts[k])))


if __name__ == "__main__":
    main()
