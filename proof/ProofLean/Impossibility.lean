import Mathlib.Order.FixedPoints
import Mathlib.Data.Set.Image

/-!
# T10: no history-only backstop is exact on all finite chains

A *backstop* watches one slot at a time.  At each round it sees that slot's own value history
(newest first, including the candidate value of this round) and either lets the candidate through
or widens it by joining a value `w` it chooses.  Values accumulate, so a widening is sticky.  The
backstop may depend on anything in the history (its length, so the round number, included) but
not on the program's equations or dependency graph: that is what "history-only" means.

* `R`: one slot, `X = Int | Array[X]` (recursive).
* `C N`: slots `F₀ … F_N`, `F_i = Int | Array[F_{i+1}]`, `F_N = Int` (an acyclic chain).

`T10`: if a backstop makes `R` stop at round `K`, then on the chain `C K` the value of `F₀`
contains `Array^(K+1)[Int]` from round `K` on, forever, while the least solution of `C K` does not:
the run is never exact.  The proof makes the T10 observation precise: up to
round `K`, slot `F₀` of `C K` has exactly the history of `R`'s slot, so the backstop does the same
thing on both, and what made `R` stop (a value closed under `Array[·]`) is too big for the chain.

Origins escape the theorem: they look at the dependency graph (`C K` is acyclic), not at histories,
and the site analysis computes both least solutions exactly (`ProofLean.Core`).
-/

namespace ProofLean.Impossibility

/-- Types of the example: `Int`, and `Array[t]`. -/
inductive Ty
  | int
  | arr (t : Ty)
deriving DecidableEq

open Ty

/-- `Array^j[Int]`. -/
def nest : ℕ → Ty
  | 0 => int
  | j + 1 => arr (nest j)

theorem nest_injective : Function.Injective nest := by
  intro a b h
  induction a generalizing b with
  | zero => cases b with
    | zero => rfl
    | succ b => simp [nest] at h
  | succ a ih => cases b with
    | zero => simp [nest] at h
    | succ b =>
      simp only [nest, arr.injEq] at h
      rw [ih h]

/-- One round of a slot system over sets of types. -/
abbrev System (ι : Type) := (ι → Set Ty) → ι → Set Ty

/-- The recursive slot `X = Int | Array[X]`. -/
def R : System Unit := fun Y _ => {int} ∪ arr '' Y ()

/-- The acyclic chain of length `N` (slots beyond `N` behave like `F_N`). -/
def C (N : ℕ) : System ℕ := fun Y i => if i < N then {int} ∪ arr '' Y (i + 1) else {int}

/-- A backstop: from a slot's history (newest first), `none` to accept the candidate, `some w` to
join `w` into it. -/
abbrev Backstop := List (Set Ty) → Option (Set Ty)

/-- Histories of a run under backstop `β`, newest first.  Round `k + 1` forms the candidate
`F(current) ∪ current` (accumulation) and lets `β` widen it. -/
def run {ι : Type} (F : System ι) (β : Backstop) : ℕ → ι → List (Set Ty)
  | 0 => fun _ => [∅]
  | k + 1 => fun i =>
    let H := run F β k
    let c := F (fun j => (H j).headD ∅) i ∪ (H i).headD ∅
    (match β (c :: H i) with
      | some w => c ∪ w
      | none => c) :: H i

/-- The current value of a slot. -/
def cur {ι : Type} (F : System ι) (β : Backstop) (k : ℕ) (i : ι) : Set Ty := (run F β k i).headD ∅

theorem cur_succ {ι : Type} (F : System ι) (β : Backstop) (k : ℕ) (i : ι) :
    cur F β (k + 1) i =
      match β ((F (cur F β k) i ∪ cur F β k i) :: run F β k i) with
      | some w => (F (cur F β k) i ∪ cur F β k i) ∪ w
      | none => F (cur F β k) i ∪ cur F β k i := by
  simp only [cur, run, List.headD_cons]
  rfl

