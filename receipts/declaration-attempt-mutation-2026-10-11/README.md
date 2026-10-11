# Separating declarations, attempted writers and mutations

**Verdict: Killed for this fixture envelope.** October 11, 2026. Unscored public reference.

On October 11 condition `declaration-attempt-mutation-20261011-v2`, the declaration shadow at recorded `7972f4c` over structure base `abda389c` is **killed for its fixture envelope**: 18 covered memberships are absent, at nine targets, and nine unaudited channel groups leave raw coverage incomplete. Declaration start/end and sets match across unset/1/2/unset-repeat. Separately, Campfire retains the same 740 attempted and 678 successful writer identity counts per schedule, but four controller mutation identities differ while declarations and attempt sets agree. All 16 paired value and diagnostic comparisons match the control. Shuffled answers still differ; this is a failed observational envelope, not proof that complete static declaration is impossible or that any-order inference is repaired.

## Pins and condition

Condition: `declaration-attempt-mutation-20261011-v2`. Labels are descriptive translations of the recorded experiment labels.

- Published base: [`abda389cbf30b7c0219d766134e0522b2ffe346f`](https://github.com/bunnykong/roundhouse/tree/abda389cbf30b7c0219d766134e0522b2ffe346f).
- Recorded experiment source: `7972f4cdfac1449ddf4b58cc47c6322391f1a6bd`.
- Proposed fork branch: [`declaration-attempt-mutation`](https://github.com/bunnykong/roundhouse/tree/declaration-attempt-mutation).
- Public source: [`7972f4cdfac1449ddf4b58cc47c6322391f1a6bd`](https://github.com/bunnykong/roundhouse/tree/7972f4cdfac1449ddf4b58cc47c6322391f1a6bd).
- Frozen input lab: [`76cdb1ea`](https://github.com/bunnykong/roundhouse-fixpoint-lab/tree/76cdb1ea24b0c4c88af4c42c78f567d759b7731d).

Campfire `90b330024dec3e757c79b6a7e6568f93da8e3148`; unchanged two-file `structure_fixture` from the structure pin. `raw/evidence/manifest.json.gz` indexes original hashes. Rust/Cargo 1.98.1, four build jobs, locked dependencies; app checks use CRuby 4.0.7 with Prism, library controls use CRuby 3.4.4, and recording used Python 3.9.6.

Snapshot: no; the measured history is retained. No new native Rust run is implied by publication. Recorded binary hashes name the measured artifacts. [Pins](pins.json), [summary](summary.json) and [file hashes and omissions](recorded-files.json) retain the evidence boundaries.

## Results

| Measure | Fixture | Campfire |
| --- | ---: | ---: |
| Declared slots | 1,065,641 | 48,693 |
| Potential writer facts | 2,596 | 50,496 |
| Attempted identities | 10 | 740 |
| Successful identities | 10 | 678 |
| Missing memberships | 18 | 38,443 |
| Missing targets | 9 | 12,461 |
| Unaudited groups | 9 | 9 |
| Final sweep exit | 1 | 1 |

## Commands

From the lab root, validate file hashes and recompute the bounded saved checks:

```sh
RECEIPT=receipts/declaration-attempt-mutation-2026-10-11
python3 -B "$RECEIPT/rerun.py" saved
```

For fresh native candidate checks, use an empty work directory and set `RESEARCH_LOCK` to the host lock shared by all other analysis jobs. Native mode clones the exact public pins, captures commands and expected failing exits, and creates new observations:

```sh
python3 -B "$RECEIPT/rerun.py" native \
  --work "$PWD/fresh-declaration-attempt-mutation" --lock "$RESEARCH_LOCK"
```

[Rerun script](rerun.py) and [portable runners](runners/) preserve the original checker/observer conventions. Native reproduction needs the proposed fork branches pushed first. Saved checks require neither a source clone nor a compiler build. They validate retained evidence; they do not turn a failing native gate into a pass.

## Caveats

Five closure-parameter, twelve parameter and one registry memberships miss the fixture envelope. All are mapped to a source; closure path mapping may itself need correction. Both inputs retain shuffled value differences and zero measured extra-round movement. Sixteen paired value comparisons and sixteen diagnostic comparisons match the control; two separate flags-off pairs also match. Equal declaration/attempt sets do not certify equal equations or complete reads. Four controller mutation differences reproduce the narrow successful-insertion interpretation of F31. Guarded-edge counts are factorized relation cardinalities, not materialized graph edges. The raw-access count remains unknown. Full declaration and cumulative structure streams are omitted for size; the excerpts keep every attempt/mutation, every fixture missing member, harvest events and 100 Campfire missing examples per schedule. Native reruns regenerate full streams. This observation changes no inference rule. The default suite and 105 emission pairs were not rerun; no performance or soundness claim is made.

Raw files use portable path placeholders and descriptive labels; original and public SHA-256 hashes are separate. Numeric measurements, diagnostic messages, type shapes and failed exits are preserved. Gzip/xz compression is lossless after those declared text translations. Existing frozen lab inputs and previous receipts are unchanged.
