# Soundness and settling

Restoring Ruby's destructuring flow removes the witnessed type omissions but makes main hit its round caps.
With staged S2/S3 and the corrected rules enabled, this app settles and admits all 12 recorded CRuby values.

## Run

From the lab root, with Git, Python 3.9+, and Roundhouse's pinned Rust toolchain installed:

```sh
git clone https://github.com/bunnykong/roundhouse.git _work/settle-source
git -C _work/settle-source fetch origin fixpoint-staged fixpoint-sound main-flowfix
python3 reproductions/settle_sound/run.py \
  --source _work/settle-source --output _work/settle-results
```

The source branches are `fixpoint-staged` (`92844f68`), `fixpoint-sound` (`96cdea9a`) and `main-flowfix` (`a7e06b1e`); main is pinned to `194f26cf`. The runner builds four separate arms with
`CARGO_BUILD_JOBS=4 cargo build --release --locked`, using its own target directory and the small
`settle_probe.rs` API exporter. `RH_FIXPOINT_STATS=1` is set for each analysis; the exporter reads
`Analyzer::fixpoint_rounds()` directly, including on main, which predates the staged JSON canary.

S2/S3 enables exactly:

```sh
RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_BRK_ALLARMS=1 RH_FOLD_TAIL=1 RH_SCHED=sccq
```

The runner checks the CLI's loop endings against the API's, exports the final parameter and return
types, and runs `oracle/check.py` against `trace.jsonl`. It also runs the fixed staged arm with
`RH_FIXPOINT_VERIFY=1`. Logs, type grammars, full oracle reports, source commits, binary hashes,
and the complete-state verification are saved under `_work/settle-results/`.

## Verified table (also the expected rerun)

Condition: **settle-sound-published-v1**, this app, the pinned commits above, and CRuby **4.0.7**.
Loop counts are zero-based `LoopEnd::Settled` values, in production / views-and-tests / absorb order.

| Arm | Loops | Rejected values |
| --- | --- | --- |
| main | 3 / 0 / not run | 6 of 12 |
| main + binding fix | cap / 2 / cap | 0 of 12 |
| S2/S3 | 2 / 1 / 1 | 8 of 12 |
| S2/S3 + corrected fixes | 2 / 1 / 1 | 0 of 12 |

Fresh builds of all four named commits reproduce the earlier table without a changed cell.
[verified.json](verified.json) retains the binary hashes, loop endings, and complete-state canaries.
The extra full round in the fixed staged arm moves nothing in each recorded part of carried state. The oracle column is final-type membership of these 12 snapshots; it is a witnessed
soundness check, not a proof about all executions. The standalone main fix is an experimental control:
its non-settling behavior is why the flow restoration is staged with the fixpoint.

## Record the trace again

No Rails installation is needed; the recorder stubs `ApplicationController`.

```sh
ruby --version
ruby oracle/record.rb \
  --source reproductions/settle_sound/app/controllers/trees_controller.rb \
  --entry 'TreesController#index' --returns canonical --params canonical:value \
  --output _work/settle-trace.jsonl
python3 oracle/check.py _work/settle-trace.jsonl _work/settle-results/sound.rbs \
  --slots reproductions/settle_sound/slots.json --json
```

Use CRuby 4.0.7. The supplied trace retains the original source hash and every recorded value;
only absolute workstation paths in metadata were replaced with relative paths.
