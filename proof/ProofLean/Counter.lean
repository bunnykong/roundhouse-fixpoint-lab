import ProofLean.Fixpoint
import Mathlib.Data.Fintype.Powerset

/-!
# The transfer hypotheses are necessary

The theorems of `ProofLean.Fixpoint` assume three things about a round: the state is exactly the fact
set (no hidden state), the round is a monotone function of it, and iteration starts at `∅`.  Each
counterexample below drops one assumption on a lattice with two facts and loses termination or
leastness.

* `flip` is counterexample `arm_flip` (the model): `F(Hash) = Hash | Array[Int]` but
  `F(Hash | Array[Int]) = Hash`.  It is not monotone, has no fixpoint at all, and its iteration from
  `∅` is a 2-cycle forever.  Joining at the handoff (`X ∪ F X`) converges, but to a set that is not a
  fixpoint of `F` (counterexample post-fixpoint).
* `selfVar` is counterexample `unit_tail` (the model): `R ⊇ R ∪ {String}` iterated from the seed
  `{Var}` stops at `{String, Var}`, a fixpoint that is not the least one (`{String}`).
* `stamped` keeps a hidden round stamp: two monotone (constant) rounds alternate and the visible
  facts never settle, although each round is monotone and the lattice is finite.
-/

namespace ProofLean.Counter

/-- Two facts: the row holds a `Hash` arm, or an `Array[Integer]` arm (a `String` and a `Var` arm in
the second example). -/
inductive Arm
  | hash
  | arr
deriving DecidableEq, Repr

open Arm

instance : Fintype Arm := ⟨{hash, arr}, fun x => by cases x <;> simp⟩

/-! ## Non-monotone: counterexample `arm_flip` -/

/-- The round function of `arm_flip`: the call site always supplies `Hash`; with a `Hash`-only row
the block binds `val` to the Hash value and feeds `Array[Integer]` back; once the row also holds the
Array arm, the first-arm rule binds the block to the Array arm and the feedback disappears. -/
def flip (X : Finset Arm) : Finset Arm :=
  if arr ∈ X then {hash} else if hash ∈ X then {hash, arr} else {hash}

theorem flip_hash : flip {hash} = {hash, arr} := by decide

theorem flip_both : flip {hash, arr} = {hash} := by decide

/-- `flip` is not monotone. -/
theorem flip_not_monotone : ¬ Monotone flip := by
  intro h
  have := h (show ({hash} : Finset Arm) ≤ {hash, arr} by decide)
  rw [flip_hash, flip_both] at this
  exact absurd this (by decide)

/-- `flip` has no fixpoint at all, so no theorem can promise one without monotonicity. -/
theorem flip_no_fixpoint : ∀ X : Finset Arm, flip X ≠ X := by decide

/-- Iterating `flip` from `∅` is a 2-cycle: odd rounds `{Hash}`, even rounds `{Hash, Array}`. -/
theorem flip_iterate (k : ℕ) :
    flip^[2 * k + 1] ∅ = {hash} ∧ flip^[2 * k + 2] ∅ = {hash, arr} := by
  induction k with
  | zero => decide
  | succ k ih =>
    have e1 : 2 * (k + 1) + 1 = (2 * k + 2) + 1 := by omega
    have e2 : 2 * (k + 1) + 2 = 3 + (2 * k + 1) := by omega
    constructor
    · rw [e1, Function.iterate_succ_apply', ih.2, flip_both]
    · rw [e2, Function.iterate_add_apply, ih.1]; decide

/-- The round loop never reaches a fixpoint from `∅`. -/
theorem flip_never_stable (k : ℕ) : flip (flip^[k] ∅) ≠ flip^[k] ∅ := flip_no_fixpoint _

/-- The monotone handoff repair `X ∪ F X` (`RH_FOLD_JOIN`) converges in two rounds, to
`{Hash, Array}`, which is a post-fixpoint of `flip` (`flip X ⊆ X`) but not a fixpoint. -/
theorem join_repair :
    (fun X => X ∪ flip X)^[2] ∅ = {hash, arr} ∧
      (fun X => X ∪ flip X) {hash, arr} = {hash, arr} ∧
      flip {hash, arr} ⊆ {hash, arr} ∧ flip {hash, arr} ≠ {hash, arr} := by
  decide

/-! ## Not from bottom: counterexample `unit_tail` -/

/-- `pass(n, acc) = n.zero? ? acc : pass(n - 1, acc)` called with a String: `R ⊇ {String} ∪ R`.
`hash` stands for `String` and `arr` for the round-0 `Var` placeholder. -/
def selfVar (X : Finset Arm) : Finset Arm := {hash} ∪ X

theorem selfVar_mono : Monotone selfVar := fun _ _ h => Finset.union_subset_union le_rfl h

/-- From `∅` the least fixpoint `{String}` is reached in one round. -/
theorem selfVar_from_bot : selfVar ∅ = {hash} ∧ selfVar {hash} = {hash} := by decide

/-- From the seed `{Var}` the iteration stops at `{String, Var}`: a fixpoint, but not the least. -/
theorem selfVar_from_seed :
    selfVar {arr} = {hash, arr} ∧ selfVar {hash, arr} = {hash, arr} ∧
      ({hash} : Finset Arm) ⊂ {hash, arr} := by
  decide

/-! ## Hidden state: rounds that read a stamp outside the fact set -/

/-- Two monotone rounds selected by a hidden stamp. -/
def stamped (b : Bool) (_X : Finset Arm) : Finset Arm := if b then {hash} else {arr}

theorem stamped_mono (b : Bool) : Monotone (stamped b) := fun _ _ _ => le_rfl

/-- The visible facts after `k` rounds, with the stamp flipping each round. -/
def run : ℕ → Bool × Finset Arm
  | 0 => (true, ∅)
  | k + 1 => let s := run k; (!s.1, stamped s.1 s.2)

/-- The visible facts never settle. -/
theorem run_never_stable (k : ℕ) : (run (k + 2)).2 ≠ (run (k + 1)).2 := by
  have h : ∀ k, (run (k + 1)).2 = if (run k).1 then {hash} else {arr} := fun k => rfl
  have hb : ∀ k, (run (k + 1)).1 = !(run k).1 := fun k => rfl
  rw [h (k + 1), h k, hb k]
  cases (run k).1 <;> decide

end ProofLean.Counter
