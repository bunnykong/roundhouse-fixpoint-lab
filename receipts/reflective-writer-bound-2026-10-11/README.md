# Reflective ivar writes reach the complete-body bound

**Verdict: Confirmed for the narrow reflective writer repair.** October 11, 2026. Unscored public reference.

On October 11 condition `reflective-writer-bound-20261011-bf2f052f`, the main-based reflective-ivar repair is **confirmed for its narrow bound entrance**. The 50-case reflective storage check changes from fail to pass; the plain complete-batch check remains passing. All 300 eligible entrances retain native plain/reflective storage equality, with 19,392 finite membership checks and zero extra opaque paths relative to the same plain bound. Existing pairwise-cut failures remain. Across 32,928 partition/order/round schedules, 2,104 outcomes differ from a complete batch and 548 second-round outcomes differ from the first; 418,656 finite membership checks still pass. This closes one reflective writer boundary, without making the widening algebra lawful, porting it to S3, or establishing app runtime soundness.

## Pins and condition

Condition: `reflective-writer-bound-20261011-bf2f052f`. Labels are descriptive translations of the recorded experiment labels.

- Published base: [`bf2f052ff34a240dab0cb05b1185c0e3ad571888`](https://github.com/bunnykong/roundhouse/tree/bf2f052ff34a240dab0cb05b1185c0e3ad571888).
- Recorded experiment source: `7a7004c27a6fa4ddb0806ca9663b6d19c5a8015f`.
- Proposed fork branch: [`reflective-writer-bound`](https://github.com/bunnykong/roundhouse/tree/reflective-writer-bound).
- Public source: [`c91d4324aec001d25684cba98656f73911023b86`](https://github.com/bunnykong/roundhouse/tree/c91d4324aec001d25684cba98656f73911023b86).
- Frozen input lab: [`76cdb1ea`](https://github.com/bunnykong/roundhouse-fixpoint-lab/tree/76cdb1ea24b0c4c88af4c42c78f567d759b7731d).

The public `bf2f052f` main-based writer-law harness and its 50 closed boundary samples; no application timing. Full recorded compiler/input/runner and binary hashes are retained. Rust/Cargo 1.98.1, four build jobs, locked dependencies; app checks use CRuby 4.0.7 with Prism, library controls use CRuby 3.4.4, and recording used Python 3.9.6.

Snapshot: yes; internal names and helper paths were translated mechanically. No new native Rust run is implied by publication. Recorded binary hashes name the measured artifacts. [Pins](pins.json), [summary](summary.json) and [file hashes and omissions](recorded-files.json) retain the evidence boundaries.

## Results

| Check | Control | Candidate |
| --- | --- | --- |
| Reflective storage, 50 cases | fail | pass |
| Plain batch, 4,116 comparisons | pass | pass |
| Eligible entrances | — | 300 pass |
| Finite membership checks | — | 19,392 pass |
| Extra opacity vs plain bound | — | 0 |
| Existing pairwise-cut laws | fail | fail |
| Partition schedules | — | 32,928 |
| Different from complete batch | — | 2,104 |
| Different second-round results | — | 548 |

## Commands

From the lab root, validate file hashes and recompute the bounded saved checks:

```sh
RECEIPT=receipts/reflective-writer-bound-2026-10-11
python3 -B "$RECEIPT/rerun.py" saved
```

For fresh native candidate checks, use an empty work directory and set `RESEARCH_LOCK` to the host lock shared by all other analysis jobs. Native mode clones the exact public pins, captures commands and expected failing exits, and creates new observations:

```sh
python3 -B "$RECEIPT/rerun.py" native \
  --work "$PWD/fresh-reflective-writer-bound" --lock "$RESEARCH_LOCK"
```

[Rerun script](rerun.py) and [portable runners](runners/) preserve the original checker/observer conventions. Native reproduction needs the proposed fork branches pushed first. Saved checks require neither a source clone nor a compiler build. They validate retained evidence; they do not turn a failing native gate into a pass.

## Caveats

Successful reflective writes now return their destination to the complete-body touched set. Eligibility, name folding, joins, limits, model projection and history cuts keep their original policies. The narrow storage gate passes; partition/regrouping/replay algebra still fails at exit 101. The minimum new witness has 513 nodes; one answer is Untyped and another Untyped | Array[Integer], both admitting every sampled value. The partition matrix performs 418,656 finite membership checks with no sampled omission. Four opaque paths already come from the plain bound; this repair reproduces those cuts on reflection, without a precision gain. Six old reflection integration tests pass. Library control/candidate share 43 failures and 42 ignores; no new failure appears in the fresh-clone condition. This unflagged main-harness patch is not a next/S3 port. No application census, fresh runtime trace, full emission campaign or universal soundness/termination/leastness result was produced. Unsupported concrete shapes and generic interiors are outside the finite membership certificate. Raw test markers are mechanically translated in the public snapshot and receipts.

Raw files use portable path placeholders and descriptive labels; original and public SHA-256 hashes are separate. Numeric measurements, diagnostic messages, type shapes and failed exits are preserved. Gzip/xz compression is lossless after those declared text translations. Existing frozen lab inputs and previous receipts are unchanged.
