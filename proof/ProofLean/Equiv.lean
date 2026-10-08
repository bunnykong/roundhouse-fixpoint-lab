import ProofLean.Lower

/-!
# The lowering is exact: the core computes model.py's own least model

`RefStep e` states the rules of `models/datalog/model.py`'s `core_rules`, verbatim, as a
monotone operator on the reframer's derived facts (`Pt`, `Flow`, `Target`, `Dispatch`,
`MergePair`): the 19 rules that derive them (`call_active` and `bad_use` derive relations nothing
reads), with the input `Flow` facts included.  Its least fixpoint is the least Herbrand model of
those rules on input `e`.

`pt_iff`: for every well-formed input (site names unique; every allocated, produced or merged site
declared), `Pt(v, h)` holds in that least model **iff** `(v, h)` is in `Prog.solve` of the lowered
core program.  So every theorem about the core (termination, leastness, semi-naive, worklist,
denotation) is a theorem about model.py's rule set, for every input, not only the 18 checked cases.
-/

namespace ProofLean.Equiv

open ProofLean

/-- The reframer's derived facts. -/
inductive DFact
  | pt (v h : String)
  | flow (x y : String)
  | target (call arg out ctx : String)
  | disp (c arg out p r : String)
  | mpair (l r out new : String)

variable (e : REDB)

/-- `Kind(h, k)`, from the site declarations. -/
def Kind (h k : String) : Prop := ∃ s ∈ e.sites, s.name = h ∧ s.kind = k

/-- `Field(h, f, cell)`, from the site declarations. -/
def Field (h f cell : String) : Prop :=
  ∃ s ∈ e.sites, s.name = h ∧ f ∈ s.fields ∧ cell = REDB.cellName h f

/-- The rules of `core_rules`, one disjunct each, in model.py's order (input `Flow` facts second). -/
def RefStep (X : Set DFact) : Set DFact := fun d =>
  (∃ x h, d = .pt x h ∧ (x, h) ∈ e.alloc) ∨                                         -- input Alloc
  (∃ x y, d = .flow x y ∧ (x, y) ∈ e.flow) ∨                                        -- input Flow
  (∃ x y h, d = .pt y h ∧ DFact.flow x y ∈ X ∧ DFact.pt x h ∈ X) ∨                   -- flow
  (∃ recv f out h cell, d = .flow cell out ∧ (recv, f, out) ∈ e.load ∧
      DFact.pt recv h ∈ X ∧ Field e h f cell) ∨                                    -- load
  (∃ recv f v h cell, d = .flow v cell ∧ (recv, f, v) ∈ e.store ∧
      DFact.pt recv h ∈ X ∧ Field e h f cell) ∨                                    -- store
  (∃ src k out h, d = .pt out h ∧ (src, k, out) ∈ e.filter ∧ DFact.pt src h ∈ X ∧
      Kind e h k) ∨                                                                 -- filter
  (∃ src k out new h, d = .pt out new ∧ (src, k, out, new) ∈ e.produce ∧
      DFact.pt src h ∈ X ∧ Kind e h k) ∨                                            -- produce
  (∃ src out h, d = .pt out "atom:str" ∧ (src, out) ∈ e.toStr ∧ DFact.pt src h ∈ X) ∨ -- key_to_string
  (∃ call arg out ctx h k, d = .target call arg out ctx ∧ (call, arg, out) ∈ e.invoke ∧
      DFact.pt arg h ∈ X ∧ Kind e h k ∧ (call, k, ctx) ∈ e.select) ∨                -- call_target
  (∃ call arg out ctx h k param, d = .pt param h ∧ DFact.target call arg out ctx ∈ X ∧
      DFact.pt arg h ∈ X ∧ Kind e h k ∧ (call, k, ctx) ∈ e.select ∧
      (ctx, param) ∈ e.formal) ∨                                                    -- call_argument
  (∃ call arg out ctx r, d = .flow r out ∧ DFact.target call arg out ctx ∈ X ∧
      (ctx, r) ∈ e.ret) ∨                                                           -- call_return
  (∃ c recv m arg out h k p r, d = .disp c arg out p r ∧ (c, recv, m, arg, out) ∈ e.send ∧
      DFact.pt recv h ∈ X ∧ Kind e h k ∧ (k, m, p, r) ∈ e.method) ∨                 -- dispatch
  (∃ c arg out p r, d = .flow arg p ∧ DFact.disp c arg out p r ∈ X) ∨                -- dispatch_argument
  (∃ c arg out p r, d = .flow r out ∧ DFact.disp c arg out p r ∈ X) ∨                -- dispatch_return
  (∃ b arg out h p r, d = .flow arg p ∧ (b, arg, out) ∈ e.yieldTo ∧
      DFact.pt b h ∈ X ∧ (h, p, r) ∈ e.block) ∨                                     -- yield_argument
  (∃ b arg out h p r, d = .flow r out ∧ (b, arg, out) ∈ e.yieldTo ∧
      DFact.pt b h ∈ X ∧ (h, p, r) ∈ e.block) ∨                                     -- yield_return
  (∃ x y out new l r, d = .mpair l r out new ∧ (x, y, out, new) ∈ e.merge ∧
      DFact.pt x l ∈ X ∧ Kind e l "hash" ∧ DFact.pt y r ∈ X ∧ Kind e r "hash") ∨    -- merge_pair
  (∃ l r out new, d = .pt out new ∧ DFact.mpair l r out new ∈ X) ∨                   -- merge_result
  (∃ l r out new f src dst, d = .flow src dst ∧ DFact.mpair l r out new ∈ X ∧
      Field e l f src ∧ Field e new f dst) ∨                                        -- merge_l
  (∃ l r out new f src dst, d = .flow src dst ∧ DFact.mpair l r out new ∈ X ∧
      Field e r f src ∧ Field e new f dst)                                          -- merge_r

