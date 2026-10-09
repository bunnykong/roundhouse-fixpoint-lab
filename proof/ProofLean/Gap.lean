import ProofLean.Denotation

/-!
# The productivity side condition of goal D is necessary

The plain site operator (the relational engine, `Prog.solve`) fires a condition on a site as soon as
the site reaches the slot, even when the site can never build a finite value.  The set-constraint
semantics fires it only when the slot holds a tree rooted at that site.  Here is a three-slot program
where the two differ at the level of languages, not just facts.

Ruby reading: `x = { a: 1, b: diverge() }; out = x[:a]`.  The record is never built (its required
field `b` has no value), so `out` is never assigned: the least solution of the set constraints gives
`out` the empty language, while the plain grammar gives it `Integer`.  The plain answer is sound
(an over-approximation on dead code) but not the least solution.
-/

namespace ProofLean.Gap

/-- Slots: the record variable, the two field cells, and the projection's result. -/
inductive Slot
  | x
  | c1
  | c2
  | out
deriving DecidableEq, Repr

/-- Sites: a record with two required fields, and the Integer atom. -/
inductive Site
  | record
  | int
deriving DecidableEq, Repr

/-- Arities. -/
def ar : Site → ℕ
  | .record => 2
  | .int => 0

/-- The signature: the record's fields are cells `c1` and `c2`, both required. -/
def σ : Sig Slot Site where
  ar := ar
  cell h i := match h, i with
    | .record, i => if i.val = 0 then .c1 else .c2
    | .int, i => i.elim0
  req h _ := match h with
    | .record => true
    | .int => false

/-- `x ∋ record`, `c1 ∋ Integer`, and the load `out ⊇ x.a` as a guard on `(x, record)`. -/
def P : Prog Slot Site where
  allocs := [⟨[], .x, .record⟩, ⟨[], .c1, .int⟩]
  guards := [⟨[(.x, .record)], .c1, .out, fun _ => true⟩]

theorem mem_solve_of_step {p : Slot × Site} (h : p ∈ P.stepSet ↑P.solve) : p ∈ P.solve := by
  rw [← P.coe_step, P.solve_fixed] at h; exact h

/-- The plain solution types the projection as `Integer`. -/
theorem out_int_in_plain : (Slot.out, Site.int) ∈ P.solve := by
  have hx : (Slot.x, Site.record) ∈ P.solve :=
    mem_solve_of_step (Or.inl ⟨⟨[], .x, .record⟩, by simp [P], by simp, rfl⟩)
  have hc : (Slot.c1, Site.int) ∈ P.solve :=
    mem_solve_of_step (Or.inl ⟨⟨[], .c1, .int⟩, by simp [P], by simp, rfl⟩)
  exact mem_solve_of_step (Or.inr ⟨⟨[(.x, .record)], .c1, .out, fun _ => true⟩, by simp [P],
    by simpa using hx, rfl, hc, rfl⟩)

/-- The Integer leaf as a tree. -/
def intTree : STree σ.ar := .node .int (fun i => absurd i.isLt (by simp [σ, ar]))

/-- Its membership in the plain grammar's language of `out`. -/
theorem intTree_in_plain : intTree ∈ langPlain P σ .out := by
  show Mem σ ↑P.solve .out intTree
  rw [intTree, mem_node]
  exact ⟨Finset.mem_coe.2 out_int_in_plain, fun i => absurd i.isLt (by simp [σ, ar])⟩

/-- A pre-fixpoint of the set constraints in which `out` is empty. -/
def Y : Slot → Set (STree σ.ar)
  | .c1 => {t | ∃ ch, t = .node .int ch}
  | _ => ∅

theorem Phi_Y_le : Phi P σ Y ≤ Y := by
  intro v t ht
  rcases ht with ⟨a, ha, rfl, -, ch, rfl, hch⟩ | ⟨g, hg, rfl, hc, -, -⟩
  · simp only [P, List.mem_cons, List.not_mem_nil, or_false] at ha
    rcases ha with rfl | rfl
    · -- the record needs a value in its required cell `c2`, which `Y` leaves empty
      exfalso
      rcases hch ⟨1, by decide⟩ with h | ⟨-, h⟩
      · exact h
      · exact absurd h (by decide)
    · exact ⟨ch, rfl⟩
  · simp only [P, List.mem_cons, List.not_mem_nil, or_false] at hg
    subst hg
    obtain ⟨ch, hch⟩ := hc (.x, .record) (by simp)
    exact hch.elim

/-- The least solution of the set constraints gives `out` the empty language. -/
theorem xstar_out_empty : Xstar P σ .out = ∅ := by
  have h : Xstar P σ ≤ Y := OrderHom.lfp_le _ Phi_Y_le
  exact Set.subset_eq_empty (h .out) rfl

/-- **The gap.** The plain grammar's language strictly contains the least solution of the set
constraints, so goal D's exact equality needs the productivity refinement or the side condition of
`ptPlus_eq_solve_of_productive`. -/
theorem plain_ne_exact : Xstar P σ ≠ langPlain P σ := by
  intro h
  have := intTree_in_plain
  rw [← h, xstar_out_empty] at this
  exact this

end ProofLean.Gap
