# Quick-test checker

Run a spine-v3 idea and compare saved observations with a control. Python 3.9+, standard library only.

```bash
python3 tools/probe/probe.py run --bin BINARY --profile PROFILE.json --label trial --set RH_FLAG=1
python3 tools/probe/probe.py report --control baseline --candidate trial
python3 -m unittest discover -s tools/probe -p test_probe.py -v
```

Defaults: Campfire, Forem, Chatwoot and Mastodon; unset/1/2/repeat at V0A0.
Select subsets with `--apps forem,chatwoot` and `--settings unset-v0-a0,1-v0-a0`.
Every cell uses `tools/observers/obs.py`, its named settings, cache, runtime pin and shared locks.
The profile is a JSON flag map; `--set K=V` accepts repeated flags or multiple pairs. JSON null unsets an observer default.
`RH_CONTRIBUTOR_VALUES=1` is mandatory. Schedule/audit/verification and dump destinations belong to the observer.
Runs use four jobs and a 600-second native timeout (`--jobs` / `--timeout`); lock queues and reduction add time.
`--fresh` explicitly retries through the observer's immutable attempt mechanism.
Choose a new label after changing a binary or profile. Labels may accumulate apps/settings of the same condition.

Reports default to `tools/probe/reports/CONTROL--CANDIDATE/report.{md,json}`; `--out DIR` overrides this.
Both commands accept `--cache-root DIR` (default: `tools/observers/cache`). Report invokes no analyzer.
Each app and V/A group is separate; equality always requires all four schedules, including the independent repeat.
The Markdown is at most 60 lines; JSON retains full conditions, identities, narrowed types and missing-data reasons.

- Equal tables: identical native value digests in all four schedules, separately for control and candidate.
- Varying rows: union of `(table,key)` identities with different `(hash,note,module)` signatures or presence.
  Parameters count positions and present empty vectors; controller cache counts bindings/expressions.
  Other fingerprint-only tables count native entries. IR annotations therefore also affect row differences.
- Unset F61: candidate types that admit a strict subset of control values are listed with full identities.
  Untyped/raw Var admit everything; containers recurse through the F61 runtime-set relation. Widen/equal/incomparable are separate.
  Symbolic references use the retained symbolic-reference resolver, including stable references whose targets may have changed.
- Diagnostics: complete observed counts by severity/kind and total, per cell. An absent kind in a valid map is zero.
- Wall seconds: native process time from the observer; excludes lock queues and Python reduction. Shared-host profiles only.

Missing/invalid cells, unsupported values and unresolved relations stay missing/null. They never become zero counts.
Five tables currently serialize types (R/P/CC/IR/ST); changed fingerprint-only rows cannot receive an F61 verdict.
Identical fingerprints count unchanged. Structural row additions/removals and unresolved cycles need separate review.
Dump SHA-256, native fingerprint coverage and parameter/cache parent differences are checked before row claims.
Different inputs/runtimes or mixed binaries/profiles across schedules invalidate the corresponding comparison.
Report exits 0 for complete evidence, 1 for missing evidence, 2 for a bad request; narrowing itself does not change exit status. Soundness needs runtime witnesses.

## Public tool copy

F70 is the first fact measured with this standard quick-test checker. This copy includes the exact row
signatures, symbolic-reference resolver and F61 runtime-set predicates it imports, selected without logic changes.
The [port record](port.json) binds every original and public file. Paths, flags and labels use public spellings.
All original tests are retained, including the F68 thirteen-row positive fixture; the test run must have no skips.
The [F70 receipt](../../receipts/strict-stub-completion-2026-10-16/README.md) retains the original incomplete report.
Its two cyclic Chatwoot rows need separate exact-graph evidence; this tool does not silently classify them as equal.

Use the public compiler and the observer's pinned applications under `corpus/apps/`. Clear ambient research
flags; the observer supplies the runtime and shared lock. No binary, app checkout or native result is bundled
as a substitute for a fresh run. The checker tests use synthetic cache controls and the recorded F68 fixture;
they start no native analyzer. `report` verifies saved captures and starts no analyzer.

Receipt label map: `quick-probe-v1 / observers-v1-20261015 / F61` becomes
`quick-test-v1 / cached-observers-20261015-source-rebuild / F61`. The native flag `RH_S2_VALUES` becomes
`RH_CONTRIBUTOR_VALUES`, and `s2-values.jsonl` becomes `contributor-values.jsonl`, matching the public compiler.
