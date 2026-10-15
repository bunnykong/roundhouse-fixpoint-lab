#!/usr/bin/env python3
"""Sanity receipt: CARD-RESEARCH_PROFILE's K1, K4 and W checks applied to the recorded arm A against its baseline.

Reads agents/ownership-runtime-values/observer-cache (condition ownership-runtime-value-probes-20261015-f78d995f), the cells that
reproduce ownership-runtime-values-20261015-f78d995f. Expected: arm A fails K1 and W on Forem and Mastodon and K4 on all
three apps. Writes evidence/armA-through-card.json. No analyzer run.
"""
import json
import sys
from pathlib import Path

F = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(F / "phase2/contributor-ownership/contributor-protocol"))
import verdict as V  # noqa: E402

cache = F / "agents/ownership-runtime-values/observer-cache"
wmap = json.loads((F / "phase2/contributor-ownership/contributor-protocol/witness-map.json").read_text())
out = []
for app in ("forem", "chatwoot", "mastodon"):
    C, J = V.records(cache, "contributor-values-baseline-" + app), V.records(cache, "contributor-values-a-" + app)
    k, _ = V.check_floor_and_scope(C, J, app, V.V0, False)
    w = V.check_witnesses(C, J, app, V.V0, wmap)
    for c in k + w:
        if c["check"] in ("K1-floor", "K4-aliases", "W-witness"):
            d = c["detail"]
            n = d.get("count", len(d.get("failures", []))) if isinstance(d, dict) else None
            out.append({"check": c["check"], "scope": c["scope"], "status": c["status"], "count": n})
            print(c["check"], c["scope"], c["status"], n)
(Path(__file__).resolve().parents[1] / "evidence/armA-through-card.json").write_text(json.dumps(out, indent=1) + "\n")
