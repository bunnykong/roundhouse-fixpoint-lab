import ProofLean.Fixpoint
import Mathlib.Data.Finset.Prod
import Mathlib.Order.Hom.Basic

/-!
# The core calculus: guarded inclusion constraints over finite slots and sites

Facts are `Pt(v, h)`: slot `v` may hold an object built at site `h` (types as sets of site facts).
Slots `V` are method returns, parameters, ivars, expression temporaries and the
field cells of construction sites; sites `S` are construction sites and scalar atoms.  Both are
whatever finite collection the program mentions: the fact universe is `dsts × sites`.

A program has two kinds of positive rules:

* `Alloc`: if every condition fact holds, `dst` may hold `site` (an allocation, or a conditional
  one such as the result of `merge` or a `Produce`);
* `Guard`: if every condition fact holds, every site of `src` that passes the filter `pass` is also a
  site of `dst` (plain flow, filter by head, load and store through a receiver site, argument and
  return flow of a call selected by the argument's head, dispatch, yield, merge copies).

The operator `step` is monotone, so the generic theorems of `ProofLean.Fixpoint` apply.
-/

set_option linter.unusedSectionVars false

namespace ProofLean

/-- Conditional allocation: if every condition fact holds, slot `dst` may hold site `site`. -/
structure Alloc (V S : Type*) where
  conds : List (V × S)
  dst : V
  site : S

/-- Guarded inclusion: if every condition fact holds, every site of `src` that passes `pass` is
also a site of `dst`. -/
structure Guard (V S : Type*) where
  conds : List (V × S)
  src : V
  dst : V
  pass : S → Bool

/-- A program of the core calculus. -/
structure Prog (V S : Type*) where
  allocs : List (Alloc V S)
  guards : List (Guard V S)

/-- Union of a family of finite sets indexed by a list. -/
def lunion {β γ : Type*} [DecidableEq γ] (l : List β) (f : β → Finset γ) : Finset γ :=
  l.foldr (fun b acc => f b ∪ acc) ∅

theorem mem_lunion {β γ : Type*} [DecidableEq γ] {l : List β} {f : β → Finset γ} {x : γ} :
    x ∈ lunion l f ↔ ∃ b ∈ l, x ∈ f b := by
  induction l with
  | nil => simp [lunion]
  | cons b l ih =>
    simp only [lunion, List.foldr_cons, Finset.mem_union, List.mem_cons] at ih ⊢
    rw [ih]
    constructor
    · rintro (h | ⟨c, hc, hx⟩)
      · exact ⟨b, Or.inl rfl, h⟩
      · exact ⟨c, Or.inr hc, hx⟩
    · rintro ⟨c, rfl | hc, hx⟩
      · exact Or.inl hx
      · exact Or.inr ⟨c, hc, hx⟩

variable {V S : Type*} [DecidableEq V] [DecidableEq S]

namespace Prog

variable (P : Prog V S)

/-! ## The finite fact universe -/

/-- Slots that can receive a fact. -/
def dsts : Finset V :=
  (P.allocs.map Alloc.dst).toFinset ∪ (P.guards.map Guard.dst).toFinset

/-- Sites that can appear in a fact. -/
def sites : Finset S := (P.allocs.map Alloc.site).toFinset

/-- The fact universe: every fact the rules can ever derive. -/
def univ : Finset (V × S) := P.dsts ×ˢ P.sites

/-- **The number of possible facts.** -/
theorem card_univ : P.univ.card = P.dsts.card * P.sites.card := Finset.card_product _ _

/-! ## Declarative semantics -/

/-- The transfer operator on arbitrary sets of facts: the declarative meaning of the rules. -/
def stepSet (X : Set (V × S)) : Set (V × S) :=
  {p | (∃ a ∈ P.allocs, (∀ c ∈ a.conds, c ∈ X) ∧ p = (a.dst, a.site)) ∨
       (∃ g ∈ P.guards, (∀ c ∈ g.conds, c ∈ X) ∧ p.1 = g.dst ∧ (g.src, p.2) ∈ X ∧
          g.pass p.2 = true)}

/-- **A.** The transfer operator is monotone. -/
theorem stepSet_mono : Monotone P.stepSet := by
  intro X Y h p hp
  rcases hp with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h1, h2, h3⟩
  · exact Or.inl ⟨a, ha, fun c hc' => h (hc c hc'), rfl⟩
  · exact Or.inr ⟨g, hg, fun c hc' => h (hc c hc'), h1, h h2, h3⟩

