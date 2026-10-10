import ProofLean.Fixpoint
import Mathlib.Data.Fintype.Powerset

/-!
# A per-run leastness certificate

`ProofLean.Fixpoint` proves that naive, semi-naive and worklist iteration of a monotone operator
`F` on a finite fact universe compute the least fixpoint.  A real run of the analyzer is none of
those schedules exactly: units are re-typed in some order, slots are overwritten, and the engine
stops when its own bookkeeping says so.  This file states what a *trace* of such a run must
exhibit for the final state to be `lfp F` anyway, in the style of translation validation.

A `Run` is a chain of states `S 0, …, S n` with three checkable properties:

* **start**: `S 0 = ∅` (iteration from `⊥`, no seeds);
* **justified**: every write is below `F` of the state it was made against,
  `S (k+1) ⊆ S k ∪ F (S k)` (a write is the image of a modeled transfer on facts that were in the
  state; nothing enters from outside the model);
* **saturated**: `F (S n) ⊆ S n` (one more full round over the complete state adds nothing).

`Run.eq_kleene`: for a monotone `F`, such a run ends exactly at the least fixpoint.  Note what is
*not* assumed: the schedule, and ascent.  A descent (a write below the previous value) does not
break leastness under a monotone `F`; it is evidence that the executed transfer is not the
modeled monotone one (`Run.ascent_of_monotone` below says a monotone unit never descends).

Two counterexamples bound what a run can check about itself:

* `Seeded`: a monotone operator and a run that ascends from `∅` and saturates, but whose one write
  is not justified (a seed).  The result is a fixpoint, not the least.
* `Twin`: two operators `G` (not monotone) and `G'` (monotone) that agree on every state the run
  visits.  The run is justified, ascending and saturated for both.  It is the least fixpoint of
  `G'` and not of `G`, which has a fixpoint strictly below the result.  Hence no function of the
  trace decides leastness: monotonicity off the visited chain is the hypothesis a run cannot
  discharge, and the descent counter can only ever refute it.
-/

namespace ProofLean

open Finset

namespace BoundedOp

variable {α : Type*} [DecidableEq α] (o : BoundedOp α)

/-- A certified run of `o.F`: the chain of states a trace exhibits, with the three checkable
properties.  `n` is the number of writes. -/
structure Run (o : BoundedOp α) where
  S : ℕ → Finset α
  n : ℕ
  start : S 0 = ∅
  justified : ∀ k, k < n → S (k + 1) ⊆ S k ∪ o.F (S k)
  saturated : o.F (S n) ⊆ S n

namespace Run

variable {o}

/-- Every state of a justified run from `∅` lies below the least fixpoint. -/
theorem below_kleene (r : Run o) : ∀ k, k ≤ r.n → r.S k ⊆ o.kleene := by
  intro k
  induction k with
  | zero =>
    intro _
    rw [r.start]
    exact Finset.empty_subset _
  | succ k ih =>
    intro hk
    have h1 : r.S k ⊆ o.kleene := ih (by omega)
    calc r.S (k + 1) ⊆ r.S k ∪ o.F (r.S k) := r.justified k (by omega)
      _ ⊆ o.kleene ∪ o.F o.kleene := Finset.union_subset_union h1 (o.mono h1)
      _ = o.kleene := by rw [o.kleene_fixed, Finset.union_self]

/-- A saturated state is a pre-fixpoint, hence above the least fixpoint. -/
theorem kleene_subset (r : Run o) : o.kleene ⊆ r.S r.n :=
  o.kleene_isLeast.2 r.saturated

/-- **The certificate.** A run from `∅` whose writes are justified and whose final state is
saturated ends at the least fixpoint, whatever its schedule and whether or not it ever descended. -/
theorem eq_kleene (r : Run o) : r.S r.n = o.kleene :=
  Finset.Subset.antisymm (r.below_kleene r.n le_rfl) r.kleene_subset

/-- The final state is the least pre-fixpoint of `o.F` (Knaster–Tarski's characterization). -/
theorem isLeast (r : Run o) : IsLeast {Y : Finset α | o.F Y ⊆ Y} (r.S r.n) := by
  rw [r.eq_kleene]
  exact o.kleene_isLeast

/-- Leastness needs no round bound: `n` is unconstrained.  But a justified run cannot be longer
than the universe allows if every write adds something: this is the bound a trace can also show. -/
theorem final_subset_univ (r : Run o) : r.S r.n ⊆ o.U := by
  rw [r.eq_kleene]
  exact o.kleene_subset_univ

end Run

omit [DecidableEq α] in
/-- A unit transfer `T` that is monotone and is re-evaluated against a larger read set never
writes below its previous write: a descent witnesses a non-monotone transfer, a hidden input,
or a write that is not the transfer's output.  (Ascent is a *detector*, not a hypothesis of
`Run.eq_kleene`.) -/
theorem ascent_of_monotone (T : Finset α → Finset α) (hT : ∀ ⦃X Y : Finset α⦄, X ⊆ Y → T X ⊆ T Y)
    {R₁ R₂ : Finset α} (h : R₁ ⊆ R₂) : T R₁ ⊆ T R₂ :=
  hT h

