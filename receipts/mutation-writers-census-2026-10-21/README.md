# Mutation-site writers census

Unscored research reference. Verdict: unsound on witnessed values.
This census is an independent runtime check of the candidate. It has had no second review.
On October 22 a proof checker found two of its hand proofs circular; see the correction below.

## Fact F73

On `mutation-writers-20261016-four-apps-v0a0`, the candidate that adds array and hash mutation sites as writers to F72's rule is unsound on witnessed values. In 21 distinct rows its type excludes a value that CRuby 4.0.7 produces, on all four schedules (unset/1/2/repeat); 17 of them were not among F72's witnessed losses. It admits the witness values of 52 of F72's 56 losing rows; 4 still fail. By family: routing or missing contribution, 13 rows (Campfire's `allow_unauthenticated_access only: %i[ new create ]` binds `options` to `{only: [:new, :create]}`, typed `Hash[Bottom, Bottom]`); container contents, 6 (Mastodon queues `[[:confirmation_instructions, ["token"], {}]]` inside a transaction, typed `Array[Bottom]`); other, 2 (a WhatsApp contact message without contacts makes `Array(message_payload[:contacts]).first&.with_indifferent_access` nil, typed `HashWithIndifferentAccess` without nil); reference return, 0. The census is sampled, not exhaustive: all 69 concrete/nil narrowings and 40 unknown-only narrowings per app, 229 of the candidate's 4,652 narrowings against spine v3. Counting the 34 rows that only a passing witness supports as possible losses, at most 2,202 of the 4,652 (47.3%) lose values, at 95% confidence; at least 21 do. Equality gains under this candidate are therefore not sound gains. V1A1 and Discourse were not run.

## Correction, October 22

The [census proof checker](../census-proof-checker-2026-10-22/README.md) finds two of the 176 source-supported
rows circular. M1708 and M1745 are per-call-site copies of `vary_by`'s `**kwargs`
(`app/controllers/concerns/cache_concern.rb:7`), where the analyzer substituted `**{}`. Their argument, a decoded
empty IR constructor, rests on the analyzer's own IR. In source the same slot also receives Symbol-keyed hashes,
`unless: :disallow_unauthenticated_api_access?` (`app/controllers/api/v1/custom_emojis_controller.rb:4`) and
`if: -> {...}` (`app/controllers/api/v1/instances/domain_blocks_controller.rb:7`), which their types,
`Hash[Str, Str]` and `Hash[Str, Str | nil]`, exclude. Only the analyzer knows which call site each occurrence is,
so the rows may still be sound, but they are unproved.

Both pass their witnesses on all four schedules, so they count as witness-only: 174 source-supported rows and 36
witness-only rows. The conservative bound becomes 2,301 of 4,652 (49.5%) instead of 2,202 (47.3%), and 2,009 of
3,974 (50.6%) on the rows a reader sees. The checker's [validate.py](../census-proof-checker-2026-10-22/validate.py)
recomputes both. The tables, [source-arguments.tsv](source-arguments.tsv) and [bounds.py](bounds.py) here keep
the original statuses.

## Condition

