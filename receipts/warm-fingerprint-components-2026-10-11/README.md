# Reusing byte-identical warm fingerprint components

**Verdict: Confirmed for the bounded Mastodon boolean edit.** October 11, 2026. Unscored public reference.

On October 11 Mastodon boolean-edit arms `warm-fingerprint-components-20261011-base-boolean` and `warm-fingerprint-components-20261011-a-fast`, candidate `1fbfee1` over warm base `d9ec78c3` is **confirmed for the bounded fingerprint optimization**. Fingerprint work falls 132.653 → 10.759 s (12.33×), and warm wall excluding shadow falls 148.097 → 23.901 s. The audited arm has 60,698 equal byte/hash and guard comparisons; shadow, separate cold and a same-path parent check agree. Fast separate cold takes 7.349 s, so warm≤cold and the 100 ms target remain unmet. Scope: one pair, shared host, a profile not a benchmark; one app/edit per arm, without five-pair or six-edit replication. Replay order, payload codec and mandatory validation retain their prior policies.

## Pins and condition

Condition: `warm-fingerprint-components-20261011-boolean`. Labels are descriptive translations of the recorded experiment labels.

- Published base: [`d9ec78c31db361db8818b13153e5ddddee484c57`](https://github.com/bunnykong/roundhouse/tree/d9ec78c31db361db8818b13153e5ddddee484c57).
- Recorded experiment source: `1fbfee1a8b1b518028176ca48aa2a912f3d31e23`.
- Proposed fork branch: [`warm-fingerprint-components`](https://github.com/bunnykong/roundhouse/tree/warm-fingerprint-components).
- Public source: [`1fbfee1a8b1b518028176ca48aa2a912f3d31e23`](https://github.com/bunnykong/roundhouse/tree/1fbfee1a8b1b518028176ca48aa2a912f3d31e23).
- Frozen input lab: [`76cdb1ea`](https://github.com/bunnykong/roundhouse-fixpoint-lab/tree/76cdb1ea24b0c4c88af4c42c78f567d759b7731d).

Mastodon `163f96cee4dea23365bff9b433871e68d20d9ee7`, frozen `sign?` true → false edit. Original/edited tree hashes, verification-off S3 flags and binaries are in raw metadata. Rust/Cargo 1.98.1, four build jobs, locked dependencies; app checks use CRuby 4.0.7 with Prism, library controls use CRuby 3.4.4, and recording used Python 3.9.6.

Snapshot: no; the measured history is retained. No new native Rust run is implied by publication. Recorded binary hashes name the measured artifacts. [Pins](pins.json), [summary](summary.json) and [file hashes and omissions](recorded-files.json) retain the evidence boundaries.

## Results

| Scope | Parent | Candidate |
| --- | ---: | ---: |
| Fingerprints / s | 132.653 | 10.759 |
| Warm analysis / s | 144.345 | 20.281 |
| Warm excluding shadow / s | 148.097 | 23.901 |
| Whole warm command / s | 155.503 | 30.492 |
| Mandatory shadow / s | 7.164 | 6.381 |
| Whole cold command / s | 7.240 | 7.349 |
| Warm RSS / MiB | 11,274 | 11,280 |

## Commands

From the lab root, validate file hashes and recompute the bounded saved checks:

```sh
RECEIPT=receipts/warm-fingerprint-components-2026-10-11
python3 -B "$RECEIPT/rerun.py" saved
```

For fresh native candidate checks, use an empty work directory and set `RESEARCH_LOCK` to the host lock shared by all other analysis jobs. Native mode clones the exact public pins, captures commands and expected failing exits, and creates new observations:

```sh
python3 -B "$RECEIPT/rerun.py" native \
  --work "$PWD/fresh-warm-fingerprint-components" --lock "$RESEARCH_LOCK"
```

[Rerun script](rerun.py) and [portable runners](runners/) preserve the original checker/observer conventions. Native reproduction needs the proposed fork branches pushed first. Saved checks require neither a source clone nor a compiler build. They validate retained evidence; they do not turn a failing native gate into a pass.

## Caveats

One pair, shared host, a profile not a benchmark. Each arm has one cold-first pair for one Mastodon boolean edit. Timed commands held the exclusive coordination lock, whose wait is excluded from the walls; unrelated host work can still interfere. The 12.33× fingerprint ratio compares parent with audit-off fast output. Audit overhead is separate: 60,698 input byte/hash and guard comparisons agree, with 59,629 accepts and 1,069 rejects. Shadow, separate cold and a fresh parent at the exact edited path agree. Absolute paths affect scheduler keys and cache bytes; smaller cache files are not a codec gain. Warm excluding shadow remains 3.25× the candidate cold command and far above 100 ms. Six fingerprint canaries and sixteen warm tests pass. Library controls match 1,139 shared outcomes, including 43 failures with missing fixtures and inherited assertions; this is not a green default suite. Canonical buffers peak at 593,311 bytes, not total heap. All six edits, five alternating pairs and broader cold regression checks remain required. Storage reasons, ordered fields, complete dependencies and runtime soundness are not certified.

Raw files use portable path placeholders and descriptive labels; original and public SHA-256 hashes are separate. Numeric measurements, diagnostic messages, type shapes and failed exits are preserved. Gzip/xz compression is lossless after those declared text translations. Existing frozen lab inputs and previous receipts are unchanged.
