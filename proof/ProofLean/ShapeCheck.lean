import ProofLean.ShapeCases

/-!
# Executable check (goal E), part 2: the verified core against `fold_model.py`

The 12 public shapes are lowered to site constraints (`ProofLean.ShapeCases`, stored in this project), solved by the verified core, and read back as node-path languages up to
five nodes.  `#guard` fails the build unless, on every equation slot of every shape, the verified
least solution has exactly the node paths of fold_model's `ref2` result and of its Kleene ground
truth.
-/

namespace ProofLean.ShapeCheck

open ProofLean

/-- Node paths of slot `v` in the site solution `sol`, with at most `k` nodes. -/
def paths (e : REDB) (sol : Finset (String × String)) : Nat → String → Finset String
  | 0, _ => ∅
  | k + 1, v =>
    (sol.filter (fun p => p.1 = v)).biUnion (fun p =>
      match e.sites.find? (fun s => s.name = p.2) with
      | none => ∅
      | some s =>
        s.fields.foldr (fun f acc => acc ∪
          (paths e sol k (REDB.cellName s.name f)).image (fun q => s.kind ++ ">" ++ f ++ ">" ++ q))
          {s.kind})

structure Row where
  name : String
  facts : Nat
  rounds : Nat
  agreeRef2 : List (String × Bool)
  agreeKleene : List (String × Bool)
deriving Repr

def runShape (c : String × REDB × List (String × List String) × List (String × List String)) : Row :=
  let (name, e, ref2, kl) := c
  let (sol, rn) := e.lower.solveN
  { name := name, facts := sol.card, rounds := rn,
    agreeRef2 := ref2.map (fun (v, ps) => (v, decide (paths e sol 5 v = ps.toFinset))),
    agreeKleene := kl.map (fun (v, ps) => (v, decide (paths e sol 5 v = ps.toFinset))) }

def report : List Row := ShapeCases.all.map runShape

#eval report

#guard report.all (fun r => r.agreeRef2.all (·.2) && r.agreeKleene.all (·.2))

end ProofLean.ShapeCheck
