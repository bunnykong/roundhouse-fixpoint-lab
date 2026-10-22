# Remaining repairs

Unscored research reference. An independent check upholds the result with corrections; the fact includes them.
The reader counts use the [census-by-reader receipt](../census-by-reader-2026-10-22/README.md).

## Fact F78

On `sound-rest-20261022-four-apps-v0a0`, four flags on top of F77's candidate repair 6 more of F73's 21 losing rows, which now admit their CRuby witnesses on all four schedules (0/4 under F77). Sidekiq rows (`RH_SIDEKIQ_ROWS=1`) make `perform_async` and its siblings write `perform`'s rows after a JSON round trip (M385, M1491); render bindings (`RH_RENDER_BINDINGS=1`) make `render :t` write template t's bindings (C1748); ivar call joins (`RH_IVAR_CALL_JOIN=1`) make an ivar read across a call join its slot (C575, C578); memo aliases (`RH_MEMO_IVAR_ALIAS=1`) bind a memoized getter to its ivar (M1545). Five of the six repairs reach a reader; C575's value is discarded. Five admit only through an Unresolved arm; only M385 gains a concrete type, `Str`. All four apps keep 10/10 equal tables with zero varying rows. Of 278 narrowed rows, 274 admit their CRuby witnesses; the other 4 are new Forem losses from render bindings: `render :index` types `@commentable` as `Article`, which exposes an old schema-ingestion bug that drops `array: true` from `co_author_ids`. 1,877 rows widen, 632 of them from a known type to Unresolved; ivar call joins alone cause 1,528. Analysis takes 1–3% longer on Chatwoot and Mastodon and 14–17% longer on Forem. Render bindings also change how views fed by two or more actions merge ivars, and ivar call joins add 2 Chatwoot diagnostics. Counted by reader, 12 of F73's 21 rows now have reader-visible repairs (class-body sites 5, String keys 2, these flags 5), since M131 is an unread cache copy of M650. Seven repairs reach no reader, C1376 and C1465 remain, and the 4 new Forem losses count against the 12. A census by reader of F73's 229 sampled rows finds 168 read by an analyzed body, 29 only by an emitter and 32 by nothing. Unread rows are 14.6% of the 4,652 narrowings, mostly controller-cache copies with a narrowed IR twin. On the 3,974 reader-visible rows, at most 1,907 (48.0%) lose values at 95% confidence, against 47.3% on all rows, and at least 15 do: the bound is wide for lack of proofs, not because of unread rows. An independent check upholds the repairs with these corrections; V1A1 and Discourse were not run.

## What changed

Four flags on top of F77's candidate, each gated on its own:

- **Sidekiq rows**, `RH_SIDEKIQ_ROWS=1`. `perform_async` and its siblings write the worker's `perform` parameter
  rows after a JSON round trip, which turns Symbols into Strings. `perform_bulk` and `.set(...).perform_*` are not
  covered.
- **Render bindings**, `RH_RENDER_BINDINGS=1`. `render :t` writes template t's bindings from the rendering action.
  The flag also changes how a view fed by two or more actions merges their ivars: Unresolved is no longer dropped
  as noise. C1748 depends on that rule.
- **Ivar call joins**, `RH_IVAR_CALL_JOIN=1`. After a statement with a call, each local ivar fact joins the ivar's
  slot before later reads; later assignments still take effect. The flag also adds a `deep_merge` diagnostic on
  union receivers.
- **Memo aliases**, `RH_MEMO_IVAR_ALIAS=1`. A zero-argument getter that returns an ivar, or memoizes into one,
  aliases that ivar in the mutation graph.

[sound-rest.patch](sound-rest.patch) holds the change: 5 files, 765 lines added and 15 removed. `sound_rest.rs`
adds 648 lines, 361 of them tests. Its one ungated change builds the mutation graph after the scope, which changes
nothing with the flags off. With all four flags off, the binary equals F77 on Campfire and Forem unset in all nine
observation fields.

