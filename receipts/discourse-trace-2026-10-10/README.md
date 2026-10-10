# Discourse runtime trace, October 10, 2026

Three of Discourse's own passing tests witness 27 of the fixed 28 `@data` reads in
`Jobs::Base::JobInstrumenter`. Condition: `sound-traces-20261010-c210f226`, CRuby 4.0.7.
The first logging test records 24 values: main accepts 24 and rejects 0; S3 accepts 17 and rejects 7.
No observation lacks a slot, and no selected static type is missing. Every acceptance involves an
uncertain or unsupported component. These are witnessed membership results on the declared coverage,
not soundness in general. [Recorded limits](LIMITS.md) retain the original wording.

The P, E and I rows below are separate runtime settings. Their union contains 127 observations of
27 distinct reads; the repeated primary test is a separate repeat and is excluded from the union.
Counts in the main and S3 columns are accepted / rejected observations.

| Runtime setting | Observations / reads | Main | S3 |
| --- | --- | --- | --- |
| P: own logging test | 24 / 24 of 28 | 24 / 0 | 17 / 7 |
| E: error caller | 75 / 25 of 28 | 75 / 0 | 54 / 21 |
| I: interval caller | 28 / 25 of 28 | 28 / 0 | 20 / 8 |
| P/E/I union | 127 / 27 of 28 | 127 / 0 | 91 / 36 |

## Exact identities

The unchanged static app is the Discourse entry in [the lab corpus](../../corpus/apps.json).
[pins.json](pins.json) records all pins, flags, binary hashes and loop endings.

