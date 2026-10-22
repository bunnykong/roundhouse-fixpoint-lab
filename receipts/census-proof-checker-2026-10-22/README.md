# Census proof checker

Unscored research reference: an independent source proof checker for F73's census, with its tests, inputs and
outputs. Anyone with CRuby 4.0.7 and the pinned apps can rerun it. It has had no second review.

## Fact F79

On F73's census (`mutation-writers-20261016-four-apps-v0a0`, unset V0A0), an independent checker proves 1,922 of the 4,652 narrowed rows sound (41.3%). It reads the pinned source with Prism, takes only each row's location and type from the cached dumps, and runs no analyzer code. Proved rows per stratum: Campfire 27 of 94; Forem 0 of 2 concrete/nil and 202 of 545 unknown-only; Chatwoot 0 of 30 and 923 of 1,994; Mastodon 20 of 37 and 750 of 1,950. By pattern: fresh constructor 1,397, fixed key schema 447, exhaustive returns within one def 53, dominating guard 25. It proves 88 of the census's 176 hand proofs and contradicts none. As a negative control it proves none of F73's 21 losses, its 34 witness-only rows or F72's 62 losses; with its mutation analysis switched off it proves 9 of F72's losses, so the control can catch errors. Two hand proofs are circular: M1708 and M1745 relied on the analyzer's own IR, and in source their slot also receives Symbol-keyed hashes. With proved rows closed, the 95% bound falls from 47.3% to 45.4%, and from 48.0% to 45.9% on reader-visible rows; counting the two circular rows as unproved, F73's bound is 49.5% (50.6% on reader-visible rows) and the proofs bring it to 46.9% (47.8%). Under the conservative rule a passing witness never closes a row, so only proofs move the bound: about 1,570 more sampled rows, each proved or shown lossy, would bring it under 10%, which needs caller enumeration and returns across methods. The checker has had no second review.

## How it proves

[checker.rb](checker.rb) takes only a locator from the dumps (source file, byte span, node kind) and the
candidate's type. It parses the pinned source with Prism and evaluates the expression at the span to a set of value
shapes. A row is PROVED only if every shape lies inside the type; otherwise the answer is CANNOT_PROVE, with a
reason. Membership is the checker's own code and follows the census's runtime-set rules: kinds must match,
`untyped` and `var` are top, and an empty container fits any container type of its kind. Nothing is imported from
the analyzer or the census tooling.

- **Fresh constructor, literal schema:** literals, assignments, setters (the value is the right-hand side; `&.`
  adds nil), sequences, branches (a missing `else` adds nil) and `freeze`.
- **Writer enumeration, for locals:** every write, plus every use that may run before the read. `h[k] = v`, `<<`,
  `push` and `h[k] << v` add contents. Any other use (an argument, an alias, an unknown method, a `<<` whose result
  is used) makes the contents unknown. Uses that can only run after the read are ignored; loops and closures count.
- **Dominating guard:** `is_a?`, `kind_of?`, `case`/`when` on app or core classes, an early
  `return`/`next`/`raise unless`, and nil guards. A guard counts only if no write can run after it. Constants
  resolve lexically, and the guard is refused if an app ancestor defines the same name.
- **Exhaustive returns, one def (return rows):** the body's value plus every `return` of that `def`.
- **Not done:** closed caller sets and calls into other methods. Reflective, framework and `super` callers make
  both unsafe.

Trust base: the core semantics of literals and of the few core methods it uses (`freeze`, `size`, `[]` on a
literal Hash, `to_s` on scalars), an `is_a?` that is not redefined, and nominal class arms, as in the census's own
checks. A row's value is the object as it is when the expression runs. ERB and Haml spans are checked without their
context.

## Agreement with the 176 hand proofs

F73's census argued 176 sampled rows sound by hand ([source-arguments.tsv](../mutation-writers-census-2026-10-21/source-arguments.tsv));
[hand-proof-patterns.tsv](hand-proof-patterns.tsv) groups their titles by pattern. [agreement.tsv](agreement.tsv)
gives the checker's answer and, for each miss, its cause.