/-- The transfer operator as a monotone map of the complete lattice `Set (V × S)`. -/
def stepHom : Set (V × S) →o Set (V × S) := ⟨P.stepSet, P.stepSet_mono⟩

/-! ## Executable semantics -/

/-- Facts produced by allocations whose conditions hold in `X`. -/
def allocFacts (X : Finset (V × S)) : Finset (V × S) :=
  ((P.allocs.filter (fun a => a.conds.all (fun c => decide (c ∈ X)))).map
    (fun a => (a.dst, a.site))).toFinset

/-- Facts produced by one guard whose conditions hold in `X`. -/
def guardFacts (X : Finset (V × S)) (g : Guard V S) : Finset (V × S) :=
  if g.conds.all (fun c => decide (c ∈ X)) then
    (X.filter (fun p => p.1 = g.src ∧ g.pass p.2 = true)).image (fun p => (g.dst, p.2))
  else ∅

/-- **A.** One round of the transfer operator on a finite set of facts (computable). -/
def step (X : Finset (V × S)) : Finset (V × S) :=
  P.allocFacts X ∪ lunion P.guards (guardFacts X)

theorem mem_allocFacts {X : Finset (V × S)} {p : V × S} :
    p ∈ P.allocFacts X ↔ ∃ a ∈ P.allocs, (∀ c ∈ a.conds, c ∈ X) ∧ p = (a.dst, a.site) := by
  simp only [allocFacts, List.mem_toFinset, List.mem_map, List.mem_filter, List.all_eq_true,
    decide_eq_true_eq]
  constructor
  · rintro ⟨a, ⟨ha, hc⟩, rfl⟩; exact ⟨a, ha, hc, rfl⟩
  · rintro ⟨a, ha, hc, rfl⟩; exact ⟨a, ⟨ha, hc⟩, rfl⟩

theorem mem_guardFacts {X : Finset (V × S)} {g : Guard V S} {p : V × S} :
    p ∈ guardFacts X g ↔
      (∀ c ∈ g.conds, c ∈ X) ∧ p.1 = g.dst ∧ (g.src, p.2) ∈ X ∧ g.pass p.2 = true := by
  unfold guardFacts
  by_cases hc : g.conds.all (fun c => decide (c ∈ X)) = true
  · rw [ite_eq_left hc]
    have hc' : ∀ c ∈ g.conds, c ∈ X := by simpa using hc
    simp only [Finset.mem_image, Finset.mem_filter]
    constructor
    · rintro ⟨q, ⟨hq, hs, hpass⟩, rfl⟩
      refine ⟨hc', rfl, ?_, hpass⟩
      rw [← hs]; exact hq
    · rintro ⟨-, h1, h2, h3⟩
      exact ⟨(g.src, p.2), ⟨h2, rfl, h3⟩, by rw [← h1]⟩
  · rw [ite_eq_right hc]
    simp only [Finset.notMem_empty, false_iff, not_and]
    intro h
    exact absurd (by simpa using h) hc

/-- **A.** The executable round agrees with the declarative operator on every finite set. -/
theorem mem_step {X : Finset (V × S)} {p : V × S} : p ∈ P.step X ↔ p ∈ P.stepSet ↑X := by
  simp only [step, Finset.mem_union, mem_lunion, P.mem_allocFacts, mem_guardFacts, stepSet,
    Set.mem_ofPred_eq, Finset.mem_coe]