theorem RefStep_mono : Monotone (RefStep e) := by
  intro X Y hXY d hd
  unfold RefStep at hd ⊢
  rcases hd with h | h | ⟨x, y, h, rfl, h1, h2⟩ | ⟨recv, f, out, h, cell, rfl, h1, h2, h3⟩ |
    ⟨recv, f, v, h, cell, rfl, h1, h2, h3⟩ | ⟨src, k, out, h, rfl, h1, h2, h3⟩ |
    ⟨src, k, out, new, h, rfl, h1, h2, h3⟩ | ⟨src, out, h, rfl, h1, h2⟩ |
    ⟨call, arg, out, ctx, h, k, rfl, h1, h2, h3, h4⟩ |
    ⟨call, arg, out, ctx, h, k, param, rfl, h1, h2, h3, h4, h5⟩ |
    ⟨call, arg, out, ctx, r, rfl, h1, h2⟩ | ⟨c, recv, m, arg, out, h, k, p, r, rfl, h1, h2, h3, h4⟩ |
    ⟨c, arg, out, p, r, rfl, h1⟩ | ⟨c, arg, out, p, r, rfl, h1⟩ |
    ⟨b, arg, out, h, p, r, rfl, h1, h2, h3⟩ | ⟨b, arg, out, h, p, r, rfl, h1, h2, h3⟩ |
    ⟨x, y, out, new, l, r, rfl, h1, h2, h3, h4, h5⟩ | ⟨l, r, out, new, rfl, h1⟩ |
    ⟨l, r, out, new, f, src, dst, rfl, h1, h2, h3⟩ | ⟨l, r, out, new, f, src, dst, rfl, h1, h2, h3⟩
  · exact Or.inl h
  · exact Or.inr (Or.inl h)
  · exact Or.inr (Or.inr (Or.inl ⟨x, y, h, rfl, hXY h1, hXY h2⟩))
  · exact Or.inr (Or.inr (Or.inr (Or.inl ⟨recv, f, out, h, cell, rfl, h1, hXY h2, h3⟩)))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inl ⟨recv, f, v, h, cell, rfl, h1, hXY h2, h3⟩))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl ⟨src, k, out, h, rfl, h1, hXY h2, h3⟩)))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl
      ⟨src, k, out, new, h, rfl, h1, hXY h2, h3⟩))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl
      ⟨src, out, h, rfl, h1, hXY h2⟩)))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl
      ⟨call, arg, out, ctx, h, k, rfl, h1, hXY h2, h3, h4⟩))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl
      ⟨call, arg, out, ctx, h, k, param, rfl, hXY h1, hXY h2, h3, h4, h5⟩)))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
      (Or.inl ⟨call, arg, out, ctx, r, rfl, hXY h1, h2⟩))))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
      (Or.inr (Or.inl ⟨c, recv, m, arg, out, h, k, p, r, rfl, h1, hXY h2, h3, h4⟩)))))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
      (Or.inr (Or.inr (Or.inl ⟨c, arg, out, p, r, rfl, hXY h1⟩))))))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
      (Or.inr (Or.inr (Or.inr (Or.inl ⟨c, arg, out, p, r, rfl, hXY h1⟩)))))))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
      (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl ⟨b, arg, out, h, p, r, rfl, h1, hXY h2, h3⟩))))))))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
      (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl
        ⟨b, arg, out, h, p, r, rfl, h1, hXY h2, h3⟩)))))))))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
      (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl
        ⟨x, y, out, new, l, r, rfl, h1, hXY h2, h3, hXY h4, h5⟩))))))))))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
      (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl
        ⟨l, r, out, new, rfl, hXY h1⟩)))))))))))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
      (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl
        ⟨l, r, out, new, f, src, dst, rfl, hXY h1, h2, h3⟩))))))))))))))))))
  · exact Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
      (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr
        ⟨l, r, out, new, f, src, dst, rfl, hXY h1, h2, h3⟩))))))))))))))))))

/-- The rules as a monotone operator. -/
def RefHom : Set DFact →o Set DFact := ⟨RefStep e, RefStep_mono e⟩

/-- The least Herbrand model of model.py's rules on input `e`. -/
def Model : Set DFact := OrderHom.lfp (RefHom e)

theorem model_closed {d : DFact} (h : d ∈ RefStep e (Model e)) : d ∈ Model e := by
  have := OrderHom.map_lfp (RefHom e)
  show d ∈ OrderHom.lfp (RefHom e)
  rw [← this]; exact h


/-! ## One lemma per rule of the least model -/

theorem m_alloc {x h : String} (h1 : (x, h) ∈ e.alloc) : DFact.pt x h ∈ Model e :=
  model_closed e (Or.inl (⟨x, h, rfl, h1⟩))

theorem m_inflow {x y : String} (h1 : (x, y) ∈ e.flow) : DFact.flow x y ∈ Model e :=
  model_closed e (Or.inr (Or.inl (⟨x, y, rfl, h1⟩)))

theorem m_flow {x y h : String} (h1 : DFact.flow x y ∈ Model e) (h2 : DFact.pt x h ∈ Model e) : DFact.pt y h ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inl (⟨x, y, h, rfl, h1, h2⟩))))

theorem m_load {recv f out h cell : String} (h1 : (recv, f, out) ∈ e.load) (h2 : DFact.pt recv h ∈ Model e) (h3 : Field e h f cell) : DFact.flow cell out ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inl (⟨recv, f, out, h, cell, rfl, h1, h2, h3⟩)))))

theorem m_store {recv f v h cell : String} (h1 : (recv, f, v) ∈ e.store) (h2 : DFact.pt recv h ∈ Model e) (h3 : Field e h f cell) : DFact.flow v cell ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨recv, f, v, h, cell, rfl, h1, h2, h3⟩))))))