| Census pattern | Hand proofs | Proved | Why the rest are not proved |
| --- | ---: | ---: | --- |
| Fresh constructor | 78 | 66 | 11 rest on the analyzer's IR alone; C648 calls a proved callee |
| Fixed key schema | 28 | 20 | 3 call a proved callee; 3 cross methods; C1528 `to_s` and F126 `map` on unknown receivers |
| Dominating guard | 14 | 2 | 11 need caller enumeration; M403 `is_a?(Hash)` |
| Closed caller set | 13 | 0 | 8 need caller enumeration; 5 cross methods |
| Exhaustive returns | 41 | 0 | 20 need caller enumeration; 19 cross methods; 2 read ivars |
| Other | 2 | 0 | F434 reads a view ivar; F465 is a vacuous slot |

Every miss is a pattern the checker does not implement or a stricter assumption, so it contradicts no hand proof.
87 of the 88 agreed rows carry the census's pattern.

- **IR-only evidence (11).** The census read emptiness from the analyzer's own IR. Nine synthetic constructors have
  no source span to check. M1708 and M1745 are per-call-site copies of `vary_by`'s `**kwargs`
  (`app/controllers/concerns/cache_concern.rb:7`), where the analyzer substituted `**{}`. In source the same slot
  also receives `unless: :disallow_unauthenticated_api_access?` (`app/controllers/api/v1/custom_emojis_controller.rb:4`)
  and `if: -> {...}`, which `Hash[Str, Str]` excludes. Only the analyzer knows which call site an occurrence is, so
  these two proofs are circular; the rows may still be sound.
- **Callee proved (4).** C648 → C1920, C503 → C1903, and F034 and F246 → F531. The callee's return row is proved;
  joining the call to it needs method resolution.
- **Stricter assumptions (3).** M403: `is_a?(Hash)` also admits `HashWithIndifferentAccess`, which hash types
  exclude. C1528 and F126 call `to_s` and `map` on unknown receivers.

## Negative controls

- **F73:** it proves none of the 21 losses and none of the 34 witness-only rows.
- **F72:** on F72's census with F72's types ([f72-rows.jsonl.xz](f72-rows.jsonl.xz), labels in
  [f72-labels.tsv](f72-labels.tsv)), it proves none of the 56 losses and none of the 6 inherited losses. Most are
  omitted array or hash mutations, which the writer enumeration must catch. With that mutation analysis switched
  off (`PC_ABLATE_USES=1`), it proves 9 of them (C761, C1176, C1431, C1432, F127, F218, F219, F287, M1299), so the
  control can catch errors. It proves 60 of F72's 75 hand-proved SOUND rows.
- **Tests:** [test_checker.rb](test_checker.rb) has 25 tests with 73 assertions, mostly claims a naive checker
  accepts: aliases, escapes, loop-carried writes, closures, invalidated guards, shadowed constants, `&.` setters and
  jumps.
- **Read against source, no error found:** every guard (25), return (53), plain def-use (28) and
  setter, branch or sequence proof (68); 22 of 68 writer proofs and 28 random literal proofs.

## Proved rows

[verdicts.jsonl.xz](verdicts.jsonl.xz) gives every row's verdict, pattern and value, or the reason it is not proved.

| Stratum | Proved / rows | Stratum | Proved / rows |
| --- | ---: | --- | ---: |
| Campfire unknown | 27 / 94 | Chatwoot unknown | 923 / 1,994 |
| Forem concrete/nil | 0 / 2 | Mastodon concrete/nil | 20 / 37 |
| Forem unknown | 202 / 545 | Mastodon unknown | 750 / 1,950 |
| Chatwoot concrete/nil | 0 / 30 | Total | 1,922 / 4,652 |

By pattern: fresh constructor 1,397, fixed key schema 447, exhaustive returns 53 and dominating guard 25. By table:
IR 1,493, controller cache 376 and returns 53; no parameter, side-table or binding row. By reader class
([census by reader](../census-by-reader-2026-10-22/README.md)): read by an analyzed body 1,199 of 3,426, only by an
emitter 348 of 548, by nothing 375 of 678.

