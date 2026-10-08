import ProofLean.Core

/-!
# Goal D: the site solution read as a regular tree grammar

A *signature* gives every site `h` an arity, the slot of each field cell, and whether the field is
required (a record field) or optional (an `Array`/`Hash` element, key or value: the container may be
empty).  Finite trees over sites (`STree`) are the Herbrand universe; `empty` marks an absent optional
child.

* `Mem σ Pt v` is the language of nonterminal `v` in the regular tree grammar whose productions are
  `v → h(cell h 0, …, cell h (n-1))` for `(v, h) ∈ Pt`: finitely many nonterminals (slots) and
  productions (facts), so it is a regular tree grammar by construction.
* `Phi P σ` is the set-constraint system the rules encode, in the style of Heintze–Jaffar: a
  construction site builds every tree whose children lie in its field cells; a guard copies every
  tree whose root passes its filter; a condition `(u, g)` holds when `u` contains a tree rooted at
  `g`.  Its least solution is `OrderHom.lfp (PhiHom P σ)`.

Results:
* `lfp_eq_lang_refined` (exact): the least solution of the set constraints is the language of the
  grammar read from the least fixpoint of the *productivity-refined* site operator `stepR`, where a
  condition fires only on a productive site.
* `lfp_le_lang_plain` (sound): the grammar of the plain site solution (`Prog.solve`, the reframer's
  engine) contains the least solution.
* `ptPlus_subset_solve` and `ptPlus_eq_solve_of_productive`: the refined solution is below the plain
  one and equal to it when every condition that holds is on a productive site; in particular when no
  condition site has a required field (`ptPlus_eq_solve_of_no_required`).
-/

set_option linter.unusedSectionVars false

namespace ProofLean

universe u v

/-- Arity, field cells and required flags of the sites. -/
structure Sig (V : Type u) (S : Type v) where
  ar : S → ℕ
  cell : (h : S) → Fin (ar h) → V
  req : (h : S) → Fin (ar h) → Bool

/-- Finite trees over sites; `empty` is an absent optional child (an empty container). -/
inductive STree {S : Type v} (ar : S → ℕ) : Type v where
  | node (h : S) (ch : Fin (ar h) → STree ar)
  | empty

variable {V : Type u} {S : Type v} [DecidableEq V] [DecidableEq S]

/-- The language of nonterminal `v` in the grammar with productions `Pt`, by recursion on the
(finite) tree. -/
def Mem (σ : Sig V S) (Pt : Set (V × S)) : V → STree σ.ar → Prop
  | _, .empty => False
  | v, .node h ch => (v, h) ∈ Pt ∧
      ∀ i, Mem σ Pt (σ.cell h i) (ch i) ∨ (ch i = .empty ∧ σ.req h i = false)

theorem mem_node {σ : Sig V S} {Pt : Set (V × S)} {v : V} {h : S} {ch : Fin (σ.ar h) → STree σ.ar} :
    Mem σ Pt v (.node h ch) ↔ (v, h) ∈ Pt ∧
      ∀ i, Mem σ Pt (σ.cell h i) (ch i) ∨ (ch i = .empty ∧ σ.req h i = false) := by
  rw [Mem]

theorem not_mem_empty {σ : Sig V S} {Pt : Set (V × S)} {v : V} : ¬ Mem σ Pt v .empty := by
  rw [Mem]; exact id

/-- The language is monotone in the productions. -/
theorem mem_mono {σ : Sig V S} {Pt Pt' : Set (V × S)} (h : Pt ⊆ Pt') :
    ∀ (t : STree σ.ar) (v : V), Mem σ Pt v t → Mem σ Pt' v t := by
  intro t
  induction t with
  | empty => intro v hv; exact absurd hv not_mem_empty
  | node g ch ih =>
    intro v hv
    rw [mem_node] at hv ⊢
    refine ⟨h hv.1, fun i => ?_⟩
    rcases hv.2 i with hi | hi
    · exact Or.inl (ih i _ hi)
    · exact Or.inr hi

