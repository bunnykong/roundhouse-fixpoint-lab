# Typed recursion in Rust and Crystal

This opt-in patch names a recursive component's type and emits a recursive Rust `enum` or Crystal `alias`.
Three controller walk shapes compile with the flag and render the same template output as CRuby 4.0.7.

## Scope

The three shapes are #589's two-method cycle, the merged-back normalizer, and a self-recursive walk.
The class-method cycle is not covered. The Rust emitter handles only the walk idioms in these inputs;
this is a research demo, not general recursive-data support.

Rust uses real-blog plus each reproduction's controller, view, and `/tree` route. The emitted runtime's
`Base#controller_name` and `Base#controller_path` fail to compile on this base even for plain real-blog;
`patch_rust_runtime.py` stubs those two uncalled methods **identically in both arms**. Crystal uses the
small apps directly, with one unrelated table so the emitter creates its required `Schema` module.
CRuby runs the original controller under a stub `ApplicationController` and renders
`ERB::Util.html_escape(@tree.to_s)` followed by a newline. Rust compares the template inside real-blog's
layout; Crystal compares the full response body.

## Apply and build

Run from the lab root. Install Roundhouse's pinned Rust toolchain, CRuby 4.0.7, Python 3.9+, and Crystal 1.21.1.

```sh
git clone https://github.com/rubys/roundhouse.git _work/rec-source
git -C _work/rec-source checkout b28b17b68d1fc879c506765cdc18142518544494
git -C _work/rec-source apply --check ../../patches/phase-c2.diff
git -C _work/rec-source apply ../../patches/phase-c2.diff
git -C _work/rec-source apply --check ../../patches/emit-rec/sound-base.diff
git -C _work/rec-source apply ../../patches/emit-rec/sound-base.diff
git -C _work/rec-source apply --check ../../patches/emit-rec/emit-rec.diff
git -C _work/rec-source apply ../../patches/emit-rec/emit-rec.diff
(cd _work/rec-source && CARGO_BUILD_JOBS=4 CARGO_TARGET_DIR="$PWD/../rec-target" \
  cargo build --release --locked --bin roundhouse)
```

`phase-c2.diff` supplies the Phase C prototype (`9b16a0f6`). `sound-base.diff` adds the five historical
flow fixes, reconstructing the emitter patch's base (`459a5e8b`); this dependency is distinct from the
corrected soundness experiment in `reproductions/settle_sound/`. `emit-rec.diff` is the clean source
patch from `459a5e8b` to the six-commit demo (`142375ac`), with team labels removed from comments:
**1,063 insertions and 15 deletions in 12 source files**. It also applies directly to `459a5e8b`.

## Compile and compare

Fetch the exact Crystal dependencies. They remain separate upstream dependencies under their MIT licenses.

```sh
git clone https://github.com/crystal-lang/crystal-sqlite3.git _work/crystal-sqlite3
git -C _work/crystal-sqlite3 checkout 36a9f0654b9a1ed236da393aa5a97134f45d65e4
git clone https://github.com/crystal-lang/crystal-db.git _work/crystal-db
git -C _work/crystal-db checkout ec7b045b3e2cf5962c029bf676f238f812f40872
RUSTUP_TOOLCHAIN=1.98.1 python3 patches/emit-rec/demo.py \
  --binary _work/rec-target/release/roundhouse --crystal "$(command -v crystal)" \
  --sqlite3 _work/crystal-sqlite3 --db _work/crystal-db --output _work/rec-results
```

The script emits each target with flags unset, then with the following flags; only the normalizer
also enables `RH_SOUND=1`:

```sh
RH_EMIT_REC=1 RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_BRK_ALLARMS=1 \
  RH_SCHED=sccq RH_FOLD_TAIL=1 RH_FOLD_PRINT=1
```

For every generated Rust crate it runs `cargo check --locked --message-format=json`, counting error
diagnostics without counting Cargo's summary, and builds successful crates with `cargo build --locked`.
`rust-app.Cargo.lock` pins the same dependencies as the reported runs. Crystal runs
`crystal build src/main.cr -o server`, with crystal-sqlite3 0.23.0 and crystal-db 0.15.0.
The Rust target and Crystal cache directories live under the output directory.
Each successful server gets a fresh port and is stopped after its response is collected.
`results.json`, compiler logs, emitted sources, CRuby references, and pages are saved in the output directory.

## Before and after

Condition: **emit-rec-phase-c-v1**, Phase C on `b28b17b6`, the patch base `459a5e8b`, the three bundled
apps, identical runtime stubs in both Rust arms, CRuby 4.0.7, and Crystal 1.21.1.
The packaged runner re-verified these rows on the demo binary at `142375ac`;
[verified.json](verified.json) retains the binary hash and compiler outcomes.
The documented three-patch recipe also builds cleanly; its generated files match that demo binary
in all 12 app × target × off/on comparisons (3 apps, 2 targets, 2 flag states), recorded in
[clean-patch-verified.json](clean-patch-verified.json).
The page column describes the successful flagged builds; the baseline builds produce no runnable page.

| Shape | Rust errors, off → on | Crystal, off → on | Page vs CRuby |
| --- | --- | --- | --- |
| two-method cycle | 5 → 0 | fail → pass | identical, 63 B |
| normalizer | 5 → 0 | fail → pass | identical, 175 B |
| self-recursive walk | 3 → 0 | fail → pass | identical, 63 B |

The two-method cycle and normalizer each lose four `E0599` errors and one `E0308`; the self-recursive
walk loses two `E0599` and one `E0308`. Without the normalizer's flow fixes its alias omits `nil`,
and Crystal rejects the program. The flag leaves the existing emission path in place when disabled.
The historical source report checked identity on 12 app/target pairs in four flag conditions;
packaging alone does not extend that claim to additional targets, apps, or the current staged branch.

The export scan is recorded in [PRIVACY.md](PRIVACY.md).

The bundled real-blog files are the public generated fixture's ingestion inputs, with no credentials,
keys, databases, or Rails installation required. All other Ruby inputs are the three small reproductions.