/-- The round's candidate is always kept. -/
theorem candidate_subset {ι : Type} (F : System ι) (β : Backstop) (k : ℕ) (i : ι) :
    F (cur F β k) i ∪ cur F β k i ⊆ cur F β (k + 1) i := by
  rw [cur_succ]
  split
  · exact Set.subset_union_left
  · exact le_rfl

/-- Values accumulate: a widening is sticky. -/
theorem cur_mono {ι : Type} (F : System ι) (β : Backstop) (i : ι) {k l : ℕ} (h : k ≤ l) :
    cur F β k i ⊆ cur F β l i := by
  induction h with
  | refl => exact le_rfl
  | step _ ih =>
    exact ih.trans (Set.subset_union_right.trans (candidate_subset F β _ i))

/-- If `R`'s run is stable at round `K`, its value is closed under `Int` and `Array[·]`, so it
contains every `Array^j[Int]`. -/
theorem R_stable_contains (β : Backstop) (K : ℕ) (hK : cur R β (K + 1) () = cur R β K ()) (j : ℕ) :
    nest j ∈ cur R β K () := by
  have hclosed : R (cur R β K) () ⊆ cur R β K () := by
    have := candidate_subset R β K ()
    rw [hK] at this
    exact Set.subset_union_left.trans this
  induction j with
  | zero => exact hclosed (Or.inl rfl)
  | succ j ih => exact hclosed (Or.inr ⟨nest j, ih, rfl⟩)

/-- Up to round `k`, every chain slot `i` with `i + k ≤ N` has exactly `R`'s history. -/
theorem histories_agree (β : Backstop) (N : ℕ) :
    ∀ k i, i + k ≤ N → run (C N) β k i = run R β k () := by
  intro k
  induction k with
  | zero => intro i _; rfl
  | succ k ih =>
    intro i hik
    have hi : i < N := by omega
    have h0 := ih i (by omega)
    have h1 := ih (i + 1) (by omega)
    have hc0 : cur (C N) β k i = cur R β k () := by simp only [cur, h0]
    have hc1 : cur (C N) β k (i + 1) = cur R β k () := by simp only [cur, h1]
    have hF : C N (cur (C N) β k) i = R (cur R β k) () := by
      simp only [C, R, ite_eq_left hi, hc1]
    show (let H := run (C N) β k
          let c := C N (fun j => (H j).headD ∅) i ∪ (H i).headD ∅
          (match β (c :: H i) with
            | some w => c ∪ w
            | none => c) :: H i) =
        (let H := run R β k
          let c := R (fun j => (H j).headD ∅) () ∪ (H ()).headD ∅
          (match β (c :: H ()) with
            | some w => c ∪ w
            | none => c) :: H ())
    simp only []
    have e1 : C N (fun j => (run (C N) β k j).headD ∅) i = C N (cur (C N) β k) i := rfl
    have e2 : R (fun j => (run R β k j).headD ∅) () = R (cur R β k) () := rfl
    rw [e1, e2, hF, h0]

/-- The chain `C N` is monotone, so it has a least solution. -/
def Chom (N : ℕ) : (ℕ → Set Ty) →o (ℕ → Set Ty) where
  toFun := C N
  monotone' := by
    intro Y Z h i t ht
    simp only [C] at ht ⊢
    split at ht
    · rcases ht with ht | ⟨s, hs, rfl⟩
      · rw [ite_eq_left (by assumption)]; exact Or.inl ht
      · rw [ite_eq_left (by assumption)]; exact Or.inr ⟨s, h _ hs, rfl⟩
    · rw [ite_eq_right (by assumption)]; exact ht

