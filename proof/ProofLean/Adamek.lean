import ProofLean.Denotation
import Mathlib.Order.FixedPoints
import Mathlib.Order.OmegaCompletePartialOrder

/-!
# Trees never stop, sites do: the round loop is Adámek's chain

On the lattice of tree sets (what `Ty` values are: finite types, or sets of finite trees), the
Kleene chain `Φ^n(⊥)` of a recursive program is Adámek's initial chain `⊥ → F⊥ → F²⊥ → …`.

* `Xstar_eq_iSup_iterate`: `Φ` is ω-continuous (every condition is a finite conjunction of
  memberships), so by Kleene's theorem the least solution is the supremum of the chain.
* For the `self` shape (`R = String | Array[R] | Hash[Symbol, R]`) the chain **ascends strictly
  forever** and **no finite stage is the least solution** (`self_iterate_lt`, `self_iterate_ne`):
  the depth bound of round `n` excludes `Array^n[String]`.  This is F16's "μ-types alone give no
  finite height", machine-checked, and it is why a loop over tree-shaped types needs caps, bounds or
  widening.
* The site iteration of the same program stops after at most `|dsts| · |sites|` rounds
  (`Prog.solveN_rounds_le`), and its grammar's language **is** the least solution
  (`self_exact`): the finite site graph presents the whole infinite chain's limit.  In
  coalgebraic terms the site graph is a finite automaton whose language is the least (inductive)
  solution; the rational fixpoint is its coinductive reading.
-/

set_option linter.unusedSectionVars false

namespace ProofLean

open OmegaCompletePartialOrder

universe u v

variable {V : Type u} {S : Type v} [DecidableEq V] [DecidableEq S]

/-! ## Kleene's theorem for the set constraints -/

/-- Finitely many monotone witnesses over a list have a common index. -/
theorem exists_common_list {β : Type*} {Q : β → ℕ → Prop}
    (hmono : ∀ b j k, j ≤ k → Q b j → Q b k) :
    ∀ l : List β, (∀ b ∈ l, ∃ k, Q b k) → ∃ k, ∀ b ∈ l, Q b k
  | [], _ => ⟨0, by simp⟩
  | b :: l, h => by
    obtain ⟨k1, hk1⟩ := h b List.mem_cons_self
    obtain ⟨k2, hk2⟩ := exists_common_list hmono l (fun b hb => h b (List.mem_cons_of_mem _ hb))
    refine ⟨max k1 k2, fun b' hb' => ?_⟩
    rcases List.mem_cons.1 hb' with rfl | hb'
    · exact hmono _ _ _ (le_max_left _ _) hk1
    · exact hmono _ _ _ (le_max_right _ _) (hk2 b' hb')

/-- Finitely many monotone witnesses over `Fin n` have a common index. -/
theorem exists_common_fin {n : ℕ} {Q : Fin n → ℕ → Prop}
    (hmono : ∀ b j k, j ≤ k → Q b j → Q b k) (h : ∀ b, ∃ k, Q b k) : ∃ k, ∀ b, Q b k := by
  obtain ⟨k, hk⟩ := exists_common_list hmono (List.finRange n) (fun b _ => h b)
  exact ⟨k, fun b => hk b (List.mem_finRange b)⟩

section Continuity

variable (P : Prog V S) (σ : Sig V S)

