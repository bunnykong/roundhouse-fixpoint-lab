import ProofLean.Lower
import Lean.Data.Json

/-!
# The verified core as a differential oracle

`lake env lean --run ProofLean/Oracle.lean INPUT.json` reads the reframer's input relations as JSON,
lowers them (`REDB.lower`), solves them with the verified naive, semi-naive and worklist solvers,
and prints the least solution as JSON.  It is meant for diffing another implementation (model.py,
or Roundhouse's Rust core once an extractor emits these relations) against the machine-checked one.

Input: an object with `"sites": [[name, kind, [field, …]], …]` and any of the relations `Alloc`,
`Flow`, `Load`, `Store`, `Filter`, `Produce`, `ToString`, `Invoke`, `Select`, `Formal`, `Return`,
`Send`, `Method`, `Yield`, `Block`, `Merge`, `Use`, `Unsupported`, each a list of string tuples in
`model.py`'s column order.

Output: `{"pt": [[slot, site], …] (sorted), "bad_use": […], "rounds_naive": n, "rounds_semi": n,
"facts": n, "solvers_agree": true}`.
-/

namespace ProofLean.Oracle

open Lean ProofLean

def strs (j : Json) : Except String (List String) := do
  let arr ← j.getArr?
  arr.toList.mapM (fun x => x.getStr?)

def rows (o : Json) (rel : String) (n : Nat) : Except String (List (List String)) := do
  match o.getObjVal? rel with
  | .error _ => pure []
  | .ok j =>
    let arr ← j.getArr?
    arr.toList.mapM (fun r => do
      let xs ← strs r
      if xs.length = n then pure xs else throw s!"{rel}: expected {n} columns")

def get2 (xs : List String) : String × String := (xs.getD 0 "", xs.getD 1 "")
def get3 (xs : List String) : String × String × String := (xs.getD 0 "", xs.getD 1 "", xs.getD 2 "")
def get4 (xs : List String) : String × String × String × String :=
  (xs.getD 0 "", xs.getD 1 "", xs.getD 2 "", xs.getD 3 "")
def get5 (xs : List String) : String × String × String × String × String :=
  (xs.getD 0 "", xs.getD 1 "", xs.getD 2 "", xs.getD 3 "", xs.getD 4 "")

def parse (o : Json) : Except String REDB := do
  let sitesJ ← (o.getObjValD "sites").getArr?
  let sites ← sitesJ.toList.mapM (fun s => do
    let a ← s.getArr?
    let name ← (a.getD 0 Json.null).getStr?
    let kind ← (a.getD 1 Json.null).getStr?
    let fields ← strs (a.getD 2 (Json.arr #[]))
    pure (⟨name, kind, fields⟩ : RSite))
  pure {
    sites := sites
    alloc := (← rows o "Alloc" 2).map get2
    flow := (← rows o "Flow" 2).map get2
    load := (← rows o "Load" 3).map get3
    store := (← rows o "Store" 3).map get3
    filter := (← rows o "Filter" 3).map get3
    produce := (← rows o "Produce" 4).map get4
    toStr := (← rows o "ToString" 2).map get2
    invoke := (← rows o "Invoke" 3).map get3
    select := (← rows o "Select" 3).map get3
    formal := (← rows o "Formal" 2).map get2
    ret := (← rows o "Return" 2).map get2
    send := (← rows o "Send" 5).map get5
    method := (← rows o "Method" 4).map get4
    yieldTo := (← rows o "Yield" 3).map get3
    block := (← rows o "Block" 3).map get3
    merge := (← rows o "Merge" 4).map get4
    use := (← rows o "Use" 3).map get3
    unsupported := (← rows o "Unsupported" 2).map get2 }

/-- The solution as a sorted list (candidates are the program's slots × sites). -/
def toRows (P : Prog String String) (sol : Finset (String × String)) : List (String × String) :=
  let dsts := (P.allocs.map (·.dst) ++ P.guards.map (·.dst)).dedup
  let sites := (P.allocs.map (·.site)).dedup
  let cands := dsts.flatMap (fun v => sites.map (fun h => (v, h)))
  (cands.filter (· ∈ sol)).mergeSort (fun a b => decide (a.1 < b.1 ∨ (a.1 = b.1 ∧ a.2 ≤ b.2)))

def pairJson (p : String × String) : Json := Json.arr #[Json.str p.1, Json.str p.2]

def solveJson (e : REDB) : Json :=
  let P := e.lower
  let (sol, rn) := P.solveN
  let (solSN, rs) := P.solveSN
  let w := P.solveW (BoundedOp.Sched.fifo _)
  Json.mkObj [
    ("pt", Json.arr ((toRows P sol).map pairJson).toArray),
    ("bad_use", Json.arr ((e.badUses sol).map pairJson).toArray),
    ("rounds_naive", Json.num rn),
    ("rounds_semi", Json.num rs),
    ("facts", Json.num sol.card),
    ("solvers_agree", Json.bool (decide (sol = solSN ∧ sol = w)))]

end ProofLean.Oracle

open ProofLean.Oracle in
def main (args : List String) : IO UInt32 := do
  match args with
  | [path] =>
    let text ← IO.FS.readFile path
    match Lean.Json.parse text >>= parse with
    | .error err => IO.eprintln s!"oracle: {err}"; pure 2
    | .ok e => IO.println (solveJson e).compress; pure 0
  | _ => IO.eprintln "usage: lake env lean --run ProofLean/Oracle.lean INPUT.json"; pure 2
