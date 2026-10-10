# Predeclared equation design

Design material, no measured performance claim. Implementation comparison: partial-structure
prototype [`f7694daa`](https://github.com/bunnykong/roundhouse/tree/f7694daa93bde5d4c0fc00fe4a3853595db47c41) on `92844f68`, with the exact flags and executed tests in
[writer-boundaries](../writer-boundaries/README.md).

Return and parameter identities distinguish definition owner, includer and class/instance side;
expression identities carry source owner and syntax path. Constants and closure parameters/results
must be in the slot inventory. Writer identities and a may-call graph come from syntax, library
summaries and explicit dynamic-send candidates. Physical allocation may be lazy if it does not
change logical membership or reference routing.

The partial prototype freezes a call graph and recursive set; it does not predeclare every logical
slot and writer or check write membership, and its routing canary does not inspect every
inline/reference read path. `src/analyze/equations.rs`, `fold.rs` and `structure.rs` at the pin expose
those boundaries. A complete contract remains a proposed design.

```sh
git grep -n 'RH_STRUCT\|declare\|membership' -- src/analyze
```
