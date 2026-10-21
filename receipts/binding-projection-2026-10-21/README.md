# Binding projection

Unscored research reference. An independent check upholds the result with corrections; the fact includes them.

## Fact F75

On `binding-projection-20261021-four-apps-v0a0`, building the controller-binding table once, after completion, from completed method bodies (on top of F74's guard) makes all four apps schedule-equal: Campfire, Forem, Chatwoot and Mastodon have 10/10 equal tables and zero varying rows across unset/1/2/repeat at V0A0, and Mastodon keeps 10/10 across twelve schedules. With the guard alone, Forem and Chatwoot were 9/10. Only the binding table changes; the other nine tables keep the guard's digests. A first version dropped Forem's `@missing_configs`, which Ruby sets; the fix (`f2597823`) also reads included-module methods and changes only that row. Against the guard's table no binding is dropped or narrowed: 482 rows change in meaning, all as supersets, and 45 differ only in JSON form. The cost: 472 bindings are added, all reachable in Ruby by a source re-derivation, and 104 known values become partly or fully Unresolved, 95 of them in Chatwoot. "No omissions" holds against the old table, not against Ruby: both tables miss 45 bindings that Ruby reaches through calls inside hash arguments or string interpolation, and 4 Chatwoot rows from helper modules; this predates the change. An independent check reran 12 cells without rebuilding and upholds the result with these corrections. F73's losses remain; V1A1 and Discourse were not run.

## What changed

Under F74's guard alone, the controller-binding table is filled during the fixpoint and keeps refinements from
earlier rounds. Four Forem rows and two Chatwoot rows vary across schedules, so those apps stay at 9/10 equal tables.

With `RH_CB_PROJECT=1`, the table is cleared at entry, round refinements are no longer stored in it, and it is
built once after completion from the completed bodies of controller actions and their included module methods
([binding-projection.patch](binding-projection.patch): a new 237-line module with three unit tests, and nine
changed lines in `src/analyze/mod.rs`). Callback records supply only the target and kind of each callback.

A first version (`ce4eaf1a`) also reached 10/10 on the four apps but dropped Forem's `@missing_configs`. Its final
lookup held controller actions only, while the writer `VerifySetupCompleted#missing_configs` is a module function
that the before-action `verify_setup_completed` reaches. The fix (`f2597823`) adds each controller's included
module methods, nested includes too, to the final lookup. Across the four apps it changes exactly that one row.
One hazard predates the fix and did not occur here: class-side `def self.x` bodies are matched by name and the
first include wins, while Ruby takes the last. No controller-included module in the four apps has a class-side
ivar writer or an ivar-writing name clash.

## Condition

- Candidate: `binding-projection-f2597823`, which is F73's candidate with `RH_STRICT_GUARD=1` and `RH_CB_PROJECT=1`.
  Commit `f2597823` over F74's `48155b34`. Binary SHA-256:
  `668efeb73c2e8a67b9321522a694de684b2b941c435168f19738800302944e8c`.
- Control: `strict-pending-guard-48155b34`, F74's research-base candidate.
- Checker: `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`, V0A0 (verification and audit off).
  Schedules: unset, 1, 2 and an independent unset repeat; Mastodon also ran `RH_SHUFFLE` seeds 3 to 10.
- Independent check: 12 fresh cells with the same binary and profile, without rebuilding: Campfire and Forem on
  unset, 1, 2 and repeat, Chatwoot on unset and 2, and Mastodon on unset and seed 7. Each cell matched its
  original in all ten digests, diagnostics, loops, writes and reason rows.

## Tables

| App | Equal tables, guard → projection | Varying binding rows, guard → projection |
| --- | ---: | ---: |
| Campfire | 10 → 10 | 0 → 0 |
| Forem | 9 → 10 | 4 → 0 |
| Chatwoot | 9 → 10 | 2 → 0 |
| Mastodon | 10 → 10 | 0 → 0 |

With the projection, no row varies in any table. Mastodon keeps 10/10 equal tables with zero varying rows across
the twelve schedules. The nine other tables keep the guard's digests in all 16 cells, with no F61 narrowing or
widening, and diagnostics are unchanged: 485, 8,820, 8,150 and 7,194 per schedule. [tables.json](tables.json)
holds every count.

## The binding audit, corrected

The original audit called all 527 changed binding rows supersets, with zero omissions. The independent check
corrects it in three ways ([binding-changes.tsv](binding-changes.tsv)):

1. 482 rows change in meaning, and all are supersets of the guard's rows. The other 45 differ only in JSON form:
   the guard stored return references where the projection stores the expanded types.
2. The precision cost:

   | App | Rows changed in meaning | Bindings added | Values widened: losses / repairs |
   | --- | ---: | ---: | ---: |
   | Campfire | 11 | 12 | 0 / 0 |
   | Forem | 100 | 130 | 3 / 6 |
   | Chatwoot | 244 | 200 | 95 / 0 |
   | Mastodon | 127 | 130 | 6 / 3 |
   | Total | 482 | 472 | 104 / 9 |

   A source re-derivation of Ruby dispatch reaches every added binding: 439 direct writes, 31 through filter
   callees and 2 through `super`. Most are unknown-typed bindings the old table left out. A loss is a known value
   that becomes partly or fully Unresolved: the projection reads the final IR, while the old table kept an
   earlier round's value. In `CreditsController#index`, for example, the old table had `Int` for
   `@user_unspent_credits_count` although its own final IR row was Unresolved. A repair widens a value the old
   table held only as nil, Bottom or an empty array, such as `@follows_limit = [per_page, max].min`.
3. "Zero omissions" holds against the old table, not against Ruby. The re-derivation finds 45 bindings in 27
   filter rows, 36 in Mastodon and 9 in Chatwoot, plus 4 whole Chatwoot rows, that both tables miss
   ([missed-bindings.tsv](missed-bindings.tsv)). The transitive walk does not enter calls inside keyword-hash
   arguments or string interpolation, and helper-module methods never become rows. This predates the change
   and remains open.

The re-derivation does not explain 12 Mastodon bindings in synthetic around-block rows; they are the same as in
the guard's table.

## `@missing_configs`

`VerifySetupCompleted#missing_configs` is the one writer: `@missing_configs ||= Settings::Mandatory.missing`.
`ApplicationController` includes the concern, and the before-action `verify_setup_completed` reaches the writer
through `setup_completed?` and `missing_configs_text`. In all four Forem schedules the projection holds
`missing_configs: Array[Symbol] | nil` in `ApplicationController#verify_setup_completed`, and in no other row.
[witness_missing_configs.rb](witness_missing_configs.rb) runs the unchanged concern on CRuby 4.0.7: Ruby sets
`[:secret_key_base, :community_name]` or `[]`, or leaves the ivar unset when a flash notice already exists.
The projected type admits all three.

## Limits

- This is an order-independence result, not a soundness certificate. F73's witnessed losses remain, the 45
  missed bindings remain, and 104 values lose precision.
- Only V0A0 was run. V1A1 and Discourse were not.
- The independent check did not rebuild or rerun the Rust tests. The original run passed 1,291 library tests
  (64 ignored), 3 focused tests and the checker's 40 tests.
- Binding values come from observer builds that add a read-only binding dump. Their cells reproduce the
  measured digests.
- The candidate's source is not part of this receipt; [binding-projection.patch](binding-projection.patch) holds
  the change from F74's candidate.

## Receipt label map

- `qt-cbproj2-f2597823` → `binding-projection-f2597823`, within `binding-projection-20261021-four-apps-v0a0`.
- `qt-cbproj-ce4eaf1a` → `binding-projection-ce4eaf1a`, the first version.
- `qt-strictguard-48155b34` → `strict-pending-guard-48155b34`.
- `qt-cbproj2-values-f2597823` → `binding-values-f2597823`; `qt-cbproj-mutate-values-e6248970` →
  `guard-binding-values-e6248970`. These are the binding-value observer builds.
- `quick-probe-v1 / observers-v1-20261015 / F61` → `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`.
- The independent check used its own labels for its fresh cells; they are separate native runs.

## Reproduce

From the lab root:

```sh
python3 -B receipts/binding-projection-2026-10-21/check.py
ruby receipts/binding-projection-2026-10-21/witness_missing_configs.rb
```

`check.py` recomputes the counts above from [tables.json](tables.json), the two TSV files and the patch; it starts
no analyzer. The witness needs CRuby 4.0.7 and the pinned Forem checkout under `corpus/apps` (`sh corpus/fetch.sh`)
or `APPS`; it checks the file's SHA-256.
