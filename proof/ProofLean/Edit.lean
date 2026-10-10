import ProofLean.Core
import ProofLean.Incremental
import ProofLean.Stratified

/-!
# Edits: when an incremental run equals a cold run

`ProofLean.Incremental` shows that adding rules warm-starts exactly from the old answer and
that deleting a rule can leave a self-supporting cycle, so a warm start from the old answer is not
exact.  This file gives the two positive results the incremental design needs.

**Generic (any monotone operator on a finite universe).**

* `WarmRun`: a per-run certificate with its `∅` start relaxed to *any seed below
  the least fixpoint*: seed ≤ lfp + justified writes + saturation ⇒ the least fixpoint
  (`WarmRun.eq_kleene`).  Leastness needs no cold start, only a *certified* seed.
* `Record`, `replay`: a persisted evaluation record is the facts a unit transfer read and the
  facts it wrote.  Replaying the records that survive an edit *in their original order against
  the state being rebuilt* (apply a record only when the state already covers its reads) gives a
  state below the new least fixpoint (`replay_subset_kleene`), so it is a certified seed for the
  engine (`IncRun.eq_kleene`).  Deleted units contribute no records; a fact that was supported
  only by a deleted write, directly or around a cycle, is never re-applied, because no record
  that produced it finds its reads covered.  This is exact without any over-deletion: the state is
  rebuilt along a chain, and a chain is well-founded.  The contrast `replayAgainst_old_keeps_cycle`
  shows that checking the reads against the *old* answer instead keeps the stale cycle.

**For the core calculus (`Prog`).**

* `Del`: DRed's over-deletion for an edit `P → P'` (rules removed and added): facts of the old
  solution whose some derivation uses a removed rule or an over-deleted fact.
* `dred_exact`: warm-starting `P'` from the old solution minus `Del` reaches exactly the new least
  solution.  The seed is below the new solution by induction on the Kleene rank of the old
  derivation (`dredSeed_subset_solve`) and it is a post-fixpoint of `P'` (`dredSeed_le_step`), so
  the warm-start theorem applies.  On `Deletion.before → Deletion.after` the over-deletion removes both facts of the
  cycle (`dredSeed_cycle_empty`).

Both routes are exact; they differ in cost.  `Del` propagates along *dependencies* (in a component
where most units reach each other it is the whole component), `replay` propagates along *values*
in time order (a record is skipped only when a fact it read is not yet there).

**Executable, and the necessity of complete reads.**

* `inflate` continues from the replayed state by `Z ↦ Z ∪ F Z` until stable (no post-fixpoint
  hypothesis on the seed), and `incrementalSolve_eq_kleene` says replay-then-inflate computes the cold
  answer; two `#guard`s evaluate it on the cycle against `solve`, with and without the deletion.
* `IncompleteReads`: a record whose recorder missed a read (a missing dependency) is not
  valid (`bad_not_valid`), and replaying it keeps a stale fact above the new least fixpoint
  (`incomplete_reads_not_least`): hypothesis V of `IncRun.eq_kleene` cannot be dropped.
-/

set_option linter.unusedSectionVars false

namespace ProofLean

open Finset

/-! ## Generic: warm runs and replayed records -/

namespace BoundedOp

variable {α : Type*} [DecidableEq α] (o : BoundedOp α)

/-- A certified warm run: like a per-run `Run`, with the start relaxed to any seed below
the least fixpoint.  `n` is the number of writes. -/
structure WarmRun (o : BoundedOp α) where
  S : ℕ → Finset α
  n : ℕ
  start : S 0 ⊆ o.kleene
  justified : ∀ k, k < n → S (k + 1) ⊆ S k ∪ o.F (S k)
  saturated : o.F (S n) ⊆ S n

namespace WarmRun

variable {o}

/-- Every state of a justified run from a certified seed lies below the least fixpoint. -/
theorem below_kleene (r : WarmRun o) : ∀ k, k ≤ r.n → r.S k ⊆ o.kleene := by
  intro k
  induction k with
  | zero => intro _; exact r.start
  | succ k ih =>
    intro hk
    have h1 : r.S k ⊆ o.kleene := ih (by omega)
    calc r.S (k + 1) ⊆ r.S k ∪ o.F (r.S k) := r.justified k (by omega)
      _ ⊆ o.kleene ∪ o.F o.kleene := Finset.union_subset_union h1 (o.mono h1)
      _ = o.kleene := by rw [o.kleene_fixed, Finset.union_self]

