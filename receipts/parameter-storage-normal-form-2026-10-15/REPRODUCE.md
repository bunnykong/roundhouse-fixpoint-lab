# Reproduce the bounded observations

Start with `python3 rerun.py saved` for the retained evidence. This command runs no analyzer.
Acquire only public inputs at the commits in `pins.json`, in a fresh output tree.
Build Rust with four jobs and an owned `CARGO_TARGET_DIR`; serialize work through the shared host lock.
New measurements need a new descriptive condition and must remain separate from these recorded results.

For the native finite-law controls, check out the public source commit from `pins.json`, then run:

```sh
SOURCE=./compiler OUTPUT=./fresh-law-results \
HOST_LOCK_WRAPPER=./tools/observers/lock.py HOST_LOCK_FILE=./host-locks/heavy.lock \
  bash native.sh
```

Resolve those paths before invoking the script. Native Ruby is 3.4.4; Rust is 1.98.1.
The unnormalized law control must fail at Cargo exit 101; zero at the outer helper means that expected
negative was retained. The normalizer-on control must pass. Inspect the emitted counts, not exit status alone.
The helper is a focused control and does not repeat the full registered matrix or the red default suite.

For fresh app observations, use the [public observer tool](../../tools/observers/README.md) with the
matching public compiler pin, named settings and explicit repair profile. CRuby is 4.0.7.
The ownership comparison uses the same binary/input under the control and ownership profiles, four schedules,
and verification/audit off. Compare value tables excluding the copy-state table for F53.
For F51/F52 use normalized-composition settings, with normalization disabled for F51's source where absent.
Preserve separate value and reason observers; available ten-table results do not certify reason equality.
The tool's fourteen unit tests use synthetic child/cache controls and are distinct from native app evidence.
Original command, effective-flag, exit and digest receipts remain indexed in `manifest.json`.
