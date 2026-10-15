# Reproduce focused native controls

The saved reducer checks retained evidence. The native recipe below runs focused controls in a fresh clone;
it was syntax-checked during publication and was not executed as a new native experiment.
Recorded command/exit files preserve the complete original experiment and review matrices.

The existing [coordination helper](../warm-fingerprint-edit-audits-2026-10-11/runners/flock.py) is included
in this lab. Set `HOST_LOCK_TOOLS` to its `runners` directory and share one `HOST_LOCK_FILE` on the host.

Use Rust/Cargo 1.98.1, Ruby 3.4.4 for library tests and Ruby 4.0.7 for application/emission controls.
Supply the published source checkout, required Ruby prerequisites and available locked dependencies.
Use a fresh output path. The host coordination helper and lock are explicit so all native work shares
the same host protocol; cost pairs require an exclusive reservation.

```sh
export SOURCE_ROOT=/path/to/fingerprint-six-edit-gates
export NATIVE_OUTPUT=/path/to/fresh-native-output
export HOST_LOCK_TOOLS=/path/to/host-lock-tools
export HOST_LOCK_FILE=/path/to/shared-host.lock
python3 rerun.py native
```

The native recipe runs the bounded fingerprint canaries and warm-check integration selector, not the missing cost campaign. Full campaign orchestration is in the public source under tools/research/fingerprint-six-edit-gates and in the manifest-indexed command records. It needs prepared frozen app copies, same-path parent controls, explicit cache/lock roots and a new deadline. Reserve an exclusive window for each complete timed pair. Do not reuse the expired October 15 deadline or claim a timing gate from audited runs. Required completion remains five parent profiles, thirty candidate pairs and thirteen broader cold pairs; the six audited edits are already recorded.

Each selected Cargo command preserves its actual stdout/stderr and exit. The wrapper continues after
expected test failures so their evidence is collected. Inspect nonempty test counts and the assertion,
not just an outer wrapper exit. The owned Cargo target is cleaned on exit. This recipe does not turn a
red default suite, missing app/export comparison or incomplete campaign into a passed gate.