/-- The set constraints are ω-continuous: whatever holds of the union of a chain holds at some
stage. -/
theorem Phi_omega (c : Chain (V → Set (STree σ.ar))) :
    Phi P σ (⨆ i, c i) ≤ ⨆ i, Phi P σ (c i) := by
  have hmono : ∀ {i j : ℕ}, i ≤ j → c i ≤ c j := fun h => c.monotone h
  have memSup : ∀ (w : V) (t : STree σ.ar), t ∈ (⨆ i, c i) w ↔ ∃ i, t ∈ c i w := by
    intro w t
    rw [iSup_apply, Set.iSup_eq_iUnion, Set.mem_iUnion]
  intro v t ht
  rw [iSup_apply, Set.iSup_eq_iUnion, Set.mem_iUnion]
  have hit : ∀ cs : List (V × S), (∀ x ∈ cs, Hit σ (⨆ i, c i) x) →
      ∃ k, ∀ x ∈ cs, Hit σ (c k) x := by
    intro cs hcs
    apply exists_common_list (Q := fun x k => Hit σ (c k) x)
    · rintro x j k hjk ⟨ch, hx⟩; exact ⟨ch, hmono hjk _ hx⟩
    · intro x hx
      obtain ⟨ch, hch⟩ := hcs x hx
      obtain ⟨k, hk⟩ := (memSup _ _).1 hch
      exact ⟨k, ch, hk⟩
  rcases ht with ⟨a, ha, hv, hc, ch, rfl, hch⟩ | ⟨g, hg, hv, hc, hs, h, ch, rfl, hp⟩
  · obtain ⟨k1, hk1⟩ := hit _ hc
    obtain ⟨k2, hk2⟩ := exists_common_fin
      (Q := fun i k => ChildOK σ (c k) a.site i (ch i))
      (by
        rintro i j k hjk (h1 | h1)
        · exact Or.inl (hmono hjk _ h1)
        · exact Or.inr h1)
      (by
        intro i
        rcases hch i with h1 | h1
        · obtain ⟨k, hk⟩ := (memSup _ _).1 h1
          exact ⟨k, Or.inl hk⟩
        · exact ⟨0, Or.inr h1⟩)
    refine ⟨max k1 k2, Or.inl ⟨a, ha, hv, fun x hx => ?_, ch, rfl, fun i => ?_⟩⟩
    · obtain ⟨ch', h'⟩ := hk1 x hx
      exact ⟨ch', hmono (le_max_left _ _) _ h'⟩
    · rcases hk2 i with h1 | h1
      · exact Or.inl (hmono (le_max_right _ _) _ h1)
      · exact Or.inr h1
  · obtain ⟨k1, hk1⟩ := hit _ hc
    obtain ⟨k2, hk2⟩ := (memSup _ _).1 hs
    refine ⟨max k1 k2, Or.inr ⟨g, hg, hv, fun x hx => ?_, hmono (le_max_right _ _) _ hk2,
      h, ch, rfl, hp⟩⟩
    obtain ⟨ch', h'⟩ := hk1 x hx
    exact ⟨ch', hmono (le_max_left _ _) _ h'⟩

theorem Phi_omegaScott : ωScottContinuous (PhiHom P σ) := by
  rw [ωScottContinuous_iff_map_ωSup_of_orderHom]
  intro c
  apply le_antisymm
  · calc (PhiHom P σ) (ωSup c) ≤ (PhiHom P σ) (⨆ i, c i) :=
          (PhiHom P σ).mono (ωSup_le c _ (fun i => le_iSup (fun i => c i) i))
      _ ≤ ⨆ i, (PhiHom P σ) (c i) := Phi_omega P σ c
      _ ≤ ωSup (c.map (PhiHom P σ)) := iSup_le (fun i => le_ωSup (c.map (PhiHom P σ)) i)
  · exact ωSup_le _ _ (fun i => (PhiHom P σ).mono (le_ωSup c i))

/-- **Kleene / Adámek.** The least solution of the set constraints is the supremum of the round
chain `Φ^n(⊥)`. -/
theorem Xstar_eq_iSup_iterate : Xstar P σ = ⨆ n, (PhiHom P σ)^[n] ⊥ :=
  fixedPoints.lfp_eq_sSup_iterate _ (Phi_omegaScott P σ)

end Continuity

/-! ## The `self` shape -/

namespace SelfShape

/-- Slots: the return `R`, the Array element cell, and the Hash key and value cells. -/
inductive Slot
  | R
  | elem
  | key
  | value
deriving DecidableEq, Repr

/-- Sites: String and Symbol atoms, one Array and one Hash construction site. -/
inductive Site
  | str
  | sym
  | arr
  | hsh
deriving DecidableEq, Repr

def ar : Site → ℕ
  | .arr => 1
  | .hsh => 2
  | _ => 0

/-- Containers have optional fields (they may be empty). -/
def σ : Sig Slot Site where
  ar := ar
  cell h i := match h, i with
    | .arr, _ => .elem
    | .hsh, i => if i.val = 0 then .key else .value
    | .str, i => absurd i.isLt (by simp [ar])
    | .sym, i => absurd i.isLt (by simp [ar])
  req _ _ := false

/-- `R = String | Array[R] | Hash[Symbol, R]`, lowered to sites. -/
def P : Prog Slot Site where
  allocs := [⟨[], .R, .str⟩, ⟨[], .R, .arr⟩, ⟨[], .R, .hsh⟩, ⟨[], .key, .sym⟩]
  guards := [⟨[], .R, .elem, fun _ => true⟩, ⟨[], .R, .value, fun _ => true⟩]

/-- `Within n t`: every path of `t` has at most `n` nodes. -/
def Within : ℕ → STree σ.ar → Prop
  | _, .empty => True
  | 0, .node _ _ => False
  | n + 1, .node _ ch => ∀ i, Within n (ch i)

theorem within_empty (n : ℕ) : Within n (.empty : STree σ.ar) := by
  cases n <;> trivial

theorem within_succ : ∀ (n : ℕ) (t : STree σ.ar), Within n t → Within (n + 1) t
  | _, .empty, _ => trivial
  | 0, .node _ _, h => h.elim
  | n + 1, .node _ ch, h => fun i => within_succ n (ch i) (h i)

