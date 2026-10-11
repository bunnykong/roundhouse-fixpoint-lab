# Rejecting newly opaque exported components

**Verdict: Inconclusive for the complete control gate.** October 11, 2026. Unscored public reference.

On October 11 condition `component-opacity-gate-f29-20261011-v1`, a stronger checker rejects eight erased initializer Hash-value components, including gradual replacements, and permits harmless union reordering. Saved F29 decisions remain main 127/0 and S3 91/36 accepted/rejected, with 27/28 selected reads observed, zero missing types and zero unmapped observations. The specified Integer | String | nil widening adds no opaque component but still rejects two recorded Time values in setting I. Verdict: **inconclusive for the complete control gate**, with the bounded erasure guard confirmed. This uses saved traces and synthetic exports; it repairs no compiler inference and establishes no general soundness.

## Pins and condition

Condition: `component-opacity-gate-f29-20261011-v1`. Labels are descriptive translations of the recorded experiment labels.

- Published base: [`48c652873a88d8bc291df1d606ad1464f9168ae3`](https://github.com/bunnykong/roundhouse/tree/48c652873a88d8bc291df1d606ad1464f9168ae3).
- Recorded experiment source: `b06cb8658f75984c332c2a39cfe3240eb7e18997`.
- Proposed fork branch: [`component-opacity-gate`](https://github.com/bunnykong/roundhouse/tree/component-opacity-gate).
- Public source: [`8f7c1af7bcaa6e5376d465d5f5ffda03702522fd`](https://github.com/bunnykong/roundhouse/tree/8f7c1af7bcaa6e5376d465d5f5ffda03702522fd).
- Frozen input lab: [`76cdb1ea`](https://github.com/bunnykong/roundhouse-fixpoint-lab/tree/76cdb1ea24b0c4c88af4c42c78f567d759b7731d).

Discourse `343b20f97ef5f6bd70826ee0e993ba348b210fd5` and all original compiler/binary/trace hashes remain in `raw/evidence/provenance.json`; the F29 saved input receipt is unchanged. Rust/Cargo 1.98.1, four build jobs, locked dependencies; app checks use CRuby 4.0.7 with Prism, library controls use CRuby 3.4.4, and recording used Python 3.9.6.

Snapshot: yes; internal names and helper paths were translated mechanically. No new native Rust run is implied by publication. Recorded binary hashes name the measured artifacts. [Pins](pins.json), [summary](summary.json) and [file hashes and omissions](recorded-files.json) retain the evidence boundaries.

## Results

| Check | Before | After |
| --- | --- | --- |
| Value erasure, exits P/E/I | 0/0/0 | 1/1/1 |
| Concrete widening, exits P/E/I | 0/0/1 | 0/0/1 |
| Main accepted/rejected | 127/0 | 127/0 |
| S3 accepted/rejected | 91/36 | 91/36 |
| Observed/selected reads | 27/28 | 27/28 |
| New component tests | — | 13 pass |
| Existing contract tests | — | 8 pass |
| Complete confirm verifier | — | exit 1 |

## Commands

From the lab root, validate file hashes and recompute the bounded saved checks:

```sh
RECEIPT=receipts/component-opacity-gate-2026-10-11
python3 -B "$RECEIPT/rerun.py" saved
```

For fresh native candidate checks, use an empty work directory and set `RESEARCH_LOCK` to the host lock shared by all other analysis jobs. Native mode clones the exact public pins, captures commands and expected failing exits, and creates new observations:

```sh
python3 -B "$RECEIPT/rerun.py" native \
  --work "$PWD/fresh-component-opacity-gate" --lock "$RESEARCH_LOCK"
```

[Rerun script](rerun.py) and [portable runners](runners/) preserve the original checker/observer conventions. Native reproduction needs the proposed fork branches pushed first. Saved checks require neither a source clone nor a compiler build. They validate retained evidence; they do not turn a failing native gate into a pass.

## Caveats

The prescribed widening omits Time at two saved initializer observations; those membership failures already occur before the new guard. No kill criterion fires, but the positive control does not fully pass. Eight newly opaque value paths are rejected even though membership admits every erased observation. Canonical union paths cover the exported renderer; unsupported interiors, recursive graph fidelity and provenance conservation need separate checks. No fresh Ruby run or compiler repair was made. The unobserved interval-tick read stays in the denominator. Single calibration runs give no speed evidence.

Raw files use portable path placeholders and descriptive labels; original and public SHA-256 hashes are separate. Numeric measurements, diagnostic messages, type shapes and failed exits are preserved. Gzip/xz compression is lossless after those declared text translations. Existing frozen lab inputs and previous receipts are unchanged.
