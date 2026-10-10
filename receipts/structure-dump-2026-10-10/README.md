# Logical structure dumps and schedule differences — October 10, 2026

The opt-in observer and comparator expose return-writer and route differences across the three schedules on all five public apps. Slot sets differ on four; Campfire's slots stay fixed. An independent unset repeat preserves slot and writer sets and carried-value digests on all five, while routes differ on four. These are observed logical facts with explicit mapping and access-coverage limits.

Condition: **structure-tools-38403140-s3-public-lab-v1-verify-off**. S3's six flags are on, verification is off, stats and digests are on, and every other experimental flag is unset. Schedules are unset, 1 and 2, followed by an independent unset repeat. Native hash iteration is uncontrolled. This is an unscored observation condition. The historical tables are reduced from supplied measurements; the packet's offline checks perform no native analyzer or Cargo run.

## Pins

- Tools: [`structure-dump`](https://github.com/bunnykong/roundhouse/tree/structure-dump), exact commit `abda389cbf30b7c0219d766134e0522b2ffe346f`.
- Public base: `fixpoint-next` `38403140379cd69759b0fe6247c6a8c4a48a37a9`, including main `c210f226`.
- Tested source tree: `5fbefd5f66868555a04505e00218a6dded0f3d58`. Measurements ran this tree as a patch on the base; the tools commit has the same tree. The original base HEAD and patch hash remain in the receipts.
- Recorded release binary SHA-256: `926da70f3f281299f946ce4588a76f42bad4887f13eca7b531c04dcf01ddeb9c`.
- Measurement lab: `d824c4355c7faae4b9bb4a77b25daa178a3df36c`; receipt added on lab base `d0b2e5dd689c04221295b9a4037dede07984c770`.
- Rust 1.98.1, four Cargo build jobs; CRuby 4.0.7 for app commands and pinned 3.4.4 for the suite, on arm64 macOS. Builds and app runs used the shared host analysis lock.

[pins.json](pins.json), [input tree identities](evidence/inputs-current.json) and [toolchain.json](evidence/toolchain.json) retain full identities. All five app trees were verified before and after the sweeps.

| App | Commit |
| --- | --- |
| campfire | `90b330024dec3e757c79b6a7e6568f93da8e3148` |
| mastodon | `163f96cee4dea23365bff9b433871e68d20d9ee7` |
| chatwoot | `9f920b549c14491a4e587687a3eed5d21c6ccc7d` |
| forem | `cd665002c660cacfc6d267c5de81206cea7bf9a3` |
| discourse | `343b20f97ef5f6bd70826ee0e993ba348b210fd5` |

## Commands

Use the pinned tools checkout, its release binary, the lab's fetched public apps, and a fresh shell with other experimental `RH_` variables unset. The probe enables the six S3 flags and stats/digests. Separate directories retain each run's diagnostics.

```sh
export RH_BIN="$PWD/rh/target/release/roundhouse"
export APPS="$PWD/lab/corpus/apps"
probe="$PWD/rh/tools/research/probe"
mkdir -p runs/campfire/unset runs/campfire/1
(cd runs/campfire/unset && env -u RH_SHUFFLE bash "$probe" campfire \
  RH_FIXPOINT_VERIFY=0 "RH_STRUCT_DUMP=$PWD/structure.jsonl" > report.json)
(cd runs/campfire/1 && RH_SHUFFLE=1 bash "$probe" campfire \
  RH_FIXPOINT_VERIFY=0 "RH_STRUCT_DUMP=$PWD/structure.jsonl" > report.json)
python3 rh/tools/struct_diff.py runs/campfire/unset/structure.jsonl \
  runs/campfire/1/structure.jsonl --json --samples 3
```

`--changes FILE` saves every differing fact; `--check` exits 1 for differences. Invalid, incomplete or incompatible dumps exit 2. Comparisons require matching input, binary, inference flags and dump phase. The optional dump never supplies an inference value; an output error is nonfatal. One path is atomically replaced by the last analysis in a process.

From this lab's root, check the saved packet or regenerate all twenty dumps and both maps:

```sh
python3 -B receipts/structure-dump-2026-10-10/recompute.py
sh corpus/fetch.sh
python3 -B receipts/structure-dump-2026-10-10/rerun.py \
  --work-dir "$PWD/_work/structure-dump-rerun" --lock "$PWD/_work/analysis.lock"
```

[rerun.py](rerun.py) clones the public fork, detaches the exact tools commit, verifies its tree and builds with `cargo +1.98.1 build --release --locked --bin roundhouse`. `--source DIR` accepts a clean checkout at that commit; `--binary FILE` accepts a supplied binary and records its SHA-256. `--apps DIR` accepts fetched pinned app clones; `--app campfire` limits the run to one app. Python 3.9+, Bash, jq, Git, Rust/native build dependencies and the recorded Ruby versions are required. Use the host's common lock path when other analyses share it. Output must be a new directory. A rerun records a new condition and binary hash; repeat-varying routes and host-dependent timings need not reproduce byte for byte.

## Divergence by app and kind

Each cell is **left-only / right-only** facts, not changed type values. Rows list kinds that differ in at least one schedule pair; other measured kinds have equal fact sets. The observer inventories syntax and cumulative discovery before final expansion, including transient inline/reference routes. A route can record when an access occurred during discovery, even when the final carried value agrees.

All five apps change return writers and dispatch/return routes in at least one pair. Context slots change on Mastodon, Chatwoot, Forem and Discourse; narrowing slots change on those four. Parameter/position slots change on Mastodon, Chatwoot and Discourse; fold-parameter slots on Mastodon and Discourse; controller slots and call-graph routes on Discourse. Source-expression, constant and closure slot sets stay equal across these pairs. Forem's narrowing difference is absent for unset versus 2. Campfire's small differences involve `Current.session` reads and authentication-method harvests.

### campfire

| Entity / kind | Unset → 1 | Unset → 2 | 1 → 2 |
| --- | ---: | ---: | ---: |
| route / dispatch | 1 / 0 | 1 / 0 | 0 / 0 |
| route / return | 3 / 4 | 4 / 4 | 3 / 2 |
| writer / return | 4 / 4 | 5 / 4 | 5 / 4 |

### mastodon

| Entity / kind | Unset → 1 | Unset → 2 | 1 → 2 |
| --- | ---: | ---: | ---: |
| route / closure-parameter | 4 / 2 | 7 / 0 | 9 / 4 |
| route / context | 41 / 388 | 28 / 373 | 54 / 52 |
| route / dispatch | 579 / 896 | 568 / 577 | 845 / 537 |
| route / fold-parameter | 79 / 237 | 88 / 236 | 79 / 69 |
| route / ivar | 4 / 0 | 4 / 0 | 0 / 0 |
| route / local | 1 / 166 | 1 / 164 | 8 / 6 |
| route / narrowing | 59 / 111 | 2 / 95 | 19 / 60 |
| route / parameter | 3 / 163 | 14 / 161 | 19 / 6 |
| route / position | 115 / 14 | 121 / 7 | 23 / 10 |
| route / reference-mode | 0 / 3 | 0 / 3 | 0 / 0 |
| route / registry | 348 / 22 | 70 / 113 | 49 / 418 |
| route / return | 1,223 / 1,116 | 692 / 993 | 981 / 1,389 |
| slot / context | 11 / 21 | 2 / 18 | 7 / 13 |
| slot / fold-parameter | 0 / 148 | 0 / 148 | 0 / 0 |
| slot / narrowing | 8 / 16 | 0 / 11 | 5 / 8 |
| slot / parameter | 0 / 1 | 3 / 0 | 4 / 0 |
| slot / position | 2 / 1 | 2 / 0 | 3 / 2 |
| writer / context | 3 / 12 | 0 / 12 | 1 / 4 |
| writer / fold-parameter | 0 / 148 | 0 / 148 | 0 / 0 |
| writer / narrowing | 14 / 24 | 0 / 15 | 9 / 14 |
| writer / parameter | 2 / 10 | 16 / 10 | 20 / 6 |
| writer / position | 6 / 1 | 2 / 0 | 3 / 6 |
| writer / return | 20 / 28 | 13 / 21 | 20 / 20 |

### chatwoot

| Entity / kind | Unset → 1 | Unset → 2 | 1 → 2 |
| --- | ---: | ---: | ---: |
| route / attribute | 6 / 0 | 0 / 0 | 0 / 6 |
| route / context | 68 / 86 | 53 / 388 | 42 / 359 |
| route / dispatch | 131 / 108 | 129 / 89 | 99 / 82 |
| route / fold-parameter | 2 / 0 | 2 / 3 | 0 / 3 |
| route / local | 2 / 11 | 11 / 13 | 11 / 4 |
| route / narrowing | 12 / 2 | 3 / 6 | 1 / 14 |
| route / parameter | 9 / 11 | 12 / 16 | 13 / 15 |
| route / position | 0 / 8 | 0 / 3 | 5 / 0 |
| route / registry | 31 / 10 | 8 / 23 | 12 / 48 |
| route / return | 193 / 144 | 153 / 156 | 129 / 181 |
| slot / context | 10 / 26 | 5 / 281 | 10 / 270 |
| slot / narrowing | 1 / 2 | 1 / 3 | 1 / 2 |
| slot / parameter | 0 / 1 | 2 / 0 | 3 / 0 |
| slot / position | 0 / 7 | 0 / 2 | 5 / 0 |
| writer / context | 12 / 12 | 5 / 272 | 1 / 268 |
| writer / narrowing | 2 / 2 | 1 / 3 | 1 / 3 |
| writer / parameter | 0 / 4 | 8 / 0 | 12 / 0 |
| writer / position | 0 / 8 | 0 / 3 | 5 / 0 |
| writer / return | 24 / 24 | 11 / 27 | 6 / 22 |

### forem

| Entity / kind | Unset → 1 | Unset → 2 | 1 → 2 |
| --- | ---: | ---: | ---: |
| route / context | 4 / 7 | 1 / 6 | 8 / 10 |
| route / dispatch | 200 / 354 | 172 / 296 | 356 / 326 |
| route / fold-parameter | 3 / 2 | 0 / 0 | 2 / 3 |
| route / local | 1 / 0 | 1 / 0 | 1 / 1 |
| route / narrowing | 4 / 1 | 0 / 0 | 1 / 4 |
| route / registry | 10 / 24 | 11 / 29 | 7 / 11 |
| route / return | 223 / 392 | 184 / 339 | 366 / 352 |
| slot / context | 2 / 2 | 0 / 1 | 2 / 3 |
| slot / narrowing | 2 / 0 | 0 / 0 | 0 / 2 |
| writer / context | 2 / 0 | 0 / 2 | 0 / 4 |
| writer / narrowing | 2 / 0 | 0 / 0 | 0 / 2 |
| writer / return | 15 / 4 | 14 / 5 | 12 / 14 |

### discourse

| Entity / kind | Unset → 1 | Unset → 2 | 1 → 2 |
| --- | ---: | ---: | ---: |
| route / attribute | 0 / 0 | 15 / 2 | 15 / 2 |
| route / call-graph | 0 / 9 | 0 / 7 | 2 / 0 |
| route / closure-parameter | 0 / 2 | 5 / 4 | 7 / 4 |
| route / context | 301 / 477 | 246 / 372 | 339 / 289 |
| route / controller | 1 / 0 | 2 / 0 | 1 / 0 |
| route / dispatch | 1,693 / 1,613 | 1,591 / 1,658 | 1,411 / 1,558 |
| route / fold-parameter | 88 / 130 | 62 / 54 | 99 / 49 |
| route / ivar | 9 / 18 | 9 / 7 | 11 / 0 |
| route / local | 87 / 34 | 63 / 41 | 35 / 66 |
| route / narrowing | 34 / 31 | 7 / 34 | 11 / 41 |
| route / parameter | 168 / 184 | 89 / 153 | 100 / 148 |
| route / position | 106 / 69 | 103 / 28 | 73 / 35 |
| route / reference-mode | 13 / 6 | 2 / 5 | 1 / 11 |
| route / registry | 647 / 757 | 579 / 670 | 390 / 371 |
| route / return | 2,854 / 2,501 | 2,450 / 2,523 | 1,900 / 2,326 |
| slot / context | 47 / 71 | 26 / 52 | 43 / 45 |
| slot / controller | 1 / 0 | 2 / 0 | 1 / 0 |
| slot / fold-parameter | 11 / 3 | 2 / 3 | 0 / 9 |
| slot / narrowing | 12 / 14 | 3 / 12 | 4 / 11 |
| slot / parameter | 5 / 8 | 5 / 10 | 3 / 5 |
| slot / position | 31 / 23 | 24 / 5 | 24 / 13 |
| writer / context | 33 / 40 | 13 / 22 | 24 / 26 |
| writer / controller | 1 / 0 | 2 / 0 | 1 / 0 |
| writer / fold-parameter | 11 / 3 | 2 / 3 | 0 / 9 |
| writer / narrowing | 12 / 16 | 3 / 14 | 5 / 12 |
| writer / parameter | 253 / 247 | 139 / 199 | 150 / 216 |
| writer / position | 33 / 24 | 26 / 5 | 25 / 13 |
| writer / return | 28 / 37 | 17 / 45 | 19 / 38 |

## Unset repeat and interpretation

| App | Slots L/R | Writers L/R | Routes L/R |
| --- | ---: | ---: | ---: |
| campfire | 0 / 0 | 0 / 0 | 0 / 0 |
| mastodon | 0 / 0 | 0 / 0 | 1,170 / 1,376 |
| chatwoot | 0 / 0 | 0 / 0 | 238 / 194 |
| forem | 0 / 0 | 0 / 0 | 356 / 244 |
| discourse | 0 / 0 | 0 / 0 | 2,604 / 2,810 |

All five unset repeats retain identical carried-value digests. Routes differ on Mastodon, Chatwoot, Forem and Discourse despite an unchanged shuffle setting, so the schedule comparisons locate observed divergence but cannot attribute each changed route solely to `RH_SHUFFLE`.

The earlier corpus F24 records aggregate structure and value digests under its own observer and verification condition; F25 records finite local writer laws. The logical dump here also keeps concrete transient accesses and their inline/reference choices. Equal carried values, equal slot/writer sets and different accumulated routes can hold together. Agreement of an older digest covers that digest's inventory, while this broader route inventory requires its own repeat control. The finite writer-law checks in F25 likewise do not establish complete discovery or order independence.

[divergence-map.json](evidence/divergence-map.json) retains every grouped comparison and samples. [map-summary.json](evidence/map-summary.json) adds entity totals, changed value-digest parts and direct inline/reference replacements with equal source, target and operation. Other added/removed routes remain in the kind tables.

## Access declarations and source mapping

Counts are instrumented access occurrences with undeclared source capability or target membership, **reads / writes**. They are advisory and never fail the build.

| App | Unset R/W | Seed 1 R/W | Seed 2 R/W |
| --- | ---: | ---: | ---: |
| campfire | 300,472 / 25,483 | 309,732 / 25,520 | 309,717 / 25,552 |
| mastodon | 4,089,538 / 177,786 | 4,686,474 / 181,516 | 4,304,167 / 180,966 |
| chatwoot | 1,616,697 / 83,892 | 1,695,997 / 85,705 | 1,670,300 / 85,341 |
| forem | 1,779,631 / 73,648 | 1,815,644 / 75,562 | 1,828,680 / 75,139 |
| discourse | 7,719,271 / 265,465 | 8,759,776 / 268,407 | 8,800,429 / 266,919 |

Declarations permit kinds of access from syntax and named analysis phases. Concrete dispatch choices are measured independently; these capabilities do not predeclare a may-call equation graph. Each dump header retains all access counts and kind inventories, with concrete missing memberships/capabilities in `undeclared` facts.

| App | Unset ambiguous/unmapped | Seed 1 | Seed 2 |
| --- | ---: | ---: | ---: |
| campfire | 3,324 / 0 | 3,343 / 0 | 3,358 / 0 |
| mastodon | 101,476 / 25 | 102,683 / 30 | 102,261 / 25 |
| chatwoot | 21,794 / 0 | 22,631 / 0 | 22,286 / 0 |
| forem | 34,016 / 2,216 | 34,780 / 2,216 | 34,458 / 2,216 |
| discourse | 109,791 / 0 | 107,531 / 0 | 105,447 / 0 |

Ambiguous sites retain the sorted candidate set instead of selecting an arbitrary syntax path. Reads do not manufacture missing target slots. The observer covers AST membership, supplied body contexts and instrumented dispatch, binding, constant, harvest, join, handoff and fold interfaces. Snapshot-only context channels, ambiguous/unmapped identities and uninstrumented raw Rust field accesses remain coverage limits. Mapping gaps also contribute to undeclared capabilities. Audit candidate-set and unmapped keys before attributing their differences to discovery. This is observation infrastructure with no complete equation declaration or any-order certificate.

## Parity and inherited failures

Emission condition: **structure-tools-38403140-default-7-fixtures-15-targets-v1**, unchanged seven fixtures and fifteen targets.

| Dump flag | Pairs | Different files | Compared files |
| --- | ---: | ---: | ---: |
| off | 105 | 0 | 11,432 |
| on | 105 | 0 | 11,432 |

[emission-parity.json](evidence/emission-parity.json) retains both controls. Each arm's 105 pair reports and 11,432 emitted-file hashes are in `emission/off/` and `emission/on/`; those saved hashes match [the baseline manifest](evidence/baseline-emission-manifest.json). The unchanged public [emission harness](../baseline-2026-10-10/emit_all.rs) has SHA-256 `e18d90850e8631886ffcd465c96be268a9be45ae839da94413fc7cddc8ac5a4e`. Packaging recomputes saved emitted-file hashes, with no fresh emission command.

Focused observer tests pass 3/3, the S3 fixture tests pass 2/2, and comparator tests pass 6/6. The class-side early-read fixture reads another method's return before its first observed write and inventories named closure parameters. Integration checks compare status, stdout and diagnostics with the dump off/on and check a nonfatal dump-output error; they impose no inferred-type expectation.

The full default command is `cargo test --locked --no-fail-fast` with one test thread and experimental flags unset: 4,975 passed, 3 failed, 236 ignored. Its failures match the same-base suite:

- `emit::rust::library::value_union_emit_tests::action_controller_runtime_emit_typechecks_hotspots`
- `runtime_src::tests::rbs_ivar_decls_stamp_empty_array_initializers`
- `spinel_renders_the_same_page`

[default-suite.json](evidence/default-suite.json), [baseline-suite.json](evidence/baseline-suite.json) and `logs/default-suite.log.gz` retain the counts and failure evidence. This is parity with a failing baseline. The tools change no inference rule and do not repair those failures.

## Retained and omitted material

The twenty full dumps total **25,196,027,218 bytes (23.47 GiB)** and are omitted. [omitted-files.json](omitted-files.json) records each omitted file's byte count and SHA-256, including each full dump and the native binaries. [source-files.json](source-files.json) records original-byte hashes for the supplied measurement files. App command elapsed times range from 2.39 to 633.61 seconds, including observer and JSONL output; these are shared-host instrumentation timings, not benchmarks.

`runs/APP/SCHEDULE/receipt.json` preserves command, condition, flags, input/binary/source identities, timings, dump header, bytes and SHA-256. The adjacent report retains value and aggregate-structure digests; compressed diagnostics retain public app output. Each pair has grouped `.diff.json` and the full differing facts in `.changes.jsonl.gz`. `samples/APP/PAIR.jsonl` provides up to three changed facts per kind and direction, also retained in the map.

Absolute host paths are normalized to relative public paths in metadata and logical source keys; source names, syntax positions, counts, flags, identities and measured outcomes are preserved. Compressed files use deterministic gzip. [recompute.py](recompute.py) checks the difference streams against grouped counts, samples, shared totals, both maps, repeat controls, suite failures, emission controls and the receipt file manifest. [files.json](files.json) hashes every retained file except itself. It does not reconstruct omitted dumps from samples; use the pinned rerun script for new dumps.

These facts make the observed membership and routing inspectable. They support auditing uncovered interfaces and either declaring the whole structure before typing or discovering it monotonically; local join laws and settled values alone leave those premises open.
