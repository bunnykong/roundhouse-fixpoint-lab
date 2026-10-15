# Cached analyzer observers

Run explicit observer settings, reuse completed cells and check named claims with Python 3.9+.
The tool requires an existing analyzer and CRuby 4.0.7. It builds nothing and uses no network.
Condition: `cached-observers-20261015-source-rebuild`; [F54 receipt](../../receipts/cached-observers-2026-10-15/README.md).

The [pins](pins.json) name public compiler snapshots and five public app commits.
The [port record](port.json) distinguishes the original tool bytes from this portable publication copy.
All 14 original tests and their assertions are retained; publication changes flag/output names and paths.

## Run, reuse and repeat

From the lab root, with the pinned app under `corpus/apps/campfire` and a built public snapshot:

```sh
O=tools/observers
python3 "$O/obs.py" run --bin ./compiler/target/release/roundhouse --app campfire \
  --matrix full --flags "$O/profiles/normalized-composition.json" --label composition
python3 "$O/obs.py" claims composition --spec "$O/claims/value-equality.json"
```

Repeating `run` reuses completed cells with zero analyzer runs. `--fresh` repeats selected cells and compares
normalized observations against the immutable first valid result. Failed attempts remain retained; a valid
fresh mismatch marks the key inconsistent, so later hits and claims fail. An explicit fresh retry can recover
a failed first attempt without deleting it. Use a new label when changing an existing app/setting condition.

`--input PATH --app NAME` overrides the example app location. `--settings` accepts a comma-separated subset;
the default is `unset-v1-a1`. `--jobs` is 1–6, default 6. `--timeout` is analyzer seconds, default 1,800,
excluding lock waits. `--cache-root` selects a separate cache.

The bundled `lock.py` takes shared slots; all invocations on one host must use the same lock file.
Use `--lock-wrapper ./tools/observers/lock.py --lock-file ./host-locks/heavy.lock` to select it explicitly.
The parent directory must exist. The default is `tools/observers/cache/heavy.lock`.
Discourse's `max_parallel=1` serializes that app across invocations sharing the host lock.

## Sixteen observers

Schedules are unset, 1, 2 and an independent unset repeat, crossed with verification 1/0 and audit 1/0.
Names such as `1-v0-a1` explicitly select all three dimensions. The repeat has its own cache key.
Verification uses `RH_FIXPOINT_VERIFY`; audit uses `RH_PROVENANCE_AUDIT`; schedule uses `RH_SHUFFLE`.
Audit is distinct from requesting structure/declaration dumps. Profiles cannot override these protected flags.

Value digests ignore reasons. Verification re-types every body but compares values only, and can hide
reason-only differences. Audit changes reason bits. Every equality claim therefore names its observer.
The rounds scheduler used by shipping defaults ignores the schedule flag; repetition is not a schedule test.

`profiles/normalized-composition.json` selects the tested storage repairs, ownership and absorbed reader view.
`profiles/ownership-control.json` and `profiles/ownership-a.json` preserve the historical baseline/ownership
settings separately. Their public flag spellings match the source snapshots in `pins.json`.
JSON null unsets a default. `--flag RH_NAME=value` supplies an individual override.

Common defaults enable folds, the dependency scheduler, value digests, statistics, precision census,
public-input mode and the error gate. Every effective flag, including absolute capture destinations,
is recorded. Ambient research variables are cleared; Ruby is pinned to 4.0.7 and `LC_ALL=C`.

## Inputs, cache and observations

Every call computes a fresh full input manifest: file paths, bytes, executable bits, symlinks and resolved
symlink dependencies. Git metadata is excluded. Configured trees must match their saved hashes.
Binary and input identities are checked again after a run. Cache keys include schema, binary SHA-256,
complete manifest SHA-256, every effective flag, schedule identity and Ruby/platform identity.
Dump paths are deterministic within a cache; moving it changes keys.

Raw stdout, stderr, requested dumps, metrics and native reports accompany normalized observations.
Large dumps are reduced as streams. Duplicate reason identities or inconsistent declaration headers fail.
Unsupported observers are null, never successful empty sets or zero violations. Value equality cannot prove
reason equality, complete writer coverage, soundness or emission identity.

Native exits 0/1 need exactly ten complete value digests; exit 1 may mean app diagnostics. Other exits,
timeouts, missing reports and invalid dumps remain failed cells. Native main's nine-table output is rejected
by this tool; no missing table is invented. Historical nine-table adapters remain separately scoped evidence.

`wait4` supplies analyzer wall/CPU time and RSS, excluding queue and reduction; total time includes those costs.
Timing noise is excluded from observation equality. Shared-host profiles establish no performance claim.
Raw artifacts are hashed on capture; warm hits check sizes, small hashes and normalized observation hashes,
without rehashing multi-gigabyte raw dumps. Full original hashes remain available for custody checks.

Under `cache/`, `inputs/` holds manifests; `objects/` holds immutable baselines and attempts; `labels/` holds
atomic references and invocation histories; `comparisons/` holds differences. OS locks prevent duplicate
execution. Interrupted captures, failures and mismatches remain recorded. Cache content is ignored by Git.

## Compare and check claims

```sh
python3 tools/observers/obs.py compare baseline ownership
python3 tools/observers/obs.py claims composition --spec tools/observers/claims/value-equality.json
```

These commands invoke no analyzer. A spec has a `claims` array; each entry names `name`, `apps`, explicit
`settings`, `kind` and optional `field` (default `value_digests`). Kinds are `equal`, `equals`, `changed_keys`,
`reason_delta` and `zero`. Exact checks use `expected` or `expected_by_setting`; changed keys use `against`;
reason deltas use a baseline and retain full identities, reasons, type hashes and missing-row sets.
Fields are value digests, reason census/rows, successful writes, law violations, diagnostics, loops,
verification and exit code. Dotted dictionary subfields are supported. Missing/invalid cells, unavailable
fields and singleton equality claims cannot pass. Claims never silently run additional settings.
Exit 0 means every claim passes; 1 means a failed claim; 2 means an invalid request.

## Check the public copy

```sh
python3 -m unittest discover -s tools/observers -p 'test_*.py' -v
```

The 14 tests exercise key dimensions, repeats, manifest changes, concurrent reuse, failed-first recovery,
fresh mismatches, unavailable observers, exact negative claims, duplicate rows, child metrics and timeouts.
They use synthetic child/cache controls and invoke no native analyzer. Their success is a tool-contract check,
not a fresh reproduction of the historical app matrix. Historical binary recovery remains inconclusive.