/-! ## The set-constraint system over trees -/

section Trees

variable (P : Prog V S) (σ : Sig V S)

/-- Condition `(u, g)` holds in `X`: slot `u` contains a tree rooted at site `g`. -/
def Hit (X : V → Set (STree σ.ar)) (c : V × S) : Prop := ∃ ch, STree.node c.2 ch ∈ X c.1

/-- Child `i` of a node built at `h` is acceptable in `X`. -/
def ChildOK (X : V → Set (STree σ.ar)) (h : S) (i : Fin (σ.ar h)) (t : STree σ.ar) : Prop :=
  t ∈ X (σ.cell h i) ∨ (t = .empty ∧ σ.req h i = false)

/-- The set constraints the rules encode, as an operator on assignments of tree sets to slots. -/
def Phi (X : V → Set (STree σ.ar)) : V → Set (STree σ.ar) := fun v =>
  {t | (∃ a ∈ P.allocs, a.dst = v ∧ (∀ c ∈ a.conds, Hit σ X c) ∧
          ∃ ch, t = .node a.site ch ∧ ∀ i, ChildOK σ X a.site i (ch i)) ∨
       (∃ g ∈ P.guards, g.dst = v ∧ (∀ c ∈ g.conds, Hit σ X c) ∧ t ∈ X g.src ∧
          ∃ h ch, t = .node h ch ∧ g.pass h = true)}

theorem Phi_mono : Monotone (Phi P σ) := by
  intro X Y hXY v t ht
  have hit : ∀ c, Hit σ X c → Hit σ Y c := fun c ⟨ch, hc⟩ => ⟨ch, hXY c.1 hc⟩
  rcases ht with ⟨a, ha, hv, hc, ch, rfl, hch⟩ | ⟨g, hg, hv, hc, hs, h, ch, rfl, hp⟩
  · refine Or.inl ⟨a, ha, hv, fun c h => hit c (hc c h), ch, rfl, fun i => ?_⟩
    rcases hch i with h1 | h1
    · exact Or.inl (hXY _ h1)
    · exact Or.inr h1
  · exact Or.inr ⟨g, hg, hv, fun c h => hit c (hc c h), hXY _ hs, h, ch, rfl, hp⟩

/-- The set-constraint operator as a monotone map of the complete lattice `V → Set (STree)`. -/
def PhiHom : (V → Set (STree σ.ar)) →o (V → Set (STree σ.ar)) := ⟨Phi P σ, Phi_mono P σ⟩

/-- The least solution of the set constraints (Knaster–Tarski). -/
noncomputable def Xstar : V → Set (STree σ.ar) := OrderHom.lfp (PhiHom P σ)

theorem Xstar_fixed : Phi P σ (Xstar P σ) = Xstar P σ := OrderHom.map_lfp (PhiHom P σ)

end Trees

/-! ## The productivity-refined site operator -/

/-- Facts of the refined operator: `pt v h` as before, and `prod h` (site `h` builds at least one
finite tree). -/
inductive RFact (V : Type u) (S : Type v) where
  | pt (v : V) (h : S)
  | prod (h : S)
deriving DecidableEq

namespace Prog

variable (P : Prog V S) (σ : Sig V S)

/-- Conditions hold and their sites are productive. -/
def OkR (X : Set (RFact V S)) (cs : List (V × S)) : Prop :=
  ∀ c ∈ cs, RFact.pt c.1 c.2 ∈ X ∧ RFact.prod c.2 ∈ X

/-- The refined transfer operator (declarative). -/
def stepRSet (X : Set (RFact V S)) : Set (RFact V S) :=
  {f | (∃ a ∈ P.allocs, OkR X a.conds ∧ f = .pt a.dst a.site) ∨
       (∃ g ∈ P.guards, OkR X g.conds ∧ ∃ h, f = .pt g.dst h ∧ RFact.pt g.src h ∈ X ∧
          g.pass h = true) ∨
       (∃ h ∈ P.sites, f = .prod h ∧
          ∀ i, σ.req h i = true → ∃ g, RFact.pt (σ.cell h i) g ∈ X ∧ RFact.prod g ∈ X)}

