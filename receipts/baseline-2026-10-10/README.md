# Current-main baseline, October 10, 2026

Condition: **fixpoint-current-main-20261010-c210f226**. The five pinned public apps are Campfire,
Mastodon, Chatwoot, Forem and Discourse. These are the recorded October 10 runs, with their raw outputs
and commands; packaging recomputed the counts and all fifteen paired error censuses without rerunning
the analyzer. Earlier lab baselines retain their own conditions.

S3 reports every loop settled, but passes the observed any-order gate on **0/5** apps. Its fully typed
share is **69.8135%**, against the main-compatible base's **70.1619%**. Opacity and reported settling
do not establish runtime soundness or a verification fixed point.

## Source pins and commands

| Role | Published source |
| --- | --- |
| Native main control | [`c210f226346b462214866b5756b457ad53f647b1`](https://github.com/bunnykong/roundhouse/tree/c210f226346b462214866b5756b457ad53f647b1) |
| Merged `fixpoint-staged` | [`5716ddf368aa1df850b7d02906f91976bb8e573a`](https://github.com/bunnykong/roundhouse/tree/5716ddf368aa1df850b7d02906f91976bb8e573a) |
| Merged `fixpoint-next`, both probe arms | [`38403140379cd69759b0fe6247c6a8c4a48a37a9`](https://github.com/bunnykong/roundhouse/tree/38403140379cd69759b0fe6247c6a8c4a48a37a9) |
| Lab and input recipe before this addition | [`d824c4355c7faae4b9bb4a77b25daa178a3df36c`](https://github.com/bunnykong/roundhouse-fixpoint-lab/tree/d824c4355c7faae4b9bb4a77b25daa178a3df36c) |

Main was merged into staged, then staged into next; published ancestry was preserved. Exact parents,
tested trees and binary hashes are in [final-audit.json](evidence/final-audit.json). App source commits,
whole-tree hashes and counts are in [inputs.json](evidence/inputs.json). The seven public emission
fixtures and fifteen targets are in [emission-inputs.json](evidence/emission-inputs.json).

The unchanged [probe](probe) has SHA-256
`42a29d21aedeafd48ce89b1287851b2478242b5828e963a0bf3f71c6652d6a9e`.
The native parity command is `roundhouse check --continue .`, with every `RH_` variable unset.
The probe's base is `PROBE_BASE=1` in the next binary, rather than the separate native main executable.
Its five Boolean stage controls are 0 and `RH_SCHED=rounds`; S3 uses the controls below.

```sh
RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1 RH_BRK_ALLARMS=1 RH_SCHED=sccq
# Both probe arms:
RH_FIXPOINT_STATS=1 RH_FIXPOINT_DIGEST=1 RH_PRECISION_CENSUS=1
# Precision and reported loop endings:
RH_FIXPOINT_VERIFY=0
# Separate schedule and repeat runs:
RH_FIXPOINT_VERIFY=1 RH_ERRGATE=1 RH_PUBLIC_INPUT=1
# Three schedules: RH_SHUFFLE unset, then RH_SHUFFLE=1, then RH_SHUFFLE=2.
```

Every other `RH_` variable was unset. `RH_SHUFFLE` perturbs the S3 worklist; base rounds are controls.
Each run's `receipt.json` retains the exact command, flags, compiler tree, binary and input hashes,
Ruby version and start time. Recording-machine paths are normalized to logical relative roots.
[environment.json](evidence/environment.json) retains tool versions: Rust/Cargo 1.98.1, Ruby 4.0.7 for
app runs, Ruby 3.4.4 for tests, GNU Bash 5.2.0, Python 3.12.13 and jq 1.7.1 on arm64 macOS. Go was unavailable.

## Precision and loop endings

Each app name links to its raw probe directory. `precision-unset/report.json` is the source for both
counts and loop endings. Fully typed includes bottom and measures absence of `Var` and `untyped`;
the category partition and missing positions remain explicit in every report.

| App | Base fully typed | S3 fully typed | Typed positions |
| --- | ---: | ---: | ---: |
| [Campfire](runs/probe/campfire) | 25,453 | 25,442 | 32,505 |
| [Mastodon](runs/probe/mastodon) | 157,598 | 157,606 | 209,667 |
| [Chatwoot](runs/probe/chatwoot) | 95,116 | 94,803 | 151,528 |
| [Forem](runs/probe/forem) | 131,410 | 131,219 | 160,116 |
| [Discourse](runs/probe/discourse) | 319,219 | 316,107 | 484,919 |
| Pooled | 728,796 | 725,177 | 1,038,735 |

There are 24,699 missing positions in each arm, excluded from that denominator. The pooled shares
are 70.1618796% and 69.8134750%; S3 is **0.3484045 percentage points** lower. This aggregate reduction
does not redo historical F7's paired loss/gain attribution. No application runtime oracle was run
for this condition; lower opacity alone cannot certify soundness.

Round numbers are zero-based. These are verification-off loop reports, not the extra-round verification.

| App / arm | Production | Views / tests | Absorb |
| --- | --- | --- | --- |
| Campfire / base | settled 6 | settled 4 | settled 4 |
| Campfire / S3 | settled 3 | settled 4 | settled 1 |
| Mastodon / base | cap | settled 1 | settled 6 |
| Mastodon / S3 | settled 3 | settled 1 | settled 1 |
| Chatwoot / base | cap | settled 1 | settled 4 |
| Chatwoot / S3 | settled 4 | settled 1 | settled 2 |
| Forem / base | settled 10 | settled 1 | settled 4 |
| Forem / S3 | settled 4 | settled 1 | settled 2 |
| Discourse / base | cap | settled 1 | cap |
| Discourse / S3 | settled 5 | settled 1 | settled 2 |

## Any-order and error census

The gate requires equal final structure and all carried-value digests across unset/1/2 schedules,
plus zero verification movement in every schedule. Structure schema **2** includes parameter receiver
side; its digest strings cannot be compared with schema 1's strings.

| S3 app | Same structure | Same values | Verify moved: unset / 1 / 2 |
| --- | --- | --- | --- |
| Campfire | yes | no | 0 / 0 / 0 |
| Mastodon | no | no | 1 / 1 / 1 |
| Chatwoot | no | no | 1 / 1 / 2 |
| Forem | no | no | 3 / 3 / 3 |
| Discourse | no | no | 2 / 2 / 2 |

S3 passes on 0/5; base passes on 1/5 (Campfire). Base verification movement is respectively
0, 41, 77, 8 and 352 on each of its three schedules. S3's identical unshuffled repeat preserves
all value digests on 5/5 apps, but observed structure on only 2/5. The cumulative observer still
discovers structure during typing in both arms on every app. Three schedules are a measured check,
not a proof of any-order equality. See [baseline-summary.json](evidence/baseline-summary.json) for
complete per-component digests, verification and worklist counters, and schedule-enabled precision.

For the unshuffled comparison, the matched-site census finds one new-only error (Mastodon,
undetermined) and fifteen old-only errors. Nine removed errors are hidden by unknown receivers;
four have gained answering arms, one is missing a non-failing observation, and one is undetermined.
Discourse contributes twelve removals: eight hidden, three gained-arm and one missing. Each app's
`errgate-{unset,1,2}.json` retains the per-kind deltas and verdicts. These are catalog-based
classifications, with no runtime confirmation. [errgate.py](errgate.py) recomputes them from the full
paired raw census logs.

The separate [Discourse inspection](evidence/f8-summary.json) pairs 28 `@data` reads. On the pinned
public [source](https://github.com/discourse/discourse/blob/343b20f97ef5f6bd70826ee0e993ba348b210fd5/app/jobs/base.rb#L53),
the hostname String is written before the PID Integer. S3's receiver value type is Integer alone at
lines 55–57, but Integer or String at line 75. [Serialized IR](runs/f8) is retained separately;
this source-level witness has no runtime trace or isolated causal attribution.

## Flags-off parity and inherited suite failures

The [emission outputs](emission) retain all 105 pair rows per arm and SHA-256 inventories for 11,432
unique emitted paths. Recorded byte comparisons find no differences for either merged branch.
[Native outputs](runs/native) reproduce all five main error-kind dictionaries: totals are Campfire 0,
Mastodon 1,474, Chatwoot 890, Forem 541 and Discourse 2,349.

The full default selections ran to completion. Main is 4,927 passed / 3 failed / 236 ignored;
staged is 4,957 / 3 / 236; next is 4,970 / 3 / 236. All three share the same inherited failures:
the Rust runtime header-guard assertion, the RBS empty-Array initializer assertion, and the Haml
Spinel runtime's Inflector reference. The library selections and full raw logs are in `evidence/`.
Neither ignored prerequisites nor an unavailable SDK is counted as successful coverage.

## Recompute or rerun

From the lab root, recompute all numbers, including the fifteen paired raw error censuses:

```sh
python3 -B receipts/baseline-2026-10-10/recompute.py
# Optional source-to-IR verification after fetching the pinned apps:
python3 -B receipts/baseline-2026-10-10/recompute.py --app-root corpus/apps
```

[archive.json](archive.json) retains source and normalized hashes, stored hashes, sizes and compression
for each copied input. Gzip is lossless; the only textual normalization removes recording-machine
paths and formats JSON. Raw stdout, census rows, diagnostic multiplicities and inferred types remain
available. Generated public Rails fixtures are archived byte for byte, with a separate input inventory.

For fresh analyzer runs, install the pinned Rust/native dependencies, Ruby versions, Bash and jq.
Fetch the five public apps, then use a new output directory. The script builds the three exact pins,
checks every input hash, runs the same emission selection, native parity, precision, schedules,
repeat and source inspection, and records commands and outputs. `--suites` adds the inherited default
selections with Ruby 3.4.4; Spinel and its native libraries must be available for integration coverage.

```sh
sh corpus/fetch.sh
python3 -B receipts/baseline-2026-10-10/rerun.py --work-dir _work/baseline-2026-10-10-rerun
```

Run one live measurement at a time; on a shared host, hold its shared heavy-work lock around the whole
command. Fresh timings and binary hashes belong to that rerun's environment. The portable rerun
script was syntax-checked and its input extraction verified during packaging; a fresh native build
and analyzer rerun were not performed during this recording step.
