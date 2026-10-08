import Mathlib.Order.FixedPoints
import Mathlib.Data.Finset.Card
import Mathlib.Logic.Function.Iterate

/-!
# Kleene, semi-naive and worklist iteration on a finite powerset

Everything here is generic: facts of any type `α` with decidable equality, a monotone operator
`F` on finite sets of facts, and a finite universe `U` that `F` never leaves.  The core calculus
(`ProofLean.Core`) instantiates it.

* `BoundedOp.kleeneN` — naive (Kleene) iteration from `∅`, with its round count.
* `BoundedOp.semiN` — semi-naive (delta) iteration, given a delta operator that is sound and
  complete in the usual Datalog sense.
* `BoundedOp.work` — fact-at-a-time worklist iteration (the reframer's `Engine.solve`).

All three terminate by well-founded recursion on `|U| - |X|` (no fuel), and the theorems show:
termination within `|U|` rounds, leastness (equal to Mathlib's `OrderHom.lfp` of any set-level
operator that agrees with `F` on finite sets), and equality of the three results (semi-naive equals
naive round by round).
-/

namespace ProofLean

open Finset

/-- A monotone operator on finite fact sets that never leaves a finite universe `U`. -/
structure BoundedOp (α : Type*) [DecidableEq α] where
  F : Finset α → Finset α
  U : Finset α
  mono : ∀ ⦃X Y : Finset α⦄, X ⊆ Y → F X ⊆ F Y
  bound : ∀ ⦃X : Finset α⦄, X ⊆ U → F X ⊆ U

namespace BoundedOp

variable {α : Type*} [DecidableEq α] (o : BoundedOp α)

/-! ## Naive (Kleene) iteration -/

/-- Kleene iteration from a set `X ⊆ F X` inside the universe; returns the fixpoint reached and
the number of rounds (applications of `F` that changed the set). -/
def kleeneAux (X : Finset α) (hU : X ⊆ o.U) (hX : X ⊆ o.F X) : Finset α × ℕ :=
  if hfix : o.F X = X then (X, 0)
  else
    let r := kleeneAux (o.F X) (o.bound hU) (o.mono hX)
    (r.1, r.2 + 1)
termination_by o.U.card - X.card
decreasing_by
  have hss : X ⊂ o.F X := Finset.ssubset_iff_subset_ne.2 ⟨hX, fun h => hfix h.symm⟩
  have h1 : X.card < (o.F X).card := Finset.card_lt_card hss
  have h2 : (o.F X).card ≤ o.U.card := Finset.card_le_card (o.bound hU)
  omega

/-- Naive iteration from `∅`: the fixpoint and its round count. -/
def kleeneN : Finset α × ℕ :=
  o.kleeneAux ∅ (Finset.empty_subset _) (Finset.empty_subset _)

/-- The result of naive iteration. -/
def kleene : Finset α := o.kleeneN.1

/-- Specification of one call of `kleeneAux`: the result is the `n`-th iterate of `F` from `X`, it
is a fixpoint, each round adds a fact, and the result stays inside the universe. -/
theorem kleeneAux_spec (X : Finset α) (hU : X ⊆ o.U) (hX : X ⊆ o.F X) :
    (o.kleeneAux X hU hX).1 = o.F^[(o.kleeneAux X hU hX).2] X ∧
    o.F (o.kleeneAux X hU hX).1 = (o.kleeneAux X hU hX).1 ∧
    X.card + (o.kleeneAux X hU hX).2 ≤ (o.kleeneAux X hU hX).1.card ∧
    (o.kleeneAux X hU hX).1 ⊆ o.U := by
  induction X, hU, hX using kleeneAux.induct (o := o) with
  | case1 X hU hX hfix =>
    rw [kleeneAux, dite_eq_left hfix]
    exact ⟨rfl, hfix, by simp, hU⟩
  | case2 X hU hX hfix ih =>
    rw [kleeneAux, dite_eq_right hfix]
    obtain ⟨h1, h2, h3, h4⟩ := ih
    refine ⟨?_, h2, ?_, h4⟩
    · simp only [Function.iterate_succ, Function.comp_apply]
      exact h1
    · have hss : X ⊂ o.F X := Finset.ssubset_iff_subset_ne.2 ⟨hX, fun h => hfix h.symm⟩
      have := Finset.card_lt_card hss
      simp only
      omega

/-- **B (naive).** The naive result is the `n`-th Kleene iterate from `∅`, with `n` its round
count. -/
theorem kleene_eq_iterate : o.kleene = o.F^[o.kleeneN.2] ∅ :=
  (o.kleeneAux_spec ∅ _ _).1

/-- **B (naive).** The naive result is a fixpoint. -/
theorem kleene_fixed : o.F o.kleene = o.kleene :=
  (o.kleeneAux_spec ∅ _ _).2.1

/-- **B (naive).** Every round adds at least one fact, so the number of rounds is at most the size
of the result. -/
theorem kleeneN_rounds_le_card : o.kleeneN.2 ≤ o.kleene.card := by
  have := (o.kleeneAux_spec ∅ (Finset.empty_subset _) (Finset.empty_subset _)).2.2.1
  simpa [kleene, kleeneN] using this

/-- The result stays inside the universe. -/
theorem kleene_subset_univ : o.kleene ⊆ o.U :=
  (o.kleeneAux_spec ∅ _ _).2.2.2

/-- **B (naive).** Naive iteration needs at most `|U|` rounds (the number of possible facts). -/
theorem kleeneN_rounds_le : o.kleeneN.2 ≤ o.U.card :=
  le_trans o.kleeneN_rounds_le_card (Finset.card_le_card o.kleene_subset_univ)

/-- Every Kleene iterate from `∅` is below every pre-fixpoint. -/
theorem iterate_subset_of_prefix {Y : Finset α} (hY : o.F Y ⊆ Y) (n : ℕ) :
    o.F^[n] ∅ ⊆ Y := by
  induction n with
  | zero => exact Finset.empty_subset _
  | succ n ih =>
    rw [Function.iterate_succ_apply']
    exact (o.mono ih).trans hY

/-- **C (naive).** The naive result is the least pre-fixpoint (hence the least fixpoint). -/
theorem kleene_isLeast : IsLeast {Y : Finset α | o.F Y ⊆ Y} o.kleene := by
  refine ⟨?_, fun Y hY => ?_⟩
  · show o.F o.kleene ⊆ o.kleene
    rw [o.kleene_fixed]
  · rw [o.kleene_eq_iterate]
    exact o.iterate_subset_of_prefix hY _

/-- **C (naive).** Leastness among fixpoints. -/
theorem kleene_le_of_fixed {Y : Finset α} (hY : o.F Y = Y) : o.kleene ⊆ Y :=
  o.kleene_isLeast.2 (by simp [hY])

/-- The Kleene chain from `∅` is stable after the round count. -/
theorem iterate_eq_kleene_of_le {n : ℕ} (hn : o.kleeneN.2 ≤ n) : o.F^[n] ∅ = o.kleene := by
  obtain ⟨k, rfl⟩ := Nat.exists_eq_add_of_le hn
  rw [Nat.add_comm, Function.iterate_add_apply, ← o.kleene_eq_iterate]
  clear hn
  induction k with
  | zero => rfl
  | succ k ih => rw [Function.iterate_succ_apply', ih, o.kleene_fixed]

/-- **B (naive).** After `|U|` rounds the Kleene chain from `∅` has reached the least fixpoint. -/
theorem iterate_card_eq_kleene : o.F^[o.U.card] ∅ = o.kleene :=
  o.iterate_eq_kleene_of_le o.kleeneN_rounds_le

/-- Iterates of a monotone operator preserve "below the least fixpoint". -/
theorem iterate_subset_kleene {X : Finset α} (hX : X ⊆ o.kleene) (n : ℕ) :
    o.F^[n] X ⊆ o.kleene := by
  induction n with
  | zero => exact hX
  | succ n ih =>
    rw [Function.iterate_succ_apply']
    exact (o.mono ih).trans (le_of_eq o.kleene_fixed)

/-- **C (warm start, certified seed).** Iterating from a seed `X ⊆ F X` that is below the least
fixpoint reaches exactly the least fixpoint.  (A seed that is not below it, such as a round-0 `Var`
placeholder, cannot: the result contains the seed; see `Counter.selfVar_from_seed`.) -/
theorem kleeneAux_eq_kleene_of_le (X : Finset α) (hU : X ⊆ o.U) (hX : X ⊆ o.F X)
    (hle : X ⊆ o.kleene) : (o.kleeneAux X hU hX).1 = o.kleene := by
  obtain ⟨h1, h2, -, -⟩ := o.kleeneAux_spec X hU hX
  apply le_antisymm
  · rw [h1]; exact o.iterate_subset_kleene hle _
  · exact o.kleene_le_of_fixed h2

/-- A seed is always contained in the fixpoint iteration reaches from it. -/
theorem seed_subset_kleeneAux (X : Finset α) (hU : X ⊆ o.U) (hX : X ⊆ o.F X) :
    X ⊆ (o.kleeneAux X hU hX).1 := by
  obtain ⟨h1, -, -, -⟩ := o.kleeneAux_spec X hU hX
  rw [h1]
  have : ∀ n, X ⊆ o.F^[n] X := by
    intro n
    induction n with
    | zero => exact le_rfl
    | succ n ih =>
      rw [Function.iterate_succ_apply']
      exact hX.trans (o.mono ih)
  exact this _

/-- If one round from `∅` already gives a fixpoint, naive iteration takes at most one round. -/
theorem kleeneN_rounds_le_one (h : o.F (o.F ∅) = o.F ∅) : o.kleeneN.2 ≤ 1 := by
  unfold kleeneN
  rw [kleeneAux]
  split
  · simp
  · rw [kleeneAux, dite_eq_left h]

/-- **C (naive), Mathlib form.** If a monotone operator `G` on all sets of facts agrees with `F` on
finite sets, the naive result is `OrderHom.lfp G` (Knaster–Tarski). -/
theorem kleene_eq_lfp (G : Set α →o Set α) (hG : ∀ X : Finset α, G (X : Set α) = (o.F X : Set α)) :
    (o.kleene : Set α) = OrderHom.lfp G := by
  apply le_antisymm
  · -- every iterate is below lfp G
    have key : ∀ n, ((o.F^[n] ∅ : Finset α) : Set α) ≤ OrderHom.lfp G := by
      intro n
      induction n with
      | zero => simp
      | succ n ih =>
        rw [Function.iterate_succ_apply', ← hG]
        calc G ((o.F^[n] ∅ : Finset α) : Set α) ≤ G (OrderHom.lfp G) := G.mono ih
          _ = OrderHom.lfp G := OrderHom.map_lfp G
    rw [o.kleene_eq_iterate]
    exact key _
  · apply OrderHom.lfp_le_fixed
    rw [hG, o.kleene_fixed]

/-! ## Semi-naive (delta) iteration -/

/-- A delta operator for `F`: from the current set `X` and the facts `D ⊆ X` that are new since
the previous round, it derives (at least) every consequence of `X` that uses a new fact. -/
structure Delta (o : BoundedOp α) where
  dF : Finset α → Finset α → Finset α
  sound : ∀ ⦃X D : Finset α⦄, D ⊆ X → dF X D ⊆ o.F X
  complete : ∀ ⦃X D : Finset α⦄, D ⊆ X → o.F X ⊆ o.F (X \ D) ∪ dF X D

variable {o}

/-- Semi-naive iteration: `S` is the set so far and `Δ` the facts derived in the last round that
were not yet in `S`.  Stops when the delta is empty.  (`hd` is used only by the termination
proof, which the unused-variable linter does not see.) -/
def semiAux (d : Delta o) (S Δ : Finset α) (hU : S ∪ Δ ⊆ o.U) (_hd : Disjoint S Δ) :
    Finset α × ℕ :=
  if hE : Δ = ∅ then (S, 0)
  else
    have hΔU : d.dF (S ∪ Δ) Δ \ (S ∪ Δ) ⊆ o.U :=
      (Finset.sdiff_subset).trans ((d.sound Finset.subset_union_right).trans (o.bound hU))
    let r := semiAux d (S ∪ Δ) (d.dF (S ∪ Δ) Δ \ (S ∪ Δ))
      (Finset.union_subset hU hΔU) Finset.disjoint_sdiff
    (r.1, r.2 + 1)
termination_by o.U.card - S.card
decreasing_by
  have hne : Δ.Nonempty := Finset.nonempty_iff_ne_empty.2 hE
  have h1 : (S ∪ Δ).card = S.card + Δ.card := Finset.card_union_of_disjoint _hd
  have h2 : 0 < Δ.card := Finset.card_pos.2 hne
  have h3 : (S ∪ Δ).card ≤ o.U.card := Finset.card_le_card hU
  omega

/-- Semi-naive iteration from `∅`, first delta `F ∅`. -/
def semiN (d : Delta o) : Finset α × ℕ :=
  semiAux d ∅ (o.F ∅) (by simpa using o.bound (Finset.empty_subset _)) (Finset.disjoint_empty_left _)

/-- One semi-naive round as a step function on `(S, Δ)`. -/
def snStep (d : Delta o) (p : Finset α × Finset α) : Finset α × Finset α :=
  (p.1 ∪ p.2, d.dF (p.1 ∪ p.2) p.2 \ (p.1 ∪ p.2))

/-- The key invariant step: if `S ∪ Δ = F S` with `S`, `Δ` disjoint, the next state satisfies the
same invariant. -/
theorem snStep_inv (d : Delta o) {S Δ : Finset α} (hd : Disjoint S Δ) (hinv : S ∪ Δ = o.F S) :
    (S ∪ Δ) ∪ (d.dF (S ∪ Δ) Δ \ (S ∪ Δ)) = o.F (S ∪ Δ) := by
  rw [Finset.union_sdiff_self_eq_union]
  apply le_antisymm
  · apply Finset.union_subset
    · rw [hinv]; exact o.mono (hinv ▸ Finset.subset_union_left)
    · exact d.sound Finset.subset_union_right
  · have hc := d.complete (X := S ∪ Δ) (D := Δ) Finset.subset_union_right
    have hS : (S ∪ Δ) \ Δ = S := by
      rw [Finset.union_sdiff_right]; exact hd.sdiff_eq_left
    rw [hS, ← hinv] at hc
    exact hc

/-- **C (semi-naive equals naive, round by round).** The `k`-th semi-naive state is
`(F^k ∅, F^(k+1) ∅ \ F^k ∅)`: the same sets as naive iteration, with the delta equal to exactly the
new facts. -/
theorem snStep_iterate (d : Delta o) :
    ∀ k, (snStep d)^[k] (∅, o.F ∅) = (o.F^[k] ∅, o.F^[k + 1] ∅ \ o.F^[k] ∅)
  | 0 => by simp
  | k + 1 => by
    rw [Function.iterate_succ_apply', snStep_iterate d k]
    -- naive chain facts
    have hmono : o.F^[k] ∅ ⊆ o.F^[k + 1] ∅ := by
      have : ∀ j, o.F^[j] ∅ ⊆ o.F^[j + 1] ∅ := by
        intro j
        induction j with
        | zero => exact Finset.empty_subset _
        | succ j ih =>
          rw [Function.iterate_succ_apply', Function.iterate_succ_apply' (n := j + 1)]
          exact o.mono ih
      exact this k
    have hd : Disjoint (o.F^[k] ∅) (o.F^[k + 1] ∅ \ o.F^[k] ∅) := Finset.disjoint_sdiff
    have hu : o.F^[k] ∅ ∪ (o.F^[k + 1] ∅ \ o.F^[k] ∅) = o.F^[k + 1] ∅ :=
      Finset.union_sdiff_of_subset hmono
    have hinv : o.F^[k] ∅ ∪ (o.F^[k + 1] ∅ \ o.F^[k] ∅) = o.F (o.F^[k] ∅) := by
      rw [hu, Function.iterate_succ_apply']
    have key := snStep_inv d hd hinv
    simp only [snStep, Prod.mk.injEq]
    rw [hu] at key ⊢
    refine ⟨rfl, ?_⟩
    rw [Function.iterate_succ_apply' (n := k + 1)]
    -- (dF X Δ \ X) = F X \ X, using X ∪ (dF X Δ \ X) = F X
    ext a
    constructor
    · intro ha
      have h1 : a ∈ o.F^[k + 1] ∅ ∪ (d.dF (o.F^[k + 1] ∅) (o.F^[k + 1] ∅ \ o.F^[k] ∅) \
          o.F^[k + 1] ∅) := Finset.mem_union_right _ ha
      rw [key] at h1
      exact Finset.mem_sdiff.2 ⟨h1, (Finset.mem_sdiff.1 ha).2⟩
    · intro ha
      obtain ⟨h1, h2⟩ := Finset.mem_sdiff.1 ha
      rw [← key] at h1
      rcases Finset.mem_union.1 h1 with h | h
      · exact absurd h h2
      · exact h

/-- `kleeneAux` only depends on the set it starts from. -/
theorem kleeneAux_congr (o : BoundedOp α) {X Y : Finset α} (h : X = Y) (hU : X ⊆ o.U)
    (hX : X ⊆ o.F X) (hU' : Y ⊆ o.U) (hY : Y ⊆ o.F Y) :
    o.kleeneAux X hU hX = o.kleeneAux Y hU' hY := by
  subst h; rfl

/-- Semi-naive iteration returns exactly what naive iteration returns from the same state, with the
same round count. -/
theorem semiAux_eq_kleeneAux (d : Delta o) (S Δ : Finset α) (hU : S ∪ Δ ⊆ o.U)
    (hd : Disjoint S Δ) (hinv : S ∪ Δ = o.F S) :
    semiAux d S Δ hU hd =
      o.kleeneAux S (Finset.union_subset_left hU) (hinv ▸ Finset.subset_union_left) := by
  induction S, Δ, hU, hd using semiAux.induct (d := d) with
  | case1 S hU hd =>
    rw [semiAux, dite_eq_left rfl, kleeneAux, dite_eq_left (by rw [← hinv, Finset.union_empty])]
  | case2 S Δ hU hd hE hΔU ih =>
    rw [semiAux, dite_eq_right hE]
    have hne : ¬ o.F S = S := by
      intro h
      rw [← hinv] at h
      apply hE
      have hsub : Δ ⊆ S := fun a ha => h ▸ Finset.mem_union_right S ha
      exact Finset.subset_empty.1 (fun a ha => absurd (hsub ha) (Finset.disjoint_right.1 hd ha))
    rw [kleeneAux, dite_eq_right hne]
    dsimp only
    rw [ih (snStep_inv d hd hinv), kleeneAux_congr o hinv]

/-- **C (semi-naive equals naive).** Semi-naive iteration from `∅` returns the naive result and
the same number of rounds. -/
theorem semiN_eq_kleeneN (d : Delta o) : semiN d = o.kleeneN := by
  unfold semiN kleeneN
  rw [semiAux_eq_kleeneAux d ∅ (o.F ∅) _ _ (by simp)]

/-- **B + C (semi-naive).** Semi-naive iteration terminates within `|U|` rounds and returns the least
fixpoint. -/
theorem semiN_spec (d : Delta o) :
    (semiN d).2 ≤ o.U.card ∧ o.F (semiN d).1 = (semiN d).1 ∧
      IsLeast {Y : Finset α | o.F Y ⊆ Y} (semiN d).1 := by
  rw [semiN_eq_kleeneN]
  exact ⟨o.kleeneN_rounds_le, o.kleene_fixed, o.kleene_isLeast⟩


/-! ## Fact-at-a-time worklist iteration -/

/-- A fact-at-a-time trigger for `F` (the reframer's `Engine.solve`): `init` lists `F ∅`, and
`fire L f` lists (at least) every consequence of `insert f L` that uses the fact `f`, where the
processed facts are given as the list `L`. -/
structure Trigger (o : BoundedOp α) where
  init : List α
  init_spec : init.toFinset = o.F ∅
  fire : List α → α → List α
  sound : ∀ L f, (fire L f).toFinset ⊆ o.F (insert f L.toFinset)
  complete : ∀ L f, o.F (insert f L.toFinset) ⊆ o.F L.toFinset ∪ (fire L f).toFinset

/-- A queue discipline: how the remaining queue and the newly found facts are combined.  Any
function that keeps exactly their members and does not grow the length is allowed (FIFO, LIFO,
SCC or priority order, ...). -/
structure Sched (α : Type*) where
  merge : List α → List α → List α
  mem : ∀ r n a, a ∈ merge r n ↔ a ∈ r ∨ a ∈ n
  len : ∀ r n, (merge r n).length ≤ r.length + n.length

/-- First in, first out (the reframer's `deque`). -/
def Sched.fifo (α : Type*) : Sched α :=
  ⟨fun r n => r ++ n, fun _ _ _ => List.mem_append, fun r n => by simp⟩

/-- Last in, first out. -/
def Sched.lifo (α : Type*) : Sched α :=
  ⟨fun r n => n ++ r, fun _ _ _ => by rw [List.mem_append]; exact Or.comm, fun r n => by
    simp [Nat.add_comm]⟩

/-- Worklist iteration.  `Done` lists the processed facts and `Known` holds every fact found so far
(the processed ones and the queue).  Popping `f` fires its consequences against `Done`; the ones not
yet known join the queue in the order chosen by the scheduler `sc`, so each fact is queued at most
once.  Terminates by the lexicographic measure (`|U| - |Known|`, queue length). -/
def workAux (t : Trigger o) (sc : Sched α) (Done : List α) (Known : Finset α) (q : List α)
    (hK : Known ⊆ o.U) (hD : Done.toFinset ⊆ Known) (hq : ∀ a ∈ q, a ∈ Known) : Finset α :=
  match q, hq with
  | [], _ => Done.toFinset
  | f :: rest, hq =>
    have hf : f ∈ Known := hq f List.mem_cons_self
    have hins : (f :: Done).toFinset ⊆ Known := by
      rw [List.toFinset_cons]; exact Finset.insert_subset hf hD
    let new := ((t.fire Done f).filter (fun a => a ∉ Known)).dedup
    have hnew : new.toFinset ⊆ o.U := by
      intro a ha
      have ha' : a ∈ t.fire Done f := by
        simp only [new, List.mem_toFinset, List.mem_dedup, List.mem_filter] at ha
        exact ha.1
      have hins' : insert f Done.toFinset ⊆ o.U := by
        rw [← List.toFinset_cons]; exact hins.trans hK
      exact o.bound hins' (t.sound Done f (List.mem_toFinset.2 ha'))
    workAux t sc (f :: Done) (Known ∪ new.toFinset) (sc.merge rest new)
      (Finset.union_subset hK hnew)
      (hins.trans Finset.subset_union_left)
      (by
        intro a ha
        rcases (sc.mem _ _ _).1 ha with h | h
        · exact Finset.mem_union_left _ (hq a (List.mem_cons_of_mem _ h))
        · exact Finset.mem_union_right _ (List.mem_toFinset.2 h))
termination_by (o.U.card - Known.card, q.length)
decreasing_by
  by_cases hne : ((t.fire Done f).filter (fun a => a ∉ Known)).dedup = []
  · apply Prod.Lex.right'
    · rw [hne]; simp
    · rw [hne]
      have := sc.len rest []
      simp only [List.length_nil, Nat.add_zero] at this
      simp only [List.length_cons]
      omega
  · apply Prod.Lex.left
    obtain ⟨b, hb⟩ := List.exists_mem_of_ne_nil _ hne
    have hbK : b ∉ Known := by
      simp only [List.mem_dedup, List.mem_filter, decide_eq_true_eq] at hb
      exact hb.2
    have hss : Known ⊂ Known ∪ (((t.fire Done f).filter (fun a => a ∉ Known)).dedup).toFinset := by
      refine Finset.ssubset_iff_subset_ne.2 ⟨Finset.subset_union_left, fun h => hbK ?_⟩
      rw [h]
      exact Finset.mem_union_right _ (List.mem_toFinset.2 hb)
    have h1 := Finset.card_lt_card hss
    have h2 : (Known ∪ (((t.fire Done f).filter (fun a => a ∉ Known)).dedup).toFinset).card ≤
        o.U.card := Finset.card_le_card (Finset.union_subset hK hnew)
    omega

/-- Worklist iteration from `∅` with the initial queue `init = F ∅`. -/
def work (t : Trigger o) (sc : Sched α) : Finset α :=
  workAux t sc [] t.init.toFinset t.init
    (by rw [t.init_spec]; exact o.bound (Finset.empty_subset _))
    (by simp) (fun a ha => List.mem_toFinset.2 ha)

/-- The worklist invariant, by functional induction: if every consequence of the processed facts is
known, `Known` is exactly the processed facts plus the queue, and every known fact lies below every
pre-fixpoint, then the result is the least fixpoint. -/
theorem workAux_spec (t : Trigger o) (sc : Sched α) (Done : List α) (Known : Finset α)
    (q : List α) (hK : Known ⊆ o.U) (hD : Done.toFinset ⊆ Known) (hq : ∀ a ∈ q, a ∈ Known)
    (hcl : o.F Done.toFinset ⊆ Known) (hkn : Known = Done.toFinset ∪ q.toFinset)
    (hle : ∀ Y : Finset α, o.F Y ⊆ Y → Known ⊆ Y) :
    o.F (workAux t sc Done Known q hK hD hq) ⊆ workAux t sc Done Known q hK hD hq ∧
      ∀ Y : Finset α, o.F Y ⊆ Y → workAux t sc Done Known q hK hD hq ⊆ Y := by
  induction Done, Known, q, hK, hD, hq using workAux.induct (t := t) (sc := sc) with
  | case1 Done Known hK hD hq =>
    rw [workAux]
    simp only [List.toFinset_nil, Finset.union_empty] at hkn
    subst hkn
    exact ⟨hcl, fun Y hY => hle Y hY⟩
  | case2 Done Known hK hD f rest hq hf hins new hnew hq' ih =>
    rw [workAux]
    apply ih
    · -- closure: F (insert f Done) ⊆ Known ∪ new
      intro a ha
      rw [List.toFinset_cons] at ha
      rcases Finset.mem_union.1 (t.complete Done f ha) with h | h
      · exact Finset.mem_union_left _ (hcl h)
      · by_cases hk : a ∈ Known
        · exact Finset.mem_union_left _ hk
        · apply Finset.mem_union_right
          simp only [new, List.mem_toFinset, List.mem_dedup, List.mem_filter,
            decide_eq_true_eq]
          exact ⟨List.mem_toFinset.1 h, hk⟩
    · -- Known ∪ new = (f :: Done) ∪ (merge rest new)
      rw [hkn]
      ext a
      simp only [Finset.mem_union, List.mem_toFinset, sc.mem, List.mem_cons]
      tauto
    · -- every known fact is below every pre-fixpoint
      intro Y hY
      apply Finset.union_subset (hle Y hY)
      intro a ha
      have ha' : a ∈ t.fire Done f := by
        simp only [new, List.mem_toFinset, List.mem_dedup, List.mem_filter] at ha
        exact ha.1
      have h1 := t.sound Done f (List.mem_toFinset.2 ha')
      have hsub : insert f Done.toFinset ⊆ Y := by
        rw [← List.toFinset_cons]; exact hins.trans (hle Y hY)
      exact hY (o.mono hsub h1)

/-- **B + C (worklist).** For every queue discipline, the worklist result is the naive result
(the least fixpoint): scheduling never changes the answer. -/
theorem work_eq_kleene (t : Trigger o) (sc : Sched α) : work t sc = o.kleene := by
  have h := workAux_spec t sc [] t.init.toFinset t.init
    (by rw [t.init_spec]; exact o.bound (Finset.empty_subset _))
    (by simp) (fun a ha => List.mem_toFinset.2 ha)
    (by simp [t.init_spec])
    (by simp)
    (fun Y hY => by
      rw [t.init_spec]
      exact (o.mono (Finset.empty_subset Y)).trans hY)
  apply le_antisymm
  · exact h.2 _ (by rw [o.kleene_fixed])
  · exact o.kleene_isLeast.2 h.1

end BoundedOp

end ProofLean