theorem coe_step (X : Finset (V × S)) : (↑(P.step X) : Set (V × S)) = P.stepSet ↑X := by
  ext p; exact P.mem_step

theorem step_mono ⦃X Y : Finset (V × S)⦄ (h : X ⊆ Y) : P.step X ⊆ P.step Y := by
  intro p hp
  exact P.mem_step.2 (P.stepSet_mono (Finset.coe_subset.2 h) (P.mem_step.1 hp))

theorem step_bound ⦃X : Finset (V × S)⦄ (hX : X ⊆ P.univ) : P.step X ⊆ P.univ := by
  intro p hp
  rcases P.mem_step.1 hp with ⟨a, ha, -, rfl⟩ | ⟨g, hg, -, h1, h2, -⟩
  · simp only [univ, dsts, sites, Finset.mem_product, Finset.mem_union, List.mem_toFinset,
      List.mem_map]
    exact ⟨Or.inl ⟨a, ha, rfl⟩, ⟨a, ha, rfl⟩⟩
  · have h2' := hX h2
    simp only [univ, Finset.mem_product] at h2' ⊢
    refine ⟨?_, h2'.2⟩
    simp only [dsts, Finset.mem_union, List.mem_toFinset, List.mem_map]
    exact Or.inr ⟨g, hg, h1.symm⟩

/-- The program's transfer operator, packaged for the generic fixpoint theory. -/
def toOp : BoundedOp (V × S) where
  F := P.step
  U := P.univ
  mono := P.step_mono
  bound := P.step_bound

/-! ## Semi-naive deltas -/

/-- New allocation facts: conditions hold in `X` and at least one condition is new. -/
def deltaAllocs (X D : Finset (V × S)) : Finset (V × S) :=
  ((P.allocs.filter (fun a => a.conds.all (fun c => decide (c ∈ X)) &&
      a.conds.any (fun c => decide (c ∈ D)))).map (fun a => (a.dst, a.site))).toFinset

/-- New facts of one guard: if a condition is new, all of `src`'s passing sites flow; otherwise
only `src`'s new sites do. -/
def deltaGuard (X D : Finset (V × S)) (g : Guard V S) : Finset (V × S) :=
  if g.conds.all (fun c => decide (c ∈ X)) then
    if g.conds.any (fun c => decide (c ∈ D)) then
      (X.filter (fun p => p.1 = g.src ∧ g.pass p.2 = true)).image (fun p => (g.dst, p.2))
    else
      (D.filter (fun p => p.1 = g.src ∧ g.pass p.2 = true)).image (fun p => (g.dst, p.2))
  else ∅

/-- The semi-naive delta operator. -/
def delta (X D : Finset (V × S)) : Finset (V × S) :=
  P.deltaAllocs X D ∪ lunion P.guards (deltaGuard X D)

theorem mem_deltaAllocs {X D : Finset (V × S)} {p : V × S} :
    p ∈ P.deltaAllocs X D ↔ ∃ a ∈ P.allocs, (∀ c ∈ a.conds, c ∈ X) ∧ (∃ c ∈ a.conds, c ∈ D) ∧
      p = (a.dst, a.site) := by
  simp only [deltaAllocs, List.mem_toFinset, List.mem_map, List.mem_filter, Bool.and_eq_true,
    List.all_eq_true, List.any_eq_true, decide_eq_true_eq]
  constructor
  · rintro ⟨a, ⟨ha, hc, hd⟩, rfl⟩; exact ⟨a, ha, hc, hd, rfl⟩
  · rintro ⟨a, ha, hc, hd, rfl⟩; exact ⟨a, ⟨ha, hc, hd⟩, rfl⟩

