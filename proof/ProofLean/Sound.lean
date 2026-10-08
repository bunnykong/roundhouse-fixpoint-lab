import ProofLean.Core

/-!
# Goal F (stretch): soundness against a concrete semantics

A tiny first-order language with records, arrays and (mutual) recursion, its big-step semantics,
its constraint generation into the core calculus, and the theorem that every value a terminating
run produces is described by the least site solution.

* Values are trees `node h kids` built at a site `h`.  A site maps each child position to a field
  index (`cellIdx`): a record's child `j` is field `j`; every child of an array is field `0` (the
  element); a hash literal `[k₁, v₁, k₂, v₂]` alternates key `0` and value `1`.
* Expressions carry a label `ℓ` (their syntax-site identity).  Labels need not be unique: sharing
  a label only merges slots, which stays sound (monovariance).
* `choose` is a nondeterministic branch (`if`/`case`), `narrow` keeps a value only if its site has a
  given kind (`case … when Hash`), `proj e i` reads any child whose field index is `i` (a record field,
  or an array element, or a hash key or value), `call f e` calls a function of the program.

`sound`: if a run evaluates `e` (inside the body of `f`) to `w` from an argument described by
`param f`, then `w` is described by the slot of `e` in `Prog.solve` of the generated constraints.
-/

set_option linter.unusedSectionVars false

namespace ProofLean.Sound

variable {L F S K : Type} [DecidableEq L] [DecidableEq F] [DecidableEq S] [DecidableEq K]

/-- Runtime values: trees built at sites. -/
inductive Val (S : Type) where
  | node (h : S) (kids : List (Val S))

/-- Expressions, each with a label. -/
inductive Exp (L F S K : Type) where
  | param (ℓ : L)
  | atom (ℓ : L) (h : S)
  | mk1 (ℓ : L) (h : S) (e : Exp L F S K)
  | mk2 (ℓ : L) (h : S) (e₁ e₂ : Exp L F S K)
  | proj (ℓ : L) (e : Exp L F S K) (i : ℕ)
  | call (ℓ : L) (f : F) (e : Exp L F S K)
  | choose (ℓ : L) (e₁ e₂ : Exp L F S K)
  | narrow (ℓ : L) (e : Exp L F S K) (k : K)

namespace Exp

/-- The label of an expression's root. -/
def lab : Exp L F S K → L
  | param ℓ | atom ℓ _ | mk1 ℓ _ _ | mk2 ℓ _ _ _ | proj ℓ _ _ | call ℓ _ _ | choose ℓ _ _
  | narrow ℓ _ _ => ℓ

/-- Sites constructed in an expression. -/
def sitesIn : Exp L F S K → List S
  | param _ => []
  | atom _ h => [h]
  | mk1 _ h e => h :: e.sitesIn
  | mk2 _ h e₁ e₂ => h :: (e₁.sitesIn ++ e₂.sitesIn)
  | proj _ e _ => e.sitesIn
  | call _ _ e => e.sitesIn
  | choose _ e₁ e₂ => e₁.sitesIn ++ e₂.sitesIn
  | narrow _ e _ => e.sitesIn

end Exp

/-- A program: function names, their bodies, the kind of each site, and the child-to-field map. -/
structure Lang (L F S K : Type) where
  fns : List F
  body : F → Exp L F S K
  kind : S → K
  cellIdx : S → ℕ → ℕ

/-- Slots of the analysis: one per label, a parameter and a return per function, and the field
cells of each site. -/
inductive Slot (L F S : Type) where
  | lab (ℓ : L)
  | param (f : F)
  | ret (f : F)
  | cell (h : S) (i : ℕ)
deriving DecidableEq

namespace Lang

variable (G : Lang L F S K)

