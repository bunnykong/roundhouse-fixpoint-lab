import ProofLean.Cases
import ProofLean.Denotation
import ProofLean.Equiv
import ProofLean.Stratified

/-!
# Executable check (goal E), part 1: the verified core against `model.py`

For every case of the relational experiment, the verified core lowers `model.py`'s own input
relations (`ProofLean.Cases`, generated) and solves them three ways: naive, semi-naive and
worklist (FIFO and LIFO).  `#guard` fails the build unless all four results equal `model.py`'s
solved `Pt` relation fact for fact, and the post-fixpoint `bad_use` query equals `model.py`'s
`BadUse` rows.
-/

namespace ProofLean.Check

open ProofLean

/-- One row of the report. -/
structure Row where
  name : String
  facts : Nat
  expected : Nat
  roundsNaive : Nat
  roundsSemi : Nat
  univSize : Nat
  allAgree : Bool
  matchesModel : Bool
  badUseMatches : Bool
deriving Repr

def runCase (c : String × REDB × List (String × String) × List (String × String) ×
    List (String × String)) : Row :=
  let (name, e, pt, bad, _) := c
  let P := e.lower
  let (sol, rn) := P.solveN
  let (solSN, rs) := P.solveSN
  let w1 := P.solveW (BoundedOp.Sched.fifo _)
  let w2 := P.solveW (BoundedOp.Sched.lifo _)
  let exp := pt.toFinset
  { name := name, facts := sol.card, expected := exp.card, roundsNaive := rn, roundsSemi := rs,
    univSize := P.univ.card,
    allAgree := decide (sol = solSN ∧ sol = w1 ∧ sol = w2),
    matchesModel := decide (sol = exp),
    badUseMatches := decide ((e.badUses sol).toFinset = bad.toFinset) }

def report : List Row := Cases.all.map runCase

#eval report

#guard report.all (fun r => r.allAgree && r.matchesModel && r.badUseMatches)

-- Every case is well formed, so `Equiv.pt_iff` applies to it: the core's answer is model.py's
-- least model by proof, not only by this comparison.
#guard Cases.all.all (fun c => Equiv.wfb c.2.1)

/-! ## Plain against productivity-refined (goal D on the relational experiment's cases)

The signature of a relational case: arity and cells from `Field`, and record fields (`record_*`
kinds) required; `Array`/`Hash` fields optional (empty containers), as in `model.py`'s
`productive_records`. -/

/-- Fields of a declared site. -/
def fieldsOf (e : REDB) (h : String) : List String :=
  ((e.sites.find? (fun s => s.name = h)).map (·.fields)).getD []

/-- The signature of a relational case. -/
def sigOf (e : REDB) : Sig String String where
  ar h := (fieldsOf e h).length
  cell h i := REDB.cellName h ((fieldsOf e h).getD i.val "")
  req h _ := ((e.kindOf h).map (fun k => k.startsWith "record_")).getD false

/-- `pt` facts of the refined solution. -/
def ptsR (e : REDB) : Finset (String × String) :=
  let R := e.lower.solveR (sigOf e)
  (e.lower.univ).filter (fun p => RFact.pt p.1 p.2 ∈ R)

structure RowR where
  name : String
  plain : Nat
  refined : Nat
  equal : Bool
  refinedSubset : Bool
  extraPlainFacts : List (String × String)
deriving Repr

def runRefined (c : String × REDB × List (String × String) × List (String × String) ×
    List (String × String)) : RowR :=
  let (name, e, _, _, _) := c
  let sol := e.lower.solve
  let r := ptsR e
  { name := name, plain := sol.card, refined := r.card, equal := decide (sol = r),
    refinedSubset := decide (r ⊆ sol),
    extraPlainFacts := (Cases.all.find? (fun c => c.1 = name)).elim [] (fun c =>
      c.2.2.1.filter (fun p => p ∉ r)) }

def reportR : List RowR := Cases.all.map runRefined

#eval reportR

-- The refined solution is below the plain one everywhere (`ptPlus_subset_solve`), and equal to it
-- on every case except the unsafe re-embedding, whose `{b: b}` record cycle is unproductive.
#guard reportR.all (fun r => r.refinedSubset && (r.equal || r.name == "reembed"))
#guard reportR.any (fun r => r.name == "reembed" && !r.equal)

/-! ## Dependency-ordered evaluation on the 64-link chain

`R63 = Integer` and `R(i) ⊇ R(i+1)`: rank `R(i)` by `63 - i` (the topological order).  The layered
evaluation (`Prog.layer`) reaches the least solution, and each rank's local fixpoint takes one
round (`Prog.strict_one_round`): 64 slot evaluations, against 64 whole-program rounds. -/

/-- The chain's ranks: `R(i)` gets `63 - i`; anything else is above the chain. -/
def chainRank (v : String) : ℕ := 63 - ((v.drop 1).toNat?.getD 0)

def chainP : Prog String String := Cases.c_chain64.lower

#guard (chainP.layer chainRank 64).1 = chainP.solve
#guard (List.range 64).all (fun r =>
  ((chainP.localOp chainRank (chainP.layer chainRank r).1 (chainP.layer chainRank r).2 r).kleeneN.2 ≤ 1))

end ProofLean.Check
