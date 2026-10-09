import ProofLean.Core

/-!
# Incremental inference is two jobs (the relational model)

* **Additions are exact.**  If an edit only adds rules (new call targets, new writes, new bodies),
  the old least solution lies below the new one, so restarting the new program's iteration from the
  old solution (a warm start) reaches exactly the new least solution (`incremental_add`).  This is
  "re-type only what changed" for additive edits.
* **Deletions are not.**  Removing a rule can leave a cycle that supports itself: the old solution
  is still a fixpoint of the new program but not its least one (`deletion_keeps_cycle`).  A
  deletion needs rederivation (DRed, or a rebuild of the affected component), as the relational model shows.
-/

set_option linter.unusedSectionVars false

namespace ProofLean

variable {V S : Type*} [DecidableEq V] [DecidableEq S]

namespace Prog

/-- `P'` extends `P`: it keeps every rule of `P`. -/
def Extends (P P' : Prog V S) : Prop := (∀ a ∈ P.allocs, a ∈ P'.allocs) ∧ (∀ g ∈ P.guards, g ∈ P'.guards)

theorem stepSet_mono_prog {P P' : Prog V S} (h : Extends P P') (X : Set (V × S)) :
    P.stepSet X ⊆ P'.stepSet X := by
  intro p hp
  rcases hp with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h1, h2, h3⟩
  · exact Or.inl ⟨a, h.1 a ha, hc, rfl⟩
  · exact Or.inr ⟨g, h.2 g hg, hc, h1, h2, h3⟩

/-- Adding rules can only add facts. -/
theorem solve_mono_prog {P P' : Prog V S} (h : Extends P P') : P.solve ⊆ P'.solve := by
  have h1 : (↑P.solve : Set (V × S)) ⊆ ↑P'.solve := by
    rw [P.solve_eq_lfp, P'.solve_eq_lfp]
    apply OrderHom.lfp_le
    calc P.stepHom (OrderHom.lfp P'.stepHom) ⊆ P'.stepHom (OrderHom.lfp P'.stepHom) :=
          stepSet_mono_prog h _
      _ = OrderHom.lfp P'.stepHom := OrderHom.map_lfp _
  exact fun p hp => h1 hp

/-- The old solution is a valid seed for the new program: below `F'` of itself. -/
theorem old_le_step_new {P P' : Prog V S} (h : Extends P P') : P.solve ⊆ P'.step P.solve := by
  intro p hp
  have : p ∈ P.step P.solve := by rw [P.solve_fixed]; exact hp
  exact P'.mem_step.2 (stepSet_mono_prog h _ (P.mem_step.1 this))

/-- The old solution lies in the new universe. -/
theorem old_subset_univ_new {P P' : Prog V S} (h : Extends P P') : P.solve ⊆ P'.univ :=
  (solve_mono_prog h).trans P'.toOp.kleene_subset_univ

/-- **Additions are exact.**  Warm-starting the extended program from the old solution reaches
exactly the new least solution. -/
theorem incremental_add {P P' : Prog V S} (h : Extends P P') :
    (P'.toOp.kleeneAux P.solve (old_subset_univ_new h) (old_le_step_new h)).1 = P'.solve :=
  P'.toOp.kleeneAux_eq_kleene_of_le _ _ _ (solve_mono_prog h)

end Prog

/-! ## Deletions: a cycle that supports itself -/

namespace Deletion

/-- Two slots that flow into each other, and one site. -/
inductive Slot
  | x
  | y
deriving DecidableEq

/-- Before the edit: `x` is seeded with the site, and `x`, `y` feed each other. -/
def before : Prog Slot Unit where
  allocs := [⟨[], .x, ()⟩]
  guards := [⟨[], .x, .y, fun _ => true⟩, ⟨[], .y, .x, fun _ => true⟩]

/-- After the edit: the seed is deleted; the cycle stays. -/
def after : Prog Slot Unit where
  allocs := []
  guards := before.guards

theorem mem_before (p : Slot × Unit) : p ∈ before.solve := by
  have hx : (Slot.x, ()) ∈ before.solve := by
    rw [← before.solve_fixed]
    exact before.mem_step.2 (Or.inl ⟨⟨[], .x, ()⟩, by simp [before], by simp, rfl⟩)
  have hy : (Slot.y, ()) ∈ before.solve := by
    rw [← before.solve_fixed]
    exact before.mem_step.2 (Or.inr ⟨⟨[], .x, .y, fun _ => true⟩, by simp [before], by simp, rfl,
      hx, rfl⟩)
  obtain ⟨v, ⟨⟩⟩ := p
  cases v
  · exact hx
  · exact hy

/-- The new least solution is empty: nothing seeds the cycle any more. -/
theorem after_solve_empty : after.solve = ∅ := by
  apply Finset.subset_empty.1
  apply after.solve_isLeast.2
  intro p hp
  rcases after.mem_step.1 hp with ⟨a, ha, -, -⟩ | ⟨g, -, -, -, h2, -⟩
  · simp [after] at ha
  · simp at h2

/-- **Deletions are not exact.**  The old solution is still a fixpoint of the edited program (the
cycle supports itself), so a warm start from it never moves, yet the edited program's least
solution is empty. -/
theorem deletion_keeps_cycle :
    after.step before.solve = before.solve ∧ before.solve ≠ after.solve := by
  constructor
  · ext p
    constructor
    · intro _; exact mem_before p
    · intro _
      obtain ⟨v, ⟨⟩⟩ := p
      cases v
      · exact after.mem_step.2 (Or.inr ⟨⟨[], .y, .x, fun _ => true⟩, by simp [after, before],
          by simp, rfl, mem_before _, rfl⟩)
      · exact after.mem_step.2 (Or.inr ⟨⟨[], .x, .y, fun _ => true⟩, by simp [after, before],
          by simp, rfl, mem_before _, rfl⟩)
  · rw [after_solve_empty]
    intro h
    have := mem_before (Slot.x, ())
    rw [h] at this
    simp at this

end Deletion

end ProofLean