theorem m_filter {src k out h : String} (h1 : (src, k, out) ∈ e.filter) (h2 : DFact.pt src h ∈ Model e) (h3 : Kind e h k) : DFact.pt out h ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨src, k, out, h, rfl, h1, h2, h3⟩)))))))

theorem m_produce {src k out new h : String} (h1 : (src, k, out, new) ∈ e.produce) (h2 : DFact.pt src h ∈ Model e) (h3 : Kind e h k) : DFact.pt out new ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨src, k, out, new, h, rfl, h1, h2, h3⟩))))))))

theorem m_tostr {src out h : String} (h1 : (src, out) ∈ e.toStr) (h2 : DFact.pt src h ∈ Model e) : DFact.pt out "atom:str" ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨src, out, h, rfl, h1, h2⟩)))))))))

theorem m_target {call arg out ctx h k : String} (h1 : (call, arg, out) ∈ e.invoke) (h2 : DFact.pt arg h ∈ Model e) (h3 : Kind e h k) (h4 : (call, k, ctx) ∈ e.select) : DFact.target call arg out ctx ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨call, arg, out, ctx, h, k, rfl, h1, h2, h3, h4⟩))))))))))

theorem m_arg {call arg out ctx h k param : String} (h1 : DFact.target call arg out ctx ∈ Model e) (h2 : DFact.pt arg h ∈ Model e) (h3 : Kind e h k) (h4 : (call, k, ctx) ∈ e.select) (h5 : (ctx, param) ∈ e.formal) : DFact.pt param h ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨call, arg, out, ctx, h, k, param, rfl, h1, h2, h3, h4, h5⟩)))))))))))

theorem m_ret {call arg out ctx r : String} (h1 : DFact.target call arg out ctx ∈ Model e) (h2 : (ctx, r) ∈ e.ret) : DFact.flow r out ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨call, arg, out, ctx, r, rfl, h1, h2⟩))))))))))))

theorem m_disp {c recv m arg out h k p r : String} (h1 : (c, recv, m, arg, out) ∈ e.send) (h2 : DFact.pt recv h ∈ Model e) (h3 : Kind e h k) (h4 : (k, m, p, r) ∈ e.method) : DFact.disp c arg out p r ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨c, recv, m, arg, out, h, k, p, r, rfl, h1, h2, h3, h4⟩)))))))))))))

theorem m_disparg {c arg out p r : String} (h1 : DFact.disp c arg out p r ∈ Model e) : DFact.flow arg p ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨c, arg, out, p, r, rfl, h1⟩))))))))))))))

theorem m_dispret {c arg out p r : String} (h1 : DFact.disp c arg out p r ∈ Model e) : DFact.flow r out ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨c, arg, out, p, r, rfl, h1⟩)))))))))))))))

theorem m_yarg {b arg out h p r : String} (h1 : (b, arg, out) ∈ e.yieldTo) (h2 : DFact.pt b h ∈ Model e) (h3 : (h, p, r) ∈ e.block) : DFact.flow arg p ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨b, arg, out, h, p, r, rfl, h1, h2, h3⟩))))))))))))))))

theorem m_yret {b arg out h p r : String} (h1 : (b, arg, out) ∈ e.yieldTo) (h2 : DFact.pt b h ∈ Model e) (h3 : (h, p, r) ∈ e.block) : DFact.flow r out ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨b, arg, out, h, p, r, rfl, h1, h2, h3⟩)))))))))))))))))

theorem m_mpair {x y out new l r : String} (h1 : (x, y, out, new) ∈ e.merge) (h2 : DFact.pt x l ∈ Model e) (h3 : Kind e l "hash") (h4 : DFact.pt y r ∈ Model e) (h5 : Kind e r "hash") : DFact.mpair l r out new ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨x, y, out, new, l, r, rfl, h1, h2, h3, h4, h5⟩))))))))))))))))))

theorem m_mres {l r out new : String} (h1 : DFact.mpair l r out new ∈ Model e) : DFact.pt out new ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨l, r, out, new, rfl, h1⟩)))))))))))))))))))

theorem m_ml {l r out new f src dst : String} (h1 : DFact.mpair l r out new ∈ Model e) (h2 : Field e l f src) (h3 : Field e new f dst) : DFact.flow src dst ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl (⟨l, r, out, new, f, src, dst, rfl, h1, h2, h3⟩))))))))))))))))))))

theorem m_mr {l r out new f src dst : String} (h1 : DFact.mpair l r out new ∈ Model e) (h2 : Field e r f src) (h3 : Field e new f dst) : DFact.flow src dst ∈ Model e :=
  model_closed e (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr (⟨l, r, out, new, f, src, dst, rfl, h1, h2, h3⟩))))))))))))))))))))

/-! ## Well-formed inputs and the site tables -/

/-- Inputs as model.py's `Program` builds them: site names are unique, and every site that can
enter a `Pt` fact is declared. -/
structure WF : Prop where
  nodup : (e.sites.map RSite.name).Nodup
  alloc_decl : ∀ x h, (x, h) ∈ e.alloc → ∃ s ∈ e.sites, s.name = h
  produce_decl : ∀ src k out new, (src, k, out, new) ∈ e.produce → ∃ s ∈ e.sites, s.name = new
  merge_decl : ∀ x y out new, (x, y, out, new) ∈ e.merge → ∃ s ∈ e.sites, s.name = new
  str_decl : ∃ s ∈ e.sites, s.name = "atom:str"

variable {e}

theorem find_name {h : String} {s : RSite} (hf : e.sites.find? (fun t => t.name = h) = some s) :
    s ∈ e.sites ∧ s.name = h :=
  ⟨List.mem_of_find?_eq_some hf, by simpa using List.find?_some hf⟩