theorem stepRSet_mono : Monotone (P.stepRSet σ) := by
  intro X Y hXY f hf
  have ok : ∀ cs, OkR X cs → OkR Y cs := fun cs h c hc => ⟨hXY (h c hc).1, hXY (h c hc).2⟩
  rcases hf with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h, rfl, hs, hp⟩ | ⟨h, hh, rfl, hreq⟩
  · exact Or.inl ⟨a, ha, ok _ hc, rfl⟩
  · exact Or.inr (Or.inl ⟨g, hg, ok _ hc, h, rfl, hXY hs, hp⟩)
  · refine Or.inr (Or.inr ⟨h, hh, rfl, fun i hi => ?_⟩)
    obtain ⟨g, h1, h2⟩ := hreq i hi
    exact ⟨g, hXY h1, hXY h2⟩

def stepRHom : Set (RFact V S) →o Set (RFact V S) := ⟨P.stepRSet σ, P.stepRSet_mono σ⟩

/-- Executable helpers. -/
def okRb (X : Finset (RFact V S)) (cs : List (V × S)) : Bool :=
  cs.all (fun c => decide (RFact.pt c.1 c.2 ∈ X) && decide (RFact.prod c.2 ∈ X))

/-- `f` is `pt c g` with `g` productive in `X`. -/
def isProdPt (X : Finset (RFact V S)) (c : V) : RFact V S → Bool
  | .pt w g => decide (w = c) && decide (RFact.prod g ∈ X)
  | .prod _ => false

/-- `f` is a fact of the guard's source that passes its filter. -/
def isSrcPass (g : Guard V S) : RFact V S → Bool
  | .pt w h => decide (w = g.src) && g.pass h
  | .prod _ => false

/-- Move a source fact to the guard's destination. -/
def retarget (g : Guard V S) : RFact V S → RFact V S
  | .pt _ h => .pt g.dst h
  | .prod h => .prod h

/-- One round of the refined operator (computable). -/
def stepR (X : Finset (RFact V S)) : Finset (RFact V S) :=
  ((P.allocs.filter (fun a => okRb X a.conds)).map (fun a => RFact.pt a.dst a.site)).toFinset ∪
  lunion P.guards (fun g => if okRb X g.conds then
      (X.filter (fun f => isSrcPass g f = true)).image (retarget g) else ∅) ∪
  (P.sites.filter (fun h => ∀ i : Fin (σ.ar h), σ.req h i = true →
      ∃ f ∈ X, isProdPt X (σ.cell h i) f = true)).image RFact.prod

theorem okRb_iff {X : Finset (RFact V S)} {cs : List (V × S)} :
    okRb X cs = true ↔ OkR (↑X) cs := by
  simp [okRb, OkR]