end BoundedOp

namespace Certificate

/-- Two facts, as in `ProofLean.Counter`. -/
inductive Atom
  | a
  | b
deriving DecidableEq, Repr

open Atom

instance : Fintype Atom := ⟨{a, b}, fun x => by cases x <;> simp⟩

/-- The run both counterexamples share: `∅`, then `{a}`, then `{a, b}`. -/
def run : ℕ → Finset Atom
  | 0 => ∅
  | 1 => {a}
  | _ => {a, b}

/-! ## `Seeded`: ascent and saturation without justification -/

/-- A monotone operator whose least fixpoint is `{a}`. -/
def H (X : Finset Atom) : Finset Atom := if b ∈ X then {a, b} else {a}

theorem H_mono : ∀ X Y : Finset Atom, X ⊆ Y → H X ⊆ H Y := by decide

/-- The seeded run `∅ → {a, b}` ascends and is saturated for `H`. -/
theorem seeded_ascends_saturates : (∅ : Finset Atom) ⊆ {a, b} ∧ H {a, b} ⊆ {a, b} := by decide

/-- But its write is not justified: `{a, b} ⊄ ∅ ∪ H ∅`. -/
theorem seeded_not_justified : ¬ ({a, b} : Finset Atom) ⊆ ∅ ∪ H ∅ := by decide

/-- And it is not least: `{a}` is a fixpoint strictly below. -/
theorem seeded_not_least : H {a} = {a} ∧ ({a} : Finset Atom) ⊂ {a, b} := by decide

/-! ## `Twin`: a justified, ascending, saturated run that is least for `G'` and not for `G` -/

/-- Not monotone: `G {b} = {b}` while `G ∅ = {a}`. -/
def G (X : Finset Atom) : Finset Atom :=
  if X = {b} then {b} else if a ∈ X then {a, b} else {a}

/-- Monotone, and equal to `G` on `∅`, `{a}` and `{a, b}`. -/
def G' (X : Finset Atom) : Finset Atom := if a ∈ X ∨ b ∈ X then {a, b} else {a}

theorem G'_mono : ∀ X Y : Finset Atom, X ⊆ Y → G' X ⊆ G' Y := by decide

theorem G_not_monotone : ¬ Monotone G := by
  intro h
  have h2 : G ∅ ⊆ G {b} := h (Finset.empty_subset _)
  revert h2
  decide

/-- The two operators agree on every state the run visits. -/
theorem twins_agree : G (run 0) = G' (run 0) ∧ G (run 1) = G' (run 1) ∧ G (run 2) = G' (run 2) := by
  decide

/-- The run is justified and ascending for `G` (hence for `G'`), and saturated. -/
theorem run_justified_G :
    run 1 ⊆ run 0 ∪ G (run 0) ∧ run 2 ⊆ run 1 ∪ G (run 1) ∧ G (run 2) ⊆ run 2 := by decide

theorem run_ascends : run 0 ⊆ run 1 ∧ run 1 ⊆ run 2 := by decide

/-- `G'` as a bounded monotone operator on the full universe. -/
def oG' : BoundedOp Atom where
  F := G'
  U := Finset.univ
  mono := fun _ _ h => G'_mono _ _ h
  bound := fun _ _ => Finset.subset_univ _

/-- The same trace as a certified run of `G'`. -/
def runG' : BoundedOp.Run oG' where
  S := run
  n := 2
  start := rfl
  justified := by
    intro k hk
    rcases k with _ | _ | k
    · decide
    · decide
    · exact absurd hk (by omega)
  saturated := by decide

/-- For `G'` the certificate holds: the run ends at the least fixpoint `{a, b}`. -/
theorem run_least_for_G' : run 2 = oG'.kleene := runG'.eq_kleene

/-- For `G` it does not: `{b}` is a fixpoint of `G` strictly below the result. -/
theorem run_not_least_for_G : G {b} = {b} ∧ ({b} : Finset Atom) ⊂ run 2 := by decide

/-- **What a run cannot check about itself.** The trace `run` satisfies every runtime condition
(start at `∅`, justified writes, ascent, saturation) for both `G` and `G'`, which agree on all
visited states; it is least for the monotone twin and not for the other.  Leastness therefore
rests on monotonicity *off* the visited chain, a static property of the transfers. -/
theorem run_cannot_tell :
    (G (run 0) = G' (run 0) ∧ G (run 1) = G' (run 1) ∧ G (run 2) = G' (run 2)) ∧
    (run 1 ⊆ run 0 ∪ G (run 0) ∧ run 2 ⊆ run 1 ∪ G (run 1) ∧ G (run 2) ⊆ run 2) ∧
    (run 0 ⊆ run 1 ∧ run 1 ⊆ run 2) ∧
    run 2 = oG'.kleene ∧
    (G {b} = {b} ∧ ({b} : Finset Atom) ⊂ run 2) :=
  ⟨twins_agree, run_justified_G, run_ascends, run_least_for_G', run_not_least_for_G⟩

end Certificate

end ProofLean
