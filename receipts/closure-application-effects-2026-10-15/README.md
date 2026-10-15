# Closure application effects

Bounded confirmation after two missing controls completed. This is an unscored research reference, prepared for lead review.

## Fact F57

On October 15 condition `closure-application-effects-20261015-ea3ec744`, compiler `fdc00ee9` with implementation `a59defd6` confirms the syntactic closure-application rule on its synthetic fixtures and all five pinned apps. The first independent review upheld an inconclusive verdict; the final review upholds confirmation after exactly two missing Discourse controls completed, with the checker and 36 earlier receipts unchanged. The consumer of a closure value determines whether to harvest its body: Proc calls, block/argument positions and local bindings select its may-apply traversal; storing it in an Array, Hash, splat or ivar, returning it or inspecting it does not itself apply it. The 66 fixtures plus 21 twins confirm 87 runtime predictions; the base fixtures run on CRuby 4.0.7 and 3.4.4, and twins on 4.0.7. All 38 required app cells pass the registered checks, and the reflective traversal/bound repairs are restored. Static scanning predicts new invoked-closure writes only on Mastodon (three) and Discourse (twelve); Discourse also has one report-only entrance-site miss outside the scan scope. Application through container flow, branches and `curry` remains outside the syntactic rule; one ineligible fixture is excluded only from the declared harvest gates. The flags-off suite retains 41 matched-baseline failures, and the flags-on suite is unrun. This bounded confirmation is not general Ruby soundness or app schedule independence.

## Condition and pins

Public condition: `closure-application-effects-20261015-ea3ec744`.
The [public source](https://github.com/bunnykong/roundhouse/tree/37a076d89d02959493b70ec954aabcc3e60544f5) is a clean snapshot on the published storage-repair baseline.
[Pins](pins.json) include all public app commits and toolchain versions; [source equivalence](source-equivalence.json) binds compiler spelling translations.

## Receipt label map

- `p2-v2-s4-closures-card1-ea3ec744-observers-v1` → `closure-application-effects-20261015-ea3ec744`.

Only this historical-label map preserves internal condition spellings in public prose. Raw data is not renamed.
`raw/` preserves original bytes after lossless decompression. `derived/` contains disclosed path, label, flag
and fixture-name translations with original, public uncompressed and published-file hashes. No measured
source or original receipt was edited. Native union fields, type shapes, numerical outcomes and failed exits
retain their meaning. Machine series keys retain their recorded values.

## Evidence and independent review

The final review replays the unchanged checker and audits raw artifacts; it runs no new analyzer. The first review includes sampled native controls and the five compiled breaker tests. The follow-up contributes exactly the two required Discourse entrance controls, with 36 earlier cells unchanged. The 66 base fixtures have both CRuby versions; the 21 twins have 4.0.7 only. One ineligible case-pattern fixture is excluded from harvest gates while value/identity controls still include it. The static scan misses an additional Discourse entrance site outside app/ and lib/. The flags-off suite remains red with 41 matched-baseline failures; the flags-on suite is unrun.

The [manifest](manifest.json) lists every retained member, report hash, decompressed archive and omission.
Reports, messages and transcripts are omitted from Git. Compiler/app/dependency trees, binaries and repeated
large streams are omitted; captured artifact identities remain in command receipts. Omitted multi-gigabyte
streams are not described as freshly inspected. Public input paths are portable examples.

## Reproduction

```sh
python3 rerun.py saved
```

This verifies retained hashes and recomputes the bounded saved comparisons. Zero means the recorded
confirmation, negative result or missing coverage was reproduced from saved evidence; it starts no analyzer.
The [native recipe](REPRODUCE.md) supplies focused public-source controls. Its commands are syntax-checked,
with no new Cargo build, native app matrix or performance measurement during packaging.
All six public inference frontiers remain open.

The [tool port](tool-port.json) retains the actual checker logic and all original regression assertions.
`python3 replay_apps.py` checks the completed snapshot and the missing-control negative;
`python3 check_regressions.py` runs the six synthetic controls with portable fixture/scan inputs.
These checks invoke no native analyzer.
