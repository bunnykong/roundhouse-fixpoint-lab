# Pinned public corpus

The runner supervises a supplied Roundhouse binary on 27 small fixtures and five pinned public apps.
No gems, databases, application boot, or Ruby execution are needed for static ingest.

```sh
sh corpus/fetch.sh
python3 corpus/run.py --binary ./roundhouse --set all --label example
python3 corpus/reproduce.py baseline
```

`reproduce.py` builds the pinned source, fetches the apps, and runs the selected configuration in one command.
It needs Git, a Rust installation that honors Roundhouse's toolchain file, and the native tools required by Cargo.
`--binary` skips building. Configuration flags are in `patches/configurations.json`.
`--set micro|apps|all` selects inputs. Repeated `--env K=V` supplies explicit flags.
`--limit-gib` and `--seconds` override both selected sets. Micro defaults are 4 GiB / 120 seconds;
app defaults are 40 GiB / 1,200 seconds. `--reference-micro` selects the original 13-fixture subset.

Each invocation acquires `corpus/run.lock` and checks for another running Roundhouse process.
The overlap check uses POSIX ps or conservative macOS libproc. If process visibility is unavailable,
the runner fails instead of reporting an unsupervised measurement.

`fetch.sh` clones only the five public repository URLs in `apps.json`, at their full commit SHAs.
Existing clones are verified and never overwritten. `--verify` checks without downloading. Source hashes
and Git trees are recorded in `MANIFEST.json`; edits fail verification before analysis. Forem's 2021 stable
tag is a historical condition. Git metadata is omitted from source-tree hashes.

Results go to a new `results/<label>/` directory. They record the binary hash, source hashes, host, flags,
resource limits, peak RSS, wall time, exit outcome, and diagnostics by kind. Raw diagnostic messages are
reduced in memory and discarded. Inherited analyzer and Ruby/Gem overrides are stripped.
Peak RSS is max(exact wait4 peak, sampled RSS); sampling is every 100 ms. Limits can overshoot between
samples. Child wall time excludes the final watchdog polling delay. Diagnostics after a kill are incomplete.
A normal exit without the checker summary is a harness failure. Completion is not a convergence certificate.
The accepted `rh-dyn` fields contain aggregates and explicit convergence observations only.
Candidate fold, scheduler, EP3, and sharing telemetry is retained through an explicit field whitelist.
Complete-state verification includes IR changes; a stable signature alone cannot substitute for it.

The [historical baseline](published/baseline.json) retains field-whitelisted measurements from
`public-corpus-v1`. Its numbers were not rerun during packaging; wall time is descriptive and host-dependent.
`public-lab-v1` is the expanded condition. Compare only runs with the same subset, pins, flags, and limits.

```sh
python3 -B -m unittest discover -s corpus -p test_harness.py
```
