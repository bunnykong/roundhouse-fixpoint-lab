import ProofLean.Core

/-!
# Lowering the relational relational vocabulary into the core calculus

`REDB` holds the input (extensional) relations of `models/datalog/model.py` exactly as its
`Program` builder records them: sites with their kind and field labels (`Kind`, `Field`), and the
facts `Alloc`, `Flow`, `Load`, `Store`, `Filter`, `Produce`, `ToString`, `Invoke`, `Select`,
`Formal`, `Return`, `Send`, `Method`, `Yield`, `Block`, `Merge`, `Use`, `Unsupported`.

`REDB.lower` compiles every rule of `core_rules` into guarded inclusions and conditional
allocations.  The derived relations of `model.py` (`Flow`, `Target`, `Dispatch`, `MergePair`)
become guards whose conditions are the `Pt` facts their rules join on; `Pt` is the only relation the
core computes.  A field cell is the slot `site ++ "." ++ label`, as in `model.py`.
-/

namespace ProofLean

/-- A construction site or scalar atom: name, kind (head) and field labels. -/
structure RSite where
  name : String
  kind : String
  fields : List String
deriving Repr, DecidableEq

/-- The input relations of the relational model. -/
structure REDB where
  sites : List RSite := []
  alloc : List (String × String) := []
  flow : List (String × String) := []
  load : List (String × String × String) := []
  store : List (String × String × String) := []
  filter : List (String × String × String) := []
  produce : List (String × String × String × String) := []
  toStr : List (String × String) := []
  invoke : List (String × String × String) := []
  select : List (String × String × String) := []
  formal : List (String × String) := []
  ret : List (String × String) := []
  send : List (String × String × String × String × String) := []
  method : List (String × String × String × String) := []
  yieldTo : List (String × String × String) := []
  block : List (String × String × String) := []
  merge : List (String × String × String × String) := []
  use : List (String × String × String) := []
  unsupported : List (String × String) := []
deriving Repr

namespace REDB

variable (e : REDB)

/-- The kind of a site, if declared. -/
def kindOf (h : String) : Option String := (e.sites.find? (·.name = h)).map (·.kind)

/-- Names of the declared sites of a kind. -/
def sitesOfKind (k : String) : List String := (e.sites.filter (·.kind = k)).map (·.name)

/-- The field cell of a site. -/
def cellName (h f : String) : String := h ++ "." ++ f

/-- The kind filter of `Filter`, argument selection and dispatch. -/
def kindIs (k : String) (h : String) : Bool := e.kindOf h == some k

/-- The filter that passes every site. -/
def passAll : String → Bool := fun _ => true

/-- `allocation`, `produce`, `key_to_string`, `merge_result`. -/
def allocs : List (Alloc String String) :=
  e.alloc.map (fun (x, h) => ⟨[], x, h⟩) ++
  e.produce.flatMap (fun (src, k, out, new) =>
    (e.sitesOfKind k).map (fun h => ⟨[(src, h)], out, new⟩)) ++
  e.toStr.flatMap (fun (src, out) =>
    e.sites.map (fun s => ⟨[(src, s.name)], out, "atom:str"⟩)) ++
  e.merge.flatMap (fun (x, y, out, new) =>
    (e.sitesOfKind "hash").flatMap (fun l =>
      (e.sitesOfKind "hash").map (fun r => ⟨[(x, l), (y, r)], out, new⟩)))

/-- `flow` (input edges), `load`, `store`, `filter`, `call_argument`, `call_return`, `dispatch_*`,
`yield_*`, `merge_l`, `merge_r`. -/
def guards : List (Guard String String) :=
  e.flow.map (fun (x, y) => ⟨[], x, y, passAll⟩) ++
  e.load.flatMap (fun (recv, f, out) =>
    e.sites.filterMap (fun s =>
      if f ∈ s.fields then some ⟨[(recv, s.name)], cellName s.name f, out, passAll⟩ else none)) ++
  e.store.flatMap (fun (recv, f, v) =>
    e.sites.filterMap (fun s =>
      if f ∈ s.fields then some ⟨[(recv, s.name)], v, cellName s.name f, passAll⟩ else none)) ++
  e.filter.map (fun (src, k, out) => ⟨[], src, out, e.kindIs k⟩) ++
  e.invoke.flatMap (fun (call, arg, _out) =>
    (e.select.filter (fun c => c.1 = call)).flatMap (fun (_, k, ctx) =>
      (e.formal.filter (fun c => c.1 = ctx)).map (fun (_, param) =>
        ⟨[], arg, param, e.kindIs k⟩))) ++
  e.invoke.flatMap (fun (call, arg, out) =>
    (e.select.filter (fun c => c.1 = call)).flatMap (fun (_, k, ctx) =>
      (e.ret.filter (fun c => c.1 = ctx)).flatMap (fun (_, r) =>
        (e.sitesOfKind k).map (fun h => ⟨[(arg, h)], r, out, passAll⟩)))) ++
  e.send.flatMap (fun (_c, recv, m, arg, out) =>
    (e.method.filter (fun t => t.2.1 = m)).flatMap (fun (k, _, p, r) =>
      (e.sitesOfKind k).flatMap (fun h =>
        [⟨[(recv, h)], arg, p, passAll⟩, ⟨[(recv, h)], r, out, passAll⟩]))) ++
  e.yieldTo.flatMap (fun (b, arg, out) =>
    e.block.flatMap (fun (h, p, r) =>
      [⟨[(b, h)], arg, p, passAll⟩, ⟨[(b, h)], r, out, passAll⟩])) ++
  e.merge.flatMap (fun (x, y, _out, new) =>
    let newFields := ((e.sites.find? (·.name = new)).map (·.fields)).getD []
    (e.sitesOfKind "hash").flatMap (fun l =>
      (e.sitesOfKind "hash").flatMap (fun r =>
        let fl := ((e.sites.find? (·.name = l)).map (·.fields)).getD []
        let fr := ((e.sites.find? (·.name = r)).map (·.fields)).getD []
        (fl.filter (· ∈ newFields)).map (fun f =>
            (⟨[(x, l), (y, r)], cellName l f, cellName new f, passAll⟩ : Guard String String)) ++
        (fr.filter (· ∈ newFields)).map (fun f =>
            (⟨[(x, l), (y, r)], cellName r f, cellName new f, passAll⟩ : Guard String String)))))

/-- The core program of a relational input. -/
def lower : Prog String String := ⟨e.allocs, e.guards⟩

/-- `bad_use`, evaluated on a solution (a post-fixpoint query, not part of the fixpoint). -/
def badUses (pt : Finset (String × String)) : List (String × String) :=
  ((e.use.flatMap (fun (call, src, m) =>
    (e.unsupported.filter (fun u => u.1 = m)).flatMap (fun (_, k) =>
      if (pt.filter (fun p => p.1 = src ∧ e.kindOf p.2 = some k)).Nonempty then [(call, k)]
      else [])))).dedup

end REDB

end ProofLean
