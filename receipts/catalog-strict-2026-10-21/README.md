# Strict catalog

Unscored research reference. An independent check upholds the result with corrections; the fact includes them.

## Fact F76

On `catalog-strict-20261021-four-apps-v0a0`, a flag (`RH_STRICT_CATALOG=1`) on top of F75's candidate makes the send catalog answer Pending while an operand is entirely Pending. In the law-harness pair that isolates the flag, all 21 registered catalog strictness failures pass; the other laws still have 916 FAIL and 123 UNKNOWN. All four apps keep 10/10 equal tables with zero varying rows across unset/1/2/repeat at V0A0, Mastodon also across twelve schedules, and no value set narrows or widens against F75. The 38 added side-table identities (30 Param, 7 Narrow, 1 At) carry no new value. The costs: in every cell, 3.6–7.7% more values are still Pending at the completion barrier, where completion makes them Unresolved; and one Chatwoot reason row's provenance now depends on the schedule (Unresolved at unset and repeat, Gradual at 1 and 2), where F75 had one form. The flag exposes older gaps it does not cause: once the operand resolves, `Int + Float` is still typed `Int`, and a BigDecimal or Float count to `first`, `last` or `sample` still gives a scalar where Ruby returns an Array. An independent check reran 8 cells without rebuilding and upholds the result with these corrections. F73's losses remain; V1A1 and Discourse were not run.

## What changed

With `RH_STRICT_CATALOG=1`, the send catalog waits while an operand is entirely Pending: receiver conversions,
numeric promotion, counted and indexed Array and Relation calls, Date arguments, object protocols and
`deep_merge` answer Pending instead of a definite type. Known containers with Pending children stay readable.
The production change is in `src/analyze/body/send.rs` ([catalog-strict.patch](catalog-strict.patch)); the branch
also carries the tagged operator-law audit and its focused tests.

The gates reach further than the 21 registered projections. Dispatch on a Pending receiver waits for every
method, and so does every object-protocol method. Class-side and Relation counted `first`/`last` have no
registered projection.

