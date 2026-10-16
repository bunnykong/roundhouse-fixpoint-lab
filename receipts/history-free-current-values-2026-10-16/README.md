# History-free current values

Unscored research reference. More schedule equality, with witnessed value loss. Review: WEAKENED; corrections applied.

## Fact F71

On `history-free-current-values-20261016-four-apps`, current writer contributions make all ten Forem value tables schedule-equal (six before) across unset/1/2/repeat at V0A0 and V1A1. The candidate is unsound: audited unset-V0A0 rows lose CRuby 4.0.7 values—Campfire 1, Forem 6, Chatwoot 44, Mastodon 10. It combines parameter views, real unknowns kept, current call-site rows/site values, F70 stub completion and canonical unknown spelling. Campfire stays at ten equal tables; Chatwoot rises from five to six; Mastodon stays at five, with varying IR rows falling from 1,920 to 269. Two traced losses omit arguments when the receiver is unknown: preview transformation arrays and includes options. Routing follow-ups restore those two witnesses but leave another audited failure and bring back order dependence; this cause is not shown to dominate all losses. V0A0 disables verification/audit; V1A1 enables both. Many narrowings remain unaudited. Discourse was not run; soundness and order independence are not achieved together.

## Condition and pins

[Pins](pins.json) identify the [public branch](https://github.com/bunnykong/roundhouse/tree/4a80f31d27c624039a58e81f275fdc8664d21c93), original executable, public inputs and toolchains.
The five parts are parameter views, retained real unknowns, current call-site rows and site values,
F70 stub completion, and a final canonical spelling for retained unknowns. Bare holes and explicit Pending remain.
All four apps use the research profile with ownership and stabilization bypass on. V0A0 and V1A1 are separate
observers, each comparing unset, 1, 2 and an independent repeat. Discourse and other observers were not run.

| App | Equal tables before → after, at each observer | Confirmed new loss rows, unset V0A0 |
| --- | --- | --- |
| Campfire | 10 → 10 | 1 |
| Forem | 6 → 10 | 6 |
| Chatwoot | 5 → 6 | 44 |
| Mastodon | 5 → 5 | 10 |

Mastodon IR varies in 269 rows, down from 1,920, separately at each observer. This is table-digest equality at
the four named schedules, not equality for all possible orders. [Cause notes](cause-notes.md) retain the two
upheld omissions and the failed routing follow-ups next to this gain.

## Receipt label map

- `quick-probe-v1 / observers-v1-20261015 / F61` → `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`.
- `qt-canon-09181f25` → `history-free-current-values-09181f25`, within `history-free-current-values-20261016-four-apps`.
- `spine3-control` → `response-return-spine-control`.
- `qt-m461-4d452925` → `current-call-values-4d452925`, the prior classification reference.
- `qt-cand1-b4b3ae9f` → `completed-current-values-b4b3ae9f`, the immediate pre-canonical comparison.
- `qt-top-44182d62` → `unresolved-route-followup-44182d62`.
- `qt-route-2006ff94-df6d5f4` → `static-route-followup-2006ff94`.
- `RH_S6_PARAM_VIEWS`, `RH_ROW_CURRENT`, `RH_S3D_COMPLETE`, `RH_CANON_VAR` →
  `RH_PARAMETER_VIEWS`, `RH_CURRENT_CALL_ROWS`, `RH_STRICT_STUB_COMPLETE`, `RH_CANONICAL_UNKNOWN`.

Raw labels occur only in this map and unchanged evidence. The [manifest](manifest.json) binds original,
public uncompressed and stored bytes. `raw/` preserves exact decompressed bytes; `derived/` and `native/`
contain declared public spelling, path, dependency or selected-function copies. Original evidence is unchanged.
Original result/review/cause reports remain outside Git, with hashes retained. Full app streams, binaries and
app/dependency trees are omitted; compact native reports retain captured identities.

## Classification and review limits

The [classification summary](classification-summary.json) separates the prior reference from this candidate.
Prior narrowed counts are 1/105/202/272; this candidate has 1/105/199/269, in app order above. It removes three
Chatwoot and three Mastodon identities, adding none. The earlier source report's exact-identity claim is not retained.
The original classification covers all 74 concrete/nil rows plus 40 random rows and 18 additional checks.
It adjudicates 132 rows of the prior reference; many others have only provenance. That coverage is not blanket
certification of this candidate. Its 61 new-loss rows are rechecked against native candidate values and runtime
witnesses. Chatwoot's inherited C114 mismatch is retained and excluded from those 61. Five rows received fresh
Ruby executions in the independent review; other review witnesses reuse retained runtime receipts.

The standard report remains `complete=false`, exit 1. At unset V0A0 and, separately, unset V1A1, missing or
unclassified rows number 18/59/873/340. Native cells, ten-table digests and row-variance counts are complete.
Five fresh Forem cells match every standard observation; other apps use retained native cells in the light review.

All four portable witness programs ran during publication, matching recorded observation types, classes,
expressions and application-source hashes. They use finite source-preserving boundaries and real pinned libraries;
they do not boot whole apps. Four in-memory/local fixtures do not establish reachability beyond the retained source proofs.
Dynamic display strings are not claimed byte-identical. No native analyzer ran during packaging.

The recorded focused native run passes six checks. Both library modes pass 1,258 tests with 37 ignored.
The earlier setup failure remains retained. No full integration or emission suite is claimed.
[Source equivalence](source-equivalence.json) binds 13 native files; assertions, tests and ignores are retained.
The public Rust spelling port was parsed, not compiled. Prerequisite protocol/tool files remain outside the code branch.

## Reproduce

From this receipt directory:

```sh
python3 -B rerun.py saved
python3 -B -m unittest discover -s ../../tools/probe -p test_probe.py -v
```

The saved replay verifies retained hashes, 64 native grid result/report pairs, equality memberships,
the changed narrowing sets, runtime admission failures, selected call traces and the remaining routing rejection.
It checks reported row-variance counts against the independent recount, without reconstructing omitted full streams.
The [reusable checker](../../tools/probe/README.md) retains incomplete relations; these checks start no analyzer.

For the source-preserving Ruby witnesses, install the libraries in [dependency pins](native/dependency-pins.json),
put pinned inputs under `inputs/APP` and select fresh output and gem roots:

```sh
export RBENV_VERSION=4.0.7 PUBLIC_INPUTS=$PWD/inputs CAMPFIRE_INPUT=$PWD/inputs/campfire
export WITNESS_GEM_ROOTS=$PWD/gems WITNESS_OUTPUT=$PWD/witness-output
mkdir -p "$WITNESS_OUTPUT"
for app in campfire forem chatwoot mastodon; do
  rbenv exec ruby "native/witnesses/witness_$app.rb"
done
```

Multiple gem roots use the platform path separator. Default gems without retained packages have null package
hashes; all loaded versions are recorded. Membership aliases for Time, Arel nodes and request values remain explicit.
For fresh native observations, use `profiles/control.json` and `profiles/candidate.json` with the public checker,
selecting both V0A0 and V1A1. The observer pins Ruby/inputs and takes the shared host lock.
The focused `native.sh` recipe is syntax-checked and unexecuted during publication; it needs the pinned compiler,
fresh OUTPUT and public HOST_LOCK_WRAPPER/HOST_LOCK_FILE. No whole-analyzer soundness claim follows.
