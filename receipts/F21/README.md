# Spinel extraction and manual kernel references

Spinel `e527d205d274ccdbbca926edaddce386b8c17fa2`, CRuby 4.0.7, arm64 macOS;
manual generated-C replacements compiled at `-O2` with the same runtime ABI.
[condition.json](condition.json) pins all flags, repetitions and validation scope.
[Programs and replacements](../../patches/spinel-recursive/) retain the inputs and complete C bodies.
`compile.json` keeps native and CRuby outputs; `probes.json` and `*.seed` retain alias extraction.
`fastpaths.json` holds seven alternating control/replacement pairs; the allocation reports are raw.

```sh
python3 -B receipts/F21/recompute.py
python3 -B patches/spinel-recursive/rerun.py --output _work/spinel-recursive
```

The reduction computes ratios of medians: 2.05×, 2.85×, 3.80×. Canonicalizer samples vary widely.
The recursive alias probe loses the required-parameter method signature; compilation still succeeds
through ordinary inference. Validation is limited to the closed builtin JSON domain.
These are unscored kernel references: recursive-alias compiler support and application gains remain unimplemented.

`inputs.json` records both historical and relocated source hashes; changes remove source comments
host names in C line directives, and trailing whitespace. Function implementations are retained.

A fresh public-source build and repeat of all three kernels also passed the 96-value
CRuby comparisons and GC stress checks. Its new timing pairs are retained separately
in [release-recheck](release-recheck/); the historical ratios above keep their original condition.