theorem mem_deltaGuard {X D : Finset (V × S)} {g : Guard V S} {p : V × S} :
    p ∈ deltaGuard X D g ↔
      (∀ c ∈ g.conds, c ∈ X) ∧ p.1 = g.dst ∧ g.pass p.2 = true ∧
        (((∃ c ∈ g.conds, c ∈ D) ∧ (g.src, p.2) ∈ X) ∨
          ((¬ ∃ c ∈ g.conds, c ∈ D) ∧ (g.src, p.2) ∈ D)) := by
  unfold deltaGuard
  by_cases hc : g.conds.all (fun c => decide (c ∈ X)) = true
  · have hc' : ∀ c ∈ g.conds, c ∈ X := by simpa using hc
    rw [ite_eq_left hc]
    by_cases hd : g.conds.any (fun c => decide (c ∈ D)) = true
    · have hd' : ∃ c ∈ g.conds, c ∈ D := by simpa using hd
      rw [ite_eq_left hd]
      simp only [Finset.mem_image, Finset.mem_filter]
      constructor
      · rintro ⟨q, ⟨hq, hs, hpass⟩, rfl⟩
        exact ⟨hc', rfl, hpass, Or.inl ⟨hd', by rw [← hs]; exact hq⟩⟩
      · rintro ⟨-, h1, h3, (⟨-, h2⟩ | ⟨hn, -⟩)⟩
        · exact ⟨(g.src, p.2), ⟨h2, rfl, h3⟩, by rw [← h1]⟩
        · exact absurd hd' hn
    · have hd' : ¬ ∃ c ∈ g.conds, c ∈ D := by simpa using hd
      rw [ite_eq_right hd]
      simp only [Finset.mem_image, Finset.mem_filter]
      constructor
      · rintro ⟨q, ⟨hq, hs, hpass⟩, rfl⟩
        exact ⟨hc', rfl, hpass, Or.inr ⟨hd', by rw [← hs]; exact hq⟩⟩
      · rintro ⟨-, h1, h3, (⟨hn, -⟩ | ⟨-, h2⟩)⟩
        · exact absurd hn hd'
        · exact ⟨(g.src, p.2), ⟨h2, rfl, h3⟩, by rw [← h1]⟩
  · rw [ite_eq_right hc]
    simp only [Finset.notMem_empty, false_iff, not_and]
    intro h
    exact absurd (by simpa using h) hc

theorem delta_sound ⦃X D : Finset (V × S)⦄ (hD : D ⊆ X) : P.delta X D ⊆ P.step X := by
  intro p hp
  apply P.mem_step.2
  simp only [delta, Finset.mem_union, mem_lunion, P.mem_deltaAllocs, mem_deltaGuard] at hp
  rcases hp with ⟨a, ha, hc, -, rfl⟩ | ⟨g, hg, hc, h1, h3, (⟨-, h2⟩ | ⟨-, h2⟩)⟩
  · exact Or.inl ⟨a, ha, hc, rfl⟩
  · exact Or.inr ⟨g, hg, hc, h1, h2, h3⟩
  · exact Or.inr ⟨g, hg, hc, h1, hD h2, h3⟩

theorem delta_complete ⦃X D : Finset (V × S)⦄ (_hD : D ⊆ X) :
    P.step X ⊆ P.step (X \ D) ∪ P.delta X D := by
  intro p hp
  rw [Finset.mem_union]
  rcases P.mem_step.1 hp with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h1, h2, h3⟩
  · by_cases hd : ∃ c ∈ a.conds, c ∈ D
    · right
      simp only [delta, Finset.mem_union, P.mem_deltaAllocs]
      exact Or.inl ⟨a, ha, hc, hd, rfl⟩
    · left
      apply P.mem_step.2
      refine Or.inl ⟨a, ha, fun c hc' => ?_, rfl⟩
      simp only [Finset.coe_sdiff, Set.mem_sdiff, Finset.mem_coe]
      exact ⟨hc c hc', fun h => hd ⟨c, hc', h⟩⟩
  · by_cases hd : ∃ c ∈ g.conds, c ∈ D
    · right
      simp only [delta, Finset.mem_union, mem_lunion, mem_deltaGuard]
      exact Or.inr ⟨g, hg, hc, h1, h3, Or.inl ⟨hd, h2⟩⟩
    · by_cases hs : (g.src, p.2) ∈ D
      · right
        simp only [delta, Finset.mem_union, mem_lunion, mem_deltaGuard]
        exact Or.inr ⟨g, hg, hc, h1, h3, Or.inr ⟨hd, hs⟩⟩
      · left
        apply P.mem_step.2
        refine Or.inr ⟨g, hg, fun c hc' => ?_, h1, ?_, h3⟩
        · simp only [Finset.coe_sdiff, Set.mem_sdiff, Finset.mem_coe]
          exact ⟨hc c hc', fun h => hd ⟨c, hc', h⟩⟩
        · simp only [Finset.coe_sdiff, Set.mem_sdiff, Finset.mem_coe]
          exact ⟨h2, hs⟩