theorem find_of_mem (hnd : (e.sites.map RSite.name).Nodup) {s : RSite} (hs : s ∈ e.sites) :
    e.sites.find? (fun t => t.name = s.name) = some s := by
  cases hf : e.sites.find? (fun t => t.name = s.name) with
  | none =>
    rw [List.find?_eq_none] at hf
    exact absurd (by simp) (hf s hs)
  | some t =>
    obtain ⟨ht, hn⟩ := find_name hf
    rw [List.inj_on_of_nodup_map hnd ht hs hn]

theorem kind_of_kindOf {h k : String} (hk : e.kindOf h = some k) : Kind e h k := by
  unfold REDB.kindOf at hk
  cases hf : e.sites.find? (fun s => s.name = h) with
  | none => rw [hf] at hk; cases hk
  | some s =>
    rw [hf] at hk
    simp only [Option.map_some, Option.some.injEq] at hk
    exact ⟨s, (find_name hf).1, (find_name hf).2, hk⟩

theorem kindOf_of_kind (hnd : (e.sites.map RSite.name).Nodup) {h k : String} (hk : Kind e h k) :
    e.kindOf h = some k := by
  obtain ⟨s, hs, rfl, rfl⟩ := hk
  unfold REDB.kindOf
  rw [find_of_mem hnd hs]
  rfl

theorem kindIs_iff (hnd : (e.sites.map RSite.name).Nodup) {k h : String} :
    e.kindIs k h = true ↔ Kind e h k := by
  unfold REDB.kindIs
  constructor
  · intro hk; exact kind_of_kindOf (by simpa using hk)
  · intro hk; simp [kindOf_of_kind hnd hk]

theorem mem_sitesOfKind {k h : String} : h ∈ e.sitesOfKind k ↔ Kind e h k := by
  simp only [REDB.sitesOfKind, List.mem_map, List.mem_filter, decide_eq_true_eq, Kind]
  constructor
  · rintro ⟨s, ⟨hs, hk⟩, rfl⟩; exact ⟨s, hs, rfl, hk⟩
  · rintro ⟨s, hs, rfl, hk⟩; exact ⟨s, ⟨hs, hk⟩, rfl⟩

/-- The field labels of a site, as the merge lowering reads them. -/
def fieldsOf (e : REDB) (h : String) : List String :=
  ((e.sites.find? (·.name = h)).map (·.fields)).getD []

theorem mem_fieldsOf (hnd : (e.sites.map RSite.name).Nodup) {h f : String} :
    f ∈ fieldsOf e h ↔ ∃ s ∈ e.sites, s.name = h ∧ f ∈ s.fields := by
  unfold fieldsOf
  constructor
  · intro hf
    cases hfind : e.sites.find? (fun t => t.name = h) with
    | none => rw [hfind] at hf; simp at hf
    | some s =>
      rw [hfind] at hf
      exact ⟨s, (find_name hfind).1, (find_name hfind).2, by simpa using hf⟩
  · rintro ⟨s, hs, rfl, hf⟩
    rw [find_of_mem hnd hs]
    simpa using hf

theorem field_iff (hnd : (e.sites.map RSite.name).Nodup) {h f cell : String} :
    Field e h f cell ↔ f ∈ fieldsOf e h ∧ cell = REDB.cellName h f := by
  rw [mem_fieldsOf hnd, Field]
  constructor
  · rintro ⟨s, hs, rfl, hf, rfl⟩; exact ⟨⟨s, hs, rfl, hf⟩, rfl⟩
  · rintro ⟨⟨s, hs, rfl, hf⟩, rfl⟩; exact ⟨s, hs, rfl, hf, rfl⟩

/-! ## Direction 1: every core fact is in model.py's least model -/

