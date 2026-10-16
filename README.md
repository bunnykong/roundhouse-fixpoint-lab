# Roundhouse fixpoint lab

Companion to the RFC [rubys/roundhouse#617](https://github.com/rubys/roundhouse/issues/617), *a fixpoint that settles*. Related work and credits are in [RELATED-WORK.md](RELATED-WORK.md).

The [research index](https://github.com/bunnykong/roundhouse/blob/fixpoint-research/docs/research/README.md)
maps the open work; the [facts](https://github.com/bunnykong/roundhouse/blob/fixpoint-research/docs/research/facts.md)
keep each claim's condition, pins and receipt together.

A small, reproducible place to explore why structural inference grows, what makes iteration converge,
and how finite constructor-site identities give a least solution. It contains public Ruby reproductions,
pinned public-app recipes, executable models, a runtime shape oracle, experimental Roundhouse patches,
and a Lean proof of the finite-site core. Original lab material is Apache-2.0 licensed; derivative-source credits and licenses are in [NOTICE](NOTICE).

The [typed-recursion demo](patches/emit-rec/README.md) compiles three controller walk shapes
as native recursive types in Rust and Crystal, with their pages checked against CRuby
([F13](https://github.com/bunnykong/roundhouse/blob/fixpoint-research/docs/research/facts.md#f13)).
The [soundness/settling 2×2](reproductions/settle_sound/README.md) shows why correcting Ruby
flow and making inference settle are both needed on the merged-back normalizer.
The [research receipts](receipts/README.md) include pending-return counterexamples, a destructuring
matrix, writer and cache boundaries, and manual recursive-kernel references.

Start with the [small fixtures](reproductions/README.md), [models](models/README.md), or
[proof scope](proof/PROOF.md). The patches are research configurations; the docs retain failed designs
and the difference between completion, observed convergence, and proved properties.

## Reproduce a claim

Run from the repository root. Python commands need Python 3.9+ and its standard library.
Runtime traces need CRuby 4.0.7. Source acquisition needs Git. Building Roundhouse needs its pinned
Rust toolchain and native Cargo dependencies. Lean builds need elan, network access, and dependency cache space.

| Claim or observation | Command |
| --- | --- |
| Pinned baseline on public code | `python3 corpus/reproduce.py baseline` |
| All 27 small fixtures with a supplied binary | `python3 corpus/run.py --binary ./roundhouse --set micro` |
| Sharing through stage 1g | `python3 corpus/reproduce.py sharing-1g` |
| Origin-aware fold with slot dependencies | `python3 corpus/reproduce.py fold2` |
| SCC scheduler | `python3 corpus/reproduce.py sccq` |
| Complete-state Phase C1 | `python3 corpus/reproduce.py phase-c1a` |
| Phase C2 with repaired sharing | `python3 corpus/reproduce.py phase-c2a` |
| Anonymous EP3 cut | `python3 corpus/reproduce.py ep3-m1prime` |
| Identity-carrying EP3 cut | `python3 corpus/reproduce.py ep3-m2` |
| Solver work, edit handling, and certified seeds | `python3 -B models/control/run.py` |
| Runtime witnesses against emitted grammars | `python3 -B models/control/run.py` |
| Compact cyclic comparison and its limits | `python3 -B -m models.cyclic_eq.bench` |
| Termination, leastness, and soundness theorems | `(cd proof && lake exe cache get && lake build)` |
| Patch applicability on the historical baseline | `python3 patches/check.py` |
| Python/Ruby regression checks | `python3 -B check.py` |

Use `--binary ./roundhouse` with `corpus/reproduce.py` to supply a prebuilt binary, or `--set micro`
to run the small suite first. Every experiment's exact flags are in [configurations.json](patches/configurations.json).
Historical timing is a reference measurement; a rerun produces a new measurement with its own binary hash,
host, limits, flags, and input hashes. No timing recipe guarantees the same wall-clock value on a different host.
The claim table covers the evidence in this lab; an RFC must retain the same qualifications.

## Public reference results

Condition: **public-corpus-v1**, Roundhouse **b28b17b6**, flags unset, five pinned apps,
40 GiB / 1,200 seconds per app, arm64 macOS. Single-run historical measurements; no rerun is implied by packaging.
Peak is max(wait4 peak, sampled RSS); wall is the child interval. Raw diagnostic messages are not included.

| Public app | Outcome | Peak GiB | Wall seconds |
| --- | --- | ---: | ---: |
| campfire | completed | 0.154 | 0.542 |
| chatwoot | completed | 0.521 | 6.410 |
| discourse | completed | 1.317 | 34.269 |
| forem | completed | 0.398 | 4.847 |
| mastodon | completed | 0.665 | 18.202 |

Under the same reference condition, with 4 GiB / 120 seconds for each small fixture, 9 of 13 completed.
The two-method cycle, three-method cycle, merge-feedback normalizer, and parameter-only argument tree
were memory-killed. Completion is compatible with reported type errors and with hitting an inference round cap;
it does not certify a true fixpoint. [baseline.json](corpus/published/baseline.json) contains every reference row,
the binary hash, limits, input commits, and diagnostics by kind.

The expanded condition is **public-lab-v1**, with 27 small fixtures. Its outcomes must be measured;
the historical 13-fixture completion count is not a claim about that expanded set.

## Explore and contribute

Try a counterexample, inspect the assumptions it violates, and compare an executable model with its Lean statement.
Useful contributions include small public reproductions, source-to-site lowering certificates, complete-state
convergence checks, and measurements that retain their condition and flags. Each model README gives a starting command.
The [oracle](oracle/README.md) distinguishes witnessed soundness from proofs; the
[proof](proof/PROOF.md) distinguishes an exact abstraction from concrete executions.

Roundhouse credit and derivative-source attribution are in [NOTICE](NOTICE). The license is [Apache-2.0](LICENSE).
The public applications and Mathlib dependencies are fetched separately under their respective licenses.

## October 15 evening observations

The [five evening references](receipts/README.md#october-15-evening-references) cover the killed storage composition,
its bounded normal-form repair, negative ownership generalization, explicit observers and the partial five-app grid.
The [cached observer tool](tools/observers/README.md) retains its fourteen tests and public pins.
These are research references; they close no whole-program inference or replay frontier.

## October 15 later evening results

Six separately conditioned, unscored references preserve bounded confirmations, failed generalization,
negative storage laws and finite runtime counterexamples. The source snapshots remain uncompiled public ports.

- [F56: strict producer reasons](receipts/strict-producer-reasons-2026-10-15/README.md).
- [F57: closure application effects](receipts/closure-application-effects-2026-10-15/README.md).
- [F58: declared contributor join](receipts/declared-contributor-join-2026-10-15/README.md).
- [F59: schedule row attribution](receipts/schedule-row-attribution-2026-10-15/README.md).
- [F60: writer partition replay](receipts/writer-partition-replay-2026-10-15/README.md).
- [F61: ownership runtime values](receipts/ownership-runtime-values-2026-10-15/README.md).

## October 15 integrated repair result

[F62: fixpoint spine](receipts/fixpoint-spine-2026-10-15/README.md) combines the measured repairs.
Campfire reason rows agree; partition failures and larger-app value equalities remain.

## October 16 response and return results

[F63: response return values](receipts/response-return-values-2026-10-15/README.md) confirms its stabilization-off witnesses.
[F64: latest writer returns](receipts/latest-writer-returns-2026-10-15/README.md) remains inconclusive with reproduced descents.

## October 16 negative and inconclusive results

[F65: literal current writes](receipts/literal-current-writes-2026-10-16/README.md).
[F66: deferred unresolved](receipts/deferred-unresolved-2026-10-16/README.md).
[F67: boundary row carry](receipts/boundary-row-carry-2026-10-16/README.md).

## October 16 strict stubs and response composition

[F68: strict stub runtime values](receipts/strict-stub-runtime-values-2026-10-16/README.md).
[F69: response return spine](receipts/response-return-spine-2026-10-16/README.md).

## October 16 strict stub completion

[F70: strict stub completion](receipts/strict-stub-completion-2026-10-16/README.md).
[Reusable quick-test checker](tools/probe/README.md).

## October 16 history-free current values

[F71: equality gains with runtime value loss](receipts/history-free-current-values-2026-10-16/README.md).

## October 16 integrated current writers

[F72: unsound equality gains and the mutation census](receipts/integrated-current-writers-2026-10-16/README.md).