/-- The program's semi-naive delta operator. -/
def deltaOp : P.toOp.Delta where
  dF := P.delta
  sound := P.delta_sound
  complete := P.delta_complete

/-! ## Fact-at-a-time trigger -/

/-- The unconditional allocations: the first queue. -/
def initFacts : List (V × S) :=
  (P.allocs.filter (fun a => a.conds.isEmpty)).map (fun a => (a.dst, a.site))

/-- Consequences of the fact `f` given the processed facts `L`. -/
def fire (L : List (V × S)) (f : V × S) : List (V × S) :=
  (P.allocs.filter (fun a => decide (f ∈ a.conds) &&
      a.conds.all (fun c => decide (c ∈ f :: L)))).map (fun a => (a.dst, a.site)) ++
  P.guards.flatMap (fun g =>
    if g.conds.all (fun c => decide (c ∈ f :: L)) then
      if decide (f ∈ g.conds) then
        ((f :: L).filter (fun q => decide (q.1 = g.src) && g.pass q.2)).map (fun q => (g.dst, q.2))
      else if decide (f.1 = g.src) && g.pass f.2 then [(g.dst, f.2)] else []
    else [])

theorem mem_fire {L : List (V × S)} {f p : V × S} :
    p ∈ P.fire L f ↔
      (∃ a ∈ P.allocs, f ∈ a.conds ∧ (∀ c ∈ a.conds, c ∈ insert f L.toFinset) ∧
          p = (a.dst, a.site)) ∨
      (∃ g ∈ P.guards, (∀ c ∈ g.conds, c ∈ insert f L.toFinset) ∧ p.1 = g.dst ∧
          g.pass p.2 = true ∧
          ((f ∈ g.conds ∧ (g.src, p.2) ∈ insert f L.toFinset) ∨
            (f ∉ g.conds ∧ f = (g.src, p.2)))) := by
  have hmem : ∀ c : V × S, c ∈ f :: L ↔ c ∈ insert f L.toFinset := by
    intro c; simp
  simp only [fire, List.mem_append, List.mem_map, List.mem_filter, Bool.and_eq_true,
    decide_eq_true_eq, List.all_eq_true, List.mem_flatMap]
  apply or_congr
  · constructor
    · rintro ⟨a, ⟨ha, hf, hc⟩, rfl⟩
      exact ⟨a, ha, hf, fun c h => (hmem c).1 (hc c h), rfl⟩
    · rintro ⟨a, ha, hf, hc, rfl⟩
      exact ⟨a, ⟨ha, hf, fun c h => (hmem c).2 (hc c h)⟩, rfl⟩
  · constructor
    · rintro ⟨g, hg, hp⟩
      split_ifs at hp with hc hf hs
      · simp only [List.mem_map, List.mem_filter, Bool.and_eq_true, decide_eq_true_eq] at hp
        obtain ⟨q, ⟨hq, hs, hpass⟩, rfl⟩ := hp
        refine ⟨g, hg, fun c h => (hmem c).1 (hc c h), rfl, hpass, Or.inl ⟨hf, ?_⟩⟩
        rw [← hs]; exact (hmem q).1 hq
      · simp only [List.mem_singleton] at hp
        subst hp
        refine ⟨g, hg, fun c h => (hmem c).1 (hc c h), rfl, hs.2, Or.inr ⟨hf, ?_⟩⟩
        rw [← hs.1]
      · simp at hp
      · simp at hp
    · rintro ⟨g, hg, hc, h1, hpass, (⟨hf, hs⟩ | ⟨hf, hs⟩)⟩
      · refine ⟨g, hg, ?_⟩
        have hc' : ∀ c ∈ g.conds, c ∈ f :: L := fun c h => (hmem c).2 (hc c h)
        rw [ite_eq_left hc', ite_eq_left hf]
        simp only [List.mem_map, List.mem_filter, Bool.and_eq_true, decide_eq_true_eq]
        refine ⟨(g.src, p.2), ⟨(hmem _).2 hs, rfl, hpass⟩, ?_⟩
        rw [← h1]
      · refine ⟨g, hg, ?_⟩
        have hc' : ∀ c ∈ g.conds, c ∈ f :: L := fun c h => (hmem c).2 (hc c h)
        have hs' : f.1 = g.src ∧ g.pass f.2 = true := by
          subst hs; exact ⟨rfl, hpass⟩
        rw [ite_eq_left hc', ite_eq_right hf, ite_eq_left hs']
        simp only [List.mem_singleton]
        subst hs
        rw [← h1]

theorem fire_sound (L : List (V × S)) (f : V × S) :
    (P.fire L f).toFinset ⊆ P.step (insert f L.toFinset) := by
  intro p hp
  rw [List.mem_toFinset, P.mem_fire] at hp
  apply P.mem_step.2
  rcases hp with ⟨a, ha, -, hc, rfl⟩ | ⟨g, hg, hc, h1, hpass, (⟨-, hs⟩ | ⟨-, hs⟩)⟩
  · exact Or.inl ⟨a, ha, fun c h => Finset.mem_coe.2 (hc c h), rfl⟩
  · exact Or.inr ⟨g, hg, fun c h => Finset.mem_coe.2 (hc c h), h1, hs, hpass⟩
  · refine Or.inr ⟨g, hg, fun c h => Finset.mem_coe.2 (hc c h), h1, ?_, hpass⟩
    rw [← hs]; exact Finset.mem_coe.2 (Finset.mem_insert_self _ _)

theorem fire_complete (L : List (V × S)) (f : V × S) :
    P.step (insert f L.toFinset) ⊆ P.step L.toFinset ∪ (P.fire L f).toFinset := by
  intro p hp
  rw [Finset.mem_union, List.mem_toFinset, P.mem_fire]
  rcases P.mem_step.1 hp with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h1, h2, h3⟩
  · by_cases hf : f ∈ a.conds
    · exact Or.inr (Or.inl ⟨a, ha, hf, hc, rfl⟩)
    · left
      apply P.mem_step.2
      refine Or.inl ⟨a, ha, fun c h => ?_, rfl⟩
      have := hc c h
      simp only [Finset.coe_insert, Set.mem_insert_iff, Finset.mem_coe] at this ⊢
      rcases this with rfl | h'
      · exact absurd h hf
      · exact h'
  · by_cases hf : f ∈ g.conds
    · exact Or.inr (Or.inr ⟨g, hg, hc, h1, h3, Or.inl ⟨hf, h2⟩⟩)
    · have h2' := h2
      simp only [Finset.coe_insert, Set.mem_insert_iff, Finset.mem_coe] at h2'
      rcases h2' with hs | hs
      · exact Or.inr (Or.inr ⟨g, hg, hc, h1, h3, Or.inr ⟨hf, hs.symm⟩⟩)
      · left
        apply P.mem_step.2
        refine Or.inr ⟨g, hg, fun c h => ?_, h1, Finset.mem_coe.2 hs, h3⟩
        have := hc c h
        simp only [Finset.coe_insert, Set.mem_insert_iff, Finset.mem_coe] at this ⊢
        rcases this with rfl | h'
        · exact absurd h hf
        · exact h'

theorem initFacts_spec : P.initFacts.toFinset = P.step ∅ := by
  ext p
  rw [List.mem_toFinset, P.mem_step]
  simp only [initFacts, List.mem_map, List.mem_filter, List.isEmpty_iff, stepSet,
    Set.mem_ofPred_eq, Finset.coe_empty, Set.mem_empty_iff_false]
  constructor
  · rintro ⟨a, ⟨ha, hc⟩, rfl⟩
    exact Or.inl ⟨a, ha, fun c h => by simp [hc] at h, rfl⟩
  · rintro (⟨a, ha, hc, rfl⟩ | ⟨g, -, -, -, h, -⟩)
    · refine ⟨a, ⟨ha, ?_⟩, rfl⟩
      cases h : a.conds with
      | nil => rfl
      | cons c cs => exact absurd (hc c (by simp [h])) id
    · exact h.elim

/-- The program's fact-at-a-time trigger. -/
def trigger : P.toOp.Trigger where
  init := P.initFacts
  init_spec := P.initFacts_spec
  fire := P.fire
  sound := P.fire_sound
  complete := P.fire_complete

/-! ## The three solvers and the main theorems for the core -/

/-- Naive solver: the least solution and its round count. -/
def solveN : Finset (V × S) × ℕ := P.toOp.kleeneN

/-- The least abstract solution, by naive iteration. -/
def solve : Finset (V × S) := P.toOp.kleene

/-- Semi-naive solver. -/
def solveSN : Finset (V × S) × ℕ := BoundedOp.semiN P.deltaOp

/-- Worklist solver with a queue discipline. -/
def solveW (sc : BoundedOp.Sched (V × S)) : Finset (V × S) := BoundedOp.work P.trigger sc

/-- **B (core).** Naive iteration stops within `|dsts| · |sites|` rounds (the number of possible
facts), and within `|solution|` rounds. -/
theorem solveN_rounds_le : P.solveN.2 ≤ P.solve.card ∧ P.solveN.2 ≤ P.dsts.card * P.sites.card :=
  ⟨P.toOp.kleeneN_rounds_le_card, P.card_univ ▸ P.toOp.kleeneN_rounds_le⟩

/-- **B/C (core).** The result is a fixpoint and the least pre-fixpoint of the executable round. -/
theorem solve_fixed : P.step P.solve = P.solve := P.toOp.kleene_fixed

theorem solve_isLeast : IsLeast {Y : Finset (V × S) | P.step Y ⊆ Y} P.solve :=
  P.toOp.kleene_isLeast

/-- **C (core), Knaster–Tarski form.** The computed solution is Mathlib's least fixpoint of the
declarative transfer operator on `Set (V × S)`. -/
theorem solve_eq_lfp : (↑P.solve : Set (V × S)) = OrderHom.lfp P.stepHom :=
  P.toOp.kleene_eq_lfp P.stepHom (fun X => (P.coe_step X).symm)

/-- **C (core).** Semi-naive evaluation equals naive evaluation (same result, same rounds). -/
theorem solveSN_eq_solveN : P.solveSN = P.solveN := BoundedOp.semiN_eq_kleeneN P.deltaOp

/-- **C (core).** Semi-naive evaluation equals naive evaluation round by round: after `k` rounds
the semi-naive state is `(F^k ∅, F^(k+1) ∅ \ F^k ∅)`. -/
theorem solveSN_iterate (k : ℕ) :
    (BoundedOp.snStep P.deltaOp)^[k] (∅, P.step ∅) =
      (P.step^[k] ∅, P.step^[k + 1] ∅ \ P.step^[k] ∅) :=
  BoundedOp.snStep_iterate P.deltaOp k

/-- **C (core).** The worklist engine returns the least solution for every queue discipline. -/
theorem solveW_eq_solve (sc : BoundedOp.Sched (V × S)) : P.solveW sc = P.solve :=
  BoundedOp.work_eq_kleene P.trigger sc

end Prog

end ProofLean
