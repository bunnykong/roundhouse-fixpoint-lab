# Integrated current writers

Unscored research reference. Review: UPHELD. The schedule-equality gain is unsound.

## Fact F72

On `integrated-current-writers-20261016-four-apps-v0a0`, the integrated rule makes Campfire/Forem/Chatwoot/Mastodon 10/9/10/5 value tables schedule-equal across unset/1/2/repeat at V0A0, versus spine v3’s 10/6/5/5. It is unsound: Chatwoot loses witnessed values in 16/40 sampled concrete/nil drops (40%; exact 95% interval 26.4–55.0%) and 5/15 unknown drops (33.3%; 11.9–61.5%). Forem and Mastodon also lose sampled values. Two newly equal Chatwoot rows lose values. Array appends, loop-carried values and hash updates/merges dominate sampled losses; current transfers omit their additions. The rule uses current writers, source Unresolved, waiting Pending inputs then completion, conservative unknown-receiver routing, F70 stub completion and current harvested returns. Its saved 300-check regression gate passes; settlement has zero Pending. Light review upholds these scoped results. Most narrowed rows remain unaudited; rates describe rows within each stratum. Verification/audit are off; Discourse was not run.

## Condition and pins

[Pins](pins.json) identify the [public branch](https://github.com/bunnykong/roundhouse/tree/991ec4b356a21cf53271737124533c617e01e847), executable hash, public app commits and toolchains.
The candidate joins current writer contributions instead of history; retains real unknowns as Unresolved at their
source; waits for Pending inputs before a second completion phase; conservatively routes receivers still unknown
after completion; includes F70 stub completion; and joins current harvested returns.

The research profile enables ownership and bypasses stabilization. V0A0 disables verification and audit.
Equality compares native table digests across unset, 1, 2 and an independent repeat. Only these four apps and
this observer were tested. Discourse and V1A1 were not run for this candidate. This is no all-order or speed result.

| App | Equal value tables, spine v3 → candidate |
| --- | --- |
| Campfire | 10 → 10 |
| Forem | 6 → 9 |
| Chatwoot | 5 → 10 |
| Mastodon | 5 → 5 |

All 16 candidate cells have zero Pending at completion and settlement. The saved regression gate passes
300 checks: 288 earlier row checks, eight export checks and four indifferent-access checks. This replays saved
native types against saved Ruby receipts; it is not 300 fresh Ruby executions or a soundness certificate.

## Stratified census

Unset-V0A0 narrowed rows form two disjoint strata per app: a concrete/nil drop, or unknown-only drops.
Samples use sorted `(table,key)` identities without replacement. A new loss is a runtime value admitted by
control and rejected by the candidate. The [summary](census-summary.json) retains all counts and intervals.

| App / stratum | Population | New losses / sample | Estimate | Exact 95% interval |
| --- | --- | --- | --- | --- |
| Chatwoot concrete/nil | 220 | 16/40 | 40.0% | 26.4–55.0% |
| Chatwoot unknown only | 2,405 | 5/15 | 33.3% | 11.9–61.5% |
| Mastodon concrete/nil | 247 | 16/30 | 53.3% | 35.6–70.4% |
| Mastodon unknown only | 2,627 | 4/10 | 40.0% | 12.2–73.7% |
| Forem concrete/nil | 95 | 11/30 | 36.7% | 23.2–52.6% |
| Forem unknown only | 639 | 2/10 | 20.0% | 2.7–55.2% |

These are marginal row intervals from exact hypergeometric-tail inversion, not unique-bug rates or a pooled
estimate. Of 135 sampled rows, 54 are new losses, six inherited errors and 75 adjudicated sound. Two additional
targeted Chatwoot losses, C1431/C1432, are excluded from the rates. Of 6,233 narrowed rows, 6,096 remain unadjudicated.
The census excludes incomparable, missing/unserialized rows and other schedules; Campfire has no sample here.

[Cause notes](cause-notes.md) connect array/hash omissions to the witnessed losses and retain attribution limits.
Array/hash/missing-caller sampled loss counts are Chatwoot 13/6/2, Mastodon 11/6/3 and Forem 11/2/0.
Two newly equal Chatwoot rows reject reachable nonempty hashes: equality improves by losing values.

## Light check and limits

The independent light check freshly reruns Chatwoot unset and repeat, with zero cache hits. All available standard
observations, binary/input/runtime and effective flags match. Across 254,601 serialized identities per capture,
types/provenance agree after normalization; repeat renumbers 583 debug reference IDs. Writes, law violations and
verification are unavailable on both sides, not zero. Both fresh completion replays close after 11 iterations.

The light check freshly executes 23 Chatwoot observations and checks four counterexamples across the native schedules.
It reproduces all six sample selections, counts and exact intervals, but does not re-audit every sample adjudication.
Its earlier failed comparison/witness-check attempts remain in the packet. The standard report stays `complete=false`,
exit 1: missing/unserialized comparisons are Campfire 1,574, Forem 9,158, Chatwoot 10,582 and Mastodon 14,429.
All eight control/candidate Chatwoot cells and ten equality comparisons are valid; this is not a complete F61 audit.

During publication all three portable CRuby 4.0.7 witness programs reproduce observation types, classes, expressions,
boundaries and source hashes. They execute unchanged source with finite request/database/library boundaries,
not full app boots. Dynamic display strings are not byte-identical. The first Forem port attempt selected a newer
JSON library and failed; restoring the original 2.18.0 pin fixes that dependency selection. Its error log is retained.

Original native logs retain focused checks and 1,288 library passes with 54 ignored. The earlier missing-fixture
library failure remains. No full integration or emission suite is claimed. [Source equivalence](source-equivalence.json)
binds all 23 changed native files, with assertions and test/ignore counts retained. Nine prerequisite protocol/tool
files stay outside the code branch. The public Rust spelling port was parsed, not compiled. Packaging runs no analyzer.

## Receipt label map

- `quick-probe-v1 / observers-v1-20261015 / F61` → `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`.
- `qt-whole3-f9a7e620` → `integrated-current-writers-f9a7e620`, within `integrated-current-writers-20261016-four-apps-v0a0`.
- `spine3-control` → `response-return-spine-control`.
- `qt-whole2-3aec0c0b` → `completed-current-writers-3aec0c0b`.
- `qt-canon-09181f25` → `history-free-current-values-09181f25`.
- `RH_S6_PARAM_VIEWS`, `RH_ROW_CURRENT`, `RH_S3D_COMPLETE`, `RH_CANON_VAR`, `RH_RS5` →
  `RH_PARAMETER_VIEWS`, `RH_CURRENT_CALL_ROWS`, `RH_STRICT_STUB_COMPLETE`, `RH_CANONICAL_UNKNOWN`, `RH_PENDING_INPUT_SEEDS`.
- Original seed prefix `ast-whole3-census-20261016` → `integrated-current-writers-census-20261016`.

The [manifest](manifest.json) binds original, public uncompressed and stored bytes. `raw/` retains exact decompressed
bytes; `derived/` and `native/` contain declared public spelling/path/selection copies. Originals are unchanged.
The public sampler uses the exact Python version-2 integer representation of each original string seed;
[seed data](native/census-seeds.json) and assertions preserve the same six ID sets. The full census is retained;
the Ruby fixture selects only its 135 sampled and two targeted rows. Native wire fields retain their schema.
Original narrative reports stay outside Git with hashes retained; full app streams, binaries and dependency trees are omitted.

## Reproduce

From this receipt directory:

```sh
python3 -B rerun.py saved
python3 -B -m unittest discover -s ../../tools/probe -p test_probe.py -v
```

The saved replay checks hashes, 32 native grid result/report pairs, two fresh review cells, sample selection/arithmetic,
runtime admissions, targeted stabilizing losses and the 300 saved regression checks. It does not recount omitted
full streams or establish every sound adjudication anew. The [reusable checker](../../tools/probe/README.md) retains
incomplete relations. Its 40 controls and the 14 observer tests start no analyzer.

For fresh witnesses, install [pinned dependencies](native/dependency-pins.json), acquire the pinned apps and select
fresh output/tmp directories. PAPERCLIP_ROOT is the installed kt-paperclip 7.3.0 source root.

```sh
export RBENV_VERSION=4.0.7 PUBLIC_INPUTS=$PWD/inputs CAMPFIRE_INPUT=$PWD/inputs/campfire
export WITNESS_GEM_ROOTS=$PWD/gems WITNESS_OUTPUT=$PWD/witness-output
export WITNESS_TMPDIR=$PWD/witness-tmp PAPERCLIP_ROOT=$PWD/gems/gems/kt-paperclip-7.3.0
mkdir -p "$WITNESS_OUTPUT" "$WITNESS_TMPDIR"
for app in forem chatwoot mastodon; do
  rbenv exec ruby "native/witnesses/witness_$app.rb"
done
```

Multiple gem roots use the platform path separator. Loaded default gems without retained archives have null
package hashes. Membership aliases for Time, Arel nodes and request values remain explicit.
Use `profiles/control.json` and `profiles/candidate.json` with the public checker for fresh V0A0 observations;
the observer supplies pinned runtime/inputs and the shared lock. The focused `native.sh` recipe is syntax-checked
and unexecuted here; it needs the pinned compiler, fresh OUTPUT and the public host lock helper/file.
