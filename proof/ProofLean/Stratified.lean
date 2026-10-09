import ProofLean.Core

/-!
# Dependency-ordered evaluation is exact (DESIGN v0.6: dependency-ordered queries with delta kernels)

Give every slot a rank such that a rule's premises (its conditions and its source) never have a
higher rank than its conclusion: the condensation order of the slot graph, with each strongly
connected component at one rank.  Then solving rank by rank, each rank to its own least fixpoint
with the lower ranks frozen, computes exactly the global least solution (`layer_eq_solve`, a finite
form of Bekić's lemma).  When premises are strictly lower (an acyclic part), each rank's local
iteration takes at most one round (`strict_one_round`): the 64-link chain needs one evaluation per
slot, the count the control experiment measured.
-/

set_option linter.unusedSectionVars false

namespace ProofLean

variable {V S : Type*} [DecidableEq V] [DecidableEq S]

namespace Prog

variable (P : Prog V S) (rk : V → ℕ)

/-- Premises never outrank conclusions. -/
def Ranked : Prop :=
  (∀ a ∈ P.allocs, ∀ c ∈ a.conds, rk c.1 ≤ rk a.dst) ∧
  (∀ g ∈ P.guards, rk g.src ≤ rk g.dst ∧ ∀ c ∈ g.conds, rk c.1 ≤ rk g.dst)

/-- Premises are strictly below conclusions (an acyclic program, ranked topologically). -/
def StrictRanked : Prop :=
  (∀ a ∈ P.allocs, ∀ c ∈ a.conds, rk c.1 < rk a.dst) ∧
  (∀ g ∈ P.guards, rk g.src < rk g.dst ∧ ∀ c ∈ g.conds, rk c.1 < rk g.dst)

/-- The rank-`r` facts derivable in one step from the frozen lower layer `L` and the current
rank-`r` facts `Y`. -/
def localStep (L : Finset (V × S)) (r : ℕ) (Y : Finset (V × S)) : Finset (V × S) :=
  (P.step (L ∪ Y)).filter (fun p => rk p.1 = r)

/-- The local operator of rank `r`. -/
def localOp (L : Finset (V × S)) (hL : L ⊆ P.univ) (r : ℕ) : BoundedOp (V × S) where
  F := P.localStep rk L r
  U := P.univ
  mono := fun _ _ h => Finset.filter_subset_filter _ (P.step_mono (Finset.union_subset_union le_rfl h))
  bound := fun _ hX => (Finset.filter_subset _ _).trans (P.step_bound (Finset.union_subset hL hX))

/-- The layers: rank by rank, each solved to its local least fixpoint. -/
def layer : ℕ → {L : Finset (V × S) // L ⊆ P.univ}
  | 0 => ⟨∅, Finset.empty_subset _⟩
  | r + 1 =>
    let L := layer r
    ⟨L.1 ∪ (P.localOp rk L.1 L.2 r).kleene,
      Finset.union_subset L.2 (P.localOp rk L.1 L.2 r).kleene_subset_univ⟩

theorem solve_closed {p : V × S} (h : p ∈ P.step P.solve) : p ∈ P.solve := by
  rw [P.solve_fixed] at h; exact h

/-- **Each layer is exactly the least solution below its rank.** -/
theorem layer_spec (hrk : P.Ranked rk) :
    ∀ r, (P.layer rk r).1 = P.solve.filter (fun p => rk p.1 < r) := by
  intro r
  induction r with
  | zero => simp [layer]
  | succ r ih =>
    set L := P.layer rk r with hLdef
    set o := P.localOp rk L.1 L.2 r with hodef
    have hL : L.1 = P.solve.filter (fun p => rk p.1 < r) := ih
    have hLsub : L.1 ⊆ P.solve := by rw [hL]; exact Finset.filter_subset _ _
    -- the local fixpoint is inside the solution, at rank r
    have hKsub : o.kleene ⊆ P.solve.filter (fun p => rk p.1 = r) := by
      apply o.kleene_isLeast.2
      intro p hp
      simp only [hodef, localOp, localStep, Finset.mem_filter] at hp ⊢
      refine ⟨P.solve_closed (P.step_mono ?_ hp.1), hp.2⟩
      exact Finset.union_subset hLsub (Finset.filter_subset _ _)
    have hKfix : P.localStep rk L.1 r o.kleene = o.kleene := o.kleene_fixed
    -- every solution fact below rank r + 1 is in the new layer
    have hcover : P.solve ⊆ L.1 ∪ o.kleene ∪ P.solve.filter (fun p => r < rk p.1) := by
      apply P.solve_isLeast.2
      intro p hp
      have hM : L.1 ∪ o.kleene ∪ P.solve.filter (fun p => r < rk p.1) ⊆ P.solve :=
        Finset.union_subset (Finset.union_subset hLsub ((hKsub).trans (Finset.filter_subset _ _)))
          (Finset.filter_subset _ _)
      have hpsol : p ∈ P.solve := P.solve_closed (P.step_mono hM hp)
      -- premises of rank at most rk p.1 lie in the lower parts
      have hprem : ∀ q ∈ L.1 ∪ o.kleene ∪ P.solve.filter (fun p => r < rk p.1), rk q.1 ≤ r →
          q ∈ L.1 ∪ o.kleene := by
        intro q hq hqr
        rcases Finset.mem_union.1 hq with hq | hq
        · exact hq
        · exact absurd (Finset.mem_filter.1 hq).2 (by omega)
      rcases lt_trichotomy (rk p.1) r with hlt | heq | hgt
      · -- below rank r: derived from facts of rank < r, all in L
        apply Finset.mem_union_left; apply Finset.mem_union_left
        rw [hL, Finset.mem_filter]
        exact ⟨hpsol, hlt⟩
      · -- at rank r: derived from L and the local fixpoint
        apply Finset.mem_union_left; apply Finset.mem_union_right
        rw [← hKfix]
        simp only [localStep, Finset.mem_filter]
        refine ⟨?_, heq⟩
        rcases P.mem_step.1 hp with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h1, h2, h3⟩
        · exact P.mem_step.2 (Or.inl ⟨a, ha, fun c hcc => Finset.mem_coe.2
            (hprem c (hc c hcc) (by have := hrk.1 a ha c hcc; simp at heq; omega)), rfl⟩)
        · refine P.mem_step.2 (Or.inr ⟨g, hg, fun c hcc => Finset.mem_coe.2
            (hprem c (hc c hcc) ?_), h1, Finset.mem_coe.2 (hprem _ h2 ?_), h3⟩)
          · have := (hrk.2 g hg).2 c hcc; rw [← h1] at this; omega
          · have := (hrk.2 g hg).1; rw [← h1] at this; dsimp only; omega
      · apply Finset.mem_union_right
        exact Finset.mem_filter.2 ⟨hpsol, hgt⟩
    -- conclude
    show L.1 ∪ o.kleene = P.solve.filter (fun p => rk p.1 < r + 1)
    ext p
    simp only [Finset.mem_union, Finset.mem_filter]
    constructor
    · rintro (hp | hp)
      · rw [hL, Finset.mem_filter] at hp; exact ⟨hp.1, by omega⟩
      · have := Finset.mem_filter.1 (hKsub hp); exact ⟨this.1, by omega⟩
    · rintro ⟨hp, hpr⟩
      rcases Finset.mem_union.1 (hcover hp) with hq | hq
      · rcases Finset.mem_union.1 hq with hq | hq
        · exact Or.inl hq
        · exact Or.inr hq
      · exact absurd (Finset.mem_filter.1 hq).2 (by omega)

/-- **Dependency-ordered evaluation is exact.**  Once every slot of the universe is below rank
`R`, the layers have computed the least solution. -/
theorem layer_eq_solve (hrk : P.Ranked rk) {R : ℕ} (hR : ∀ p ∈ P.univ, rk p.1 < R) :
    (P.layer rk R).1 = P.solve := by
  rw [P.layer_spec rk hrk R]
  ext p
  simp only [Finset.mem_filter, and_iff_left_iff_imp]
  exact fun hp => hR p (P.toOp.kleene_subset_univ hp)

/-- The local step of an acyclic program does not read the rank-`r` facts it is building. -/
theorem local_const (hrk : P.StrictRanked rk) (L : Finset (V × S)) (r : ℕ) (Y : Finset (V × S))
    (hY : ∀ q ∈ Y, rk q.1 = r) : P.localStep rk L r Y = P.localStep rk L r ∅ := by
  ext p
  simp only [localStep, Finset.mem_filter, Finset.union_empty]
  constructor
  · rintro ⟨hp, hpr⟩
    refine ⟨?_, hpr⟩
    have inL : ∀ q ∈ L ∪ Y, rk q.1 < r → q ∈ L := by
      intro q hq hqr
      rcases Finset.mem_union.1 hq with h | h
      · exact h
      · exact absurd (hY q h) (by omega)
    rcases P.mem_step.1 hp with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h1, h2, h3⟩
    · refine P.mem_step.2 (Or.inl ⟨a, ha, fun c hcc => Finset.mem_coe.2 (inL c (hc c hcc) ?_), rfl⟩)
      have := hrk.1 a ha c hcc; simp only at hpr; omega
    · refine P.mem_step.2 (Or.inr ⟨g, hg, fun c hcc => Finset.mem_coe.2 (inL c (hc c hcc) ?_), h1,
        Finset.mem_coe.2 (inL _ h2 ?_), h3⟩)
      · have := (hrk.2 g hg).2 c hcc; rw [← h1] at this; omega
      · have := (hrk.2 g hg).1; rw [← h1] at this; dsimp only; omega
  · rintro ⟨hp, hpr⟩
    exact ⟨P.step_mono Finset.subset_union_left hp, hpr⟩

/-- **On an acyclic (strictly ranked) program, each rank's local iteration takes at most one
round:** one evaluation per slot. -/
theorem strict_one_round (hrk : P.StrictRanked rk) (L : Finset (V × S)) (hL : L ⊆ P.univ) (r : ℕ) :
    (P.localOp rk L hL r).kleeneN.2 ≤ 1 := by
  apply BoundedOp.kleeneN_rounds_le_one
  show P.localStep rk L r (P.localStep rk L r ∅) = P.localStep rk L r ∅
  apply P.local_const rk hrk L r
  intro q hq
  exact (Finset.mem_filter.1 hq).2

/-- A strictly ranked program is ranked. -/
theorem StrictRanked.ranked {P : Prog V S} {rk : V → ℕ} (h : P.StrictRanked rk) : P.Ranked rk :=
  ⟨fun a ha c hc => le_of_lt (h.1 a ha c hc),
    fun g hg => ⟨le_of_lt (h.2 g hg).1, fun c hc => le_of_lt ((h.2 g hg).2 c hc)⟩⟩

end Prog

end ProofLean
