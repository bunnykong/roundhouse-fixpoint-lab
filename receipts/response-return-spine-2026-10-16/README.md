# Response return spine

Unscored research reference.

## Fact F69

On condition `response-return-spine-20261016-five-apps`, spine v3 adds F63's response-return repair, on by default, a test-side `data_factory_constants` fix and gated read-only value dumps to v2. F63's checks confirm. Across unset/1/2/independent-repeat, schedule-equal value tables remain unchanged with ownership on and off: Campfire 10/10 on and 9/10 off; Forem 6/10, Chatwoot 5/10 and Mastodon 5/10 at each V1A1, V1A0, V0A1 and V0A0; Discourse 3/10 at V0A0 only. V means verification; A means audit. Ownership on also bypasses stabilization. Independent review reproduces 60 digests in six fresh cells and preserves all 34 equality sets. No larger-app gain; the research profile still includes F68's unsound strict stubs.

## Pins and evidence

[Pins](pins.json) identify the [public compiler](https://github.com/bunnykong/roundhouse/tree/e6e974a63707363f725df032ceb8b3500539df84) and application snapshots.
The [manifest](manifest.json) binds original, public uncompressed and stored bytes. `raw/` preserves exact
decompressed bytes; `derived/` and `native/` contain declared public spelling, path or selection copies.
Original evidence is unchanged. Reports remain outside Git; their hashes bind the original result and upheld review.

## Receipt label map

- `p2-v3-spine3-response-returns-369d963d-observers-v1` → `response-return-spine-20261016-five-apps`.
- `p2-v3-spine3-s7-composition-369d963d-v1` → `response-return-spine-witnesses-20261016`.
- `p2-v3-spine3-on` / `p2-v3-spine3-off` → `response-return-spine-ownership-on` / `response-return-spine-ownership-off`.
- `rv-p2-v3-spine3-on` → `response-return-spine-ownership-review`.

Raw labels occur only in this map and unchanged evidence. Native wire keys retain their recorded meanings.

## Replay saved evidence

```sh
python3 -B rerun.py saved
```

This verifies every retained file hash and recomputes the bounded result. It starts no analyzer.
Full application streams, binaries and dependency trees are omitted; compact receipts retain their captured identities.

## Conditions and limits

V1A1 enables verification and audit; V1A0 enables verification only; V0A1 enables audit only;
V0A0 disables both. Campfire, Forem, Chatwoot and Mastodon have all four settings with ownership on and off.
Discourse has V0A0 with ownership on and off. Each uses unset, 1, 2 and an independent repeat.
Ownership on also enables the stabilization bypass; those two changes are not isolated.

The replay grounds all 272 native result/report pairs, recomputes all 34 table memberships, and checks
the six independent fresh cells against 60 cached digests. The full response verdict matches the independent
replay byte for byte before public spelling changes. Its primary and Discourse checks confirm; the ordering gate is unblocked.
The response comparison retains 69 required cells, with 46 control/repair/profile cells and the reference checks.
Emission retains 156 pairs: 128 identical and 28 permitted differences.

The original v3 library run passes 1,245 tests with 26 ignores; `data_factory_constants` passes 23.
The response-composition full suites are not green: off has 5,915 passes, 24 failures and 363 ignores;
on has 5,914 passes, 25 failures and 363 ignores. Both cover 6,302 entries across all 861 targets.
The added on failure is `analyze::if_branches_union_merge`, whose assertion expects the historical nil result.
All original failures remain in the packet. The public Rust spelling port was parsed, not compiled.

The branch advances the existing public v2 with the five-file native delta, retaining public names.
Its tree hash differs from the internal source tree. [Source equivalence](source-equivalence.json)
records both identities and the exact changed-file translations. F62 remains pinned to v2.

## Checker controls and focused native recipe

```sh
python3 -B -m unittest discover -s native -p 'test_*.py' -v
```

All 61 portable checker tests pass. The focused native recipe uses the pinned public compiler and
the [public lock helper](../../tools/observers/README.md):

```sh
SOURCE=$PWD/compiler OUTPUT=$PWD/native-output \
  HOST_LOCK_WRAPPER=$PWD/tools/observers/lock.py HOST_LOCK_FILE=$PWD/host-locks/heavy.lock \
  bash native.sh
```

Prepare compiler fixtures first. This recipe is syntax-checked and unexecuted during publication;
it does not repeat the application matrix or response-composition full suite. This profile still has F68's unsound strict stubs.