/-- **The warm certificate.** Seed below the least fixpoint, justified writes, saturation: the
run ends at the least fixpoint, whatever its schedule. -/
theorem eq_kleene (r : WarmRun o) : r.S r.n = o.kleene :=
  Finset.Subset.antisymm (r.below_kleene r.n le_rfl) (o.kleene_isLeast.2 r.saturated)

end WarmRun

/-- A persisted evaluation record: the facts one unit transfer read, and the facts it wrote. -/
structure Record (α : Type*) where
  reads : Finset α
  write : Finset α

/-- A record is *valid for* `o` when its write is (below) what some monotone transfer below
`o.F` produces from its reads: the unit that produced it is unchanged by the edit and is one of
the new system's transfers. -/
def Record.Valid (o : BoundedOp α) (r : Record α) : Prop :=
  ∃ T : Finset α → Finset α,
    (∀ ⦃X Y : Finset α⦄, X ⊆ Y → T X ⊆ T Y) ∧ (∀ X, T X ⊆ o.F X) ∧ r.write ⊆ T r.reads

/-- A valid record is justified in every state that covers its reads, larger ones included: the
replay check is "reads covered", not "reads equal". -/
theorem Record.justified {o : BoundedOp α} {r : Record α} (hv : r.Valid o) {S : Finset α}
    (hS : r.reads ⊆ S) : r.write ⊆ S ∪ o.F S := by
  obtain ⟨T, hmono, hle, hw⟩ := hv
  exact (hw.trans ((hmono hS).trans (hle S))).trans Finset.subset_union_right

/-- One replay step: apply the record if the state already covers its reads, else skip it. -/
def replayStep (S : Finset α) (r : Record α) : Finset α :=
  if r.reads ⊆ S then S ∪ r.write else S

/-- Replay a trace of records in order, from `∅`. -/
def replay (recs : List (Record α)) : Finset α :=
  recs.foldl replayStep ∅

/-- The same fold with the reads checked against a fixed set `X` (the old answer) instead of the
state being rebuilt.  This is the unsound shortcut, see `replayAgainst_old_keeps_cycle`. -/
def replayAgainst (X : Finset α) (recs : List (Record α)) : Finset α :=
  recs.foldl (fun S r => if r.reads ⊆ X then S ∪ r.write else S) ∅

variable {o}

theorem foldl_replayStep_subset_kleene {recs : List (Record α)} (hv : ∀ r ∈ recs, r.Valid o) :
    ∀ S : Finset α, S ⊆ o.kleene → recs.foldl replayStep S ⊆ o.kleene := by
  induction recs with
  | nil => intro S hS; simpa using hS
  | cons r rs ih =>
    intro S hS
    rw [List.foldl_cons]
    apply ih (fun q hq => hv q (List.mem_cons_of_mem _ hq))
    unfold replayStep
    split_ifs with h
    · apply Finset.union_subset hS
      calc r.write ⊆ S ∪ o.F S := Record.justified (hv r List.mem_cons_self) h
        _ ⊆ o.kleene ∪ o.F o.kleene := Finset.union_subset_union hS (o.mono hS)
        _ = o.kleene := by rw [o.kleene_fixed, Finset.union_self]
    · exact hS

/-- **Replayed records are a certified seed.** If every record in the trace is valid for the new
system, the replayed state lies below the new least fixpoint. -/
theorem replay_subset_kleene {recs : List (Record α)} (hv : ∀ r ∈ recs, r.Valid o) :
    replay recs ⊆ o.kleene :=
  foldl_replayStep_subset_kleene hv ∅ (Finset.empty_subset _)

/-- An incremental run: replay the surviving records, then write only justified facts until
saturation. -/
structure IncRun (o : BoundedOp α) (recs : List (Record α)) where
  S : ℕ → Finset α
  n : ℕ
  valid : ∀ r ∈ recs, r.Valid o
  start : S 0 = replay recs
  justified : ∀ k, k < n → S (k + 1) ⊆ S k ∪ o.F (S k)
  saturated : o.F (S n) ⊆ S n