/-- Big-step semantics: `Eval a e w` — with argument `a`, expression `e` evaluates to `w`. -/
inductive Eval : Val S → Exp L F S K → Val S → Prop
  | param {a ℓ} : Eval a (.param ℓ) a
  | atom {a ℓ h} : Eval a (.atom ℓ h) (.node h [])
  | mk1 {a ℓ h e v} : Eval a e v → Eval a (.mk1 ℓ h e) (.node h [v])
  | mk2 {a ℓ h e₁ e₂ v₁ v₂} : Eval a e₁ v₁ → Eval a e₂ v₂ → Eval a (.mk2 ℓ h e₁ e₂) (.node h [v₁, v₂])
  | proj {a ℓ e i h kids j} (hj : j < kids.length) :
      Eval a e (.node h kids) → G.cellIdx h j = i → Eval a (.proj ℓ e i) (kids.get ⟨j, hj⟩)
  | call {a ℓ f e v w} : Eval a e v → Eval v (G.body f) w → Eval a (.call ℓ f e) w
  | choose₁ {a ℓ e₁ e₂ v} : Eval a e₁ v → Eval a (.choose ℓ e₁ e₂) v
  | choose₂ {a ℓ e₁ e₂ v} : Eval a e₂ v → Eval a (.choose ℓ e₁ e₂) v
  | narrow {a ℓ e k h kids} : Eval a e (.node h kids) → G.kind h = k →
      Eval a (.narrow ℓ e k) (.node h kids)

/-- All construction sites of the program. -/
def allSites : List S := G.fns.flatMap (fun f => (G.body f).sitesIn)

/-- Constraint generation for an expression in the body of `f`. -/
def gen (f : F) : Exp L F S K → List (Alloc (Slot L F S) S) × List (Guard (Slot L F S) S)
  | .param ℓ => ([], [⟨[], .param f, .lab ℓ, fun _ => true⟩])
  | .atom ℓ h => ([⟨[], .lab ℓ, h⟩], [])
  | .mk1 ℓ h e =>
    let r := gen f e
    (⟨[], .lab ℓ, h⟩ :: r.1, ⟨[], .lab e.lab, .cell h (G.cellIdx h 0), fun _ => true⟩ :: r.2)
  | .mk2 ℓ h e₁ e₂ =>
    let r₁ := gen f e₁
    let r₂ := gen f e₂
    (⟨[], .lab ℓ, h⟩ :: (r₁.1 ++ r₂.1),
      ⟨[], .lab e₁.lab, .cell h (G.cellIdx h 0), fun _ => true⟩ ::
      ⟨[], .lab e₂.lab, .cell h (G.cellIdx h 1), fun _ => true⟩ :: (r₁.2 ++ r₂.2))
  | .proj ℓ e i =>
    let r := gen f e
    (r.1, (G.allSites.map (fun h => (⟨[(.lab e.lab, h)], .cell h i, .lab ℓ, fun _ => true⟩ :
      Guard (Slot L F S) S))) ++ r.2)
  | .call ℓ g e =>
    let r := gen f e
    (r.1, ⟨[], .lab e.lab, .param g, fun _ => true⟩ :: ⟨[], .ret g, .lab ℓ, fun _ => true⟩ :: r.2)
  | .choose ℓ e₁ e₂ =>
    let r₁ := gen f e₁
    let r₂ := gen f e₂
    (r₁.1 ++ r₂.1, ⟨[], .lab e₁.lab, .lab ℓ, fun _ => true⟩ ::
      ⟨[], .lab e₂.lab, .lab ℓ, fun _ => true⟩ :: (r₁.2 ++ r₂.2))
  | .narrow ℓ e k =>
    let r := gen f e
    (r.1, ⟨[], .lab e.lab, .lab ℓ, fun h => decide (G.kind h = k)⟩ :: r.2)

/-- The core program of the whole language program. -/
def toProg : Prog (Slot L F S) S where
  allocs := G.fns.flatMap (fun f => (G.gen f (G.body f)).1)
  guards := G.fns.flatMap (fun f =>
    ⟨[], .lab (G.body f).lab, .ret f, fun _ => true⟩ :: (G.gen f (G.body f)).2)