- Discourse: [`343b20f97ef5f6bd70826ee0e993ba348b210fd5`](https://github.com/discourse/discourse/tree/343b20f97ef5f6bd70826ee0e993ba348b210fd5),
  corpus tag `v2026.9.0`, Git tree `489a5c0b678235dd773e6274bf97f6e8879fee8d`.
- Lab at measurement: `56255dd54bed3815b4774282ae92380524b13136`.
- Main: [`c210f226346b462214866b5756b457ad53f647b1`](https://github.com/bunnykong/roundhouse/tree/c210f226346b462214866b5756b457ad53f647b1).
  Recorded `main-sound-types` SHA256:
  `6c4bc7111c188fe68d31c92d73e0a474394d34e7d8018ccfef5b4d361f547ccb`.
- S3: [`38403140379cd69759b0fe6247c6a8c4a48a37a9`](https://github.com/bunnykong/roundhouse/tree/38403140379cd69759b0fe6247c6a8c4a48a37a9).
  Recorded unmodified `s3-sound-types` SHA256:
  `d677f637b0d273db5eadc62a8e8fb943438b030a16e4170024360c76b4147934`.
- Historical local adapter identity: `6b55749cf12a9299636b5f53957f0a2bb2ec1544`;
  it is not a public commit pin. Public equivalent:
  [`48c652873a88d8bc291df1d606ad1464f9168ae3`](https://github.com/bunnykong/roundhouse/tree/48c652873a88d8bc291df1d606ad1464f9168ae3/tools/sound-exporter)
  on [`sound-exporter`](https://github.com/bunnykong/roundhouse/tree/sound-exporter/tools/sound-exporter).
  The adapter trees differ: `docker_session.py` uses a configurable lock path, permits lock-file creation,
  and shortens container prefixes; the public tree also adds `README.md` and `provenance.json`.
  The other 15 recorded files are byte-identical. Membership, selection, recorder, exporter and final
  observation overlays are unchanged; [adapter-files.json](adapter-files.json) pins all 18 public files.
  Recorded builds used Rust 1.98.1 and four Cargo jobs.

Selected `app/jobs/base.rb` SHA256:
`8085676c5a125751d2b99b23794712cad6435674a3363fdb942a15d1d82d93f6`.
Fixed selection SHA256:
`cb8c6f7fbdae23b2fa1f1570db4f68516f1b0756e5ca80e2884c93e7e458ebf9`.
The unchanged static source and separately instrumented runtime source have separate hashes in each trace.

## Tests and recorded values

All three tests ran with seed `20261010`; each passed one example with zero failures.
The read wrapper evaluates `@data` once, snapshots it immediately before the surrounding operation,
and returns the same object. Test bodies and assertions were not edited.

- P: [`spec/jobs/jobs_base_spec.rb:169`](https://github.com/discourse/discourse/blob/343b20f97ef5f6bd70826ee0e993ba348b210fd5/spec/jobs/jobs_base_spec.rb#L169),
  "writes the job to the Sidekiq log". Its own setup enables logging and calls
  `GoodJob.new.perform({ some_param: "some_value" })`.
- E: [`spec/jobs/jobs_base_spec.rb:80`](https://github.com/discourse/discourse/blob/343b20f97ef5f6bd70826ee0e993ba348b210fd5/spec/jobs/jobs_base_spec.rb#L80),
  "handles errors in multisite", with `DISCOURSE_LOG_SIDEKIQ=1`. It exercises three BadJob executions
  and the exception branch.
- I: [`spec/jobs/jobs_base_spec.rb:74`](https://github.com/discourse/discourse/blob/343b20f97ef5f6bd70826ee0e993ba348b210fd5/spec/jobs/jobs_base_spec.rb#L74),
  "handles correct jobs", with `DISCOURSE_LOG_SIDEKIQ=1` and `DISCOURSE_LOG_SIDEKIQ_INTERVAL=60`.
  It calls `GoodJob.perform({})` and observes the starting-log branch.

Raw tagged snapshots are in [P](traces/P.jsonl), [E](traces/E.jsonl), [I](traces/I.jsonl) and the
[primary repeat](traces/P-repeat.jsonl). A host-identifying String payload is replaced with
`trace-host.example` in the public copy. Value tags, object IDs, slots and every other runtime payload
remain intact. [recorded-files.json](recorded-files.json) retains original and public hashes and records
every normalization. Paths in operational metadata are relative; container labels omit agent names.
Replaying the public copy reproduces every original acceptance/rejection decision.

[selection.json](selection.json) retains all 28 source-span selections, and [slots.json](slots.json)
maps every stable runtime slot to its static alias. [COVERAGE.md](COVERAGE.md) shows the per-read
main/S3 counts. [per-slot-decisions.json](per-slot-decisions.json) joins both arms' accept/reject decisions
with trace-line references for every observation, including an empty entry for the unobserved read.
The complete comparisons are in [P main](comparisons/P-main.json), [P S3](comparisons/P-s3.json),
[E main](comparisons/E-main.json), [E S3](comparisons/E-s3.json), [I main](comparisons/I-main.json)
and [I S3](comparisons/I-s3.json). [summary.json](summary.json) is their recomputed reduction.

For P, S3 rejects seven Hash snapshots. At initializer reads 55–57, `hostname` is a String while
the selected Hash value type admits Integer alone. At reads 58, 59, 66 and 75, direct `perform`
leaves `job_id` nil while the static type admits Integer or String. E repeats these seven witnesses
for each invocation; I adds the initializer line-62 nil witness. The remaining unobserved read is
`write_to_log` at 145:9, byte span 4187–4192, the conditional pending-duration assignment.

## Static exports and uncertainty

Both arms use `SOUND_MISSING=1 RH_FOLD_PRINT=1 RH_FIXPOINT_STATS=1`; S3 also uses:

```text
RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1 RH_BRK_ALLARMS=1 RH_SCHED=sccq
```

Inherited analyzer flags are cleared. [Main](exports/main/receipt.json) and [S3](exports/s3/receipt.json)
receipts identify the exact command, binary, input tree, selection and flags. Their directories retain
the full serde/Debug export (`stdout.json`), raw types (`raw.json`), final grammar, category paths and
loop telemetry. Main has Var, untagged unknowns and unsupported rendering in all 28 selections.
S3 has Var in 28, gradual unknowns in 18 and unsupported rendering in 18. These categories overlap.
Both have zero missing, Bottom, pending and unresolved-tagged selected reads in this app export.
The paired comparison introduces no new opaque selected alias/category.

Original main and S3 graph grammars repeat their final grammars and are explicitly `final-only` in
[pins.json](pins.json). The separately retained [earlier observer](exports/s3-instrumented/receipt.json)
has 28 actual pre-expansion roots, zero reachable fold nodes, and identical selected final exports.
Its exact [overlay](evidence/earlier-graph-observer.patch), graph JSON and categories are retained.
Its counts match the unmodified S3 counts; this is selected-slot parity only. The final JSON-only
observer's app repeat was not run. Main hits production and absorb caps; S3 reports loop endings
5/1/2. No fresh app extra-round verification or complete-state acceptance is claimed.

Historical control condition `settle-sound-published-v1` remains separate: adapter builds at main
`1ce9969564303ebe1bf5b8ca3304f982272079c1` and corrected S3
`96cdea9a1e6e6bb32a267a247d72f99b98a50b70` reproduce 6 and 0 rejections of 12 values.
[The recorded match](evidence/f17-live-adapter-match.json) and the unchanged
[F17 receipt](../F17/README.md) retain the limits of that historical check. Those counts are not
the current S3 result.

## Commands

From the lab root, replay all recorded values against the saved grammars and check every decision:

```sh
python3 -B receipts/discourse-trace-2026-10-10/rerun.py replay
```

The script fetches the exact public adapter snapshot and checks its file hashes. To use an existing
checkout, pass `--adapter /path/to/roundhouse/tools/sound-exporter`. To retain results, pass
`--output /path/to/new-output-directory`. Replay also checks the primary repeat and recomputes F17.
It performs no analyzer build or Docker run.

For new runtime observations, select CRuby 4.0.7 and have Rust 1.98.1, Git, Docker, Bundler's native
dependencies and the app's system libraries available. Use a new measurement directory:

```sh
SOUND_DOCKER_LOCK=/tmp/roundhouse-docker.lock \
  python3 -B receipts/discourse-trace-2026-10-10/rerun.py live --output /path/to/new-measurement
```

Use the host's shared Docker lock if it already has one; serialize analyzer work under that host's
analysis lock as well. The script prepares independent pinned main/S3 and static/runtime app clones,
generates the same selection with Prism, installs the locked gems, builds both exporters and runs
P, E and I sequentially. Each test owns its disposable databases through cleanup. Outputs retain
their own binary, input, command, environment, value and comparison receipts. New raw values and
timings are separate observations.

The runtime Gemfile copy changes Ruby `~> 3.4` to `~> 4.0`, and the lockfile records `4.0.7p0` in
place of `3.4.7p58`. Four optional migration-gem paths point to the unchanged pinned app clone;
all dependency versions stay locked. The [Gemfile](runtime/Gemfile.patch) and
[lockfile](runtime/Gemfile.lock.patch) diffs and [recorded hashes](evidence/runtime-dependencies.json)
make this boot condition explicit. The installation used 281 locked gems, excluding development,
with Bundler selecting 4.0.11 from the lockfile. No frontend dependencies were installed.
The Docker driver pins the recorded pgvector and Valkey image digests in its source.

For a prepared measurement directory, the individual test commands are:

```sh
python3 -B adapter/docker_session.py --work "$MEASUREMENT" --output session/repeat-P
python3 -B adapter/docker_session.py --work "$MEASUREMENT" --output session/repeat-E \
  --force-logging spec/jobs/jobs_base_spec.rb:80
python3 -B adapter/docker_session.py --work "$MEASUREMENT" --output session/repeat-I \
  --force-logging --interval spec/jobs/jobs_base_spec.rb:74
```

Export once per fixed input/selection, using separate main/S3 output directories:

```sh
python3 -B adapter/export.py --binary bin/main-sound-types --role main --source main \
  --app lab/corpus/apps/discourse --selection session/discourse/selection.json \
  --lab lab --output session/exports-repeat-main
python3 -B adapter/export.py --binary bin/s3-sound-types --role s3 --source s3 \
  --app lab/corpus/apps/discourse --selection session/discourse/selection.json \
  --lab lab --output session/exports-repeat-s3
python3 -B adapter/compare.py --lab lab --trace session/repeat-P/trace.jsonl \
  --export session/exports-repeat-main --slots session/discourse/slots.json \
  --output session/repeat-P/main.json --require-membership
python3 -B adapter/compare.py --lab lab --trace session/repeat-P/trace.jsonl \
  --export session/exports-repeat-s3 --slots session/discourse/slots.json \
  --baseline-export session/exports-repeat-main --output session/repeat-P/s3.json --require-membership
```

The last command is expected to exit 1 for S3's valid counterexamples. Exit 0 passes only the declared
membership gate; exit 2 means invalid or incomplete input. Omit `--require-membership` for reporting
only. Add `--verify` to a separate S3 export for a new extra-round control, preserving the ordinary
export, and inspect every telemetry `verify[].moved` field. Acceptance alone does not verify settlement.

The publication replay and adapter/oracle boundary tests were rerun while packaging. No new app
runtime session, analyzer build, full analyzer suite or emission gate was run for this publication.
