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
export SOURCE_ROOT=/path/to/reflective-evaluated-containers
export NATIVE_OUTPUT=/path/to/fresh-native-output
export HOST_LOCK_TOOLS=/path/to/host-lock-tools
export HOST_LOCK_FILE=/path/to/shared-host.lock
python3 rerun.py native
```

The recipe adds the minimal and closure-matrix tests only in its fresh clone, plus the exact Ruby fixtures. Ruby must execute all thirteen matrix cases; eleven write and two defer. The native missing-write assertions are expected to fail with exit 101 under all four schedules. The original entrance, partition and broader app/export campaigns remain separate evidence.

Each selected Cargo command preserves its actual stdout/stderr and exit. The wrapper continues after
expected test failures so their evidence is collected. Inspect nonempty test counts and the assertion,
not just an outer wrapper exit. The owned Cargo target is cleaned on exit. This recipe does not turn a
red default suite, missing app/export comparison or incomplete campaign into a passed gate.
