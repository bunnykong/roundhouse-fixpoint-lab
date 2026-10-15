# Fixpoint spine

Unscored research reference. Integration is confirmed within the recorded tests; the partition law still fails.

## Fact F62

On October 15 condition `fixpoint-spine-20261015-ea3ec744`, one branch combines Pending identity, the storage normal form, strict producers (F56) and closure application with reflective repairs (F57). It passes 1,245 library tests; all earlier reproduction kits pass. Independent review upholds the result. Across unset/1/2/independent-repeat at each tested verification/audit setting, Campfire's complete reason rows agree with ownership on or off; all ten value digests agree with it on, nine with it off. The on profile also disables #521's stabilizer, so this does not isolate ownership. F60's reflective bound bypass is repaired. The partition law still fails. Forem, Chatwoot, Mastodon and Discourse retain F55's sets of schedule-equal value digests. These bounded results do not establish general schedule independence or soundness.

## Condition and pins

Public condition: `fixpoint-spine-20261015-ea3ec744`.
[Source README](https://github.com/bunnykong/roundhouse/blob/14ee6a88c63f36a2b4ed7f8dae31ecd4e4dd3d58/research/fixpoint-spine/README.md) lists all thirteen public flags and defaults.
[Pins](pins.json) identify the compiler, inputs, binary and toolchains; [source equivalence](source-equivalence.json)
binds spelling changes to the measured source. The public Rust snapshot was not compiled during packaging.

## Receipt label map

- `p2-v3-spine2-SK-Apply-ea3ec744-observers-v1` → `fixpoint-spine-20261015-ea3ec744`.
- `p2-v2-s1-phaseB-ec633faf-a5d73fdf-observers-v1` → `storage-repair-five-apps-20261015-ec633faf-a5d73fdf`.

Historical labels appear only in this map and unchanged raw evidence. `raw/` preserves original decompressed bytes.
`derived/` discloses public path, flag and label copies. The [manifest](manifest.json) records separate original,
public uncompressed and published-file hashes, report hashes and omissions. Original evidence is unchanged.

## Evidence and limits

The packet retains all 136 native cell records, 34 digest groups, complete Campfire reason rows, 272 reason deltas,
native test logs and kit command/exit records. Independent review reconstructed the grid, replayed the kits and
repeated three app cells. It checked the 1,245-test library log without rerunning that full suite.

The first library run failed 41 tests because its generated `real-blog` fixture was missing. After restoring the
baseline fixture, both reruns pass 1,245 tests with 26 ignored. All three runs and the 127-entry fixture manifest
remain. The original partition assertion exits 101; reproducing its failure does not make the law pass.

Campfire has eight ownership/observer groups. Other apps use all four verification/audit settings except Discourse,
which uses off/off only. Each group compares unset, 1, 2 and an independent unset repeat. Ownership on also disables
the stabilizer. No ownership soundness, general schedule independence, latency or performance result follows.
Unavailable fields remain null. Full app dumps, binaries, dependencies and repeated streams are omitted explicitly.

## Reproduce

From this receipt directory, verify retained hashes and recompute the bounded result:

```sh
python3 rerun.py saved
```

This starts zero native analyzers. Native checks are separate and were not run during publication:

```sh
SOURCE=$PWD/compiler OUTPUT=$PWD/native-output \
  HOST_LOCK_WRAPPER=$PWD/tools/observers/lock.py HOST_LOCK_FILE=$PWD/host-locks/heavy.lock \
  bash native.sh
```

Use the exact compiler pin. Generate `fixtures/real-blog` with its documented `bin/rh fixture` command first;
the retained manifest identifies the original input. Run heavy work under the shared host lock.
`native.sh` checks the library and negative partition law, not the full app matrix or earlier fixture kits.
Earlier kits and their native recipes remain in the [producer receipt](../strict-producer-reasons-2026-10-15/README.md),
[closure receipt](../closure-application-effects-2026-10-15/README.md) and
[writer receipt](../writer-partition-replay-2026-10-15/README.md). Historical ablations need explicit zero flags
because this branch enables the repairs by default.

For fresh app cells, use the [public observer](../../tools/observers/README.md), the pinned public app checkout,
and `research-on.json` or `research-off.json`. For example, from the lab root:

```sh
python3 tools/observers/obs.py run --bin ./compiler/target/release/roundhouse --app campfire \
  --input ./corpus/apps/campfire --matrix full --flags receipts/fixpoint-spine-2026-10-15/research-on.json \
  --label fixpoint-spine-on --jobs 1
```

Use only `unset-v0-a0,1-v0-a0,2-v0-a0,repeat-v0-a0` for Discourse's recorded comparison.