/-- `e` is a subexpression of `e'`. -/
inductive Sub : Exp L F S K → Exp L F S K → Prop
  | refl {e} : Sub e e
  | mk1 {e e' ℓ h} : Sub e e' → Sub e (.mk1 ℓ h e')
  | mk2l {e e₁ e₂ ℓ h} : Sub e e₁ → Sub e (.mk2 ℓ h e₁ e₂)
  | mk2r {e e₁ e₂ ℓ h} : Sub e e₂ → Sub e (.mk2 ℓ h e₁ e₂)
  | proj {e e' ℓ i} : Sub e e' → Sub e (.proj ℓ e' i)
  | call {e e' ℓ g} : Sub e e' → Sub e (.call ℓ g e')
  | choosel {e e₁ e₂ ℓ} : Sub e e₁ → Sub e (.choose ℓ e₁ e₂)
  | chooser {e e₁ e₂ ℓ} : Sub e e₂ → Sub e (.choose ℓ e₁ e₂)
  | narrow {e e' ℓ k} : Sub e e' → Sub e (.narrow ℓ e' k)

theorem Sub.trans {e e' e'' : Exp L F S K} (h1 : Sub e e') (h2 : Sub e' e'') : Sub e e'' := by
  induction h2 with
  | refl => exact h1
  | mk1 _ ih => exact .mk1 ih
  | mk2l _ ih => exact .mk2l ih
  | mk2r _ ih => exact .mk2r ih
  | proj _ ih => exact .proj ih
  | call _ ih => exact .call ih
  | choosel _ ih => exact .choosel ih
  | chooser _ ih => exact .chooser ih
  | narrow _ ih => exact .narrow ih

/-- Every allocation the generator emits is at a site of the expression. -/
theorem gen_alloc_site {f : F} : ∀ (e : Exp L F S K) (a : Alloc (Slot L F S) S),
    a ∈ (G.gen f e).1 → a.site ∈ e.sitesIn := by
  intro e
  induction e with
  | param ℓ => intro a ha; simp [gen] at ha
  | atom ℓ h => intro a ha; simp only [gen, List.mem_singleton] at ha; subst ha; simp [Exp.sitesIn]
  | mk1 ℓ h e ih =>
    intro a ha
    simp only [gen, List.mem_cons] at ha
    rcases ha with rfl | ha
    · simp [Exp.sitesIn]
    · exact List.mem_cons_of_mem _ (ih a ha)
  | mk2 ℓ h e₁ e₂ ih₁ ih₂ =>
    intro a ha
    simp only [gen, List.mem_cons, List.mem_append] at ha
    rcases ha with rfl | ha | ha
    · simp [Exp.sitesIn]
    · exact List.mem_cons_of_mem _ (List.mem_append_left _ (ih₁ a ha))
    · exact List.mem_cons_of_mem _ (List.mem_append_right _ (ih₂ a ha))
  | proj ℓ e i ih => intro a ha; exact ih a ha
  | call ℓ g e ih => intro a ha; exact ih a ha
  | choose ℓ e₁ e₂ ih₁ ih₂ =>
    intro a ha
    simp only [gen, List.mem_append] at ha
    rcases ha with ha | ha
    · exact List.mem_append_left _ (ih₁ a ha)
    · exact List.mem_append_right _ (ih₂ a ha)
  | narrow ℓ e k ih => intro a ha; exact ih a ha

/-- Constraints of a subexpression are constraints of the whole. -/
theorem gen_sub {f : F} {e e' : Exp L F S K} (h : Sub e e') :
    (∀ a ∈ (G.gen f e).1, a ∈ (G.gen f e').1) ∧ (∀ g ∈ (G.gen f e).2, g ∈ (G.gen f e').2) := by
  induction h with
  | refl => exact ⟨fun a ha => ha, fun g hg => hg⟩
  | mk1 _ ih =>
    exact ⟨fun a ha => List.mem_cons_of_mem _ (ih.1 a ha),
      fun g hg => List.mem_cons_of_mem _ (ih.2 g hg)⟩
  | mk2l _ ih =>
    refine ⟨fun a ha => ?_, fun g hg => ?_⟩
    · simp only [gen]; exact List.mem_cons_of_mem _ (List.mem_append_left _ (ih.1 a ha))
    · simp only [gen]
      exact List.mem_cons_of_mem _ (List.mem_cons_of_mem _ (List.mem_append_left _ (ih.2 g hg)))
  | mk2r _ ih =>
    refine ⟨fun a ha => ?_, fun g hg => ?_⟩
    · simp only [gen]; exact List.mem_cons_of_mem _ (List.mem_append_right _ (ih.1 a ha))
    · simp only [gen]
      exact List.mem_cons_of_mem _ (List.mem_cons_of_mem _ (List.mem_append_right _ (ih.2 g hg)))
  | proj _ ih =>
    refine ⟨fun a ha => ?_, fun g hg => ?_⟩
    · simp only [gen]; exact ih.1 a ha
    · simp only [gen]; exact List.mem_append_right _ (ih.2 g hg)
  | call _ ih =>
    refine ⟨fun a ha => ?_, fun g hg => ?_⟩
    · simp only [gen]; exact ih.1 a ha
    · simp only [gen]; exact List.mem_cons_of_mem _ (List.mem_cons_of_mem _ (ih.2 g hg))
  | choosel _ ih =>
    refine ⟨fun a ha => ?_, fun g hg => ?_⟩
    · simp only [gen]; exact List.mem_append_left _ (ih.1 a ha)
    · simp only [gen]
      exact List.mem_cons_of_mem _ (List.mem_cons_of_mem _ (List.mem_append_left _ (ih.2 g hg)))
  | chooser _ ih =>
    refine ⟨fun a ha => ?_, fun g hg => ?_⟩
    · simp only [gen]; exact List.mem_append_right _ (ih.1 a ha)
    · simp only [gen]
      exact List.mem_cons_of_mem _ (List.mem_cons_of_mem _ (List.mem_append_right _ (ih.2 g hg)))
  | narrow _ ih =>
    refine ⟨fun a ha => ?_, fun g hg => ?_⟩
    · simp only [gen]; exact ih.1 a ha
    · simp only [gen]; exact List.mem_cons_of_mem _ (ih.2 g hg)

/-- Sites of a subexpression are sites of the whole. -/
theorem sites_sub {e e' : Exp L F S K} (h : Sub e e') : ∀ s ∈ e.sitesIn, s ∈ e'.sitesIn := by
  induction h with
  | refl => exact fun s hs => hs
  | mk1 _ ih => exact fun s hs => List.mem_cons_of_mem _ (ih s hs)
  | mk2l _ ih => exact fun s hs => List.mem_cons_of_mem _ (List.mem_append_left _ (ih s hs))
  | mk2r _ ih => exact fun s hs => List.mem_cons_of_mem _ (List.mem_append_right _ (ih s hs))
  | proj _ ih => exact ih
  | call _ ih => exact ih
  | choosel _ ih => exact fun s hs => List.mem_append_left _ (ih s hs)
  | chooser _ ih => exact fun s hs => List.mem_append_right _ (ih s hs)
  | narrow _ ih => exact ih

/-! ## Description of values by the site solution -/

/-- `Desc Pt v w`: value `w` is described by slot `v`: its site reaches `v`, and every child is
described by the field cell it is stored in. -/
inductive Desc (Pt : Set (Slot L F S × S)) : Slot L F S → Val S → Prop
  | node {v h kids} : (v, h) ∈ Pt →
      (∀ j (hj : j < kids.length), Desc Pt (.cell h (G.cellIdx h j)) (kids.get ⟨j, hj⟩)) →
      Desc Pt v (.node h kids)

/-- The least site solution of the generated constraints. -/
def Pt : Set (Slot L F S × S) := ↑G.toProg.solve

/-- Every site in the solution is a construction site of the program. -/
theorem site_of_pt {v : Slot L F S} {h : S} (hp : (v, h) ∈ G.Pt) : h ∈ G.allSites := by
  have hu := G.toProg.toOp.kleene_subset_univ (show (v, h) ∈ G.toProg.solve from hp)
  simp only [Prog.toOp, Prog.univ, Finset.mem_product, Prog.sites, List.mem_toFinset,
    List.mem_map] at hu
  obtain ⟨-, a, ha, rfl⟩ := hu
  obtain ⟨f, hf, ha'⟩ := List.mem_flatMap.1 ha
  exact List.mem_flatMap.2 ⟨f, hf, G.gen_alloc_site _ a ha'⟩

theorem pt_closed {p : Slot L F S × S} (h : p ∈ G.toProg.stepSet (G.Pt)) : p ∈ G.Pt := by
  have := G.toProg.coe_step G.toProg.solve
  rw [G.toProg.solve_fixed] at this
  show p ∈ (↑G.toProg.solve : Set _)
  rw [this]; exact h

/-- An unconditional allocation of the program holds in the solution. -/
theorem pt_alloc {v : Slot L F S} {h : S} (ha : (⟨[], v, h⟩ : Alloc (Slot L F S) S) ∈ G.toProg.allocs) :
    (v, h) ∈ G.Pt :=
  G.pt_closed (Or.inl ⟨_, ha, by simp, rfl⟩)

/-- A flow (unconditional guard) of the program moves descriptions. -/
theorem desc_flow {x y : Slot L F S} {pass : S → Bool}
    (hg : (⟨[], x, y, pass⟩ : Guard (Slot L F S) S) ∈ G.toProg.guards) {h : S} {kids : List (Val S)}
    (hd : Desc G G.Pt x (.node h kids)) (hp : pass h = true) : Desc G G.Pt y (.node h kids) := by
  cases hd with
  | node hx hk =>
    exact .node (G.pt_closed (Or.inr ⟨_, hg, by simp, rfl, hx, hp⟩)) hk

/-- Constraints of an expression inside a function body are constraints of the program. -/
theorem in_prog {f : F} (hf : f ∈ G.fns) {e : Exp L F S K} (hs : Sub e (G.body f)) :
    (∀ a ∈ (G.gen f e).1, a ∈ G.toProg.allocs) ∧ (∀ g ∈ (G.gen f e).2, g ∈ G.toProg.guards) := by
  obtain ⟨h1, h2⟩ := G.gen_sub (f := f) hs
  refine ⟨fun a ha => List.mem_flatMap.2 ⟨f, hf, h1 a ha⟩, fun g hg => ?_⟩
  exact List.mem_flatMap.2 ⟨f, hf, List.mem_cons_of_mem _ (h2 g hg)⟩

/-- **F (soundness).** Every value a terminating run produces is described by the least site
solution of the generated constraints: if `e` occurs in the body of a program function `f`, its
argument is described by `param f`, and the run evaluates `e` to `w`, then `w` is described by
the slot of `e`.  Labels need not be unique. -/
theorem sound (hfns : ∀ f, f ∈ G.fns) :
    ∀ {a : Val S} {e : Exp L F S K} {w : Val S}, Eval G a e w →
      ∀ f, Sub e (G.body f) → Desc G G.Pt (.param f) a → Desc G G.Pt (.lab e.lab) w := by
  intro a e w hev
  induction hev with
  | param =>
    intro f hs ha
    obtain ⟨-, hg⟩ := G.in_prog (hfns f) hs
    cases ha with
    | node hx hk =>
      exact G.desc_flow (hg _ List.mem_cons_self) (.node hx hk) rfl
  | atom =>
    intro f hs _
    obtain ⟨ha, -⟩ := G.in_prog (hfns f) hs
    exact .node (G.pt_alloc (ha _ List.mem_cons_self)) (fun j hj => absurd hj (by simp))
  | @mk1 a ℓ h e v _ ih =>
    intro f hs ha
    obtain ⟨hA, hG⟩ := G.in_prog (hfns f) hs
    have hv := ih f (Sub.mk1 Sub.refl |>.trans hs) ha
    refine .node (G.pt_alloc (hA _ List.mem_cons_self)) (fun j hj => ?_)
    have hj0 : j = 0 := by simpa using hj
    subst hj0
    cases v with
    | node hv' kv =>
      exact G.desc_flow (hG _ List.mem_cons_self) hv rfl
  | @mk2 a ℓ h e₁ e₂ v₁ v₂ _ _ ih₁ ih₂ =>
    intro f hs ha
    obtain ⟨hA, hG⟩ := G.in_prog (hfns f) hs
    have hv₁ := ih₁ f (Sub.mk2l Sub.refl |>.trans hs) ha
    have hv₂ := ih₂ f (Sub.mk2r Sub.refl |>.trans hs) ha
    refine .node (G.pt_alloc (hA _ List.mem_cons_self)) (fun j hj => ?_)
    have hj2 : j = 0 ∨ j = 1 := by simp at hj; omega
    rcases hj2 with rfl | rfl
    · cases v₁ with
      | node _ _ => exact G.desc_flow (hG _ List.mem_cons_self) hv₁ rfl
    · cases v₂ with
      | node _ _ =>
        exact G.desc_flow (hG _ (List.mem_cons_of_mem _ List.mem_cons_self)) hv₂ rfl
  | @proj a ℓ e i h kids j hj _ hidx ih =>
    intro f hs ha
    obtain ⟨-, hG⟩ := G.in_prog (hfns f) hs
    have he := ih f (Sub.proj Sub.refl |>.trans hs) ha
    cases he with
    | node hx hk =>
      have hkid := hk j hj
      rw [hidx] at hkid
      have hsite : h ∈ G.allSites := G.site_of_pt hx
      cases hc : kids.get ⟨j, hj⟩ with
      | node h' kids' =>
        rw [hc] at hkid
        cases hkid with
        | node hcell hk' =>
          refine .node (G.pt_closed (Or.inr ⟨_, hG _ (List.mem_append_left _
            (List.mem_map.2 ⟨h, hsite, rfl⟩)), ?_, rfl, hcell, rfl⟩)) hk'
          intro c hc'
          simp only [List.mem_singleton] at hc'
          subst hc'
          exact hx
  | @call a ℓ g e v w _ _ ih₁ ih₂ =>
    intro f hs ha
    obtain ⟨-, hG⟩ := G.in_prog (hfns f) hs
    have hv := ih₁ f (Sub.call Sub.refl |>.trans hs) ha
    have hpv : Desc G G.Pt (.param g) v := by
      cases v with
      | node _ _ => exact G.desc_flow (hG _ List.mem_cons_self) hv rfl
    have hw := ih₂ g Sub.refl hpv
    have hret : Desc G G.Pt (.ret g) w := by
      cases w with
      | node _ _ =>
        exact G.desc_flow (List.mem_flatMap.2 ⟨g, hfns g, List.mem_cons_self⟩) hw rfl
    cases w with
    | node _ _ => exact G.desc_flow (hG _ (List.mem_cons_of_mem _ List.mem_cons_self)) hret rfl
  | @choose₁ a ℓ e₁ e₂ v _ ih =>
    intro f hs ha
    obtain ⟨-, hG⟩ := G.in_prog (hfns f) hs
    have hv := ih f (Sub.choosel Sub.refl |>.trans hs) ha
    cases v with
    | node _ _ => exact G.desc_flow (hG _ List.mem_cons_self) hv rfl
  | @choose₂ a ℓ e₁ e₂ v _ ih =>
    intro f hs ha
    obtain ⟨-, hG⟩ := G.in_prog (hfns f) hs
    have hv := ih f (Sub.chooser Sub.refl |>.trans hs) ha
    cases v with
    | node _ _ => exact G.desc_flow (hG _ (List.mem_cons_of_mem _ List.mem_cons_self)) hv rfl
  | @narrow a ℓ e k h kids _ hk ih =>
    intro f hs ha
    obtain ⟨-, hG⟩ := G.in_prog (hfns f) hs
    have hv := ih f (Sub.narrow Sub.refl |>.trans hs) ha
    exact G.desc_flow (hG _ List.mem_cons_self) hv (by simp [hk])

end Lang

end ProofLean.Sound