Source: [research/sound-rest-3b96ce25](https://github.com/bunnykong/roundhouse/tree/693a9f3cb97c51fa73aa7a6af7d10a8f779604fe),
stacked on F77's branch. It holds a build-identical snapshot of the measured commit with the `research/` harness
files removed, so its hash differs.

## Condition

- Candidate `sound-rest-3b96ce25`: F77's candidate with the four flags, within
  `sound-rest-20261022-four-apps-v0a0`. Binary SHA-256
  `2545e353cc3d32984d5cb2fd9af417ca2a8dab0a97b1939eac2e656763b39bc2`.
- Control: F77's candidate `params-string-keys-953680ad`, rerun at the same moment. Its cells equal F77's
  published ones.
- Checker: `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`, V0A0, schedules unset, 1, 2 and an
  independent unset repeat.
- Independent check: 7 fresh cells of each arm without rebuilding (Campfire on 2, Forem on unset and 1, Chatwoot
  on unset and repeat, Mastodon on unset and 2), plus one-flag and all-off cells. All match their records in all
  nine observation fields.

## F73's losing rows

[f73-rows.json](f73-rows.json) gives every row's type in each condition, the census's CRuby 4.0.7 witness types
and each row's reader. A row passes when its type admits every witness on all four schedules. The six rows below
admit 0/4 under F77 and 4/4 with the four flags. Unset cells with one flag at a time show that each flag admits
its own rows and no others.

| Row | Flag | F77 → four flags | Reader of the repaired value |
| --- | --- | --- | --- |
| M1491 | Sidekiq rows | `Hash[Sym, Bottom]` → `Hash[Sym, U]` | `**` into `FetchRemoteStatusService#call`, whose `request_id` row was already U |
| M385 | Sidekiq rows | `Bool \| nil` → adds `Str` and U | `.presence` into `JsonLdHelper#fetch_collection_page`, whose argument gains `Str` |
| C1748 | render bindings | Bottom → U | the view's `r[...]` sends, already U under F77 |
| C575 | ivar call joins | `Array[Bottom] \| nil` → `U \| nil` | none: a statement whose value is discarded |
| C578 | ivar call joins | `Array[Bottom]` → U | `perform`'s call (`conditions_filter_service.rb:37`), which feeds only C575 |
| M1545 | memo aliases | `Array[Bottom]` → `Array[U]` | `.each`, whose block parameter goes from Bottom to U |

U is Unresolved. All six are IR rows. With their Unresolved arms removed, only M385 still admits its witness, so
five repairs admit only through Unresolved. C575 assigns `records`, and line 39 reads it in `records.any?`; that
read is `Relation[Conversation]` in both conditions, so it still rejects the witness `[Conversation]`.

All 21 rows after F77, its correction and this change:

| Rows | Repaired by | Reader-visible |
| --- | --- | --- |
| A010 A013 A014 M945 M1273 | class-body sites (F77) | yes |
| M130 M650 | String parameter keys (F77) | yes |
| M385 M1491 C1748 C578 M1545 | the four flags | yes |
| C1855 C1856 M1786 M1848 M1904 | per-class routes (F77) | no: parameter rows of methods with no analyzer body |
| M131 | String parameter keys (F77) | no: the cache copy of M650, which nothing reads |
| C575 | ivar call joins | no: the value is discarded |
| C1376 C1465 | none; both still reject | not repaired |

So 12 of F73's 21 rows have reader-visible repairs. The census rule counts every IR row as read, so it also counts
C575. Render bindings add 4 new witnessed losses in Forem (below), which count against the 12.

The original run reads the two remaining rows this way; no independent check covers these readings. C1376: a
block `find` on an array of model records takes ActiveRecord's finder type and omits nil. C1465: the census row is
the right operand of a safe-navigation expression, but the nil belongs to the whole expression, which admits nil.

## Against F77

| App | Equal tables | Narrowed / widened / incomparable | Diagnostics |
| --- | ---: | ---: | ---: |
| Campfire | 10/10 | 0 / 0 / 0 | 485 → 485 |
| Forem | 10/10 | 160 / 1,010 / 6 | 8,820 → 8,915 |
| Chatwoot | 10/10 | 1 / 166 / 2 | 8,150 → 8,170 |
| Mastodon | 10/10 | 117 / 701 / 1 | 7,176 → 7,168 |

No row varies across the four schedules, in either condition. 1,243 rows stay unclassified: 1,139 exist only with
the flags, 88 only without them, and 16 have no serialized type. The 9 incomparable rows: render bindings turn six
Forem `.class` results into the generic `Class`; memo aliases expand Chatwoot's `soft_deleted_users` from
`Array[Bottom]` to `Array[Hash]` inside two records that the record checker cannot order; and ivar call joins
change one guarded `MoveWorker` read from nil to `StandardError`. [tables.json](tables.json) holds the counts.

Diagnostics: Forem gains 96 gradual-untyped warnings and loses one missing-preload warning. Chatwoot gains 18
gradual-untyped warnings and 2 `unsupported` errors, the `deep_merge` diagnostic of ivar call joins at
`contact_identify_action.rb:131` and `:137`. Mastodon loses one `unsupported` error and 7 warnings.

## The 278 narrowings

[narrowings.tsv](narrowings.tsv) lists each narrowing with its types, flag and witness.

- 201 replace a bare Unresolved, 43 replace a nested Unresolved and 33 drop an Unresolved arm. One drops concrete
  arms: Mastodon's `ISO_639_1_REGIONAL` constant, whose whole literal value it admits.
- By flag: Sidekiq rows 219, render bindings 50, memo aliases 7; 2 need Sidekiq rows and ivar call joins together.
  Ivar call joins alone narrow nothing.
- Witness programs from the original run, re-executed under CRuby 4.0.7 by the independent check, give one value
  per row. The census checker admits 274 and rejects 4; none is missing. Four of the admitted are guarded
  `sign_with` reads: the right operand of `&&` did not run, so the witness is the same expression's value in the
  left operand. 22 admit through an encoding of the runtime value: 15 indifferent hashes as a nominal
  `HashWithIndifferentAccess`, 5 form builders as their superclass and 2 Dates as the analyzer's Date.
- These witnesses use values picked by parameter name (`*_id` is 1), not values from callers. So the independent
  check read the callers of 15 declarations (110 rows): the enqueue sites of 6 workers,
  `EdgeCache::BustPodcastEpisode.call` and the renderers of 6 views. No narrowed type excludes a value these callers
  pass. The `perform_bulk` and `.set(...).perform_*` sites pass the same types or reach no narrowed row.

## The four Forem losses

They are new losses that expose an old one. `comments/index.html.erb:129` reads `@commentable&.co_author_ids`. F77
typed its four rows Unresolved or `Unresolved | nil`, which admit `[2, 3]`. Render bindings alone reproduce the new
types: `render :index` (`comments_controller.rb:165`) adds `Article` to `@commentable`, and `Article#co_author_ids`
returns `Int | nil` because schema ingestion drops `array: true` (`db/schema.rb:95`). That return type is old: F77
already types reads of it `Int | nil` at `article.rb:98-100` and `admin/articles/_individual_article.html.erb:129`.

## Widenings

| Flag | Widened | To bare Unresolved |
| --- | ---: | ---: |
| Ivar call joins | 1,528 | 606 |
| Sidekiq rows | 176 | 6 |
| Render bindings | 101 | 17 |
| Memo aliases | 61 | 1 |
| Two flags together | 11 | 2 |
| Total | 1,877 | 632 |

Unset cells with one flag at a time attribute each row ([widenings.tsv.xz](widenings.tsv.xz)). By table: IR 1,075,
controller cache 672, params 82, returns 44, side table 4. Besides the 632 that become a bare Unresolved, 921 gain
Unresolved where the F77 type had none, 123 have Unresolved on both sides and 201 have none on either side.

Ivar call joins join each ivar's entry type after any call. `Admin::OrganizationsController#index` reads
`@organizations` after `params[:search].blank?`, so `Relation[Organization]` becomes Unresolved. In a fixed-seed
sample of 40 widened rows ([widening-readers.tsv](widening-readers.tsv)), 25 are read by an analyzed body (12 IR,
4 params, 4 returns, 4 side table, 1 view seed), 9 are cached controller bodies and 6 have no reader. Unlike the
per-class-route widenings of F77, these reach readers.

## Cost

Each pair ran at the same moment as its F77 cell ([timing.tsv](timing.tsv)). In the independent check's pairs,
analysis takes 14–17% longer on Forem, 1–3% on Chatwoot and Mastodon and 4% on Campfire (0.2 s). CPU ratios equal
the wall ratios, and peak memory moves at most 6%. A loaded host slowed both arms of the Mastodon pairs. The
original run's medians over four schedules are 1.16 on Campfire, 1.10 on Forem and 1.03 on Chatwoot and Mastodon.

## Limits

- C1376 and C1465 still reject their witnesses, and render bindings add 4 losses.
- Only V0A0 on the four schedules was run. Extra seeds, V1A1 and Discourse were not. Emitters were not audited
  target by target.
- The original run passed 1,293 library tests (74 ignored) and the 8 focused flag tests at `3b96ce25`. The full
  default suite ran on its parent commit; all 26 failures there also fail on F77's commit. The independent check
  did not rebuild or run tests.

## Receipt label map

- `qt-sound-rest-3b96ce25` → `sound-rest-3b96ce25`, within `sound-rest-20261022-four-apps-v0a0`.
- `qt-sound-rest-f77-3b96ce25` → F77's `params-string-keys-953680ad`, rerun at the same moment; its cells equal the
  published `qt-sound-k3-953680ad`.
- `qt-sound-rest-r2-`, `-r4-`, `-k1-`, `-k2-` and `-off-3b96ce25` → cells of the same binary with one flag on, or
  all four off.
- The working names R2, R4, K1 and K2 are Sidekiq rows, render bindings, ivar call joins and memo aliases. F77's R3,
  R1 and K3 are per-class routes, class-body sites and String parameter keys.
- `quick-probe-v1 / observers-v1-20261015 / F61` → `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`.
- The independent check used its own labels for its fresh cells; they are separate native runs.

## Reproduce

From the lab root, with Python 3.9 or later:

```sh
python3 -B receipts/remaining-repairs-2026-10-22/check.py
```

It recomputes every row admission from [f73-rows.json](f73-rows.json) with the F73 receipt's checker, every
narrowing verdict from its witness type, and every count above from the TSV files; it starts no analyzer.