/-- Round `n` of the tree chain only holds trees with at most `n` nodes per path. -/
theorem iterate_within : ∀ (n : ℕ) (v : Slot) (t : STree σ.ar),
    t ∈ (PhiHom P σ)^[n] ⊥ v → Within n t := by
  intro n
  induction n with
  | zero => intro v t ht; exact ht.elim
  | succ n ih =>
    intro v t ht
    rw [Function.iterate_succ_apply'] at ht
    rcases ht with ⟨a, -, -, -, ch, rfl, hch⟩ | ⟨g, -, -, -, hs, -, -, -, -⟩
    · intro i
      rcases hch i with h1 | ⟨h1, -⟩
      · exact ih _ _ h1
      · rw [h1]; exact within_empty n
    · exact within_succ n t (ih _ _ hs)

/-- `Array^k[String]`. -/
def arrays : ℕ → STree σ.ar
  | 0 => .node .str (fun i => absurd i.isLt (by simp [σ, ar]))
  | k + 1 => .node .arr (fun _ => arrays k)

theorem arrays_not_within : ∀ k, ¬ Within k (arrays k)
  | 0 => fun h => h
  | k + 1 => fun h => arrays_not_within k (h ⟨0, by simp [σ, ar]⟩)

theorem arrays_mem : ∀ k, arrays k ∈ Xstar P σ .R := by
  intro k
  induction k with
  | zero =>
    rw [← Xstar_fixed]
    exact Or.inl ⟨⟨[], .R, .str⟩, by simp [P], rfl, by simp, _, rfl,
      fun i => absurd i.isLt (by simp [σ, ar])⟩
  | succ k ih =>
    have helem : arrays k ∈ Xstar P σ .elem := by
      rw [← Xstar_fixed]
      refine Or.inr ⟨⟨[], .R, .elem, fun _ => true⟩, by simp [P], rfl, by simp, ih, ?_⟩
      cases k with
      | zero => exact ⟨.str, _, rfl, rfl⟩
      | succ k => exact ⟨.arr, _, rfl, rfl⟩
    rw [← Xstar_fixed]
    exact Or.inl ⟨⟨[], .R, .arr⟩, by simp [P], rfl, by simp, _, rfl, fun _ => Or.inl helem⟩

/-- **No finite stage of the tree chain is the least solution.** -/
theorem self_iterate_ne (n : ℕ) : (PhiHom P σ)^[n] ⊥ ≠ Xstar P σ := by
  intro h
  have hm := arrays_mem n
  rw [← h] at hm
  exact arrays_not_within n (iterate_within n _ _ hm)

/-- Every stage of the tree chain is below the least solution. -/
theorem iterate_le_Xstar (n : ℕ) : (PhiHom P σ)^[n] ⊥ ≤ Xstar P σ := by
  induction n with
  | zero => exact bot_le
  | succ n ih =>
    rw [Function.iterate_succ_apply']
    calc (PhiHom P σ) ((PhiHom P σ)^[n] ⊥) ≤ (PhiHom P σ) (Xstar P σ) := (PhiHom P σ).mono ih
      _ = Xstar P σ := Xstar_fixed P σ

/-- **The tree chain ascends strictly forever** (an infinite strictly ascending chain). -/
theorem self_iterate_lt (n : ℕ) : (PhiHom P σ)^[n] ⊥ < (PhiHom P σ)^[n + 1] ⊥ := by
  have hle : (PhiHom P σ)^[n] ⊥ ≤ (PhiHom P σ)^[n + 1] ⊥ := by
    have : ∀ m, (PhiHom P σ)^[m] ⊥ ≤ (PhiHom P σ)^[m + 1] ⊥ := by
      intro m
      induction m with
      | zero => exact bot_le
      | succ m ih =>
        rw [Function.iterate_succ_apply', Function.iterate_succ_apply' (n := m + 1)]
        exact (PhiHom P σ).mono ih
    exact this n
  refine lt_of_le_of_ne hle (fun heq => self_iterate_ne n ?_)
  apply le_antisymm (iterate_le_Xstar n)
  apply OrderHom.lfp_le_fixed
  rw [Function.iterate_succ_apply'] at heq
  exact heq.symm

/-- **The site iteration presents the limit exactly**: no condition anywhere, so the plain site
solution's grammar is the least solution of the set constraints, and it is reached within
`|dsts| · |sites|` rounds. -/
theorem self_exact : Xstar P σ = langPlain P σ ∧ P.solveN.2 ≤ P.dsts.card * P.sites.card := by
  refine ⟨lfp_eq_lang_plain_of_no_required P σ (fun c hc i => rfl), P.solveN_rounds_le.2⟩

end SelfShape

end ProofLean
