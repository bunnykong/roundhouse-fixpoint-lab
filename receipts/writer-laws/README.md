# A carried-slot writer-law instrument

Condition: **writer-laws-20261010-c210f226**, on main
`c210f226346b462214866b5756b457ad53f647b1`. The test-only instrument is published on
[`writer-law-harness`](https://github.com/bunnykong/roundhouse/tree/writer-law-harness) at
[`bf2f052ff34a240dab0cb05b1185c0e3ad571888`](https://github.com/bunnykong/roundhouse/tree/bf2f052ff34a240dab0cb05b1185c0e3ad571888).
It leaves analyzer policy unchanged. The supplied runs were recomputed from archived output during
packaging; a new Cargo run was not performed here.

There are **55 writer checks: 14 pass, 41 known violations are ignored** in the default selection.
The include-ignored selection runs every check and fails as expected: **199 passing properties and 116 failing properties**,
across **13,256,907 generated comparisons**. Every failed property retains a counterexample.
This measures finite local policies; it does not certify the complete carried product or whole-app order independence.

## Inventory and counterexamples

- [inventory.md](inventory.md) lists W01–W55, operation kinds, every property vector, and C01–C23
  composition paths. Those composition paths are inventory, not additional generated passes.
- [law-results.json](law-results.json) and [law-results.tsv](law-results.tsv) contain all 315
  property rows, comparison counts, witness sizes and counterexamples, linked to test names.
- [known-failures.json](known-failures.json) maps exactly the 41 ignored tests to their reasons.
- [laws-final.log.gz](logs/laws-final.log.gz) is the complete include-ignored output.
  [selected-laws.txt](logs/selected-laws.txt) and [writer-function-map.txt](logs/writer-function-map.txt)
  retain source locations at this pin.

The generated universe extends the [ivar join harness](https://github.com/rubys/roundhouse/pull/705)
and [parameter join harness](https://github.com/rubys/roundhouse/pull/724). It contains 40 type
representations: both field orders, empty and unequal tuples, functions, generic classes, nested
containers, and Nil/pending/gradual unions. Bound checks add 52 samples around depth 15/16/17 and
node counts 511/512/513, with 686 triples and all six arrival permutations.

Binary policies check commutativity, regrouping, idempotence, pending identities, duplicate replay,
and arrival permutation. Transfers check repeated application, pending and join preservation,
union-arm permutation, and monotonicity under `join_ivar_slot`. Other checks compare one bound
after a complete batch with pairwise cuts, or inspect actual reflective storage. Every failed
property keeps the finite-domain minimum by input node count, then printed input/output text.
This is not a claim of the smallest possible Ruby program.

The normalized ivar and parameter joins, their small wrappers, bounded batches and several local
policies pass. Remaining counterexamples include harvested-return replacement/stabilization,
ordered copies, first-owner and last-write policies, raw-union pending arms, gates, narrowing,
destructuring, closure refinement and IR stamps. A recorded counterexample calls for assessing the
writer's intended semantics; source-priority rules are not automatically semilattice joins.

## Commands and the default suite

Run from a checkout of the exact harness commit, with Rust/Cargo 1.98.1 and Ruby 3.4.4. Use a dedicated
`CARGO_TARGET_DIR` and `CARGO_BUILD_JOBS=4`. The commands recorded for the law selections are:

```sh
# Enabled checks: expected 14 passed, 41 ignored, exit 0.
cargo test --locked --lib writer_law_ -- --nocapture --test-threads=1
# All checks: expected 14 passed, 41 failed, exit 101.
cargo test --locked --lib writer_law_ -- --include-ignored --nocapture --test-threads=1
# Only the known violations: expected exit 101.
cargo test --locked --lib writer_law_ -- --ignored --nocapture --test-threads=1
```

The full default suite is **4,941 passed, 3 failed, 277 ignored** across 692 result blocks.
Its 277 ignores comprise the original 236 plus the 41 known writer violations. The three inherited
failures reproduce on untouched main: the Rust header-guard assertion, the RBS empty-Array initializer
assertion, and the Haml/Spinel Inflector reference. These are recorded failures, not green gates.
[default-suite.log.gz](logs/default-suite.log.gz), [main-control-results.json](main-control-results.json)
and the three `logs/main-control-*.log.gz` files retain commands, selections and full outputs.
[verification.json](verification.json) retains the toolchain and Spinel binary hash.

```sh
cargo test --locked --no-fail-fast -- --test-threads=1
```

The recording used GNU Bash 5.2.0 and the native integration prerequisites. Ignored prerequisites
do not establish coverage. All analyzer work was serialized under the recording host's shared lock.

## Recompute or rerun

From the lab root:

```sh
python3 -B receipts/writer-laws/recompute.py
python3 -B receipts/writer-laws/rerun.py --work-dir _work/writer-laws-rerun
```

The reduction checks all counterexample rows against the original raw log, confirms every known
violation is ignored in the default output, and counts all suite blocks. [archive.json](archive.json)
retains source, normalized and stored hashes; only recording-machine paths and JSON formatting were normalized.

The rerun clones the public fork or accepts `--source`, builds at the exact pin and records the
enabled and include-ignored commands. `--default-suite` adds the full integration selection, which
needs prepared public fixtures, Spinel and its native libraries. Run one live job at a time under
the shared host's heavy-work lock. Script syntax and command-line parsing were checked during
packaging; the historical native suite was not rerun by this packaging task.

## Limits

The generated domain uses fixed names, positions, registries and closure contexts. It does not
certify slot identities, producer discovery, complete dependencies, framework coverage, every arity,
or all branch predicates. Semantic equality canonicalizes union arms and ignores record field order;
wire order, emitted-code identity and diagnostic parity are separate checks. Passing local laws
does not prove Ruby denotational soundness, least fixed points or a lawful whole carried state.
Snapshot/cache compositions and non-type metadata remain inventoried rather than exhaustively tested.
