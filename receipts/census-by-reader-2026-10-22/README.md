# Census by reader

Unscored research reference. It classifies the rows of F73's census by whether anything reads them and recomputes
F73's bound on the rows a reader sees. It backs the census part of
[F78](../remaining-repairs-2026-10-22/README.md#fact-f78) and has had no second review.

**Result:** 14.6% of the narrowed rows and 6 of F73's 21 losses are unread, but dropping them does not lower the
bound. At most 1,907 of 3,974 reader-visible rows (48.0%) lose values at 95% confidence, against F73's 2,202 of
4,652 (47.3%), and at least 15 do. The bound is wide for lack of proofs, not because of unread rows.

## Condition

- Rows: [F73's census](../mutation-writers-census-2026-10-21/README.md) of `mutation-writers-66c06f52` against
  `response-return-spine-control`: the 4,652 rows the candidate narrows at unset V0A0, and its 229 sampled rows.
- Rules: read from the candidate's source, published as
  [research/mutation-writers-66c06f52](https://github.com/bunnykong/roundhouse/tree/18fcc75d611fc7fc7a5dfc00b4d0fd2fbea124a6).
  Line numbers below refer to it.
- Inputs: the cached unset dumps of both conditions, and Prism 1.8.1 for parameter kinds. No build, no analyzer
  run and no Ruby witness. The control's dumps give the same classes for all 4,652 rows.

## The rule

Each row gets the first class that applies: **a**, read by an analyzed body; **b**, read only by an emitter;
**c**, read by nothing. A dump that cannot decide counts as read.

- **ir**: every row is the type of an emitted expression (`src/analyze/fixpoint_check.rs:981`). a if the root has a
  declaration (a library or model method, or a controller action), else b (tests, views, defaults, class bodies).
- **params `C#m[i]`**: a if a seeded body reads position i: C#m's own body (`seed_method_params` reads every
  parameter, `src/analyze/mod.rs:4967`; `seed_action_params` only an action's required positionals, `:5063`), a
  test-class helper (`src/analyze/test_module.rs:138`), or a module method M#m that C's ancestors include
  (`src/analyze/mod.rs:6578`). b if only the controller lowering reads it, as for an action's optional or keyword
  parameter (`src/lower/controller_to_library/mod.rs:2894`). c: no body, an action's rest slot, or a position past
  the def.
- **returns `C#m`**: a if an IR send of m has C, a subclass or an includer as receiver, or has no receiver inside
  such a body or an undeclared root. b: a library method with no call site, whose signature the lowering stamps
  (`src/analyze/mod.rs:2193`). c: the rest.
- **controller_cache**: clones of typed action bodies (`src/analyze/mod.rs:3099`) that only the ivar harvest reads
  (`:9171`, `:7503`). a if the node is an ivar write's value or a binding, and an IR root reads that ivar; else c.
- **side_table**: a, since parameter slots exist only for seeded bodies (`src/analyze/fold.rs:270`) and position
  slots sit inside them.

## The 229 sampled rows

[sample-readers.tsv](sample-readers.tsv) gives each sampled row's class and the reason, next to F73's status.

| Reader | Rows | Losses | Witness only | Source-supported |
| --- | ---: | ---: | ---: | ---: |
| a | 168 | 13 | 23 | 132 |
| b | 29 | 0 | 1 | 28 |
| c | 32 | 6 | 10 | 16 |

- The 32 unread rows are 18 controller-cache copies, 12 parameter rows of methods with no analyzer body, M1869's
  scope parameter (scopes get no seeds, `src/analyze/sccq.rs:2137`) and M1840's `**` slot (typed Unresolved,
  `src/analyze/body/mod.rs:3051`, and emitted untyped).
- The unread losses are C1855, C1856, M1786, M1848 and M1904, F77's per-class-route rows, and M131, the
  controller-cache copy of loss M650.
- The rule counts every IR row as read. A statement whose value is discarded, such as C575, still counts.

## Bound

[bounds.py](bounds.py) reuses F73's exact hypergeometric inversion and its strata unchanged, at 0.05/4 in each
sampled stratum. Given n', the sampled reader-visible rows of a stratum are a simple random sample of its N'
reader-visible rows, so the same inversion applies to (N', n', k').

| Stratum | Rows N → N' | Sample n → n' | Losses + unproved | 95% upper count |
| --- | ---: | ---: | ---: | ---: |
| Campfire unknown | 94 → 81 | 40 → 32 | 12 → 8 | 41 → 33 |
| Forem concrete/nil | 2 → 1 | 2 → 1 | 0 → 0 | 0 → 0 |
| Forem unknown | 545 → 488 | 40 → 36 | 7 → 5 | 187 → 151 |
| Chatwoot concrete/nil | 30 → 28 | 30 → 28 | 3 → 1 | 3 → 1 |
| Chatwoot unknown | 1,994 → 1,656 | 40 → 36 | 12 → 10 | 968 → 784 |
| Mastodon concrete/nil | 37 → 32 | 37 → 32 | 6 → 2 | 6 → 2 |
| Mastodon unknown | 1,950 → 1,688 | 40 → 32 | 13 → 11 | 997 → 936 |
| Total | 4,652 → 3,974 | 229 → 197 | 53 → 37 | 2,202 → 1,907 |

On reader-visible rows the conservative bound moves from 47.3% to 48.0%, the detection-only bound from 21.9% to
25.3%, and the weighted estimate from 7.75% to 9.05%. Dropping unread rows also drops 16 source-supported rows,
and the smaller n' widens each interval. 85.4% of the population is reader-visible (86.0% of the sample), and 83.0%
to 93.3% of each stratum with more than two rows.

## Unread rows

[population-readers.tsv.xz](population-readers.tsv.xz) gives every row's class, reason, node and source span. The
678 unread rows are 14.6% of the 4,652 narrowings:

- 522 controller-cache rows. 509 of them have a narrowed IR row at the same source span and node, so the census
  counts that value twice.
- 126 parameter rows, 124 of them of methods with no analyzer body.
- 30 return rows: 13 includer copies, and 17 controller actions, model methods or `initialize` methods whose
  lowering ignores the row.

## Limits

- Unset dumps only. Schedules 1, 2 and repeat, V1A1 and Discourse are not covered.
- The cached dumps are not published. This receipt gives every row's class and reason, and the rule's source
  lines, so the classification can be audited against the branch; it cannot be rerun from the lab alone.
- The census's own sample, statuses and witness programs are F73's; nothing here reruns them.

## Receipt label map

- `qt-mutate-66c06f52` → `mutation-writers-66c06f52`; `spine3-control` → `response-return-spine-control`, as in
  F73's receipt.
- Census row IDs are F73's. Source paths in keys and spans are spelled `examples/apps/<app>/…`.

## Reproduce

From the lab root, with Python 3.9 or later:

```sh
python3 -B receipts/census-by-reader-2026-10-22/bounds.py
```

It recounts both tables from the TSV files, checks the sample against F73's receipt, recomputes F73's all-row
bound and the reader-visible bound, and recounts the unread rows; it starts no analyzer.
