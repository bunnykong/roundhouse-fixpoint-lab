# What the Lean project proves

Lean 4.34.1 and Mathlib 4.34.1 check a finite-site inference calculus: termination, leastness,
equivalent scheduling, tree-language denotation, and soundness for a small concrete language.
There are no admitted proofs. Build from this directory with `lake exe cache get && lake build`.
The results concern the calculus and the stated abstraction. They are not a proof of all Ruby semantics
or a certification of the current Roundhouse implementation.

## The core and its lowering

`Prog` has finite sets of slots and constructor sites. A site has a kind and finite field cells `cell(h,f)`.
`Pt(v,h)` means that a value constructed at site h may reach slot v. There are two positive rule schemas:
`Alloc(dst,h,conditions)` and `Guard(src,dst,optional_kind,conditions)`. A condition `(v,h)` requires that
fact to be present. Flow, field loads/stores, calls, yields, filters, merge, and produced containers lower
to these schemas. `BadUse` diagnostics are evaluated after the solution, without feeding absence back
into inference.

`Prog.step` is monotone (`Prog.stepSet_mono`) and bounded by the finite universe of slot/site pairs
(`Prog.step_subset_univ`). `Equiv.pt_iff` proves that the relational model's derivable `Pt` facts equal
the lowered core's least solution for every input. `Equiv.bad_iff` proves the same for bad uses. No
decisive case-specific assumption is built into these equivalence theorems.

## Termination

- A monotone `BoundedOp` on a finite universe U has terminating iteration from empty. If it returns R
  in n rounds, then R is the nth iterate, `F(R) = R`, and `n ≤ |R| ≤ |U|`.
  Lean names: `BoundedOp.kleeneAux`, `BoundedOp.kleeneAux_spec`,
  `BoundedOp.kleeneN_rounds_le_card`, `BoundedOp.kleeneN_rounds_le`.
- After `|U|` rounds, the chain has reached the result: `BoundedOp.iterate_card_eq_kleene`.
- Semi-naive iteration terminates within `|U|` rounds: `BoundedOp.semiAux`, `BoundedOp.semiN_spec`.
- A worklist terminates under every permitted queue discipline, by the lexicographic measure
  (unknown facts, queue length). A fact is queued only on first discovery: `BoundedOp.workAux`.
- The program solver needs at most `|answer|` and at most `|dsts| · |sites|` rounds:
  `Prog.solveN_rounds_le`. The productivity-refined solver needs at most
  `|dsts| · |sites| + |sites|`: `Prog.solveR_rounds_le`.

## Leastness, scheduling, and edits

- The naive answer is the least pre-fixpoint: `F(R) ⊆ R`, and `F(Y) ⊆ Y` implies `R ⊆ Y`.
  `BoundedOp.kleene_isLeast`, `Prog.solve_isLeast`.
- If a monotone set operator agrees with the finite operator, R equals its Knaster–Tarski least fixpoint.
  `BoundedOp.kleene_eq_lfp`, `Prog.solve_eq_lfp`.
- Sound and complete deltas give round-by-round equality: the kth semi-naive state is the kth naive
  state together with exactly the new facts in the next round. `BoundedOp.snStep_iterate`,
  `BoundedOp.semiN_eq_kleeneN`, `Prog.delta_sound`, `Prog.delta_complete`,
  `Prog.solveSN_iterate`, `Prog.solveSN_eq_solveN`.
- A scheduler may merge the remaining queue and new facts in any order that preserves their members
  and does not grow the queue length. It still returns the same least solution.
  `BoundedOp.work_eq_kleene`, `Prog.solveW_eq_solve`.
- Warm iteration from a seed X satisfying `X ⊆ F(X)` and lying below the least fixpoint returns that
  least fixpoint. Every result contains its seed, so a seed outside the least fixpoint cannot produce it.
  `BoundedOp.kleeneAux_eq_kleene_of_le`, `BoundedOp.seed_subset_kleeneAux`.
- Adding rules preserves the old answer as a safe seed: `Prog.solve_mono_prog`, `Prog.incremental_add`.
  Deleting a rule can leave a self-supporting cycle whose retained answer is fixed but not least:
  `Deletion.deletion_keeps_cycle`. Deletion needs rederivation; a deletion algorithm is not verified here.
- Rank slots so premises never outrank conclusions. Solve each rank to its local least fixpoint with
  lower ranks frozen; the result is globally least: `Prog.layer_spec`, `Prog.layer_eq_solve`.
  In acyclic parts each rank needs at most one local round: `Prog.strict_one_round`.

## Tree languages and productivity

`STree` is a finite constructor tree. The grammar of a site solution has finitely many nonterminals
and productions. `Mem` defines its language. The set-constraint operator is `Phi`; its least solution
is `Xstar = OrderHom.lfp (PhiHom P σ)`.