/-- An incremental run is a warm run from a certified seed. -/
def IncRun.toWarm {recs : List (Record α)} (r : IncRun o recs) : WarmRun o where
  S := r.S
  n := r.n
  start := by rw [r.start]; exact replay_subset_kleene r.valid
  justified := r.justified
  saturated := r.saturated

/-- **Incremental equals cold.** For a monotone system, replaying the records that survive an
edit and continuing with justified writes to saturation gives the cold run's least fixpoint. -/
theorem IncRun.eq_kleene {recs : List (Record α)} (r : IncRun o recs) : r.S r.n = o.kleene :=
  r.toWarm.eq_kleene

end BoundedOp

/-! ## The core calculus: DRed's over-deletion is a certified seed -/

variable {V S : Type*} [DecidableEq V] [DecidableEq S]

namespace Prog

/-- DRed's over-deletion for the edit `P → P'`, relative to the old solution `X`: a fact is
over-deleted when some derivation of it from `X` uses a rule `P'` no longer has, or uses an
over-deleted fact as a condition or as the source of a guard. -/
inductive Del (P P' : Prog V S) (X : Finset (V × S)) : V × S → Prop
  | allocDel (a : Alloc V S) (ha : a ∈ P.allocs) (hna : a ∉ P'.allocs)
      (hc : ∀ c ∈ a.conds, c ∈ X) : Del P P' X (a.dst, a.site)
  | guardDel (g : Guard V S) (hg : g ∈ P.guards) (hng : g ∉ P'.guards)
      (hc : ∀ c ∈ g.conds, c ∈ X) (s : S) (hs : (g.src, s) ∈ X) (hp : g.pass s = true) :
      Del P P' X (g.dst, s)
  | allocTouch (a : Alloc V S) (ha : a ∈ P.allocs) (hc : ∀ c ∈ a.conds, c ∈ X)
      (c : V × S) (hcc : c ∈ a.conds) (hd : Del P P' X c) : Del P P' X (a.dst, a.site)
  | guardTouchCond (g : Guard V S) (hg : g ∈ P.guards) (hc : ∀ c ∈ g.conds, c ∈ X)
      (s : S) (hs : (g.src, s) ∈ X) (hp : g.pass s = true)
      (c : V × S) (hcc : c ∈ g.conds) (hd : Del P P' X c) : Del P P' X (g.dst, s)
  | guardTouchSrc (g : Guard V S) (hg : g ∈ P.guards) (hc : ∀ c ∈ g.conds, c ∈ X)
      (s : S) (hs : (g.src, s) ∈ X) (hp : g.pass s = true) (hd : Del P P' X (g.src, s)) :
      Del P P' X (g.dst, s)

variable (P P' : Prog V S) [DecidablePred (Del P P' P.solve)]

/-- The DRed seed: the old solution minus the over-deleted facts. -/
def dredSeed : Finset (V × S) := P.solve.filter (fun p => ¬ Del P P' P.solve p)

/-- A fact derived from old facts that is not over-deleted is derived by a rule of `P'` from
facts that are not over-deleted. -/
theorem step_of_notDel {Z : Finset (V × S)} (hZ : Z ⊆ P.solve) {p : V × S}
    (hp : p ∈ P.step Z) (hnd : ¬ Del P P' P.solve p) :
    p ∈ P'.step (Z.filter (fun q => ¬ Del P P' P.solve q)) := by
  rcases P.mem_step.1 hp with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h1, h2, h3⟩
  · have hcX : ∀ c ∈ a.conds, c ∈ P.solve := fun c hc' => hZ (Finset.mem_coe.1 (hc c hc'))
    have ha' : a ∈ P'.allocs := by
      by_contra hna
      exact hnd (Del.allocDel a ha hna hcX)
    refine P'.mem_step.2 (Or.inl ⟨a, ha', fun c hc' => ?_, rfl⟩)
    exact Finset.mem_coe.2 (Finset.mem_filter.2
      ⟨Finset.mem_coe.1 (hc c hc'), fun hd => hnd (Del.allocTouch a ha hcX c hc' hd)⟩)
  · obtain ⟨v, s⟩ := p
    change v = g.dst at h1
    subst h1
    change (g.src, s) ∈ Z at h2
    change g.pass s = true at h3
    have hcX : ∀ c ∈ g.conds, c ∈ P.solve := fun c hc' => hZ (Finset.mem_coe.1 (hc c hc'))
    have hsX : (g.src, s) ∈ P.solve := hZ h2
    have hg' : g ∈ P'.guards := by
      by_contra hng
      exact hnd (Del.guardDel g hg hng hcX s hsX h3)
    refine P'.mem_step.2 (Or.inr ⟨g, hg', fun c hc' => ?_, rfl, ?_, h3⟩)
    · exact Finset.mem_coe.2 (Finset.mem_filter.2
        ⟨Finset.mem_coe.1 (hc c hc'), fun hd => hnd (Del.guardTouchCond g hg hcX s hsX h3 c hc' hd)⟩)
    · exact Finset.mem_coe.2 (Finset.mem_filter.2
        ⟨h2, fun hd => hnd (Del.guardTouchSrc g hg hcX s hsX h3 hd)⟩)

/-- **The DRed seed is below the new solution.**  By induction on the Kleene rank of a fact's
old derivation: a surviving fact is derived by a surviving rule from surviving facts of lower
rank. -/
theorem dredSeed_subset_solve : dredSeed P P' ⊆ P'.solve := by
  have key : ∀ k, ∀ p ∈ P.step^[k] ∅, ¬ Del P P' P.solve p → p ∈ P'.solve := by
    intro k
    induction k with
    | zero => intro p hp; simp at hp
    | succ k ih =>
      intro p hp hnd
      rw [Function.iterate_succ_apply'] at hp
      have hZ : P.step^[k] ∅ ⊆ P.solve := P.toOp.iterate_subset_kleene (Finset.empty_subset _) k
      have hstep := step_of_notDel P P' hZ hp hnd
      have hsub : (P.step^[k] ∅).filter (fun q => ¬ Del P P' P.solve q) ⊆ P'.solve := by
        intro q hq
        rw [Finset.mem_filter] at hq
        exact ih q hq.1 hq.2
      exact P'.solve_closed (P'.step_mono hsub hstep)
  intro p hp
  rw [dredSeed, Finset.mem_filter] at hp
  have hX : P.solve = P.step^[P.solveN.2] ∅ := P.toOp.kleene_eq_iterate
  exact key _ p (hX ▸ hp.1) hp.2

/-- The DRed seed is a post-fixpoint of the new program: everything it keeps is re-derived by a
surviving rule from what it keeps. -/
theorem dredSeed_le_step : dredSeed P P' ⊆ P'.step (dredSeed P P') := by
  intro p hp
  rw [dredSeed, Finset.mem_filter] at hp
  have hp' : p ∈ P.step P.solve := by rw [P.solve_fixed]; exact hp.1
  exact step_of_notDel P P' (le_refl _) hp' hp.2

theorem dredSeed_subset_univ : dredSeed P P' ⊆ P'.univ :=
  (dredSeed_subset_solve P P').trans P'.toOp.kleene_subset_univ

/-- **Deletion is exact after DRed's over-deletion.**  Warm-starting the edited program from the
old solution minus the over-deleted facts reaches exactly the new least solution. -/
theorem dred_exact :
    (P'.toOp.kleeneAux (dredSeed P P') (dredSeed_subset_univ P P') (dredSeed_le_step P P')).1 =
      P'.solve :=
  P'.toOp.kleeneAux_eq_kleene_of_le _ _ _ (dredSeed_subset_solve P P')

end Prog

/-! ## The self-supporting cycle, both ways -/

namespace EditCycle

open Deletion BoundedOp

/-- The old answer of the cycle is both facts. -/
theorem before_solve_eq : before.solve = {(Slot.x, ()), (Slot.y, ())} := by
  ext p
  constructor
  · intro _
    obtain ⟨v, ⟨⟩⟩ := p
    cases v <;> simp
  · intro _
    exact mem_before p

/-- The seed `x` is over-deleted: its only rule was removed. -/
theorem del_x : Prog.Del before after before.solve (Slot.x, ()) :=
  Prog.Del.allocDel (⟨[], Slot.x, ()⟩ : Alloc Slot Unit) (by simp [before]) (by simp [after])
    (by simp)

/-- `y` is over-deleted: it was copied from the over-deleted `x`. -/
theorem del_y : Prog.Del before after before.solve (Slot.y, ()) :=
  Prog.Del.guardTouchSrc (⟨[], Slot.x, Slot.y, fun _ => true⟩ : Guard Slot Unit)
    (by simp [before]) (by simp) () (mem_before _) rfl del_x

/-- DRed's seed for the edit is empty, so the warm start computes `after.solve = ∅`
(`dred_exact`), where the plain warm start from the old answer stayed at the cycle
(`deletion_keeps_cycle`). -/
theorem dredSeed_cycle_empty [DecidablePred (Prog.Del before after before.solve)] :
    Prog.dredSeed before after = ∅ := by
  apply Finset.subset_empty.1
  intro p hp
  rw [Prog.dredSeed, Finset.mem_filter] at hp
  obtain ⟨v, ⟨⟩⟩ := p
  cases v
  · exact absurd del_x hp.2
  · exact absurd del_y hp.2

/-- The old run's trace: the seed's write, then the two copies around the cycle. -/
def cycleTrace : List (Record (Slot × Unit)) :=
  [⟨∅, {(Slot.x, ())}⟩, ⟨{(Slot.x, ())}, {(Slot.y, ())}⟩, ⟨{(Slot.y, ())}, {(Slot.x, ())}⟩]

/-- Replaying the whole trace rebuilds the old answer. -/
theorem replay_cycle_full : replay cycleTrace = {(Slot.x, ()), (Slot.y, ())} := by decide

/-- After the edit deletes the seed's unit, its record is gone; the two copies find their reads
uncovered in time order and are skipped: the replay is `∅ = after.solve`, with no over-deletion
computed. -/
theorem replay_cycle_deleted : replay cycleTrace.tail = ∅ := by decide

/-- Checking the reads against the old answer instead keeps the stale cycle: both copies read a
fact the old answer had, so both are applied, and the self-supporting pair survives. -/
theorem replayAgainst_old_keeps_cycle :
    replayAgainst {(Slot.x, ()), (Slot.y, ())} cycleTrace.tail = {(Slot.x, ()), (Slot.y, ())} := by
  decide

end EditCycle

/-! ## An executable continuation: inflate from the replayed seed -/

namespace BoundedOp

variable {α : Type*} [DecidableEq α]

/-- Inflationary iteration `Z ↦ Z ∪ F Z` from a seed until nothing is added.  Unlike `kleeneAux` it
needs no post-fixpoint hypothesis on the seed, which a replayed state does not satisfy in general. -/
def inflate (o : BoundedOp α) (Z : Finset α) (hU : Z ⊆ o.U) : Finset α :=
  if _hfix : Z ∪ o.F Z = Z then Z
  else o.inflate (Z ∪ o.F Z) (Finset.union_subset hU (o.bound hU))
termination_by o.U.card - Z.card
decreasing_by
  have hss : Z ⊂ Z ∪ o.F Z :=
    Finset.ssubset_iff_subset_ne.2 ⟨Finset.subset_union_left, fun h => _hfix h.symm⟩
  have h1 := Finset.card_lt_card hss
  have h2 : (Z ∪ o.F Z).card ≤ o.U.card :=
    Finset.card_le_card (Finset.union_subset hU (o.bound hU))
  omega

/-- The result is a pre-fixpoint, below every pre-fixpoint above the seed, and above the seed. -/
theorem inflate_spec (o : BoundedOp α) (Z : Finset α) (hU : Z ⊆ o.U) :
    o.F (o.inflate Z hU) ⊆ o.inflate Z hU ∧
      (∀ Y : Finset α, Z ⊆ Y → o.F Y ⊆ Y → o.inflate Z hU ⊆ Y) ∧ Z ⊆ o.inflate Z hU := by
  induction Z, hU using inflate.induct (o := o) with
  | case1 Z hU hfix =>
    rw [inflate, dite_eq_left hfix]
    exact ⟨(Finset.subset_union_right).trans (le_of_eq hfix), fun Y hZY _ => hZY, le_rfl⟩
  | case2 Z hU hfix ih =>
    rw [inflate, dite_eq_right hfix]
    obtain ⟨h1, h2, h3⟩ := ih
    refine ⟨h1, fun Y hZY hY => h2 Y ?_ hY, Finset.subset_union_left.trans h3⟩
    exact Finset.union_subset hZY ((o.mono hZY).trans hY)

/-- Inflating from a seed below the least fixpoint reaches it. -/
theorem inflate_eq_kleene (o : BoundedOp α) (Z : Finset α) (hU : Z ⊆ o.U) (hZ : Z ⊆ o.kleene) :
    o.inflate Z hU = o.kleene := by
  obtain ⟨h1, h2, -⟩ := o.inflate_spec Z hU
  exact Finset.Subset.antisymm (h2 _ hZ (le_of_eq o.kleene_fixed)) (o.kleene_isLeast.2 h1)

theorem replay_subset_univ {o : BoundedOp α} {recs : List (Record α)}
    (hv : ∀ r ∈ recs, r.Valid o) : replay recs ⊆ o.U :=
  (replay_subset_kleene hv).trans o.kleene_subset_univ

/-- **The incremental solve, executable:** replay the surviving records, then inflate. -/
def incrementalSolve (o : BoundedOp α) (recs : List (Record α)) (hv : ∀ r ∈ recs, r.Valid o) :
    Finset α :=
  o.inflate (replay recs) (replay_subset_univ hv)

/-- It computes the cold run's least fixpoint. -/
theorem incrementalSolve_eq_kleene (o : BoundedOp α) (recs : List (Record α))
    (hv : ∀ r ∈ recs, r.Valid o) : o.incrementalSolve recs hv = o.kleene :=
  o.inflate_eq_kleene _ _ (replay_subset_kleene hv)

end BoundedOp

/-! The cycle, end to end, by evaluation: no edit replays the whole trace and reaches the old answer;
the seed's deletion replays the two copies, keeps nothing, and reaches the new answer `∅`. -/
#guard Deletion.before.toOp.inflate (BoundedOp.replay EditCycle.cycleTrace) (by decide) =
  Deletion.before.solve
#guard Deletion.after.toOp.inflate (BoundedOp.replay EditCycle.cycleTrace.tail) (by decide) =
  Deletion.after.solve

/-! ## Complete reads are necessary: a missing dependency -/

namespace IncompleteReads

open Deletion BoundedOp

/-- `y` is derived from `x`; nothing derives `x` once the seed's rule is gone. -/
def G (Z : Finset (Slot × Unit)) : Finset (Slot × Unit) :=
  if (Slot.x, ()) ∈ Z then {(Slot.y, ())} else ∅

def oG : BoundedOp (Slot × Unit) where
  F := G
  U := {(Slot.x, ()), (Slot.y, ())}
  mono := by
    intro X Y h
    unfold G
    split_ifs with hx hy
    · exact le_rfl
    · exact absurd (h hx) hy
    · exact Finset.empty_subset _
    · exact le_rfl
  bound := by
    intro X _
    unfold G
    split_ifs
    · decide
    · exact Finset.empty_subset _

theorem kleene_empty : oG.kleene = ∅ :=
  Finset.subset_empty.1 (oG.kleene_isLeast.2 (by show G ∅ ⊆ ∅; simp [G]))

/-- The copy `x → y` as a recorder that missed the read of `x` would store it. -/
def badRecord : Record (Slot × Unit) := ⟨∅, {(Slot.y, ())}⟩

theorem replay_bad : replay [badRecord] = {(Slot.y, ())} := by decide

/-- An incomplete record is not valid: no monotone transfer below `G` writes `y` from nothing. -/
theorem bad_not_valid : ¬ badRecord.Valid oG := by
  rintro ⟨T, -, hle, hw⟩
  have h1 : (Slot.y, ()) ∈ T badRecord.reads := hw (by simp [badRecord])
  have h2 := hle badRecord.reads h1
  simp [oG, G, badRecord] at h2

/-- And replaying it after the seed's deletion keeps the stale `y`, above the new least fixpoint:
the hypothesis V of `IncRun.eq_kleene` cannot be dropped. -/
theorem incomplete_reads_not_least : ¬ replay [badRecord] ⊆ oG.kleene := by
  rw [replay_bad, kleene_empty]
  decide

end IncompleteReads

end ProofLean