Source: [research/catalog-strict-5a6f535e](https://github.com/bunnykong/roundhouse/tree/3e115e9af84dcb710be660d0721005d6e118ee1f). The branch holds a
build-identical snapshot of measured commit `5a6f535e` with the `research/` harness files removed, so its hash
differs. It sits on F75's branch.

## Condition

- Candidate: `catalog-strict-5a6f535e`, which is F75's candidate with `RH_STRICT_CATALOG=1`. Commit `5a6f535e`
  over F75's `f2597823`. Binary SHA-256: `247a5787bc964f377eb4bd2c567683cab17011048e6e77c7e59dc1be3db7290d`.
- Control: `binding-projection-f2597823`, F75's candidate.
- Checker: `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`, V0A0 (verification and audit off).
  Schedules: unset, 1, 2 and an independent unset repeat; Mastodon also ran `RH_SHUFFLE` seeds 3 to 10.
- Independent check: 8 fresh cells with the same binary and profile, without rebuilding: Campfire on unset and
  repeat, Forem on unset and 1, Chatwoot on unset and 2, and Mastodon on unset and seed 7. Each matched its
  original in every observation field and row signature. With the flag unset, Campfire, Forem and Chatwoot
  reproduce F75 in all nine observation fields.

## Law harness

The registered harness checks 5,022 law rows. Only the pair with the same profile, flag unset against flag set,
isolates the flag. There, exactly the 21 catalog strictness rows change, all from FAIL to PASS, and all 85
registered catalog strictness projections pass ([catalog-strictness.tsv](catalog-strictness.tsv)). The other laws
still have 916 FAIL and 123 UNKNOWN rows. The plain audit pair also toggles the strict guard, so its other
changes, four `intersect_with` rows going from PASS to FAIL, belong to the guard. This is the registered finite
audit, not a proof about the whole analyzer.

## Tables

| App | Equal tables | Varying rows | Narrowed / widened / added, each schedule |
| --- | ---: | ---: | ---: |
| Campfire | 10/10 | 0 | 0 / 0 / 0 |
| Forem | 10/10 | 0 | 0 / 0 / 0 |
| Chatwoot | 10/10 | 0 | 0 / 0 / 31 |
| Mastodon, twelve schedules | 10/10 | 0 | 0 / 0 / 7 |

Some rows change form only: in Chatwoot, 25 controller-cache rows and 27 side-table rows, and one Mastodon
side-table row. A reference replaces a copy, or a union repeats an arm (`Str | Str`). Flattened, all 53 equal
F75 in every schedule. Diagnostics and writes do not change. [tables.json](tables.json) holds every count.

## The 38 added identities

All 38 appear in every schedule, none is removed, and none carries a new value
([added-identities.tsv](added-identities.tsv)):

- 30 `Param` slots, 24 in Chatwoot and 6 in Mastodon. Each equals its method's parameter row, and that row is
  unchanged from F75.
- 7 `Narrow` rows in Chatwoot: type tests on those methods' values, such as `email.present?`,
  `username.blank?` and four arms of `case legacy_params`.
- 1 `At` row in Mastodon: the `options` value in `RemoveStatusService#call`, which still resolves to `Bool`.

## Costs

- More values are still Pending at the completion barrier, in every cell
  ([completion-barrier.tsv](completion-barrier.tsv)). Campfire goes from 1,752 to 1,887 (+7.7%), Forem rises
  5.9–6.6%, Chatwoot 5.3–5.4% and Mastodon 3.6%. Completion makes these values Unresolved.
- One Chatwoot reason row's provenance now depends on the schedule ([reason-row.json](reason-row.json)). In
  `Captain::PreferencesController#features_with_account_preferences`, the row is Unresolved at unset and repeat
  and Gradual at 1 and 2. F75 has Unresolved in all four, and fresh reruns reproduce both forms. The row's type
  does not change.

## Three operators with CRuby 4.0.7

[catalog_witness.rb](catalog_witness.rb) runs three of the 21 operators in CRuby 4.0.7.

| Operator | Before, operand Pending | After it resolves | CRuby 4.0.7 |
| --- | --- | --- | --- |
| `Int` `+ - * /` | `Int` | `BigDecimal` for BigDecimal, else `Int` | Integer, Float, BigDecimal, Rational |
| `Array#first(n)`, `last`, `sample` | `Array[elem]` | `Array` for Int or Unresolved, else a scalar | Array for any numeric `n` |
| `Date.parse` | `Date` | `Date` if accepted, else Unresolved | Date; nil, Integer and BigDecimal raise |

The flag cannot lose a value on its own. A resolved operand takes the unchanged path, and an operand still
Pending at the barrier becomes Unresolved, which gets the old answer. The witness exposes gaps in the unchanged
paths that the flag neither causes nor fixes. `Int + Float` is typed `Int`, and a BigDecimal or Float count gives
a scalar where Ruby returns an Array. A slot that joins across passes could have kept an early answer that hid
such a gap; none did in the 24 cells.

## Limits

- This is a strictness and order-independence result, not a soundness certificate. F73's losses remain, and so
  do the older catalog gaps above.
- Only V0A0 was run. V1A1 and Discourse were not.
- The independent check did not rebuild, rerun the Rust tests or rerun the law harness; the law counts come from
  the original run. That run passed 1,297 library tests (69 ignored) with the flag unset and the checker's 40
  tests. The aggregate law-audit test still fails because of the other laws.
- Composed dispatch contexts outside the registered projections are not certified.

## Receipt label map

- `qt-catalogstrict-5a6f535e` → `catalog-strict-5a6f535e`, within `catalog-strict-20261021-four-apps-v0a0`.
- `qt-cbproj2-f2597823` → `binding-projection-f2597823`.
- `quick-probe-v1 / observers-v1-20261015 / F61` → `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`.
- Law-harness pairs: `profile-audit-off` and `profile-audit-on` are the flag pair; `audit-off` and `audit-on` are
  the plain audit pair, which also toggles the strict guard.
- The independent check used its own labels for its fresh cells; they are separate native runs.

## Reproduce

From the lab root:

```sh
python3 -B receipts/catalog-strict-2026-10-21/check.py
ruby receipts/catalog-strict-2026-10-21/catalog_witness.rb
```

`check.py` recomputes the counts above from [tables.json](tables.json) and the TSV files; it starts no analyzer.
The witness needs only CRuby 4.0.7 with its bundled `bigdecimal` and `date`.