/-- The least solution of the chain never contains `Array^(N+1)[Int]` at `F₀`. -/
theorem chain_lfp_excludes (N : ℕ) : nest (N + 1) ∉ OrderHom.lfp (Chom N) 0 := by
  -- a pre-fixpoint: slot `i` holds `Int` and the `Array^j[Int]` with `j + i ≤ N`
  let Z : ℕ → Set Ty := fun i => {t | t = int ∨ ∃ j, j + i ≤ N ∧ t = nest j}
  have hZ : Chom N Z ≤ Z := by
    intro i t ht
    change t ∈ C N Z i at ht
    simp only [C] at ht
    split at ht
    · rcases ht with rfl | ⟨s, hs, rfl⟩
      · exact Or.inl rfl
      · rcases hs with rfl | ⟨j, hj, rfl⟩
        · exact Or.inr ⟨1, by omega, rfl⟩
        · exact Or.inr ⟨j + 1, by omega, rfl⟩
    · simp only [Set.mem_singleton_iff] at ht
      exact Or.inl ht
  intro hmem
  rcases OrderHom.lfp_le (Chom N) hZ 0 hmem with he | ⟨j, hj, he⟩
  · simp [nest] at he
  · have := nest_injective he
    omega

/-- **T10.** Whatever history-only, accumulating backstop `β` is: if it makes the recursive slot
stop at round `K`, then on the acyclic chain of length `K` the value of `F₀` contains
`Array^(K+1)[Int]` at every round from `K` on, and the least solution of the chain does not. -/
theorem T10 (β : Backstop) (K : ℕ) (hK : cur R β (K + 1) () = cur R β K ()) :
    (∀ k, K ≤ k → nest (K + 1) ∈ cur (C K) β k 0) ∧ nest (K + 1) ∉ OrderHom.lfp (Chom K) 0 := by
  refine ⟨fun k hk => ?_, chain_lfp_excludes K⟩
  have hagree : cur (C K) β K 0 = cur R β K () := by
    simp only [cur, histories_agree β K K 0 (by omega)]
  have hin : nest (K + 1) ∈ cur (C K) β K 0 := by
    rw [hagree]; exact R_stable_contains β K hK (K + 1)
  exact cur_mono (C K) β 0 hk hin

/-- The hypothesis is not vacuous: rule M1's shape (widen to everything on the third round) stops
`R` at round 3. -/
def m1Like : Backstop := fun H => if H.length = 4 then some Set.univ else none

theorem m1Like_stops_R : cur R m1Like 4 () = cur R m1Like 3 () := by
  have h3 : cur R m1Like 3 () = Set.univ := by
    rw [cur_succ]
    have hl : ((R (cur R m1Like 2) () ∪ cur R m1Like 2 ()) :: run R m1Like 2 ()).length = 4 := by
      simp [run]
    simp only [m1Like, hl, ite_true, Set.union_univ]
  have h4 : cur R m1Like 4 () = Set.univ := by
    apply Set.eq_univ_of_univ_subset
    rw [← h3]
    exact Set.subset_union_right.trans (candidate_subset R m1Like 3 ())
  rw [h3, h4]

/-- And without any backstop `R` never stops (the plain Kleene chain grows forever). -/
theorem no_backstop_never_stops (K : ℕ) : cur R (fun _ => none) (K + 1) () ≠ cur R (fun _ => none) K () := by
  intro hK
  have hall := R_stable_contains (fun _ => none) K hK
  -- with no widening, round `K` only holds `Array^j[Int]` for `j < K`
  have bound : ∀ k t, t ∈ cur R (fun _ => none) k () → ∃ j, j < k ∧ t = nest j := by
    intro k
    induction k with
    | zero => intro t ht; simp [cur, run] at ht
    | succ k ih =>
      intro t ht
      rw [cur_succ] at ht
      simp only [R] at ht
      rcases ht with (rfl | ⟨s, hs, rfl⟩) | ht
      · exact ⟨0, by omega, rfl⟩
      · obtain ⟨j, hj, rfl⟩ := ih s hs
        exact ⟨j + 1, by omega, rfl⟩
      · obtain ⟨j, hj, rfl⟩ := ih t ht
        exact ⟨j, by omega, rfl⟩
  obtain ⟨j, hj, he⟩ := bound K (nest K) (hall K)
  have := nest_injective he
  omega

end ProofLean.Impossibility