## Bound

Proved rows are closed with zero losses. In each stratum the other rows are bounded by the sampled rows among them,
which are a simple random sample of those rows given their number. Losses and witness-only rows count as possible
losses, at 0.05/4 per sampled stratum, as in F73. [validate.py](validate.py) first reproduces F73's 2,202 and
1,907 with its own hypergeometric inversion. [bound.json](bound.json) holds every stratum.

| 95% simultaneous upper bound | F73 | Proved rows closed |
| --- | ---: | ---: |
| Conservative, all rows | 2,202 / 4,652 (47.3%) | 2,112 / 4,652 (45.4%) |
| Conservative, reader-visible rows | 1,907 / 3,974 (48.0%) | 1,824 / 3,974 (45.9%) |
| Same, with M1708 and M1745 unproved | 2,301 (49.5%) and 2,009 (50.6%) | 2,183 (46.9%) and 1,899 (47.8%) |
| Detection only, passing witnesses trusted | 1,021 / 4,652 (21.9%) | 1,055 / 4,652 (22.7%) |

Closing rows barely helps. In the four unknown-only strata the checker closes 41.5% of the rows and 42.5% of the
sample, and every sampled row it closes was already hand-proved. All 44 sampled losses and witness-only rows stay,
now among 92 sampled rows instead of 160.

Under the conservative rule a passing witness never closes a row; only a proof or a found loss does. At the
remainder's observed mix, a full census of all 2,730 unproved rows would still leave about 1,523 possible losses
(32.7%), so no number of witness runs brings the bound under 10%. If every new sampled row were resolved, proved or
shown lossy, at the observed loss rates, about 1,570 more sampled rows would bring it under 10% with proportional
allocation. The projected loss rate is 8.8%, so that margin is thin. Proving those rows needs caller enumeration
and returns across methods.

## Limits

- Unset V0A0 dumps only. Parameter, side-table and binding rows are never proved.
- The trust base above is assumed, not checked.
- The checker has had no second review. Its author read the proofs listed above against the source.

## Files and label map

- Inputs: [rows.jsonl.xz](rows.jsonl.xz), the 4,652 rows as locators plus the candidate's type, with no census
  status, witness or loss; [f72-rows.jsonl.xz](f72-rows.jsonl.xz), F72's 137 labeled rows with F72's types. Source
  paths are relative to each app's checkout; keys spell them `examples/apps/<app>/…`.
- Outputs: [verdicts.jsonl.xz](verdicts.jsonl.xz), [f72-verdicts.jsonl](f72-verdicts.jsonl),
  [f72-ablated.jsonl](f72-ablated.jsonl), [agreement.tsv](agreement.tsv) and [bound.json](bound.json).
- Every file the checker reads (each Ruby file under `app`, `lib`, `config`, `db`, `test`, `spec` and
  `enterprise`, and every row's source) matches the public pins byte for byte. Run against fresh checkouts of the
  pins, the checker reproduces all 4,652 verdicts and both F72 outputs exactly.
- `qt-mutate-66c06f52` → `mutation-writers-66c06f52`; `spine3-control` → `response-return-spine-control`.
  Census row IDs are F73's; F72's IDs are F72's census's and can look the same.

## Rerun

From the lab root, with CRuby 4.0.7 (Prism 1.8.1) and Python 3.9 or later:

```sh
sh corpus/fetch.sh
sh receipts/census-proof-checker-2026-10-22/run.sh
```

`corpus/fetch.sh` checks out the pinned apps under `corpus/apps`; to reuse other checkouts at the same pins, set
`APPS` to their parent directory instead. `run.sh` runs the tests, reruns the checker on both inputs and the
ablated control, and checks every output and every number above against the published files in about 20 seconds.
[audit.py](audit.py) prints proved rows with their source context, for reading proofs by hand.