Required record fields matter. `Prog.stepR` adds a fact `prod(h)` when all required fields can produce
finite trees. Its conditions fire only on productive sites. `Prog.solveR` is its least solution;
`Prog.ptPlus` contains its site facts.

- Exact refined denotation: `Xstar P σ = langR P σ`, proved by `lfp_eq_lang_refined`.
- Plain denotation is sound: `Xstar P σ ≤ langPlain P σ`, proved by `lfp_le_lang_plain`.
- Refined site facts are plain site facts: `ptPlus_subset_solve`.
- If every condition that holds concerns a productive site, the site solutions agree:
  `ptPlus_eq_solve_of_productive`. If no condition site has a required field, the plain language is exact:
  `lfp_eq_lang_plain_of_no_required`.
- The side condition is necessary. A record with a divergent required field is never constructed,
  yet projecting a different field in the plain grammar can produce Integer: `Gap.plain_ne_exact`.
- `Phi` is omega-continuous, and its least solution is the supremum of finite iterates:
  `Phi_omegaScott`, `Xstar_eq_iSup_iterate`.
- For `R = String | Array[R] | Hash[Symbol,R]`, no finite tree-chain stage equals the limit, and stages
  increase strictly: `SelfShape.self_iterate_ne`, `SelfShape.self_iterate_lt`.
  The finite site solver terminates and its grammar denotes that limit exactly: `SelfShape.self_exact`.

The denotation is inductive: finite trees in a least solution. A coinductive reading can retain an
unproductive cycle such as `μX.Hash[Symbol,X]`; the finite-tree least solution drops it.

## Concrete soundness and the history-only limit

`Lang.Eval` gives big-step semantics for first-order functions, scalar literals, one- and two-child
constructions, projections, mutual calls, nondeterministic branches, and kind narrowing. `Lang.gen`
generates core constraints. `Lang.sound` proves: if an expression evaluates to w from an argument
described by its parameter slot, w is described by its expression slot in the least site solution,
recursively through its field cells. Slot labels may collide; merging them remains sound.

`T10` in `ProofLean/Impossibility.lean` formalizes a limit of history-only backstops. Such a backstop
sees only one slot's value history, newest first, and values accumulate. If it stops
`X = Int | Array[X]` at round K, then on the acyclic length-K chain
`F_i = Int | Array[F_(i+1)]`, `F_K = Int`, it retains `Array^(K+1)[Int]` at `F_0` from round K onward.
The chain's least solution does not contain that value. `histories_agree` proves indistinguishability
up to K. `m1Like_stops_R` supplies a nonvacuous backstop; `no_backstop_never_stops` supplies the control.
A backstop that reads dependencies is outside this theorem's hypothesis.

## Executable checks and counterexamples

`ProofLean/Check.lean` solves 18 stored relational inputs with naive, semi-naive, FIFO, and LIFO solvers.
Its `#guard` compares every `Pt` and bad-use fact with the stored Python result. These include mutual
cycles, parameter recursion, a 64-link chain, merge-feedback contexts, and re-embedding.
The 64-link chain takes 64 naive rounds; ranked evaluation uses 64 slot evaluations.

`ProofLean/ShapeCheck.lean` compares the verified solution with regular folding and a Kleene reference
on 12 public synthetic equation systems. The yardstick is node paths up to five nodes, on every equation
slot. This is a bounded executable comparison, not a theorem of full regular-language equivalence.
The stored input relations are frozen examples; the build reruns their checks without an exporter.
`ProofLean/Oracle.lean` provides the same verified solvers as a JSON differential oracle.

`ProofLean/Counter.lean` shows why the hypotheses cannot be omitted:

- `flip_not_monotone`, `flip_no_fixpoint`, `flip_iterate`: a first-arm-dependent transfer has no fixpoint
  and alternates forever. `join_repair` reaches a pre-fixpoint that is not a fixpoint of the original transfer.
- `selfVar_from_bot`, `selfVar_from_seed`: a placeholder seed may produce a fixed answer that is not least.
- `run_never_stable`: hidden state can alternate two monotone rounds even on a finite lattice.

## Obligations for an analyzer implementation

1. Slot, site, field, and context identities come from finite tables. A field cell cannot be a growing path.
2. Transfers are positive and monotone. More input facts never remove output facts.
3. Iteration starts at empty, or from a certified pre-fixpoint seed below the least answer.
4. Every cross-round input is represented in the state. IR stamps and caches cannot be hidden inputs.
5. Absence-sensitive diagnostics run after the fixpoint, in a separate stratum.
6. Required-field record conditions use productivity, or satisfy the theorem's stated side condition.
7. Exactness is relative to the finite-site abstraction. Against concrete executions, the theorem is soundness.

Current structural type trees do not automatically satisfy these obligations. A recursive equation can
have an infinite tree approximation chain while a finite grammar presents its least language. The proof
explains why that finite presentation works and where representation, lowering, and transfer audits remain necessary.