- Candidate: F72's integrated rule plus array and hash mutation sites as writers, label `mutation-writers-66c06f52`.
  It is commit `66c06f52` over F72's recorded source `f9a7e620`
  (published as [integrated-current-writers](https://github.com/bunnykong/roundhouse/tree/991ec4b356a21cf53271737124533c617e01e847)).
  Source: [research/mutation-writers-66c06f52](https://github.com/bunnykong/roundhouse/tree/18fcc75d611fc7fc7a5dfc00b4d0fd2fbea124a6). The branch holds a build-identical snapshot of measured commit `66c06f52` with the
  `research/` harness files removed, so its hash differs.
  Binary SHA-256: `94a7b442594048b468271a5a170b1627f0d50ffb9159eec5e0390887adcd4e79`.
- Control: spine v3, `response-return-spine-control`, unset values.
- Checker: `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`, V0A0 (verification and audit off).
  Schedules: unset, 1, 2 and an independent unset repeat. The census reads cached cells and starts no analyzer.
- Runtime: CRuby 4.0.7, revision `229531a6cf`.
- Apps: the public pins in [public-app-pins.json](../public-app-pins.json). All 142 application files the census
  read match their pinned commits byte for byte.

## What was checked

The population is the 4,652 rows the candidate narrows against the control at unset V0A0, identified by
`(app, table, key)`. Each app has two strata. A concrete/nil row drops a concrete or nil variant; an unknown-only
row drops only unknown variants. Every concrete/nil row was checked. Forty unknown-only rows per app were drawn
without replacement from the sorted pool, with a fixed seed per stratum.

| App | Population C / U | Sample C / U | Losses C / U |
| --- | ---: | ---: | ---: |
| Campfire | 0 / 94 | 0 / 40 | 0 / 3 |
| Forem | 2 / 545 | 2 / 40 | 0 / 0 |
| Chatwoot | 30 / 1,994 | 30 / 40 | 3 / 3 |
| Mastodon | 37 / 1,950 | 37 / 40 | 6 / 4 |

A loss is a CRuby value that the control type admits and the candidate type rejects. Each selected row has the
same candidate type on all four schedules. The census made 992 observation-by-schedule membership checks; the
control admits every observed value.

| App | Source-supported | Witness only | Loss |
| --- | ---: | ---: | ---: |
| Campfire | 28 | 9 | 3 |
| Forem | 35 | 7 | 0 |
| Chatwoot | 55 | 9 | 6 |
| Mastodon | 58 | 9 | 10 |
| Total | 176 | 34 | 19 |

Source-supported means an all-path argument from the pinned source, such as a fresh constructor, a fixed key
schema, a dominating guard or a closed caller set ([source-arguments.tsv](source-arguments.tsv)). Eleven of
them are empty constructors decoded from the cached dumps ([ir-constructor-proofs.json](ir-constructor-proofs.json)).
These are reviewable arguments, not formal proofs of Rails behavior. Witness only means the exercised value
passes and other paths stay unproved. Forem row F465 is an empty explicit-argument contribution whose String
default is joined separately; it has no runtime value to check.

## F72's losing rows

All 56 rows that lost values under F72's rule were replayed on all four schedules ([retained.tsv](retained.tsv)).
Of 224 checks, 208 pass and 16 fail. F72 census rows C2311, C2428, M586 and M2643 fail on every schedule; the
other 52 admit their witness values. A pass admits that value; it does not prove the row sound.

## Losses and families

[losses.json](losses.json) lists the 21 distinct losing rows with their identities, witness values and control and
candidate types: 19 from the sample, plus F72 rows C2311 and M586, which the draw did not select. Two sampled
rows are F72 rows: C1856 is C2428 and M1848 is M2643. The other 17 were not among F72's witnessed losses.

| Family | Rows | Minimal witness program |
| --- | ---: | --- |
| Routing or missing contribution | 13 | [routing_campfire.rb](witnesses/routing_campfire.rb) |
| Container contents | 6 | [container_mastodon.rb](witnesses/container_mastodon.rb) |
| Other | 2 | [other_chatwoot.rb](witnesses/other_chatwoot.rb) |
| Reference return | 0 | none found |

- **Routing or missing contribution.** A010, A013, A014: Campfire's Sessions and Users declarations pass
  `{only: [:new, :create]}` through Authentication; the options are typed `Hash[Bottom, Bottom]`. C1855 and
  C1856: permitted request flag Strings reach setters typed `Array[Symbol]`. C1748 (F72 C2311): a push
  diagnostics view reads a skipped-result Hash typed Bottom. M945: captured rate-limit options typed
  `Hash[Bottom, Bottom]`. M1273: `options[:by]` is `:account`, typed `Bottom | nil`. M1491: `deep_symbolize_keys`
  gives `{request_id: "request-1"}`, typed `Hash[Symbol, Bottom]`. M1786: a list append receives an Account; the
  type keeps only Mention. M1848 (F72 M2643) and M1904: the `Symbol` class object reaches `is_a?` and is missing
  from both argument unions. M385 (F72 M586): a featured-collection URL String reaches an option typed `Bool | nil`.
- **Container contents.** C575, C578: an attribute-change filter returns `[Conversation]`, typed `Array[Bottom]`
  (C575 also nil). M130, M131, M650: strong parameters keep the String key `"home"`; the type allows only Symbol
  keys. M1545: the pending Devise notification queue holds one entry, typed `Array[Bottom]`.
- **Other.** C1376: `.find` returns nil with no matching message; the type keeps only Message. C1465: the
  safe-navigation chain returns nil before the outer fallback; the type keeps only HashWithIndifferentAccess.

Families classify witnessed failure shapes. They do not isolate which flag causes each failure.

## Bound

The sampling unit is a row. For each stratum, [bounds.py](bounds.py) finds the largest loss count K with
`P[Hypergeometric(N, K, n) <= k] > alpha`, in exact integers. For conformance, k counts the losses plus every
witness-only row. Censused strata contribute their exact counts.

| Unknown-only stratum | Losses + unproved / n | 95% upper count | Simultaneous upper count |
| --- | ---: | ---: | ---: |
| Campfire | 12 / 40 | 38 / 94 | 41 |
| Forem | 7 / 40 | 163 / 545 | 187 |
| Chatwoot | 12 / 40 | 875 / 1,994 | 968 |
| Mastodon | 13 / 40 | 906 / 1,950 | 997 |

The simultaneous column uses 0.05/4 in each sampled stratum. With the 9 censused concrete/nil losses, at most
2,202 of 4,652 narrowings (47.3%) lose values at 95% confidence. At least 21 do. The bound is wide; the census
does not show a low loss rate. If passing witnesses missed no losses, the weighted estimate would be 7.75%, with
a simultaneous upper bound of 1,021 (21.9%). That assumption is unproved for 34 rows, so these smaller figures
are not a conformance bound.

## Limits

- The census covers unset-V0A0 narrowings only. V1A1, Discourse and rows that do not narrow are outside it.
  The comparison also has 36,185 unmatched and 705 incomparable rows, outside this census.
- Witnesses run unchanged source with finite request, database, network, queue and mail boundaries, not full
  application boots. SQLite exercises real ActiveRecord behavior.
- The census's full witness programs (228 observations) are not part of this receipt. The three programs here
  re-execute one row per family; the other rows' witnesses are recorded in losses.json.
- This receipt does not rebuild the candidate; its source is on the branch named above.

## Receipt label map

- `qt-mutate-66c06f52` → `mutation-writers-66c06f52`, within `mutation-writers-20261016-four-apps-v0a0`.
- `spine3-control` → `response-return-spine-control`.
- `qt-whole3-f9a7e620` → `integrated-current-writers-f9a7e620` (F72's rule).
- `quick-probe-v1 / observers-v1-20261015 / F61` → `quick-test-v1 / cached-observers-20261015-source-rebuild / F61`.
- Source paths inside row keys are spelled `examples/apps/<app>/…`, relative to a checkout of the pinned app.
  `candidate-source/` names a file of the candidate source on that branch.
- Census row IDs (A… Campfire, F… Forem, C… Chatwoot, M… Mastodon) belong to this census. F72 census IDs are
  given separately as `f72_census_id`; the same-looking ID can name different rows in the two censuses.

## Reproduce

From the lab root, with Python 3.9 or later:

```sh
python3 -B receipts/mutation-writers-census-2026-10-21/bounds.py
```

It recounts every table above from the TSV files and recomputes the bounds; it runs no Ruby and no analyzer.

The witnesses need CRuby 4.0.7 and the pinned apps under `corpus/apps` (`sh corpus/fetch.sh`), or `APPS` set to
a directory of checkouts at the same pins. The Mastodon witness also needs the `activerecord` 8.1.3 and `sqlite3`
2.10.0 gems.

```sh
R=receipts/mutation-writers-census-2026-10-21/witnesses
ruby "$R/routing_campfire.rb" > routing.jsonl
ruby "$R/container_mastodon.rb" > container.jsonl
ruby "$R/other_chatwoot.rb" > other.jsonl
python3 -B "$R/check.py" routing.jsonl container.jsonl other.jsonl
```

Each program checks the SHA-256 of the files it reads. `check.py` applies the checker's runtime-set relation
([tools/probe/runtime_sets.py](../../tools/probe/runtime_sets.py)) and prints `LOSS reproduced` for each of the
five rows (A010, A013, A014, M1545, C1465): the value has its recorded type, the control admits it and the
candidate rejects it. All five reproduced on CRuby 4.0.7 when this receipt was prepared.
