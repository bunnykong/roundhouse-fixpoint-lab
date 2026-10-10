# Warm replay port and phase profiles — October 10, 2026

The warm replay port onto refreshed `fixpoint-next` matches both the mandatory cold shadow and a separate cold check on all six frozen F15 edits. Fingerprint construction dominates the recorded warm time. The flags-off shared suite matches next, including its three inherited failures.

**These are profiles on a shared host, not benchmarks.** Condition: **warm-next-F15-profile-20261010-c210f226**. There is one cold-first timed pair per edit, preceded by a correctness replay. These observations include profiling overhead and shared-host load; they establish neither a latency distribution nor the five-pair cost or 100 ms gates. Packaging recomputes saved outputs; it performs no new native analysis or Cargo run.

## Pins and condition

- Port: [`warm-next`](https://github.com/bunnykong/roundhouse/tree/warm-next), exact merge [`d9ec78c3`](https://github.com/bunnykong/roundhouse/tree/d9ec78c31db361db8818b13153e5ddddee484c57).
- First parent: refreshed next [`38403140`](https://github.com/bunnykong/roundhouse/tree/38403140379cd69759b0fe6247c6a8c4a48a37a9).
- Second parent: warm v2 [`990137f7`](https://github.com/bunnykong/roundhouse/tree/990137f742397a0aecc7efd14869f39c6412ba55).
- Main included in next: [`c210f226`](https://github.com/bunnykong/roundhouse/tree/c210f226346b462214866b5756b457ad53f647b1).
- Exact source tree: `8dab26db49ac9d9e723721139bae515899f47c10`.
- Recorded release binary SHA-256: `f8491bd0094efe849422cda9988bca6d13a4f0ee90526d5562b9e86beedd4c1c`.
- Host: arm64 macOS 26.3.1; Rust 1.98.1, four Cargo build jobs; app commands use CRuby 4.0.7 with Prism. Native hash order has no seed hook.

Both arms use the same release binary and `check --continue .` from scratch app copies. The unedited seed is outside each edit pair, carries this binary’s compiler stamp, and is restored before every correctness or timed replay. Heavy runs and builds were serialized under the host’s shared analysis lock; waiting for that lock is outside the measured command walls. [pins.json](pins.json) and [build metadata](evidence/build.json) retain exact identities.

Mastodon is pinned at `163f96cee4dea23365bff9b433871e68d20d9ee7`, with tree SHA-256 `56bbdec49cd7824261cb6b897004b59c45049652ec4f292b2fed08fc4a2f59c7`. Discourse is pinned at `343b20f97ef5f6bd70826ee0e993ba348b210fd5`, with tree SHA-256 `a567febb961d9a95967c0168a0dfc6a202562a64afd292632670369999ab7e07`. The supplied Mastodon snapshot has no Git metadata: its commit comes from F15 and its bytes match the frozen tree inventory. Discourse’s HEAD and tree inventory both match. [Input provenance](profiles/app-inputs.json) retains the distinction. The initial snapshot preflight failed before seeding because it read the containing repository’s HEAD; `logs/profiles-input-check.log.gz` retains that failed check.

## Frozen edits

[edits.json](edits.json) preserves all six F15 body offsets, replacements, source-file hashes and edited-tree hashes. Its cases match [the historical F15 manifest](../F15/edits.json) exactly; the historical condition ID is retained separately from this new profile condition.

- Mastodon boolean: `app/models/account.rb`, `sign?`, `true` → `false`.
- Mastodon return type: `app/models/domain_block.rb`, `to_log_human_identifier`, `domain` → `domain.length`.
- Mastodon withdraw read: `app/services/clear_domain_media_service.rb`, `blocked_domain`, `domain_block.domain` → `nil`.
- Discourse boolean: `app/models/bookmark.rb`, `auto_delete_when_reminder_sent?`, negate its existing preference comparison.
- Discourse return type: `app/models/category.rb`, `slug_url_without_id`, the interpolated URL String → `0`.
- Discourse withdraw read: `app/services/username_checker_service.rb`, `is_developer?`, the developer-email configuration read → `nil`.

## Commands

Both arms set the F15 S3 flags and the digest observer. Warm additionally sets `RH_WARM=DIR RH_WARM_SHADOW=1 RH_WARM_TIMINGS=1`. Both set `ROUNDHOUSE_TIMINGS=1`. Each run’s exact command, flags, timestamps, binary hash, exit and whole wall time remain in [runs.json](profiles/runs.json). A check that reports app type errors may return 1; a shadow mismatch returns 3 and fails parity.

```sh
export RBENV_VERSION=4.0.7 ROUNDHOUSE_TIMINGS=1
export RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1
export RH_BRK_ALLARMS=1 RH_SCHED=sccq RH_FIXPOINT_DIGEST=1
# Cold, from the edited scratch app; warm variables unset.
roundhouse check --continue .
# Warm, after restoring the original unedited seed into CACHE.
RH_WARM="$CACHE" RH_WARM_SHADOW=1 RH_WARM_TIMINGS=1 \
  roundhouse check --continue .
```

From this lab’s root, recompute the saved packet without a compiler, or rerun with Git, Python 3.9+, CRuby 4.0.7 with Prism, Rust 1.98.1 and its native build dependencies:

```sh
python3 -B receipts/warm-profile-2026-10-10/recompute.py
sh corpus/fetch.sh
python3 -B receipts/warm-profile-2026-10-10/rerun.py
```

[rerun.py](rerun.py) clones the public fork, detaches the exact port commit, verifies its tree and builds with `cargo +1.98.1 build --release --locked --bin roundhouse` and four jobs. `--binary FILE` accepts a prebuilt binary stamped with that commit; `--source DIR` accepts a clean existing checkout. `--apps DIR` selects pre-fetched pinned app snapshots. `--app mastodon --edit boolean` narrows the run; `--work-dir DIR` must be new. A rerun gets a new condition and records its own binary hash; it cannot overwrite this packet. `--lock FILE` selects a shared advisory analysis lock, defaulting to `_work/analysis.lock`. Use the same lock as other large runs on the host. Several GiB of trace storage and over 50 GiB of peak memory may be needed for Discourse. No Rails boot, database or app tests are involved.

## Port and parity

The merge retains refreshed constant resolution, receiver-side parameter keys, the class-key guard regression and chronological replay. `Ctx.instance_body` joins the input fingerprint. Cache schema version 2, invalidation, equality guards, writes and worklist policy are unchanged. The cold comparator now includes scheduler read metadata and saved typing contexts; these observations create no new scheduling edges. [Comparator inventory](evidence/comparator-inventory.json) and [merge resolutions](evidence/merge-resolutions.json) record the details.

| App / edit | Shadow + cold | Loaded / replayed | Fresh unit evals |
| --- | --- | --- | --- |
| mastodon / boolean | match | 60,698 / 59,629 | 1,069 |
| mastodon / return-type | match | 60,698 / 59,623 | 1,075 |
| mastodon / withdraw-read | match | 60,698 / 22,597 | 38,104 |
| discourse / boolean | match | 136,952 / 135,063 | 1,889 |
| discourse / return-type | match | 136,952 / 133,247 | 3,700 |
| discourse / withdraw-read | match | 136,952 / 133,207 | 3,744 |

All seeds, correctness replays and measured replays pass their shadow. For each edit the two warm/shadow digests match the separate cold digest, state-entry counts match, and error/warning/note dictionaries, diagnostic-content multisets and command summaries agree. The new scheduler/context fingerprints are nonempty. This is observed parity for these apps and edits; the Rust analyzer’s monotonicity, complete-read and saturation premises remain unproved. [Saved reductions](profiles/results.json) retain the measured pairs.

Flags-off suite condition: next `38403140`, including main `c210f226`, the same generated fixture trees, Ruby 3.4.4, default SDK selection, one test thread, and experimental variables unset. The command is `cargo test --locked --no-fail-fast`. Suite timings are not compared.

| Flags-off suite | Passed | Failed | Ignored |
| --- | --- | --- | --- |
| fixpoint-next | 4,970 | 3 | 236 |
| warm-next | 4,984 | 3 | 236 |

All 5,209 shared outcomes match; the 14 added passes cover the imported warm regressions and profiling-on/off parity. The three inherited failures remain:

- `emit::rust::library::value_union_emit_tests::action_controller_runtime_emit_typechecks_hotspots`
- `runtime_src::tests::rbs_ivar_decls_stamp_empty_array_initializers`
- `spinel_renders_the_same_page`

[Suite comparison](evidence/suite-comparison.json), `logs/suite.log.gz` and `logs/next-suite.log.gz` preserve every outcome. The focused warm tests pass 14/14. [Emission comparison](evidence/emission.json) records byte parity on 105 fixture/target pairs and 11,432 files, with [file hashes](evidence/emission-manifest.json). Default ignores and unavailable SDK coverage are inherited from the baseline. The receipt reduction checks suite logs and the recorded emission comparison; it does not regenerate emitted files.

## Per-phase profiles

Component rows below are exclusive wall-time buckets: nested fingerprint/recording work is subtracted from its parent. Load includes reading and decoding JSON. Guards include candidate matching/cloning and readiness checks; their hashes appear in fingerprinting. Replay includes restoring bodies/writes/actual reads and copying the body. Fresh typing covers all outer body-typer calls, excluding nested fingerprinting/recording. Other covers warm setup, registration, global driver passes and reporting. Shadow includes warm/cold state fingerprints, cold analysis and comparison; its preparation clone is separate and remains in F15’s warm numerator. Save includes JSON publication and fsync. Cleanup covers deallocation. Startup/ingest includes CLI setup. The residual row covers remaining reporting, diagnosis and cleanup outside the segmented warm window. The cold-in-shadow row is a subset of shadow, and command/analysis totals are reference rows. Cold analysis comes from the existing two-decimal timing output; other displayed seconds have three decimals.

### Mastodon — warm-next-F15-profile-20261010-c210f226

| Phase / seconds | Boolean | Return type | Withdraw read |
| --- | --- | --- | --- |
| Startup / ingest | 0.765 | 0.715 | 0.726 |
| Load stored state | 1.035 | 0.990 | 1.006 |
| Fingerprints | 133.389 | 135.131 | 131.112 |
| Check guards | 1.663 | 1.691 | 0.428 |
| Replay | 3.352 | 3.300 | 0.847 |
| Type fresh code | 0.179 | 0.181 | 1.505 |
| Record evaluations | 0.035 | 0.035 | 0.915 |
| Driver / setup / other | 7.119 | 7.085 | 6.842 |
| Prepare shadow clone | 0.044 | 0.045 | 0.045 |
| Discard old trace | 0.548 | 0.544 | 0.616 |
| Publish cache | 0.823 | 0.774 | 0.861 |
| Discard published trace | 0.602 | 0.530 | 0.591 |
| Report / diagnose / tail | 0.286 | 0.271 | 0.274 |
| Mandatory shadow | 6.549 | 6.734 | 6.955 |
| Cold analysis in shadow | 6.143 | 6.317 | 6.530 |
| Separate cold analysis | 6.250 | 6.140 | 6.210 |
| Separate cold command | 7.632 | 7.523 | 7.319 |
| Segmented warm window | 147.364 | 149.002 | 143.315 |
| Warm analysis | 145.572 | 147.265 | 141.482 |
| Warm excluding shadow | 149.838 | 151.292 | 145.766 |
| Whole warm command | 156.644 | 158.259 | 152.958 |

| Fingerprint detail / s | Boolean | Return type | Withdraw read |
| --- | --- | --- | --- |
| Value hashes | 7.848 | 7.754 | 7.987 |
| Class guards | 3.339 | 3.296 | 3.258 |
| Expr / context inputs | 118.913 | 120.971 | 116.559 |
| Body / other inputs | 3.289 | 3.110 | 3.308 |

| Work / storage / RSS | Boolean | Return type | Withdraw read |
| --- | --- | --- | --- |
| Input fingerprint calls | 60,698 | 60,698 | 60,701 |
| Class fingerprint calls | 627,046 | 628,586 | 625,094 |
| Input checks / replay | 1.018 | 1.018 | 2.686 |
| Seed JSON MiB | 440.9 | 440.9 | 440.9 |
| Published JSON MiB | 440.9 | 440.9 | 440.9 |
| Whole warm peak MiB | 11236 | 11214 | 11219 |
| Cold peak MiB | 710 | 712 | 700 |

### Discourse — warm-next-F15-profile-20261010-c210f226

| Phase / seconds | Boolean | Return type | Withdraw read |
| --- | --- | --- | --- |
| Startup / ingest | 2.486 | 2.737 | 2.514 |
| Load stored state | 4.487 | 4.523 | 4.571 |
| Fingerprints | 347.493 | 355.677 | 357.213 |
| Check guards | 6.391 | 7.013 | 6.867 |
| Replay | 15.566 | 16.016 | 15.907 |
| Type fresh code | 0.441 | 0.620 | 0.640 |
| Record evaluations | 0.187 | 0.300 | 0.341 |
| Driver / setup / other | 33.969 | 34.157 | 34.486 |
| Prepare shadow clone | 0.094 | 0.099 | 0.097 |
| Discard old trace | 2.526 | 2.673 | 2.494 |
| Publish cache | 3.453 | 4.298 | 3.345 |
| Discard published trace | 2.444 | 2.790 | 2.534 |
| Report / diagnose / tail | 0.683 | 0.682 | 0.691 |
| Mandatory shadow | 30.025 | 30.327 | 30.317 |
| Cold analysis in shadow | 28.965 | 29.269 | 29.255 |
| Separate cold analysis | 29.180 | 28.480 | 28.350 |
| Separate cold command | 32.862 | 32.034 | 32.090 |
| Segmented warm window | 411.155 | 421.077 | 422.616 |
| Warm analysis | 403.732 | 413.449 | 415.097 |
| Warm excluding shadow | 420.220 | 431.584 | 431.700 |
| Whole warm command | 451.002 | 462.671 | 462.728 |

| Fingerprint detail / s | Boolean | Return type | Withdraw read |
| --- | --- | --- | --- |
| Value hashes | 52.711 | 52.521 | 52.830 |
| Class guards | 9.180 | 9.436 | 9.466 |
| Expr / context inputs | 262.098 | 268.518 | 270.771 |
| Body / other inputs | 23.504 | 25.201 | 24.146 |

| Work / storage / RSS | Boolean | Return type | Withdraw read |
| --- | --- | --- | --- |
| Input fingerprint calls | 136,952 | 136,947 | 136,951 |
| Class fingerprint calls | 990,000 | 991,473 | 991,489 |
| Input checks / replay | 1.014 | 1.028 | 1.028 |
| Seed JSON MiB | 1917.5 | 1917.5 | 1917.5 |
| Published JSON MiB | 1917.5 | 1917.4 | 1917.4 |
| Whole warm peak MiB | 53272 | 51713 | 53248 |
| Cold peak MiB | 1524 | 1541 | 1527 |

## Cost location and limits

On Mastodon, all fingerprint buckets total 131.112–135.131 s, against whole warm command walls of 152.958–158.259 s and separate cold analysis of 6.14–6.25 s. The narrower `input_fingerprints` bucket is 116.559–120.971 s; load, guards, replay and fresh typing together are 3.786–6.229 s. On Discourse, all fingerprints total 347.493–357.213 s, expression/context inputs alone take 262.098–270.771 s, whole warm commands take 451.002–462.728 s, and separate cold analysis takes 28.35–29.18 s.

Across this six-profile packet, the expression/context input bucket totals 1,157.831 s (66.9% of summed warm wall excluding shadow). All fingerprint buckets total 1,460.014 s, actual replay 54.988 s and fresh body typing 3.566 s. These descriptive sums identify cost location in the packet; they are not a pooled app benchmark. Warm wall excluding shadow is 12.79–20.11× the separate cold command across the single profile pairs.

The [input-fingerprint path](https://github.com/bunnykong/roundhouse/blob/d9ec78c31db361db8818b13153e5ddddee484c57/src/analyze/warm/fingerprint.rs#L152) serializes typed expressions and contexts, sorts class names, rebuilds recursive-method/alias metadata and hashes the assembled JSON for each recordable evaluation. The profile does not separate those individual operations. Class and value serialization remain separate fingerprint buckets. No serialization, guard, reuse or replay optimization is claimed.

Warm analysis excludes cache load/save and shadow. Warm wall excluding shadow includes ingest, cache load/publication, diagnostics, cleanup and preparation of the validation clone. Whole warm command wall includes the mandatory shadow. The cold-in-shadow row is a subset of the shadow row; analysis/window/command totals are references and must not be added to the exclusive component rows. The reported total fingerprint row is the sum of four exclusive fingerprint categories, further split in the following detail table.

## Raw packet and normalization

The 20 seed/correctness/cold/warm runs are retained in `profiles/runs/`: each has `run.json`, `stderr.log.gz` and `stdout.log.gz`. The logs are full, losslessly compressed outputs, not timing excerpts. All raw profiling records, digests and diagnostics remain. [recorded-files.json](recorded-files.json) gives original and public file hashes and identifies path normalization. Absolute workstation paths, including diagnostic prefixes, become portable placeholders; public source-relative locations and message bodies are preserved. [Public diagnostic hashes](public-diagnostic-hashes.json) record the resulting byte changes separately from the original content hashes. No runtime value redaction is involved.

[recompute.py](recompute.py) verifies the copied-file hashes, reparses all raw stderr, checks every saved report and diagnostic multiset, validates six shadow/cold matches, checks exclusive phase sums, and compares every shared suite outcome. [reduction.json](reduction.json) records its output.
