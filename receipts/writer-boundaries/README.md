# Writer integration boundaries

Historical shape and partial-structure prototypes, on staged Roundhouse `92844f68`.
Public equivalents: shape [`e00feac2`](https://github.com/bunnykong/roundhouse/tree/e00feac2a6453d8a0ffd109c10bd9c866eff026c), structure [`f7694daa`](https://github.com/bunnykong/roundhouse/tree/f7694daa93bde5d4c0fc00fe4a3853595db47c41).
[conditions.json](conditions.json) records exact flags and commands; the two `*-tests.txt`
files retain the executed regression lines. [prototypes.json](../prototypes.json) maps historical pins.

```sh
python3 -B receipts/writer-boundaries/recompute.py
```

The shape prototype keeps setter verdicts separate from assignment results and recognizes tuple
operands through the shared collection view. The structure prototype reads a closure reference's
head before testing pending state and prevents narrowing identities from shadowing unbound calls.
These are integration regressions; they do not establish complete predeclaration or order independence.
