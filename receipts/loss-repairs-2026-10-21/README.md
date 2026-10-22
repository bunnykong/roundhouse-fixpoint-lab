# Loss repairs

Unscored research reference. An independent check upholds the result with corrections; the fact includes them.
A second check, on October 22, corrects what the per-class-route repairs mean; see the correction below.

## Fact F77

On `route-per-class-20261021-four-apps-v0a0`, two flags on top of F75's candidate repair 10 of F73's 21 losing rows: per-class routes (`RH_ROUTE_PER_CLASS=1`) let a call on an unknown receiver reach every per-class row with its name and arity, and class-body sites (`RH_CLASS_BODY_SITES=1`) collect sends in model and controller class bodies as call sites. String parameter keys (`RH_PARAMS_STRING_KEYS=1`, on top) repair 3 more. These 13 distinct rows (F72's C2428 and M2643 are F73's C1856 and M1848) now admit their CRuby witnesses on all four schedules; 8 of the 21 remain. All four apps keep 10/10 equal tables with zero varying rows. Against F75, narrowed/widened rows are Campfire 9/148, Forem 1/375, Chatwoot 0/644 and Mastodon 65/867. Every narrowing only drops Unresolved and excludes no value the apps' callers pass; per-class routes alone account for 1,962 of the 2,034 widenings, the expected per-class route arms. The F61 comparison is incomplete: 2,308 parameter rows changed identity (2,007 added, 301 removed), and none loses a value. Two of the 74 admitted narrowing witnesses pass only because a Proc is encoded as `fn -> Str`, and the one skipped read comes from class-body sites wrongly binding `deprecate_api`'s `only:`/`if:` keywords to `sunset`, a wrong binding that loses no value. Analysis takes 12–14% longer on Chatwoot and Mastodon, 21–22% on Forem and 0.5–0.9 s on Campfire. An independent check upholds this with these corrections; V1A1 and Discourse were not run. **Correction, October 22:** class-body sites (5 rows) and String parameter keys (3 rows) are the substantive repairs, 8 of F73's 21 losses. Per-class routes' 5 repairs and 1,962 widenings all sit in parameter rows of methods with no analyzer body, and run alone the flag changes no other table, so no analyzer body or emitter reads them: their benefit and their cost are table-only. Without rows that no body reads, 53 of the 2,034 widenings remain. F73's census counted rows that nothing reads.

## Correction, October 22

A second zero-CPU check of the cached dumps classifies every widened row by whether anything reads it
([reader-classes.tsv.xz](reader-classes.tsv.xz)). It confirms the numbers above and changes what the per-class-route
repairs mean.

- All 1,962 per-class-route widenings are `params` rows of methods with no analyzer body. 1,763 are framework
  methods (`new` 545, `render` 371, `initialize` 162), 190 are other app-declared methods without an analyzer body
  (119 `pattr_initialize` constructors and 26 scopes among them), 7 are generated setters and 2 are association
  methods. For 16 of them a `def` exists by Ruby's lookup, in a module the analyzer never types.
- Run alone, per-class routes change no row in any other table: no IR, return, side-table or controller-cache row.
- The five per-class-route repairs sit in those unread rows. The added Unresolved arm lets the census check pass,
  but the informative arms are unchanged and still exclude the witness, and no analyzer body or emitter reads
  these rows.

  | Row | Row key | F75 type, then per-class routes | CRuby witness |
  | --- | --- | --- | --- |
  | C1855 | `NotificationSetting#selected_email_flags=[0]` | `Array[Sym]`, plus Unresolved | `["email_conversation_assignment"]` |
  | C1856 | `NotificationSetting#selected_push_flags=[0]` | `Array[Sym]`, plus Unresolved | `["push_conversation_assignment"]` |
  | M1786 | `Account#<<[0]` | `Mention`, plus Unresolved | an `Account` |
  | M1848 | `Collection#is_a?[0]` | `Account`, `Collection` or `Status`, plus Unresolved | `Symbol` |
  | M1904 | `Status#is_a?[0]` | five classes, plus Unresolved | `Symbol` |

- Dropping rows that no analyzer body reads leaves 53 of the 2,034 widenings: class-body sites' 52 IR rows and
  `RateLimitable#rate_limiter[1]`.

So class-body sites (5 rows) and String parameter keys (3 rows) are the substantive repairs: 8 of F73's 21 losses.
Per-class routes' benefit and cost are both table-only. F73's census counted rows that nothing reads; a census
should classify rows by whether any analyzer body or emitter reads them.