theorem solve_subset_model (hwf : WF e) :
    ∀ p ∈ e.lower.solve, DFact.pt p.1 p.2 ∈ Model e := by
  let S : Set (String × String) := {p | DFact.pt p.1 p.2 ∈ Model e}
  have hS : e.lower.stepSet S ⊆ S := by
    intro p hp
    rcases hp with ⟨a, ha, hc, rfl⟩ | ⟨g, hg, hc, h1, h2, h3⟩
    · simp only [REDB.lower, REDB.allocs, List.mem_append, List.mem_map, List.mem_flatMap,
        Prod.exists] at ha
      rcases ha with ((⟨x, h, hxh, rfl⟩ | ⟨src, k, out, new, hp, h, hh, rfl⟩) |
          ⟨src, out, ht, s, hs, rfl⟩) | ⟨x, y, out, new, hm, l, hl, r, hr, rfl⟩
      · exact m_alloc e hxh
      · exact m_produce e hp (hc (src, h) (by simp)) (mem_sitesOfKind.1 hh)
      · exact m_tostr e ht (hc (src, s.name) (by simp))
      · exact m_mres e (m_mpair e hm (hc (x, l) (by simp)) (mem_sitesOfKind.1 hl) (hc (y, r) (by simp))
          (mem_sitesOfKind.1 hr))
    · obtain ⟨v, h⟩ := p
      simp only at h1 h2 h3
      subst h1
      have hsrc : DFact.pt g.src h ∈ Model e := h2
      show DFact.pt g.dst h ∈ Model e
      simp only [REDB.lower, REDB.guards, List.mem_append, List.mem_map, List.mem_flatMap,
        List.mem_filterMap, List.mem_filter, Prod.exists, List.mem_cons,
        List.not_mem_nil, or_false] at hg
      rcases hg with ((((((((⟨x, y, hxy, rfl⟩ | ⟨recv, f, out, hl, st, hst, hif⟩) |
          ⟨recv, f, v, hsto, st, hst, hif⟩) | ⟨src, k, out, hfil, rfl⟩) |
          ⟨call, arg, out', hinv, call', k, ctx, ⟨hsel, hcall⟩, ctx', param, ⟨hform, hctx⟩, rfl⟩) |
          ⟨call, arg, out, hinv, call', k, ctx, ⟨hsel, hcall⟩, ctx', r, ⟨hret, hctx⟩, h0, hh0, rfl⟩) |
          ⟨c, recv, m, arg, out, hsend, k, m', p, r, ⟨hmeth, hm⟩, h0, hh0, (rfl | rfl)⟩) |
          ⟨b, arg, out, hy, h0, p, r, hblk, (rfl | rfl)⟩) |
          ⟨x, y, out, new, hmer, l, hl, r, hr, (⟨f, ⟨hfl, hfn⟩, rfl⟩ | ⟨f, ⟨hfr, hfn⟩, rfl⟩)⟩)
      · exact m_flow e (m_inflow e hxy) hsrc
      · split at hif
        · next hf =>
          cases hif
          have hcond : DFact.pt recv st.name ∈ Model e := hc (recv, st.name) (by simp)
          exact m_flow e (m_load e hl hcond ⟨st, hst, rfl, hf, rfl⟩) hsrc
        · cases hif
      · split at hif
        · next hf =>
          cases hif
          have hcond : DFact.pt recv st.name ∈ Model e := hc (recv, st.name) (by simp)
          exact m_flow e (m_store e hsto hcond ⟨st, hst, rfl, hf, rfl⟩) hsrc
        · cases hif
      · exact m_filter e hfil hsrc ((kindIs_iff hwf.nodup).1 h3)
      · simp only [decide_eq_true_eq] at hcall hctx
        subst hcall hctx
        have hk : Kind e h k := (kindIs_iff hwf.nodup).1 h3
        exact m_arg e (m_target e hinv hsrc hk hsel) hsrc hk hsel hform
      · simp only [decide_eq_true_eq] at hcall hctx
        subst hcall hctx
        have hcond : DFact.pt arg h0 ∈ Model e := hc (arg, h0) (by simp)
        exact m_flow e (m_ret e (m_target e hinv hcond (mem_sitesOfKind.1 hh0) hsel) hret) hsrc
      · simp only [decide_eq_true_eq] at hm
        subst hm
        have hcond : DFact.pt recv h0 ∈ Model e := hc (recv, h0) (by simp)
        exact m_flow e (m_disparg e (m_disp e hsend hcond (mem_sitesOfKind.1 hh0) hmeth)) hsrc
      · simp only [decide_eq_true_eq] at hm
        subst hm
        have hcond : DFact.pt recv h0 ∈ Model e := hc (recv, h0) (by simp)
        exact m_flow e (m_dispret e (m_disp e hsend hcond (mem_sitesOfKind.1 hh0) hmeth)) hsrc
      · have hcond : DFact.pt b h0 ∈ Model e := hc (b, h0) (by simp)
        exact m_flow e (m_yarg e hy hcond hblk) hsrc
      · have hcond : DFact.pt b h0 ∈ Model e := hc (b, h0) (by simp)
        exact m_flow e (m_yret e hy hcond hblk) hsrc
      · have hx : DFact.pt x l ∈ Model e := hc (x, l) (by simp)
        have hy' : DFact.pt y r ∈ Model e := hc (y, r) (by simp)
        have hpair := m_mpair e hmer hx (mem_sitesOfKind.1 hl) hy' (mem_sitesOfKind.1 hr)
        have hfn' : f ∈ fieldsOf e new := by simp only [decide_eq_true_eq] at hfn; exact hfn
        exact m_flow e (m_ml e hpair ((field_iff hwf.nodup).2 ⟨hfl, rfl⟩)
          ((field_iff hwf.nodup).2 ⟨hfn', rfl⟩)) hsrc
      · have hx : DFact.pt x l ∈ Model e := hc (x, l) (by simp)
        have hy' : DFact.pt y r ∈ Model e := hc (y, r) (by simp)
        have hpair := m_mpair e hmer hx (mem_sitesOfKind.1 hl) hy' (mem_sitesOfKind.1 hr)
        have hfn' : f ∈ fieldsOf e new := by simp only [decide_eq_true_eq] at hfn; exact hfn
        exact m_flow e (m_mr e hpair ((field_iff hwf.nodup).2 ⟨hfr, rfl⟩)
          ((field_iff hwf.nodup).2 ⟨hfn', rfl⟩)) hsrc
  have hle : (↑e.lower.solve : Set (String × String)) ⊆ S := by
    rw [e.lower.solve_eq_lfp]
    exact OrderHom.lfp_le _ hS
  intro p hp
  exact hle hp

/-! ## Direction 2: model.py's least model is inside the core solution -/

theorem g_flow {x y : String} (h1 : (x, y) ∈ e.flow) :
    (⟨[], x, y, REDB.passAll⟩ : Guard String String) ∈ e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  exact List.mem_map.2 ⟨(x, y), h1, rfl⟩

theorem g_load {recv f out : String} {st : RSite} (h1 : (recv, f, out) ∈ e.load) (hs : st ∈ e.sites)
    (hf : f ∈ st.fields) :
    (⟨[(recv, st.name)], REDB.cellName st.name f, out, REDB.passAll⟩ : Guard String String) ∈
      e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(recv, f, out), h1, List.mem_filterMap.2 ⟨st, hs, by simp [hf]⟩⟩

theorem g_store {recv f v : String} {st : RSite} (h1 : (recv, f, v) ∈ e.store) (hs : st ∈ e.sites)
    (hf : f ∈ st.fields) :
    (⟨[(recv, st.name)], v, REDB.cellName st.name f, REDB.passAll⟩ : Guard String String) ∈
      e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(recv, f, v), h1, List.mem_filterMap.2 ⟨st, hs, by simp [hf]⟩⟩

theorem g_filter {src k out : String} (h1 : (src, k, out) ∈ e.filter) :
    (⟨[], src, out, e.kindIs k⟩ : Guard String String) ∈ e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_map.2 ⟨(src, k, out), h1, rfl⟩

theorem g_arg {call arg out k ctx param : String} (h1 : (call, arg, out) ∈ e.invoke)
    (h2 : (call, k, ctx) ∈ e.select) (h3 : (ctx, param) ∈ e.formal) :
    (⟨[], arg, param, e.kindIs k⟩ : Guard String String) ∈ e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(call, arg, out), h1, List.mem_flatMap.2 ⟨(call, k, ctx),
    List.mem_filter.2 ⟨h2, by simp⟩, List.mem_map.2 ⟨(ctx, param), List.mem_filter.2 ⟨h3, by simp⟩, rfl⟩⟩⟩

theorem g_ret {call arg out k ctx r h : String} (h1 : (call, arg, out) ∈ e.invoke)
    (h2 : (call, k, ctx) ∈ e.select) (h3 : (ctx, r) ∈ e.ret) (h4 : h ∈ e.sitesOfKind k) :
    (⟨[(arg, h)], r, out, REDB.passAll⟩ : Guard String String) ∈ e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(call, arg, out), h1, List.mem_flatMap.2 ⟨(call, k, ctx),
    List.mem_filter.2 ⟨h2, by simp⟩, List.mem_flatMap.2 ⟨(ctx, r), List.mem_filter.2 ⟨h3, by simp⟩,
      List.mem_map.2 ⟨h, h4, rfl⟩⟩⟩⟩

theorem g_disparg {c recv m arg out k p r h : String} (h1 : (c, recv, m, arg, out) ∈ e.send)
    (h2 : (k, m, p, r) ∈ e.method) (h4 : h ∈ e.sitesOfKind k) :
    (⟨[(recv, h)], arg, p, REDB.passAll⟩ : Guard String String) ∈ e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(c, recv, m, arg, out), h1, List.mem_flatMap.2 ⟨(k, m, p, r),
    List.mem_filter.2 ⟨h2, by simp⟩, List.mem_flatMap.2 ⟨h, h4, by simp⟩⟩⟩

theorem g_dispret {c recv m arg out k p r h : String} (h1 : (c, recv, m, arg, out) ∈ e.send)
    (h2 : (k, m, p, r) ∈ e.method) (h4 : h ∈ e.sitesOfKind k) :
    (⟨[(recv, h)], r, out, REDB.passAll⟩ : Guard String String) ∈ e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(c, recv, m, arg, out), h1, List.mem_flatMap.2 ⟨(k, m, p, r),
    List.mem_filter.2 ⟨h2, by simp⟩, List.mem_flatMap.2 ⟨h, h4, by simp⟩⟩⟩

theorem g_yarg {b arg out h p r : String} (h1 : (b, arg, out) ∈ e.yieldTo) (h2 : (h, p, r) ∈ e.block) :
    (⟨[(b, h)], arg, p, REDB.passAll⟩ : Guard String String) ∈ e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(b, arg, out), h1, List.mem_flatMap.2 ⟨(h, p, r), h2, by simp⟩⟩

theorem g_yret {b arg out h p r : String} (h1 : (b, arg, out) ∈ e.yieldTo) (h2 : (h, p, r) ∈ e.block) :
    (⟨[(b, h)], r, out, REDB.passAll⟩ : Guard String String) ∈ e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(b, arg, out), h1, List.mem_flatMap.2 ⟨(h, p, r), h2, by simp⟩⟩

theorem g_ml {x y out new l r f : String} (h1 : (x, y, out, new) ∈ e.merge) (hl : l ∈ e.sitesOfKind "hash")
    (hr : r ∈ e.sitesOfKind "hash") (hfl : f ∈ fieldsOf e l) (hfn : f ∈ fieldsOf e new) :
    (⟨[(x, l), (y, r)], REDB.cellName l f, REDB.cellName new f, REDB.passAll⟩ : Guard String String) ∈
      e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(x, y, out, new), h1, List.mem_flatMap.2 ⟨l, hl, List.mem_flatMap.2 ⟨r, hr,
    List.mem_append_left _ (List.mem_map.2 ⟨f, List.mem_filter.2 ⟨hfl, by simp only [decide_eq_true_eq]; exact hfn⟩, rfl⟩)⟩⟩⟩

theorem g_mr {x y out new l r f : String} (h1 : (x, y, out, new) ∈ e.merge) (hl : l ∈ e.sitesOfKind "hash")
    (hr : r ∈ e.sitesOfKind "hash") (hfr : f ∈ fieldsOf e r) (hfn : f ∈ fieldsOf e new) :
    (⟨[(x, l), (y, r)], REDB.cellName r f, REDB.cellName new f, REDB.passAll⟩ : Guard String String) ∈
      e.lower.guards := by
  show _ ∈ e.guards
  unfold REDB.guards
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(x, y, out, new), h1, List.mem_flatMap.2 ⟨l, hl, List.mem_flatMap.2 ⟨r, hr,
    List.mem_append_right _ (List.mem_map.2 ⟨f, List.mem_filter.2 ⟨hfr, by simp only [decide_eq_true_eq]; exact hfn⟩, rfl⟩)⟩⟩⟩

theorem a_alloc {x h : String} (h1 : (x, h) ∈ e.alloc) :
    (⟨[], x, h⟩ : Alloc String String) ∈ e.lower.allocs := by
  show _ ∈ e.allocs
  unfold REDB.allocs
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_left
  exact List.mem_map.2 ⟨(x, h), h1, rfl⟩

theorem a_produce {src k out new h : String} (h1 : (src, k, out, new) ∈ e.produce)
    (h2 : h ∈ e.sitesOfKind k) :
    (⟨[(src, h)], out, new⟩ : Alloc String String) ∈ e.lower.allocs := by
  show _ ∈ e.allocs
  unfold REDB.allocs
  apply List.mem_append_left
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(src, k, out, new), h1, List.mem_map.2 ⟨h, h2, rfl⟩⟩

theorem a_tostr {src out : String} {st : RSite} (h1 : (src, out) ∈ e.toStr) (hs : st ∈ e.sites) :
    (⟨[(src, st.name)], out, "atom:str"⟩ : Alloc String String) ∈ e.lower.allocs := by
  show _ ∈ e.allocs
  unfold REDB.allocs
  apply List.mem_append_left
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(src, out), h1, List.mem_map.2 ⟨st, hs, rfl⟩⟩

theorem a_merge {x y out new l r : String} (h1 : (x, y, out, new) ∈ e.merge) (hl : l ∈ e.sitesOfKind "hash")
    (hr : r ∈ e.sitesOfKind "hash") :
    (⟨[(x, l), (y, r)], out, new⟩ : Alloc String String) ∈ e.lower.allocs := by
  show _ ∈ e.allocs
  unfold REDB.allocs
  apply List.mem_append_right
  exact List.mem_flatMap.2 ⟨(x, y, out, new), h1, List.mem_flatMap.2 ⟨l, hl, List.mem_map.2 ⟨r, hr, rfl⟩⟩⟩

theorem sol_closed {p : String × String} (hp : p ∈ e.lower.stepSet ↑e.lower.solve) :
    p ∈ e.lower.solve := by
  rw [← e.lower.coe_step, e.lower.solve_fixed] at hp; exact hp

theorem sol_alloc {a : Alloc String String} (ha : a ∈ e.lower.allocs)
    (hc : ∀ c ∈ a.conds, c ∈ e.lower.solve) : (a.dst, a.site) ∈ e.lower.solve :=
  sol_closed (Or.inl ⟨a, ha, fun c h => Finset.mem_coe.2 (hc c h), rfl⟩)

theorem sol_guard {g : Guard String String} (hg : g ∈ e.lower.guards)
    (hc : ∀ c ∈ g.conds, c ∈ e.lower.solve) {h : String} (hs : (g.src, h) ∈ e.lower.solve)
    (hp : g.pass h = true) : (g.dst, h) ∈ e.lower.solve :=
  sol_closed (Or.inr ⟨g, hg, fun c hc' => Finset.mem_coe.2 (hc c hc'), rfl, hs, hp⟩)

/-- Every site of the core solution is declared. -/
theorem declared (hwf : WF e) {v h : String} (hsol : (v, h) ∈ e.lower.solve) :
    ∃ s ∈ e.sites, s.name = h := by
  have hu := e.lower.toOp.kleene_subset_univ hsol
  simp only [Prog.toOp, Prog.univ, Finset.mem_product, Prog.sites, List.mem_toFinset,
    List.mem_map] at hu
  obtain ⟨-, a, ha, rfl⟩ := hu
  simp only [REDB.lower, REDB.allocs, List.mem_append, List.mem_map, List.mem_flatMap,
    Prod.exists] at ha
  rcases ha with ((⟨x, h, hxh, rfl⟩ | ⟨src, k, out, new, hprod, h, -, rfl⟩) |
      ⟨src, out, -, st, -, rfl⟩) | ⟨x, y, out, new, hm, l, -, r, -, rfl⟩
  · exact hwf.alloc_decl x h hxh
  · exact hwf.produce_decl src k out new hprod
  · exact hwf.str_decl
  · exact hwf.merge_decl x y out new hm

/-- What the core solution makes true of each derived fact. -/
def tval (e : REDB) : DFact → Prop
  | .pt v h => (v, h) ∈ e.lower.solve
  | .flow x y => ∀ h, (x, h) ∈ e.lower.solve → (y, h) ∈ e.lower.solve
  | .target call arg out ctx => (call, arg, out) ∈ e.invoke ∧
      ∃ h k, (arg, h) ∈ e.lower.solve ∧ Kind e h k ∧ (call, k, ctx) ∈ e.select
  | .disp c arg out p r => ∃ recv m h k, (c, recv, m, arg, out) ∈ e.send ∧
      (recv, h) ∈ e.lower.solve ∧ Kind e h k ∧ (k, m, p, r) ∈ e.method
  | .mpair l r out new => ∃ x y, (x, y, out, new) ∈ e.merge ∧ (x, l) ∈ e.lower.solve ∧
      Kind e l "hash" ∧ (y, r) ∈ e.lower.solve ∧ Kind e r "hash"

theorem refStep_tval (hwf : WF e) : RefStep e {d | tval e d} ⊆ {d | tval e d} := by
  intro d hd
  rcases hd with ⟨x, h, rfl, h1⟩ | ⟨x, y, rfl, h1⟩ | ⟨x, y, h, rfl, h1, h2⟩ |
    ⟨recv, f, out, h, cell, rfl, h1, h2, h3⟩ | ⟨recv, f, v, h, cell, rfl, h1, h2, h3⟩ |
    ⟨src, k, out, h, rfl, h1, h2, h3⟩ | ⟨src, k, out, new, h, rfl, h1, h2, h3⟩ |
    ⟨src, out, h, rfl, h1, h2⟩ | ⟨call, arg, out, ctx, h, k, rfl, h1, h2, h3, h4⟩ |
    ⟨call, arg, out, ctx, h, k, param, rfl, h1, h2, h3, h4, h5⟩ |
    ⟨call, arg, out, ctx, r, rfl, h1, h2⟩ | ⟨c, recv, m, arg, out, h, k, p, r, rfl, h1, h2, h3, h4⟩ |
    ⟨c, arg, out, p, r, rfl, h1⟩ | ⟨c, arg, out, p, r, rfl, h1⟩ |
    ⟨b, arg, out, h, p, r, rfl, h1, h2, h3⟩ | ⟨b, arg, out, h, p, r, rfl, h1, h2, h3⟩ |
    ⟨x, y, out, new, l, r, rfl, h1, h2, h3, h4, h5⟩ | ⟨l, r, out, new, rfl, h1⟩ |
    ⟨l, r, out, new, f, src, dst, rfl, h1, h2, h3⟩ | ⟨l, r, out, new, f, src, dst, rfl, h1, h2, h3⟩
  · -- input Alloc
    exact sol_alloc (a_alloc h1) (by simp)
  · -- input Flow
    intro h hx
    exact sol_guard (g_flow h1) (by simp) hx rfl
  · -- flow
    exact h1 h h2
  · -- load
    obtain ⟨st, hs, rfl, hf, rfl⟩ := h3
    intro h' hc
    exact sol_guard (g_load h1 hs hf) (fun c hc => by rw [List.mem_singleton.1 hc]; exact h2) hc rfl
  · -- store
    obtain ⟨st, hs, rfl, hf, rfl⟩ := h3
    intro h' hc
    exact sol_guard (g_store h1 hs hf) (fun c hc => by rw [List.mem_singleton.1 hc]; exact h2) hc rfl
  · -- filter
    exact sol_guard (g_filter h1) (by simp) h2 ((kindIs_iff hwf.nodup).2 h3)
  · -- produce
    exact sol_alloc (a_produce h1 (mem_sitesOfKind.2 h3)) (fun c hc => by rw [List.mem_singleton.1 hc]; exact h2)
  · -- key_to_string
    obtain ⟨st, hs, rfl⟩ := declared hwf h2
    exact sol_alloc (a_tostr h1 hs) (fun c hc => by rw [List.mem_singleton.1 hc]; exact h2)
  · -- call_target
    exact ⟨h1, h, k, h2, h3, h4⟩
  · -- call_argument
    obtain ⟨hinv, -⟩ := h1
    exact sol_guard (g_arg hinv h4 h5) (by simp) h2 ((kindIs_iff hwf.nodup).2 h3)
  · -- call_return
    obtain ⟨hinv, h0, k0, hh0, hk0, hsel⟩ := h1
    intro h' hc
    exact sol_guard (g_ret hinv hsel h2 (mem_sitesOfKind.2 hk0)) (by simpa using hh0) hc rfl
  · -- dispatch
    exact ⟨recv, m, h, k, h1, h2, h3, h4⟩
  · -- dispatch_argument
    obtain ⟨recv, m, h0, k, hsend, hh0, hk, hmeth⟩ := h1
    intro h' hc
    exact sol_guard (g_disparg hsend hmeth (mem_sitesOfKind.2 hk)) (by simpa using hh0) hc rfl
  · -- dispatch_return
    obtain ⟨recv, m, h0, k, hsend, hh0, hk, hmeth⟩ := h1
    intro h' hc
    exact sol_guard (g_dispret hsend hmeth (mem_sitesOfKind.2 hk)) (by simpa using hh0) hc rfl
  · -- yield_argument
    intro h' hc
    exact sol_guard (g_yarg h1 h3) (fun c hc => by rw [List.mem_singleton.1 hc]; exact h2) hc rfl
  · -- yield_return
    intro h' hc
    exact sol_guard (g_yret h1 h3) (fun c hc => by rw [List.mem_singleton.1 hc]; exact h2) hc rfl
  · -- merge_pair
    exact ⟨x, y, h1, h2, h3, h4, h5⟩
  · -- merge_result
    obtain ⟨x, y, hm, hx, hl, hy, hr⟩ := h1
    exact sol_alloc (a_merge hm (mem_sitesOfKind.2 hl) (mem_sitesOfKind.2 hr))
      (by simp [hx, hy])
  · -- merge_l
    obtain ⟨x, y, hm, hx, hl, hy, hr⟩ := h1
    obtain ⟨hfl, rfl⟩ := (field_iff hwf.nodup).1 h2
    obtain ⟨hfn, rfl⟩ := (field_iff hwf.nodup).1 h3
    intro h' hc
    exact sol_guard (g_ml hm (mem_sitesOfKind.2 hl) (mem_sitesOfKind.2 hr) hfl hfn)
      (by simp [hx, hy]) hc rfl
  · -- merge_r
    obtain ⟨x, y, hm, hx, hl, hy, hr⟩ := h1
    obtain ⟨hfr, rfl⟩ := (field_iff hwf.nodup).1 h2
    obtain ⟨hfn, rfl⟩ := (field_iff hwf.nodup).1 h3
    intro h' hc
    exact sol_guard (g_mr hm (mem_sitesOfKind.2 hl) (mem_sitesOfKind.2 hr) hfr hfn)
      (by simp [hx, hy]) hc rfl

/-- **The lowering is exact.**  On every well-formed input, `Pt(v, h)` is in the least model of
model.py's rules iff `(v, h)` is in the verified core's least solution of the lowered program. -/
theorem pt_iff (hwf : WF e) (v h : String) :
    DFact.pt v h ∈ Model e ↔ (v, h) ∈ e.lower.solve := by
  constructor
  · intro hm
    have hle : Model e ⊆ {d | tval e d} := OrderHom.lfp_le (RefHom e) (refStep_tval hwf)
    exact hle hm
  · intro hs
    exact solve_subset_model hwf (v, h) hs

/-- A decidable check of `WF` (used by `ProofLean.Check` on the 18 cases). -/
def wfb (e : REDB) : Bool :=
  let declared := fun h => e.sites.any (fun s => s.name = h)
  (e.sites.map RSite.name).Nodup && e.alloc.all (fun p => declared p.2) &&
  e.produce.all (fun p => declared p.2.2.2) && e.merge.all (fun p => declared p.2.2.2) &&
  declared "atom:str"

theorem wf_of_wfb {e : REDB} (h : wfb e = true) : WF e := by
  simp only [wfb, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true, List.any_eq_true] at h
  obtain ⟨⟨⟨⟨hnd, ha⟩, hp⟩, hm⟩, hs⟩ := h
  exact ⟨hnd, fun x h hx => ha (x, h) hx, fun src k out new hx => hp (src, k, out, new) hx,
    fun x y out new hx => hm (x, y, out, new) hx, hs⟩

end ProofLean.Equiv