theorem mem_stepR {X : Finset (RFact V S)} {f : RFact V S} :
    f ∈ P.stepR σ X ↔ f ∈ P.stepRSet σ ↑X := by
  simp only [stepR, Finset.mem_union, List.mem_toFinset, List.mem_map, List.mem_filter,
    mem_lunion, Finset.mem_image, Finset.mem_filter, stepRSet, Set.mem_ofPred_eq,
    Finset.mem_coe, okRb_iff]
  constructor
  · rintro ((⟨a, ⟨ha, hc⟩, rfl⟩ | ⟨g, hg, hf⟩) | ⟨h, ⟨hh, hreq⟩, rfl⟩)
    · exact Or.inl ⟨a, ha, hc, rfl⟩
    · by_cases hc : OkR (↑X) g.conds
      · rw [ite_eq_left ((okRb_iff (X := X)).2 hc)] at hf
        simp only [Finset.mem_image, Finset.mem_filter] at hf
        obtain ⟨f', ⟨hf', hsp⟩, rfl⟩ := hf
        cases f' with
        | pt w h =>
          simp only [isSrcPass, Bool.and_eq_true, decide_eq_true_eq] at hsp
          obtain ⟨rfl, hp⟩ := hsp
          exact Or.inr (Or.inl ⟨g, hg, hc, h, rfl, hf', hp⟩)
        | prod h => simp [isSrcPass] at hsp
      · rw [ite_eq_right (fun h => hc ((okRb_iff (X := X)).1 h))] at hf
        simp at hf
    · refine Or.inr (Or.inr ⟨h, hh, rfl, fun i hi => ?_⟩)
      obtain ⟨f, hf, hpp⟩ := hreq i hi
      cases f with
      | pt w g =>
        simp only [isProdPt, Bool.and_eq_true, decide_eq_true_eq] at hpp
        obtain ⟨rfl, hg⟩ := hpp
        exact ⟨g, hf, hg⟩
      | prod g => simp [isProdPt] at hpp
  · rintro (⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h, rfl, hs, hp⟩ | ⟨h, hh, rfl, hreq⟩)
    · exact Or.inl (Or.inl ⟨a, ⟨ha, hc⟩, rfl⟩)
    · refine Or.inl (Or.inr ⟨g, hg, ?_⟩)
      rw [ite_eq_left ((okRb_iff (X := X)).2 hc)]
      simp only [Finset.mem_image, Finset.mem_filter]
      exact ⟨RFact.pt g.src h, ⟨hs, by simp [isSrcPass, hp]⟩, rfl⟩
    · refine Or.inr ⟨h, ⟨hh, fun i hi => ?_⟩, rfl⟩
      obtain ⟨g, h1, h2⟩ := hreq i hi
      exact ⟨RFact.pt (σ.cell h i) g, h1, by simp [isProdPt, h2]⟩

theorem coe_stepR (X : Finset (RFact V S)) : (↑(P.stepR σ X) : Set (RFact V S)) = P.stepRSet σ ↑X := by
  ext f; exact P.mem_stepR σ

/-- The refined universe. -/
def univR : Finset (RFact V S) :=
  P.univ.image (fun p => RFact.pt p.1 p.2) ∪ P.sites.image RFact.prod

theorem stepR_bound ⦃X : Finset (RFact V S)⦄ (hX : X ⊆ P.univR) : P.stepR σ X ⊆ P.univR := by
  intro f hf
  rcases (P.mem_stepR σ).1 hf with ⟨a, ha, -, rfl⟩ | ⟨g, hg, -, h, rfl, hs, -⟩ | ⟨h, hh, rfl, -⟩
  · apply Finset.mem_union_left
    refine Finset.mem_image.2 ⟨(a.dst, a.site), ?_, rfl⟩
    simp only [univ, dsts, sites, Finset.mem_product, Finset.mem_union, List.mem_toFinset,
      List.mem_map]
    exact ⟨Or.inl ⟨a, ha, rfl⟩, ⟨a, ha, rfl⟩⟩
  · have hs' := hX hs
    simp only [univR, Finset.mem_union, Finset.mem_image] at hs'
    rcases hs' with ⟨p, hp, hpe⟩ | ⟨h', -, hpe⟩
    · apply Finset.mem_union_left
      refine Finset.mem_image.2 ⟨(g.dst, h), ?_, rfl⟩
      simp only [RFact.pt.injEq] at hpe
      obtain ⟨-, rfl⟩ := hpe
      simp only [univ, Finset.mem_product] at hp ⊢
      refine ⟨?_, hp.2⟩
      simp only [dsts, Finset.mem_union, List.mem_toFinset, List.mem_map]
      exact Or.inr ⟨g, hg, rfl⟩
    · cases hpe
  · exact Finset.mem_union_right _ (Finset.mem_image.2 ⟨h, hh, rfl⟩)

theorem stepR_mono ⦃X Y : Finset (RFact V S)⦄ (h : X ⊆ Y) : P.stepR σ X ⊆ P.stepR σ Y := by
  intro f hf
  exact (P.mem_stepR σ).2 (P.stepRSet_mono σ (Finset.coe_subset.2 h) ((P.mem_stepR σ).1 hf))

/-- The refined operator, packaged for the generic fixpoint theory. -/
def toOpR : BoundedOp (RFact V S) where
  F := P.stepR σ
  U := P.univR
  mono := P.stepR_mono σ
  bound := P.stepR_bound σ

/-- The refined least solution (computable by naive iteration). -/
def solveR : Finset (RFact V S) := (P.toOpR σ).kleene

/-- Its `pt` facts as a relation. -/
def ptPlus : Set (V × S) := {p | RFact.pt p.1 p.2 ∈ P.solveR σ}

theorem solveR_fixed : P.stepR σ (P.solveR σ) = P.solveR σ := (P.toOpR σ).kleene_fixed

theorem coe_solveR_fixed : P.stepRSet σ ↑(P.solveR σ) = ↑(P.solveR σ) := by
  rw [← coe_stepR, solveR_fixed]

theorem solveR_eq_lfp : (↑(P.solveR σ) : Set (RFact V S)) = OrderHom.lfp (P.stepRHom σ) :=
  (P.toOpR σ).kleene_eq_lfp (P.stepRHom σ) (fun X => (P.coe_stepR σ X).symm)

/-- **B (refined).** The refined iteration also stops within the size of its universe. -/
theorem solveR_rounds_le : (P.toOpR σ).kleeneN.2 ≤ P.univR.card := (P.toOpR σ).kleeneN_rounds_le

theorem mem_solveR_of_step {f : RFact V S} (hf : f ∈ P.stepRSet σ ↑(P.solveR σ)) :
    f ∈ P.solveR σ := by
  rw [coe_solveR_fixed] at hf; exact hf

theorem site_mem_of_pt {w : V} {g : S} (h : RFact.pt w g ∈ P.solveR σ) : g ∈ P.sites := by
  have h' := (P.toOpR σ).kleene_subset_univ h
  simp only [toOpR, univR, Finset.mem_union, Finset.mem_image] at h'
  rcases h' with ⟨p, hp, hpe⟩ | ⟨h', -, hpe⟩
  · simp only [RFact.pt.injEq] at hpe
    obtain ⟨-, rfl⟩ := hpe
    exact (Finset.mem_product.1 hp).2
  · cases hpe

/-- A tree in the refined language has a productive root. -/
theorem prod_of_mem : ∀ (t : STree σ.ar) (w : V) (g : S) (ch : Fin (σ.ar g) → STree σ.ar),
    t = .node g ch → Mem σ (P.ptPlus σ) w t → RFact.prod g ∈ P.solveR σ := by
  intro t
  induction t with
  | empty => intro w g ch h; cases h
  | node g' ch' ih =>
    intro w g ch heq hm
    cases heq
    rw [mem_node] at hm
    obtain ⟨hpt, hkids⟩ := hm
    apply P.mem_solveR_of_step σ
    refine Or.inr (Or.inr ⟨g', P.site_mem_of_pt σ hpt, rfl, fun i hi => ?_⟩)
    rcases hkids i with hk | ⟨-, hk⟩
    · have hk0 := hk
      cases hci : ch' i with
      | empty => rw [hci] at hk; exact absurd hk not_mem_empty
      | node g'' ch'' =>
        rw [hci] at hk
        have hk' := hk
        rw [mem_node] at hk'
        exact ⟨g'', hk'.1, ih i _ g'' ch'' hci hk0⟩
    · rw [hi] at hk; cases hk

end Prog

/-! ## The denotation theorems -/

section Theorems

variable (P : Prog V S) (σ : Sig V S)

/-- The language of the refined grammar, as an assignment of tree sets to slots. -/
def langR : V → Set (STree σ.ar) := fun v => {t | Mem σ (P.ptPlus σ) v t}

/-- The language of the plain grammar (the reframer's engine). -/
def langPlain : V → Set (STree σ.ar) := fun v => {t | Mem σ ↑P.solve v t}

/-- Direction 1: the refined language is a pre-fixpoint of the set constraints, so it contains
their least solution. -/
theorem Xstar_le_langR : Xstar P σ ≤ langR P σ := by
  apply OrderHom.lfp_le
  intro v t ht
  have hit : ∀ c, Hit σ (langR P σ) c → RFact.pt c.1 c.2 ∈ P.solveR σ ∧
      RFact.prod c.2 ∈ P.solveR σ := by
    rintro ⟨u, g⟩ ⟨ch, hc⟩
    have hc' : Mem σ (P.ptPlus σ) u (.node g ch) := hc
    exact ⟨(mem_node.1 hc').1, P.prod_of_mem σ _ u g ch rfl hc'⟩
  rcases ht with ⟨a, ha, rfl, hc, ch, rfl, hch⟩ | ⟨g, hg, rfl, hc, hs, h, ch, rfl, hp⟩
  · show Mem σ (P.ptPlus σ) a.dst (.node a.site ch)
    rw [mem_node]
    refine ⟨?_, fun i => hch i⟩
    show RFact.pt a.dst a.site ∈ P.solveR σ
    exact P.mem_solveR_of_step σ (Or.inl ⟨a, ha, fun c h => hit c (hc c h), rfl⟩)
  · show Mem σ (P.ptPlus σ) g.dst (.node h ch)
    have hs' : Mem σ (P.ptPlus σ) g.src (.node h ch) := hs
    rw [mem_node] at hs' ⊢
    refine ⟨?_, hs'.2⟩
    show RFact.pt g.dst h ∈ P.solveR σ
    exact P.mem_solveR_of_step σ
      (Or.inr (Or.inl ⟨g, hg, fun c h => hit c (hc c h), h, rfl, hs'.1, hp⟩))

/-- The target set for direction 2: what the least tree solution makes true of each fact. -/
def Target : Set (RFact V S) :=
  {f | match f with
    | .pt w h => ∀ ch : Fin (σ.ar h) → STree σ.ar,
        (∀ i, ChildOK σ (Xstar P σ) h i (ch i)) → STree.node h ch ∈ Xstar P σ w
    | .prod h => ∀ i, σ.req h i = true → ∃ t, t ∈ Xstar P σ (σ.cell h i)}

/-- From productivity in `Target`, pick a full vector of acceptable children. -/
theorem exists_children {h : S} (hp : RFact.prod h ∈ Target P σ) :
    ∃ ch : Fin (σ.ar h) → STree σ.ar, ∀ i, ChildOK σ (Xstar P σ) h i (ch i) := by
  classical
  have hp' : ∀ i, σ.req h i = true → ∃ t, t ∈ Xstar P σ (σ.cell h i) := hp
  refine ⟨fun i => if hr : σ.req h i = true then Classical.choose (hp' i hr) else .empty,
    fun i => ?_⟩
  by_cases hr : σ.req h i = true
  · left
    simp only [hr]
    exact Classical.choose_spec (hp' i hr)
  · right
    have hr' : σ.req h i = false := by simpa using hr
    exact ⟨by simp [hr], hr'⟩

theorem hit_of_target {c : V × S} (h1 : RFact.pt c.1 c.2 ∈ Target P σ)
    (h2 : RFact.prod c.2 ∈ Target P σ) : Hit σ (Xstar P σ) c := by
  obtain ⟨ch, hch⟩ := exists_children P σ h2
  exact ⟨ch, h1 ch hch⟩

/-- `Target` is a pre-fixpoint of the refined operator. -/
theorem stepRSet_target : P.stepRSet σ (Target P σ) ⊆ Target P σ := by
  intro f hf
  rcases hf with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h, rfl, hs, hp⟩ | ⟨h, -, rfl, hreq⟩
  · intro ch hch
    rw [← Xstar_fixed]
    exact Or.inl ⟨a, ha, rfl, fun c hc' => hit_of_target P σ (hc c hc').1 (hc c hc').2,
      ch, rfl, hch⟩
  · intro ch hch
    rw [← Xstar_fixed]
    exact Or.inr ⟨g, hg, rfl, fun c hc' => hit_of_target P σ (hc c hc').1 (hc c hc').2,
      hs ch hch, h, ch, rfl, hp⟩
  · intro i hi
    obtain ⟨g, h1, h2⟩ := hreq i hi
    obtain ⟨ch, hch⟩ := exists_children P σ h2
    exact ⟨_, h1 ch hch⟩

theorem solveR_subset_target : (↑(P.solveR σ) : Set (RFact V S)) ⊆ Target P σ := by
  rw [P.solveR_eq_lfp σ]
  exact OrderHom.lfp_le _ (stepRSet_target P σ)

/-- Direction 2: every tree of the refined language is in the least solution. -/
theorem langR_le_Xstar : langR P σ ≤ Xstar P σ := by
  intro w t ht
  induction t generalizing w with
  | empty => exact absurd (show Mem σ (P.ptPlus σ) w .empty from ht) not_mem_empty
  | node h ch ih =>
    have ht' : Mem σ (P.ptPlus σ) w (.node h ch) := ht
    rw [mem_node] at ht'
    have hT := solveR_subset_target P σ (show RFact.pt w h ∈ (↑(P.solveR σ) : Set _) from ht'.1)
    apply hT
    intro i
    rcases ht'.2 i with hk | hk
    · exact Or.inl (ih i _ hk)
    · exact Or.inr hk

/-- **D (exact).** The least solution of the set-constraint system equals the language of the
regular tree grammar read from the productivity-refined site solution. -/
theorem lfp_eq_lang_refined : Xstar P σ = langR P σ :=
  le_antisymm (Xstar_le_langR P σ) (langR_le_Xstar P σ)

/-- **D (sound).** The grammar of the plain site solution (`Prog.solve`, which the reframer's engine
computes) contains the least solution of the set constraints. -/
theorem lfp_le_lang_plain : Xstar P σ ≤ langPlain P σ := by
  apply OrderHom.lfp_le
  intro v t ht
  have hsolve : ∀ p, p ∈ P.stepSet ↑P.solve → p ∈ P.solve := by
    intro p hp
    rw [← P.coe_step, P.solve_fixed] at hp
    exact hp
  have hit : ∀ c, Hit σ (langPlain P σ) c → c ∈ P.solve := by
    rintro ⟨u, g⟩ ⟨ch, hc⟩
    have hc' : Mem σ ↑P.solve u (.node g ch) := hc
    exact (mem_node.1 hc').1
  rcases ht with ⟨a, ha, rfl, hc, ch, rfl, hch⟩ | ⟨g, hg, rfl, hc, hs, h, ch, rfl, hp⟩
  · show Mem σ ↑P.solve a.dst (.node a.site ch)
    rw [mem_node]
    exact ⟨hsolve _ (Or.inl ⟨a, ha, fun c h => Finset.mem_coe.2 (hit c (hc c h)), rfl⟩),
      fun i => hch i⟩
  · show Mem σ ↑P.solve g.dst (.node h ch)
    have hs' : Mem σ ↑P.solve g.src (.node h ch) := hs
    rw [mem_node] at hs' ⊢
    exact ⟨hsolve _ (Or.inr ⟨g, hg, fun c h => Finset.mem_coe.2 (hit c (hc c h)), rfl, hs'.1,
      hp⟩), hs'.2⟩

/-- The refined facts are plain facts. -/
theorem ptPlus_subset_solve : P.ptPlus σ ⊆ ↑P.solve := by
  let T : Set (RFact V S) := {f | match f with
    | .pt w h => (w, h) ∈ P.solve
    | .prod _ => True}
  have hT : P.stepRSet σ T ⊆ T := by
    have hsolve : ∀ p, p ∈ P.stepSet ↑P.solve → p ∈ P.solve := by
      intro p hp
      rw [← P.coe_step, P.solve_fixed] at hp
      exact hp
    intro f hf
    rcases hf with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h, rfl, hs, hp⟩ | ⟨h, -, rfl, -⟩
    · exact hsolve _ (Or.inl ⟨a, ha, fun c h => Finset.mem_coe.2 (hc c h).1, rfl⟩)
    · exact hsolve _ (Or.inr ⟨g, hg, fun c h => Finset.mem_coe.2 (hc c h).1, rfl,
        Finset.mem_coe.2 hs, hp⟩)
    · trivial
  have hle : (↑(P.solveR σ) : Set (RFact V S)) ⊆ T := by
    rw [P.solveR_eq_lfp σ]; exact OrderHom.lfp_le _ hT
  intro p hp
  exact hle (show RFact.pt p.1 p.2 ∈ (↑(P.solveR σ) : Set _) from hp)

/-- The conditions of all rules. -/
def condFacts : Set (V × S) :=
  {c | (∃ a ∈ P.allocs, c ∈ a.conds) ∨ (∃ g ∈ P.guards, c ∈ g.conds)}

/-- **D (when plain is exact).** If every condition that holds in the plain solution is on a site
that is productive in the refined solution, the two site solutions coincide, so the plain grammar's
language is exactly the least solution of the set constraints. -/
theorem ptPlus_eq_solve_of_productive
    (hprod : ∀ c ∈ condFacts P, c ∈ P.solve → RFact.prod c.2 ∈ P.solveR σ) :
    P.ptPlus σ = ↑P.solve := by
  apply le_antisymm (ptPlus_subset_solve P σ)
  have hpre : P.stepSet (P.ptPlus σ) ⊆ P.ptPlus σ := by
    have ok : ∀ cs : List (V × S), (∀ c ∈ cs, c ∈ condFacts P) →
        (∀ c ∈ cs, c ∈ P.ptPlus σ) → Prog.OkR (↑(P.solveR σ)) cs := by
      intro cs hcs hc c hcc
      refine ⟨hc c hcc, hprod c (hcs c hcc) ?_⟩
      exact ptPlus_subset_solve P σ (hc c hcc)
    intro p hp
    rcases hp with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h1, h2, h3⟩
    · show RFact.pt a.dst a.site ∈ P.solveR σ
      exact P.mem_solveR_of_step σ (Or.inl ⟨a, ha,
        ok _ (fun c h => Or.inl ⟨a, ha, h⟩) hc, rfl⟩)
    · show RFact.pt p.1 p.2 ∈ P.solveR σ
      rw [h1]
      exact P.mem_solveR_of_step σ (Or.inr (Or.inl ⟨g, hg,
        ok _ (fun c h => Or.inr ⟨g, hg, h⟩) hc, p.2, rfl, h2, h3⟩))
  rw [P.solve_eq_lfp]
  exact OrderHom.lfp_le _ hpre

/-- **D (when plain is exact), syntactic form.** If no condition site has a required field (every
condition is on a container or scalar site), the plain solution's grammar is exact. -/
theorem ptPlus_eq_solve_of_no_required
    (hreq : ∀ c ∈ condFacts P, ∀ i, σ.req c.2 i = false) :
    P.ptPlus σ = ↑P.solve := by
  apply ptPlus_eq_solve_of_productive
  intro c hc hcs
  apply P.mem_solveR_of_step σ
  have hsite : c.2 ∈ P.sites := (Finset.mem_product.1 (P.toOp.kleene_subset_univ hcs)).2
  refine Or.inr (Or.inr ⟨c.2, hsite, rfl, fun i hi => ?_⟩)
  rw [hreq c hc i] at hi
  cases hi

/-- **D, plain form.** Under the same syntactic condition, the least solution of the set
constraints is exactly the language of the plain site solution's grammar. -/
theorem lfp_eq_lang_plain_of_no_required
    (hreq : ∀ c ∈ condFacts P, ∀ i, σ.req c.2 i = false) :
    Xstar P σ = langPlain P σ := by
  rw [lfp_eq_lang_refined]
  funext v
  simp only [langR, langPlain, ptPlus_eq_solve_of_no_required P σ hreq]

end Theorems

end ProofLean