## What changed

- **Per-class routes**, `RH_ROUTE_PER_CLASS=1`. A call on an unknown receiver also reaches every per-class row with
  the called name and arity, such as generated setters, association `<<` and universal methods. Each reached row
  gains an Unresolved arm: sound, but less precise. The flag acts only with the profile's `RH_ROUTE_TOP=1`.
- **Class-body sites**, `RH_CLASS_BODY_SITES=1`. Sends in model and controller class bodies, such as
  `allow_unauthenticated_access only: ...` or `rate_limit by: ...`, become call sites.
- **String parameter keys**, `RH_PARAMS_STRING_KEYS=1`. Iterating request parameters yields String or Symbol keys,
  in a seven-line change.

[route-per-class.patch](route-per-class.patch) holds the first two flags: 9 files, 340 lines added and 35 removed.
Its ungated lines are plumbing: route targets carry an arity, a keyword record gains two fields, and one helper
becomes visible to its module. [params-string-keys.patch](params-string-keys.patch) holds the third flag. With
every flag off, the binary reproduces F75 on Campfire (five observation fields) and on Forem (all nine).

Sources: [research/route-per-class-575558cd](https://github.com/bunnykong/roundhouse/tree/b391cd9781452bba589ead4ba77ca0b4ee9a1242) and
[research/params-keys-953680ad](https://github.com/bunnykong/roundhouse/tree/7ea97ec7c1b39cfb7eab95a7bf8606f6b61d05ec), stacked on F75's branch.
Each branch holds a build-identical snapshot of the measured commit with the `research/` harness files removed,
so its hash differs.

## Condition

- Candidate `route-per-class-575558cd`: F75's candidate with `RH_ROUTE_PER_CLASS=1` and `RH_CLASS_BODY_SITES=1`,
  within `route-per-class-20261021-four-apps-v0a0`.
- Candidate `params-string-keys-953680ad`: the same with `RH_PARAMS_STRING_KEYS=1`, within
  `params-string-keys-20261021-four-apps-v0a0`. It was measured stacked. Run alone on Mastodon unset, it admits the
  same three rows and changes the same 31 rows with the same relations.
- Control: `binding-projection-f2597823`, F75's candidate.
- Checker: `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`, V0A0, schedules unset, 1, 2 and an
  independent unset repeat.
- Independent check: 8 fresh cells of the first candidate without rebuilding: Campfire on unset and 2, Forem on
  unset and 1, Chatwoot on unset and repeat, and Mastodon on unset and 2. Two more cover the second candidate on
  Campfire and Forem unset. All match their records.

## F73's losing rows

[f73-rows.json](f73-rows.json) gives every row's type in each condition and the census's CRuby 4.0.7 witness
types. A row passes when its type admits every witness on all four schedules.

| Rows | F75 | Routes and class-body sites | With String keys too | Repaired by |
| --- | ---: | ---: | ---: | --- |
| C1855 C1856 M1786 M1848 M1904 | 0/4 | 4/4 | 4/4 | per-class routes, through an Unresolved arm |
| A010 A013 A014 M945 M1273 | 0/4 | 4/4 | 4/4 | class-body sites, with concrete types |
| M130 M131 M650 | 0/4 | 0/4 | 4/4 | String parameter keys |
| C575 C578 C1376 C1465 C1748 M385 M1491 M1545 | 0/4 | 0/4 | 0/4 | none: these 8 remain |

F72's C2311, C2428, M586 and M2643 are F73's C1748, C1856, M385 and M1848. Unset cells with one flag at a time
confirm which flag repairs each row. A010's type is `Hash[Sym, Sym | Array[Sym]]` rather than the predicted
`Hash[Sym, Array[Sym]]`, because another controller passes `only: :show`.

## Against F75

| App | Equal tables | Varying rows | Narrowed / widened rows |
| --- | ---: | ---: | ---: |
| Campfire | 10/10 | 0 | 9 / 148 |
| Forem | 10/10 | 0 | 1 / 375 |
| Chatwoot | 10/10 | 0 | 0 / 644 |
| Mastodon | 10/10 | 0 | 65 / 867 |

The F61 comparison is incomplete: 2,308 parameter identities change. 2,007 are added. Of the 301 removed, 295 are
empty rows of methods that gained a positional row, and 6 Chatwoot `validate_feature_*` rows move to the class side
with equal types. None drops a value. Adding String keys on top narrows nothing and widens 10, 6, 53 and 30 rows;
it leaves one identity in Chatwoot and one in Mastodon without a comparison. [tables.json](tables.json) holds the
counts.

## The 75 narrowings

[narrowings.tsv](narrowings.tsv) lists each narrowing with its types and witness. Each drops only Unresolved: 57
replace a bare Unresolved, and 18 drop an Unresolved arm, as in `Hash[Sym, Sym | U]` to `Hash[Sym, Sym]`. The
independent check read every caller of the 10 source files in the pinned apps, and no narrowed type excludes a
value they pass. Callers outside the app sources, such as tests, the console or gems, are not covered.

- The census checker admits 74 of the witnesses. Two of them, `vary_by`'s callable value, pass only because a Proc
  is encoded as `fn -> Str`; the checker rejects the raw Proc type.
- One guarded read never runs. Class-body sites bind `deprecate_api`'s braceless `only:` and `if:` keywords to
  `sunset`, so `sunset` reads `Hash[...] | nil` while `**kwargs` stays Unresolved. In Ruby, `sunset` is nil for
  all seven callers. The binding is wrong and adds a Hash arm Ruby never produces, but no value is lost.

## Widenings

| App | Widened | Per-class routes | Class-body sites | Both flags |
| --- | ---: | ---: | ---: | ---: |
| Campfire | 148 | 138 | 10 | 0 |
| Forem | 375 | 374 | 0 | 1 |
| Chatwoot | 644 | 644 | 0 | 0 |
| Mastodon | 867 | 806 | 51 | 10 |
| Total | 2,034 | 1,962 | 61 | 11 |

Unset cells with one flag at a time attribute each row ([widenings.tsv.xz](widenings.tsv.xz)). Per-class routes add
the expected route arm: a row such as `Struct#new[0]`, `Contact#try[0]` or `UploadedFile#is_a?[0]` keeps its old
type and gains Unresolved. The 61 class-body-site rows are repairs without Unresolved, such as
`Follow#rate_limiter[1]` going from `Hash[Bottom, Bottom]` to `Hash[Sym, Sym]`. The 11 rows that need both flags
add Unresolved to `public_send`, `render` and `new` rows.

## Cost

Each pair ran at the same moment as its F75 cell ([timing.tsv](timing.tsv)). Analysis takes 21–22% longer on
Forem, 12–14% on Chatwoot and Mastodon, and 0.5–0.9 s on Campfire. CPU ratios equal the wall ratios, and peak
memory grows 0–4%. Mastodon's diagnostics fall from 7,194 to 7,176: one new `unsupported` (`date.to_datetime`
in `deprecation_concern.rb:8`) and 19 fewer gradual-untyped warnings. The other apps keep theirs.

## Limits

- 8 of F73's 21 losses remain, and F73's sampled bound is not recomputed.
- Only V0A0 on the four standard schedules was run. Extra seeds, V1A1 and Discourse were not.
- The original run passed 1,291 library tests (68 ignored), 4 focused tests and 208 of 209 selected integration
  tests. The failing test, `analyze::if_branches_union_merge`, fails the same way on F75's commit. The full default
  suite was not run. The independent check did not rebuild or run tests.

## Receipt label map

- `qt-sound-r3r1-575558cd` → `route-per-class-575558cd`, within `route-per-class-20261021-four-apps-v0a0`.
- `qt-sound-k3-953680ad` → `params-string-keys-953680ad`, within `params-string-keys-20261021-four-apps-v0a0`.
- `qt-cbproj2-f2597823` → `binding-projection-f2597823`.
- The repairs' working names R3, R1 and K3 are per-class routes, class-body sites and String parameter keys.
- `quick-probe-v1 / observers-v1-20261015 / F61` → `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`.
- The independent check used its own labels for its fresh cells; they are separate native runs.

## Reproduce

From the lab root, with Python 3.9 or later:

```sh
python3 -B receipts/loss-repairs-2026-10-21/check.py
```

It recomputes every row admission from [f73-rows.json](f73-rows.json) with the F73 receipt's checker, and every
count above from the TSV files, including the October 22 correction's; it starts no analyzer. The F73 receipt's witness programs regenerate the witness
values for A010, A013, A014, M1545 and C1465.
