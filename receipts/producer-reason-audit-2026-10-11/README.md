# Producer reasons and a bounded return accumulator

**Verdict: Killed at complete producer conservation.** October 11, 2026. Unscored public reference.

On October 11 condition `producer-reason-audit-next38403140-20261011-shared-host`, recorded candidate tree `d83849d` passes four reason-conservation contracts and five local return-accumulator tests, including 6,600 finite value-membership checks. The **complete producer-conservation gate is killed**: Campfire native parameter merges still remove 72 Gradual and 234 Unresolved kind-events in 15,649 merges without producer justification. These are repeated events, not distinct Ruby omissions. Ordinary S3 values, diagnostics and opacity counts stay unchanged. Fresh candidate exports against 78 saved F19 observations at 45 selections reject none but retain five missing and 39 opaque selections, including missing ones. The local accumulator is not installed in production; incomplete origins, provenance-aware invalidation and storage conservation remain open.

## Pins and condition

Condition: `producer-reason-audit-next38403140-20261011-shared-host`. Labels are descriptive translations of the recorded experiment labels.

- Published base: [`38403140379cd69759b0fe6247c6a8c4a48a37a9`](https://github.com/bunnykong/roundhouse/tree/38403140379cd69759b0fe6247c6a8c4a48a37a9).
- Recorded experiment source: `d83849d3f7750b0121390f0c89a52ec81ad84b6e`.
- Proposed fork branch: [`producer-reason-audit`](https://github.com/bunnykong/roundhouse/tree/producer-reason-audit).
- Public source: [`f9be715d71e0b7f33b785641043e809f59085f3f`](https://github.com/bunnykong/roundhouse/tree/f9be715d71e0b7f33b785641043e809f59085f3f).
- Frozen input lab: [`76cdb1ea`](https://github.com/bunnykong/roundhouse-fixpoint-lab/tree/76cdb1ea24b0c4c88af4c42c78f567d759b7731d).

Campfire `90b330024dec3e757c79b6a7e6568f93da8e3148`; saved F19 programs and 78 runtime records at the common lab pin. Input/tree/binary/runner hashes are retained in raw conditions. Rust/Cargo 1.98.1, four build jobs, locked dependencies; app checks use CRuby 4.0.7 with Prism, library controls use CRuby 3.4.4, and recording used Python 3.9.6.

Snapshot: yes; internal names and helper paths were translated mechanically. No new native Rust run is implied by publication. Recorded binary hashes name the measured artifacts. [Pins](pins.json), [summary](summary.json) and [file hashes and omissions](recorded-files.json) retain the evidence boundaries.

## Results

| Check | Control | Candidate |
| --- | --- | --- |
| Mixed-origin contract | 1 fail | 4 pass |
| Return replacement controls | 2 fail | 2 fail |
| Local return accumulator | — | 5 pass |
| Finite value membership | — | 6,600 pass |
| Lost Gradual kind-events | — | 72 |
| Lost Unresolved kind-events | — | 234 |
| F19 accepted/rejected | 78/0 | 78/0 |
| F19 missing selections | 5 | 5 |

## Commands

From the lab root, validate file hashes and recompute the bounded saved checks:

```sh
RECEIPT=receipts/producer-reason-audit-2026-10-11
python3 -B "$RECEIPT/rerun.py" saved
```

For fresh native candidate checks, use an empty work directory and set `RESEARCH_LOCK` to the host lock shared by all other analysis jobs. Native mode clones the exact public pins, captures commands and expected failing exits, and creates new observations:

```sh
python3 -B "$RECEIPT/rerun.py" native \
  --work "$PWD/fresh-producer-reason-audit" --lock "$RESEARCH_LOCK"
```

[Rerun script](rerun.py) and [portable runners](runners/) preserve the original checker/observer conventions. Native reproduction needs the proposed fork branches pushed first. Saved checks require neither a source clone nor a compiler build. They validate retained evidence; they do not turn a failing native gate into a pass.

## Caveats

The ledger retains captured inputs and equal merges conserve reasons, but native parameter absorption still discards permanent reasons. The counts describe repeated merge events, not distinct missing values. The local accumulator tests 21 sample types and fixed toy writer identities; it is not the production return table. Observed writer sets contain 8,186 identities, with 116 unmapped/synthetic source paths and 44 reference-origin debts. F19 retains 45 selections, five missing selections, six observations at missing selections and 39 opaque selections including missing ones. Zero rejection is not full coverage. Campfire ordinary output, diagnostics and opacity counts match S3 across five pairs, while its inherited schedule-dependent return digest remains. The default command records 1,142 pass / 2 fail / 9 ignored and stops before integration tests; both failures reproduce on the untouched next pin. Measurements preceded the local commit; source hashes tie the recorded patch to its tree. Public flag, example and test names are mechanical translations, and public snapshots were not used for these measurements. The current wire format and scheduler still omit reason-set obligations. One app, shared host, no performance measurement or complete producer inventory.

Raw files use portable path placeholders and descriptive labels; original and public SHA-256 hashes are separate. Numeric measurements, diagnostic messages, type shapes and failed exits are preserved. Gzip/xz compression is lossless after those declared text translations. Existing frozen lab inputs and previous receipts are unchanged.
