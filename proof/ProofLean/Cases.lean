import ProofLean.Lower

/-! Frozen public input relations and expected results. The build reruns all checks. -/

namespace ProofLean.Cases

open ProofLean

/-- Case `self`: input relations. -/
def c_self : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"site:R/u0", "array", ["elem"]⟩,
    ⟨"site:R/u1", "hash", ["key", "value"]⟩]
  alloc := [("R", "site:R/u0"), ("R/u1/key", "atom:sym"), ("R", "site:R/u1"), ("R", "atom:str")]
  flow := [("R", "R/u0/elem"), ("R/u0/elem", "site:R/u0.elem"), ("R", "R/u1/value"), ("R/u1/key", "site:R/u1.key"),
    ("R/u1/value", "site:R/u1.value")]

/-- Case `self`: model.py's solved `Pt` rows. -/
def c_self_pt : List (String × String) := [("R", "atom:str"), ("R", "site:R/u0"), ("R", "site:R/u1"), ("R/u0/elem", "atom:str"),
    ("R/u0/elem", "site:R/u0"), ("R/u0/elem", "site:R/u1"), ("R/u1/key", "atom:sym"), ("R/u1/value", "atom:str"),
    ("R/u1/value", "site:R/u0"), ("R/u1/value", "site:R/u1"), ("site:R/u0.elem", "atom:str"), ("site:R/u0.elem", "site:R/u0"),
    ("site:R/u0.elem", "site:R/u1"), ("site:R/u1.key", "atom:sym"), ("site:R/u1.value", "atom:str"), ("site:R/u1.value", "site:R/u0"),
    ("site:R/u1.value", "site:R/u1")]

/-- Case `self`: model.py's `BadUse` rows. -/
def c_self_bad : List (String × String) := []

/-- Case `self`: printed roots. -/
def c_self_roots : List (String × String) := [("r", "R")]

/-- Case `cycle2`: input relations. -/
def c_cycle2 : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"site:R0/u0", "array", ["elem"]⟩,
    ⟨"site:R0/u1", "hash", ["key", "value"]⟩,
    ⟨"site:R1/u0", "array", ["elem"]⟩,
    ⟨"site:R1/u1", "hash", ["key", "value"]⟩]
  alloc := [("R0", "site:R0/u0"), ("R0/u1/key", "atom:sym"), ("R0", "site:R0/u1"), ("R0", "atom:str"),
    ("R1", "site:R1/u0"), ("R1/u1/key", "atom:str"), ("R1", "site:R1/u1"), ("R1", "atom:int")]
  flow := [("R1", "R0/u0/elem"), ("R0/u0/elem", "site:R0/u0.elem"), ("R1", "R0/u1/value"), ("R0/u1/key", "site:R0/u1.key"),
    ("R0/u1/value", "site:R0/u1.value"), ("R0", "R1/u0/elem"), ("R1/u0/elem", "site:R1/u0.elem"), ("R0", "R1/u1/value"),
    ("R1/u1/key", "site:R1/u1.key"), ("R1/u1/value", "site:R1/u1.value")]

/-- Case `cycle2`: model.py's solved `Pt` rows. -/
def c_cycle2_pt : List (String × String) := [("R0", "atom:str"), ("R0", "site:R0/u0"), ("R0", "site:R0/u1"), ("R0/u0/elem", "atom:int"),
    ("R0/u0/elem", "site:R1/u0"), ("R0/u0/elem", "site:R1/u1"), ("R0/u1/key", "atom:sym"), ("R0/u1/value", "atom:int"),
    ("R0/u1/value", "site:R1/u0"), ("R0/u1/value", "site:R1/u1"), ("R1", "atom:int"), ("R1", "site:R1/u0"),
    ("R1", "site:R1/u1"), ("R1/u0/elem", "atom:str"), ("R1/u0/elem", "site:R0/u0"), ("R1/u0/elem", "site:R0/u1"),
    ("R1/u1/key", "atom:str"), ("R1/u1/value", "atom:str"), ("R1/u1/value", "site:R0/u0"), ("R1/u1/value", "site:R0/u1"),
    ("site:R0/u0.elem", "atom:int"), ("site:R0/u0.elem", "site:R1/u0"), ("site:R0/u0.elem", "site:R1/u1"), ("site:R0/u1.key", "atom:sym"),
    ("site:R0/u1.value", "atom:int"), ("site:R0/u1.value", "site:R1/u0"), ("site:R0/u1.value", "site:R1/u1"), ("site:R1/u0.elem", "atom:str"),
    ("site:R1/u0.elem", "site:R0/u0"), ("site:R1/u0.elem", "site:R0/u1"), ("site:R1/u1.key", "atom:str"), ("site:R1/u1.value", "atom:str"),
    ("site:R1/u1.value", "site:R0/u0"), ("site:R1/u1.value", "site:R0/u1")]

/-- Case `cycle2`: model.py's `BadUse` rows. -/
def c_cycle2_bad : List (String × String) := []

/-- Case `cycle2`: printed roots. -/
def c_cycle2_roots : List (String × String) := [("r0", "R0"), ("r1", "R1")]

/-- Case `cycle3`: input relations. -/
def c_cycle3 : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"site:R0/u0", "array", ["elem"]⟩,
    ⟨"site:R0/u1", "hash", ["key", "value"]⟩,
    ⟨"site:R1/u0", "array", ["elem"]⟩,
    ⟨"site:R1/u1", "hash", ["key", "value"]⟩,
    ⟨"site:R2/u0", "array", ["elem"]⟩,
    ⟨"site:R2/u1", "hash", ["key", "value"]⟩]
  alloc := [("R0", "site:R0/u0"), ("R0/u1/key", "atom:sym"), ("R0", "site:R0/u1"), ("R0", "atom:str"),
    ("R1", "site:R1/u0"), ("R1/u1/key", "atom:str"), ("R1", "site:R1/u1"), ("R1", "atom:int"),
    ("R2", "site:R2/u0"), ("R2/u1/key", "atom:int"), ("R2", "site:R2/u1"), ("R2", "atom:sym")]
  flow := [("R1", "R0/u0/elem"), ("R0/u0/elem", "site:R0/u0.elem"), ("R1", "R0/u1/value"), ("R0/u1/key", "site:R0/u1.key"),
    ("R0/u1/value", "site:R0/u1.value"), ("R2", "R1/u0/elem"), ("R1/u0/elem", "site:R1/u0.elem"), ("R2", "R1/u1/value"),
    ("R1/u1/key", "site:R1/u1.key"), ("R1/u1/value", "site:R1/u1.value"), ("R0", "R2/u0/elem"), ("R2/u0/elem", "site:R2/u0.elem"),
    ("R0", "R2/u1/value"), ("R2/u1/key", "site:R2/u1.key"), ("R2/u1/value", "site:R2/u1.value")]

/-- Case `cycle3`: model.py's solved `Pt` rows. -/
def c_cycle3_pt : List (String × String) := [("R0", "atom:str"), ("R0", "site:R0/u0"), ("R0", "site:R0/u1"), ("R0/u0/elem", "atom:int"),
    ("R0/u0/elem", "site:R1/u0"), ("R0/u0/elem", "site:R1/u1"), ("R0/u1/key", "atom:sym"), ("R0/u1/value", "atom:int"),
    ("R0/u1/value", "site:R1/u0"), ("R0/u1/value", "site:R1/u1"), ("R1", "atom:int"), ("R1", "site:R1/u0"),
    ("R1", "site:R1/u1"), ("R1/u0/elem", "atom:sym"), ("R1/u0/elem", "site:R2/u0"), ("R1/u0/elem", "site:R2/u1"),
    ("R1/u1/key", "atom:str"), ("R1/u1/value", "atom:sym"), ("R1/u1/value", "site:R2/u0"), ("R1/u1/value", "site:R2/u1"),
    ("R2", "atom:sym"), ("R2", "site:R2/u0"), ("R2", "site:R2/u1"), ("R2/u0/elem", "atom:str"),
    ("R2/u0/elem", "site:R0/u0"), ("R2/u0/elem", "site:R0/u1"), ("R2/u1/key", "atom:int"), ("R2/u1/value", "atom:str"),
    ("R2/u1/value", "site:R0/u0"), ("R2/u1/value", "site:R0/u1"), ("site:R0/u0.elem", "atom:int"), ("site:R0/u0.elem", "site:R1/u0"),
    ("site:R0/u0.elem", "site:R1/u1"), ("site:R0/u1.key", "atom:sym"), ("site:R0/u1.value", "atom:int"), ("site:R0/u1.value", "site:R1/u0"),
    ("site:R0/u1.value", "site:R1/u1"), ("site:R1/u0.elem", "atom:sym"), ("site:R1/u0.elem", "site:R2/u0"), ("site:R1/u0.elem", "site:R2/u1"),
    ("site:R1/u1.key", "atom:str"), ("site:R1/u1.value", "atom:sym"), ("site:R1/u1.value", "site:R2/u0"), ("site:R1/u1.value", "site:R2/u1"),
    ("site:R2/u0.elem", "atom:str"), ("site:R2/u0.elem", "site:R0/u0"), ("site:R2/u0.elem", "site:R0/u1"), ("site:R2/u1.key", "atom:int"),
    ("site:R2/u1.value", "atom:str"), ("site:R2/u1.value", "site:R0/u0"), ("site:R2/u1.value", "site:R0/u1")]

/-- Case `cycle3`: model.py's `BadUse` rows. -/
def c_cycle3_bad : List (String × String) := []

/-- Case `cycle3`: printed roots. -/
def c_cycle3_roots : List (String × String) := [("r0", "R0"), ("r1", "R1"), ("r2", "R2")]

/-- Case `merge2`: input relations. -/
def c_merge2 : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"site:R/u0", "array", ["elem"]⟩,
    ⟨"site:R/u0/elem/u0", "array", ["elem"]⟩,
    ⟨"site:R/u1", "hash", ["key", "value"]⟩]
  alloc := [("R/u0/elem/u0/elem", "atom:str"), ("R/u0/elem", "site:R/u0/elem/u0"), ("R", "site:R/u0"), ("R/u1/key", "atom:model_u"),
    ("R", "site:R/u1"), ("R", "atom:str")]
  flow := [("R/u0/elem/u0/elem", "site:R/u0/elem/u0.elem"), ("R", "R/u0/elem"), ("R/u0/elem", "site:R/u0.elem"), ("R", "R/u1/value"),
    ("R/u1/key", "site:R/u1.key"), ("R/u1/value", "site:R/u1.value")]

/-- Case `merge2`: model.py's solved `Pt` rows. -/
def c_merge2_pt : List (String × String) := [("R", "atom:str"), ("R", "site:R/u0"), ("R", "site:R/u1"), ("R/u0/elem", "atom:str"),
    ("R/u0/elem", "site:R/u0"), ("R/u0/elem", "site:R/u0/elem/u0"), ("R/u0/elem", "site:R/u1"), ("R/u0/elem/u0/elem", "atom:str"),
    ("R/u1/key", "atom:model_u"), ("R/u1/value", "atom:str"), ("R/u1/value", "site:R/u0"), ("R/u1/value", "site:R/u1"),
    ("site:R/u0.elem", "atom:str"), ("site:R/u0.elem", "site:R/u0"), ("site:R/u0.elem", "site:R/u0/elem/u0"), ("site:R/u0.elem", "site:R/u1"),
    ("site:R/u0/elem/u0.elem", "atom:str"), ("site:R/u1.key", "atom:model_u"), ("site:R/u1.value", "atom:str"), ("site:R/u1.value", "site:R/u0"),
    ("site:R/u1.value", "site:R/u1")]

/-- Case `merge2`: model.py's `BadUse` rows. -/
def c_merge2_bad : List (String × String) := []

/-- Case `merge2`: printed roots. -/
def c_merge2_roots : List (String × String) := [("r", "R")]

/-- Case `param`: input relations. -/
def c_param : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"site:P", "hash", ["key", "value"]⟩]
  alloc := [("P/key", "atom:sym"), ("P/key", "atom:model_var"), ("P/value", "atom:int"), ("P/value", "atom:model_var"),
    ("P", "site:P")]
  flow := [("P", "P/value"), ("P/key", "site:P.key"), ("P/value", "site:P.value")]

/-- Case `param`: model.py's solved `Pt` rows. -/
def c_param_pt : List (String × String) := [("P", "site:P"), ("P/key", "atom:model_var"), ("P/key", "atom:sym"), ("P/value", "atom:int"),
    ("P/value", "atom:model_var"), ("P/value", "site:P"), ("site:P.key", "atom:model_var"), ("site:P.key", "atom:sym"),
    ("site:P.value", "atom:int"), ("site:P.value", "atom:model_var"), ("site:P.value", "site:P")]

/-- Case `param`: model.py's `BadUse` rows. -/
def c_param_bad : List (String × String) := []

/-- Case `param`: printed roots. -/
def c_param_roots : List (String × String) := [("p", "P")]

/-- Case `argument_tree`: input relations. -/
def c_argument_tree : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"site:P/u0", "hash", ["key", "value"]⟩]
  alloc := [("P", "site:P/u0"), ("P", "atom:nil"), ("R", "atom:int")]
  flow := [("P", "P/u0/key"), ("P", "P/u0/value"), ("P/u0/key", "site:P/u0.key"), ("P/u0/value", "site:P/u0.value")]

/-- Case `argument_tree`: model.py's solved `Pt` rows. -/
def c_argument_tree_pt : List (String × String) := [("P", "atom:nil"), ("P", "site:P/u0"), ("P/u0/key", "atom:nil"), ("P/u0/key", "site:P/u0"),
    ("P/u0/value", "atom:nil"), ("P/u0/value", "site:P/u0"), ("R", "atom:int"), ("site:P/u0.key", "atom:nil"),
    ("site:P/u0.key", "site:P/u0"), ("site:P/u0.value", "atom:nil"), ("site:P/u0.value", "site:P/u0")]

/-- Case `argument_tree`: model.py's `BadUse` rows. -/
def c_argument_tree_bad : List (String × String) := []

/-- Case `argument_tree`: printed roots. -/
def c_argument_tree_roots : List (String × String) := [("p", "P"), ("r", "R")]

/-- Case `chain64`: input relations. -/
def c_chain64 : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩]
  alloc := [("R63", "atom:int")]
  flow := [("R1", "R0"), ("R2", "R1"), ("R3", "R2"), ("R4", "R3"),
    ("R5", "R4"), ("R6", "R5"), ("R7", "R6"), ("R8", "R7"),
    ("R9", "R8"), ("R10", "R9"), ("R11", "R10"), ("R12", "R11"),
    ("R13", "R12"), ("R14", "R13"), ("R15", "R14"), ("R16", "R15"),
    ("R17", "R16"), ("R18", "R17"), ("R19", "R18"), ("R20", "R19"),
    ("R21", "R20"), ("R22", "R21"), ("R23", "R22"), ("R24", "R23"),
    ("R25", "R24"), ("R26", "R25"), ("R27", "R26"), ("R28", "R27"),
    ("R29", "R28"), ("R30", "R29"), ("R31", "R30"), ("R32", "R31"),
    ("R33", "R32"), ("R34", "R33"), ("R35", "R34"), ("R36", "R35"),
    ("R37", "R36"), ("R38", "R37"), ("R39", "R38"), ("R40", "R39"),
    ("R41", "R40"), ("R42", "R41"), ("R43", "R42"), ("R44", "R43"),
    ("R45", "R44"), ("R46", "R45"), ("R47", "R46"), ("R48", "R47"),
    ("R49", "R48"), ("R50", "R49"), ("R51", "R50"), ("R52", "R51"),
    ("R53", "R52"), ("R54", "R53"), ("R55", "R54"), ("R56", "R55"),
    ("R57", "R56"), ("R58", "R57"), ("R59", "R58"), ("R60", "R59"),
    ("R61", "R60"), ("R62", "R61"), ("R63", "R62")]

/-- Case `chain64`: model.py's solved `Pt` rows. -/
def c_chain64_pt : List (String × String) := [("R0", "atom:int"), ("R1", "atom:int"), ("R10", "atom:int"), ("R11", "atom:int"),
    ("R12", "atom:int"), ("R13", "atom:int"), ("R14", "atom:int"), ("R15", "atom:int"),
    ("R16", "atom:int"), ("R17", "atom:int"), ("R18", "atom:int"), ("R19", "atom:int"),
    ("R2", "atom:int"), ("R20", "atom:int"), ("R21", "atom:int"), ("R22", "atom:int"),
    ("R23", "atom:int"), ("R24", "atom:int"), ("R25", "atom:int"), ("R26", "atom:int"),
    ("R27", "atom:int"), ("R28", "atom:int"), ("R29", "atom:int"), ("R3", "atom:int"),
    ("R30", "atom:int"), ("R31", "atom:int"), ("R32", "atom:int"), ("R33", "atom:int"),
    ("R34", "atom:int"), ("R35", "atom:int"), ("R36", "atom:int"), ("R37", "atom:int"),
    ("R38", "atom:int"), ("R39", "atom:int"), ("R4", "atom:int"), ("R40", "atom:int"),
    ("R41", "atom:int"), ("R42", "atom:int"), ("R43", "atom:int"), ("R44", "atom:int"),
    ("R45", "atom:int"), ("R46", "atom:int"), ("R47", "atom:int"), ("R48", "atom:int"),
    ("R49", "atom:int"), ("R5", "atom:int"), ("R50", "atom:int"), ("R51", "atom:int"),
    ("R52", "atom:int"), ("R53", "atom:int"), ("R54", "atom:int"), ("R55", "atom:int"),
    ("R56", "atom:int"), ("R57", "atom:int"), ("R58", "atom:int"), ("R59", "atom:int"),
    ("R6", "atom:int"), ("R60", "atom:int"), ("R61", "atom:int"), ("R62", "atom:int"),
    ("R63", "atom:int"), ("R7", "atom:int"), ("R8", "atom:int"), ("R9", "atom:int")]

/-- Case `chain64`: model.py's `BadUse` rows. -/
def c_chain64_bad : List (String × String) := []

/-- Case `chain64`: printed roots. -/
def c_chain64_roots : List (String × String) := [("r0", "R0"), ("r1", "R1"), ("r10", "R10"), ("r11", "R11"),
    ("r12", "R12"), ("r13", "R13"), ("r14", "R14"), ("r15", "R15"),
    ("r16", "R16"), ("r17", "R17"), ("r18", "R18"), ("r19", "R19"),
    ("r2", "R2"), ("r20", "R20"), ("r21", "R21"), ("r22", "R22"),
    ("r23", "R23"), ("r24", "R24"), ("r25", "R25"), ("r26", "R26"),
    ("r27", "R27"), ("r28", "R28"), ("r29", "R29"), ("r3", "R3"),
    ("r30", "R30"), ("r31", "R31"), ("r32", "R32"), ("r33", "R33"),
    ("r34", "R34"), ("r35", "R35"), ("r36", "R36"), ("r37", "R37"),
    ("r38", "R38"), ("r39", "R39"), ("r4", "R4"), ("r40", "R40"),
    ("r41", "R41"), ("r42", "R42"), ("r43", "R43"), ("r44", "R44"),
    ("r45", "R45"), ("r46", "R46"), ("r47", "R47"), ("r48", "R48"),
    ("r49", "R49"), ("r5", "R5"), ("r50", "R50"), ("r51", "R51"),
    ("r52", "R52"), ("r53", "R53"), ("r54", "R54"), ("r55", "R55"),
    ("r56", "R56"), ("r57", "R57"), ("r58", "R58"), ("r59", "R59"),
    ("r6", "R6"), ("r60", "R60"), ("r61", "R61"), ("r62", "R62"),
    ("r63", "R63"), ("r7", "R7"), ("r8", "R8"), ("r9", "R9")]

/-- Case `f2_mono`: input relations. -/
def c_f2_mono : REDB where
  sites := [⟨"all/map", "array", ["elem"]⟩,
    ⟨"all/to_h", "hash", ["key", "value"]⟩,
    ⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"input_array_site", "array", ["elem"]⟩,
    ⟨"input_hash_site", "hash", ["key", "value"]⟩,
    ⟨"literal_d", "hash", ["key", "value"]⟩,
    ⟨"literal_e", "hash", ["key", "value"]⟩,
    ⟨"merge_site_d", "hash", ["key", "value"]⟩,
    ⟨"merge_site_e", "hash", ["key", "value"]⟩,
    ⟨"outer_array_site", "array", ["elem"]⟩,
    ⟨"outer_hash_site", "hash", ["key", "value"]⟩]
  alloc := [("keys", "atom:str"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("two", "atom:int"),
    ("nil", "atom:nil"), ("input_array", "input_array_site"), ("input_hash", "input_hash_site"), ("merge_arg_d", "literal_d"),
    ("merge_arg_e", "literal_e"), ("outer_array", "outer_array_site"), ("outer_hash", "outer_hash_site")]
  flow := [("all/strkey", "all/to_h.key"), ("all/hash_block_ret", "all/to_h.value"), ("all/array_block_ret", "all/map.elem"), ("one_and_x", "input_array_site.elem"),
    ("keys", "input_hash_site.key"), ("input_array", "input_hash_site.value"), ("keys", "literal_d.key"), ("two", "literal_d.value"),
    ("keys", "literal_e.key"), ("nil", "literal_e.value"), ("merged_e", "outer_array_site.elem"), ("merged_d", "outer_values"),
    ("outer_array", "outer_values"), ("keys", "outer_hash_site.key"), ("outer_values", "outer_hash_site.value")]
  load := [("all/hash_recv", "key", "all/block_k"), ("all/hash_recv", "value", "all/block_v"), ("all/array_recv", "elem", "all/block_elem")]
  filter := [("all/P", "hash", "all/hash_recv"), ("all/P", "array", "all/array_recv"), ("all/P", "str", "all/R"), ("all/P", "int", "all/R"),
    ("all/P", "nil", "all/R")]
  produce := [("all/P", "hash", "all/R", "all/to_h"), ("all/P", "array", "all/R", "all/map")]
  toStr := [("all/block_k", "all/strkey")]
  invoke := [("hash_value_call", "all/block_v", "all/hash_block_ret"), ("array_value_call", "all/block_elem", "all/array_block_ret"), ("inner_call", "input_hash", "inner"), ("outer_call", "outer_hash", "tree")]
  select := [("inner_call", "hash", "all"), ("inner_call", "array", "all"), ("inner_call", "str", "all"), ("inner_call", "int", "all"),
    ("inner_call", "nil", "all"), ("outer_call", "hash", "all"), ("outer_call", "array", "all"), ("outer_call", "str", "all"),
    ("outer_call", "int", "all"), ("outer_call", "nil", "all"), ("hash_value_call", "hash", "all"), ("hash_value_call", "array", "all"),
    ("hash_value_call", "str", "all"), ("hash_value_call", "int", "all"), ("hash_value_call", "nil", "all"), ("array_value_call", "hash", "all"),
    ("array_value_call", "array", "all"), ("array_value_call", "str", "all"), ("array_value_call", "int", "all"), ("array_value_call", "nil", "all")]
  formal := [("all", "all/P")]
  ret := [("all", "all/R")]
  merge := [("inner", "merge_arg_d", "merged_d", "merge_site_d"), ("inner", "merge_arg_e", "merged_e", "merge_site_e")]
  use := [("merge_d", "inner", "merge"), ("merge_e", "inner", "merge")]
  unsupported := [("merge", "array"), ("merge", "str"), ("merge", "int"), ("merge", "nil")]

/-- Case `f2_mono`: model.py's solved `Pt` rows. -/
def c_f2_mono_pt : List (String × String) := [("all/P", "all/map"), ("all/P", "all/to_h"), ("all/P", "atom:int"), ("all/P", "atom:nil"),
    ("all/P", "atom:str"), ("all/P", "input_array_site"), ("all/P", "input_hash_site"), ("all/P", "merge_site_d"),
    ("all/P", "merge_site_e"), ("all/P", "outer_array_site"), ("all/P", "outer_hash_site"), ("all/R", "all/map"),
    ("all/R", "all/to_h"), ("all/R", "atom:int"), ("all/R", "atom:nil"), ("all/R", "atom:str"),
    ("all/array_block_ret", "all/map"), ("all/array_block_ret", "all/to_h"), ("all/array_block_ret", "atom:int"), ("all/array_block_ret", "atom:nil"),
    ("all/array_block_ret", "atom:str"), ("all/array_recv", "all/map"), ("all/array_recv", "input_array_site"), ("all/array_recv", "outer_array_site"),
    ("all/block_elem", "all/map"), ("all/block_elem", "all/to_h"), ("all/block_elem", "atom:int"), ("all/block_elem", "atom:nil"),
    ("all/block_elem", "atom:str"), ("all/block_elem", "merge_site_e"), ("all/block_k", "atom:str"), ("all/block_v", "all/map"),
    ("all/block_v", "all/to_h"), ("all/block_v", "atom:int"), ("all/block_v", "atom:nil"), ("all/block_v", "atom:str"),
    ("all/block_v", "input_array_site"), ("all/block_v", "merge_site_d"), ("all/block_v", "outer_array_site"), ("all/hash_block_ret", "all/map"),
    ("all/hash_block_ret", "all/to_h"), ("all/hash_block_ret", "atom:int"), ("all/hash_block_ret", "atom:nil"), ("all/hash_block_ret", "atom:str"),
    ("all/hash_recv", "all/to_h"), ("all/hash_recv", "input_hash_site"), ("all/hash_recv", "merge_site_d"), ("all/hash_recv", "merge_site_e"),
    ("all/hash_recv", "outer_hash_site"), ("all/map.elem", "all/map"), ("all/map.elem", "all/to_h"), ("all/map.elem", "atom:int"),
    ("all/map.elem", "atom:nil"), ("all/map.elem", "atom:str"), ("all/strkey", "atom:str"), ("all/to_h.key", "atom:str"),
    ("all/to_h.value", "all/map"), ("all/to_h.value", "all/to_h"), ("all/to_h.value", "atom:int"), ("all/to_h.value", "atom:nil"),
    ("all/to_h.value", "atom:str"), ("inner", "all/map"), ("inner", "all/to_h"), ("inner", "atom:int"),
    ("inner", "atom:nil"), ("inner", "atom:str"), ("input_array", "input_array_site"), ("input_array_site.elem", "atom:int"),
    ("input_array_site.elem", "atom:str"), ("input_hash", "input_hash_site"), ("input_hash_site.key", "atom:str"), ("input_hash_site.value", "input_array_site"),
    ("keys", "atom:str"), ("literal_d.key", "atom:str"), ("literal_d.value", "atom:int"), ("literal_e.key", "atom:str"),
    ("literal_e.value", "atom:nil"), ("merge_arg_d", "literal_d"), ("merge_arg_e", "literal_e"), ("merge_site_d.key", "atom:str"),
    ("merge_site_d.value", "all/map"), ("merge_site_d.value", "all/to_h"), ("merge_site_d.value", "atom:int"), ("merge_site_d.value", "atom:nil"),
    ("merge_site_d.value", "atom:str"), ("merge_site_e.key", "atom:str"), ("merge_site_e.value", "all/map"), ("merge_site_e.value", "all/to_h"),
    ("merge_site_e.value", "atom:int"), ("merge_site_e.value", "atom:nil"), ("merge_site_e.value", "atom:str"), ("merged_d", "merge_site_d"),
    ("merged_e", "merge_site_e"), ("nil", "atom:nil"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"),
    ("outer_array", "outer_array_site"), ("outer_array_site.elem", "merge_site_e"), ("outer_hash", "outer_hash_site"), ("outer_hash_site.key", "atom:str"),
    ("outer_hash_site.value", "merge_site_d"), ("outer_hash_site.value", "outer_array_site"), ("outer_values", "merge_site_d"), ("outer_values", "outer_array_site"),
    ("tree", "all/map"), ("tree", "all/to_h"), ("tree", "atom:int"), ("tree", "atom:nil"),
    ("tree", "atom:str"), ("two", "atom:int")]

/-- Case `f2_mono`: model.py's `BadUse` rows. -/
def c_f2_mono_bad : List (String × String) := [("merge_d", "array"), ("merge_d", "int"), ("merge_d", "nil"), ("merge_d", "str"),
    ("merge_e", "array"), ("merge_e", "int"), ("merge_e", "nil"), ("merge_e", "str")]

/-- Case `f2_mono`: printed roots. -/
def c_f2_mono_roots : List (String × String) := [("inner", "inner"), ("tree", "tree")]

/-- Case `f2_mono_shared`: input relations. -/
def c_f2_mono_shared : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"input_array_site", "array", ["elem"]⟩,
    ⟨"input_hash_site", "hash", ["key", "value"]⟩,
    ⟨"literal_d", "hash", ["key", "value"]⟩,
    ⟨"literal_e", "hash", ["key", "value"]⟩,
    ⟨"merge_site_d", "hash", ["key", "value"]⟩,
    ⟨"merge_site_e", "hash", ["key", "value"]⟩,
    ⟨"outer_array_site", "array", ["elem"]⟩,
    ⟨"outer_hash_site", "hash", ["key", "value"]⟩,
    ⟨"shared/map", "array", ["elem"]⟩,
    ⟨"shared/to_h", "hash", ["key", "value"]⟩]
  alloc := [("keys", "atom:str"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("two", "atom:int"),
    ("nil", "atom:nil"), ("input_array", "input_array_site"), ("input_hash", "input_hash_site"), ("merge_arg_d", "literal_d"),
    ("merge_arg_e", "literal_e"), ("outer_array", "outer_array_site"), ("outer_hash", "outer_hash_site")]
  flow := [("all/strkey", "shared/to_h.key"), ("all/hash_block_ret", "shared/to_h.value"), ("all/array_block_ret", "shared/map.elem"), ("one_and_x", "input_array_site.elem"),
    ("keys", "input_hash_site.key"), ("input_array", "input_hash_site.value"), ("keys", "literal_d.key"), ("two", "literal_d.value"),
    ("keys", "literal_e.key"), ("nil", "literal_e.value"), ("merged_e", "outer_array_site.elem"), ("merged_d", "outer_values"),
    ("outer_array", "outer_values"), ("keys", "outer_hash_site.key"), ("outer_values", "outer_hash_site.value")]
  load := [("all/hash_recv", "key", "all/block_k"), ("all/hash_recv", "value", "all/block_v"), ("all/array_recv", "elem", "all/block_elem")]
  filter := [("all/P", "hash", "all/hash_recv"), ("all/P", "array", "all/array_recv"), ("all/P", "str", "all/R"), ("all/P", "int", "all/R"),
    ("all/P", "nil", "all/R")]
  produce := [("all/P", "hash", "all/R", "shared/to_h"), ("all/P", "array", "all/R", "shared/map")]
  toStr := [("all/block_k", "all/strkey")]
  invoke := [("hash_value_call", "all/block_v", "all/hash_block_ret"), ("array_value_call", "all/block_elem", "all/array_block_ret"), ("inner_call", "input_hash", "inner"), ("outer_call", "outer_hash", "tree")]
  select := [("inner_call", "hash", "all"), ("inner_call", "array", "all"), ("inner_call", "str", "all"), ("inner_call", "int", "all"),
    ("inner_call", "nil", "all"), ("outer_call", "hash", "all"), ("outer_call", "array", "all"), ("outer_call", "str", "all"),
    ("outer_call", "int", "all"), ("outer_call", "nil", "all"), ("hash_value_call", "hash", "all"), ("hash_value_call", "array", "all"),
    ("hash_value_call", "str", "all"), ("hash_value_call", "int", "all"), ("hash_value_call", "nil", "all"), ("array_value_call", "hash", "all"),
    ("array_value_call", "array", "all"), ("array_value_call", "str", "all"), ("array_value_call", "int", "all"), ("array_value_call", "nil", "all")]
  formal := [("all", "all/P")]
  ret := [("all", "all/R")]
  merge := [("inner", "merge_arg_d", "merged_d", "merge_site_d"), ("inner", "merge_arg_e", "merged_e", "merge_site_e")]
  use := [("merge_d", "inner", "merge"), ("merge_e", "inner", "merge")]
  unsupported := [("merge", "array"), ("merge", "str"), ("merge", "int"), ("merge", "nil")]

/-- Case `f2_mono_shared`: model.py's solved `Pt` rows. -/
def c_f2_mono_shared_pt : List (String × String) := [("all/P", "atom:int"), ("all/P", "atom:nil"), ("all/P", "atom:str"), ("all/P", "input_array_site"),
    ("all/P", "input_hash_site"), ("all/P", "merge_site_d"), ("all/P", "merge_site_e"), ("all/P", "outer_array_site"),
    ("all/P", "outer_hash_site"), ("all/P", "shared/map"), ("all/P", "shared/to_h"), ("all/R", "atom:int"),
    ("all/R", "atom:nil"), ("all/R", "atom:str"), ("all/R", "shared/map"), ("all/R", "shared/to_h"),
    ("all/array_block_ret", "atom:int"), ("all/array_block_ret", "atom:nil"), ("all/array_block_ret", "atom:str"), ("all/array_block_ret", "shared/map"),
    ("all/array_block_ret", "shared/to_h"), ("all/array_recv", "input_array_site"), ("all/array_recv", "outer_array_site"), ("all/array_recv", "shared/map"),
    ("all/block_elem", "atom:int"), ("all/block_elem", "atom:nil"), ("all/block_elem", "atom:str"), ("all/block_elem", "merge_site_e"),
    ("all/block_elem", "shared/map"), ("all/block_elem", "shared/to_h"), ("all/block_k", "atom:str"), ("all/block_v", "atom:int"),
    ("all/block_v", "atom:nil"), ("all/block_v", "atom:str"), ("all/block_v", "input_array_site"), ("all/block_v", "merge_site_d"),
    ("all/block_v", "outer_array_site"), ("all/block_v", "shared/map"), ("all/block_v", "shared/to_h"), ("all/hash_block_ret", "atom:int"),
    ("all/hash_block_ret", "atom:nil"), ("all/hash_block_ret", "atom:str"), ("all/hash_block_ret", "shared/map"), ("all/hash_block_ret", "shared/to_h"),
    ("all/hash_recv", "input_hash_site"), ("all/hash_recv", "merge_site_d"), ("all/hash_recv", "merge_site_e"), ("all/hash_recv", "outer_hash_site"),
    ("all/hash_recv", "shared/to_h"), ("all/strkey", "atom:str"), ("inner", "atom:int"), ("inner", "atom:nil"),
    ("inner", "atom:str"), ("inner", "shared/map"), ("inner", "shared/to_h"), ("input_array", "input_array_site"),
    ("input_array_site.elem", "atom:int"), ("input_array_site.elem", "atom:str"), ("input_hash", "input_hash_site"), ("input_hash_site.key", "atom:str"),
    ("input_hash_site.value", "input_array_site"), ("keys", "atom:str"), ("literal_d.key", "atom:str"), ("literal_d.value", "atom:int"),
    ("literal_e.key", "atom:str"), ("literal_e.value", "atom:nil"), ("merge_arg_d", "literal_d"), ("merge_arg_e", "literal_e"),
    ("merge_site_d.key", "atom:str"), ("merge_site_d.value", "atom:int"), ("merge_site_d.value", "atom:nil"), ("merge_site_d.value", "atom:str"),
    ("merge_site_d.value", "shared/map"), ("merge_site_d.value", "shared/to_h"), ("merge_site_e.key", "atom:str"), ("merge_site_e.value", "atom:int"),
    ("merge_site_e.value", "atom:nil"), ("merge_site_e.value", "atom:str"), ("merge_site_e.value", "shared/map"), ("merge_site_e.value", "shared/to_h"),
    ("merged_d", "merge_site_d"), ("merged_e", "merge_site_e"), ("nil", "atom:nil"), ("one_and_x", "atom:int"),
    ("one_and_x", "atom:str"), ("outer_array", "outer_array_site"), ("outer_array_site.elem", "merge_site_e"), ("outer_hash", "outer_hash_site"),
    ("outer_hash_site.key", "atom:str"), ("outer_hash_site.value", "merge_site_d"), ("outer_hash_site.value", "outer_array_site"), ("outer_values", "merge_site_d"),
    ("outer_values", "outer_array_site"), ("shared/map.elem", "atom:int"), ("shared/map.elem", "atom:nil"), ("shared/map.elem", "atom:str"),
    ("shared/map.elem", "shared/map"), ("shared/map.elem", "shared/to_h"), ("shared/to_h.key", "atom:str"), ("shared/to_h.value", "atom:int"),
    ("shared/to_h.value", "atom:nil"), ("shared/to_h.value", "atom:str"), ("shared/to_h.value", "shared/map"), ("shared/to_h.value", "shared/to_h"),
    ("tree", "atom:int"), ("tree", "atom:nil"), ("tree", "atom:str"), ("tree", "shared/map"),
    ("tree", "shared/to_h"), ("two", "atom:int")]

/-- Case `f2_mono_shared`: model.py's `BadUse` rows. -/
def c_f2_mono_shared_bad : List (String × String) := [("merge_d", "array"), ("merge_d", "int"), ("merge_d", "nil"), ("merge_d", "str"),
    ("merge_e", "array"), ("merge_e", "int"), ("merge_e", "nil"), ("merge_e", "str")]

/-- Case `f2_mono_shared`: printed roots. -/
def c_f2_mono_shared_roots : List (String × String) := [("inner", "inner"), ("tree", "tree")]

/-- Case `f2_receiver_type`: input relations. -/
def c_f2_receiver_type : REDB where
  sites := [⟨"TreesController/map", "array", ["elem"]⟩,
    ⟨"TreesController/to_h", "hash", ["key", "value"]⟩,
    ⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"input_array_site", "array", ["elem"]⟩,
    ⟨"input_hash_site", "hash", ["key", "value"]⟩,
    ⟨"literal_d", "hash", ["key", "value"]⟩,
    ⟨"literal_e", "hash", ["key", "value"]⟩,
    ⟨"merge_site_d", "hash", ["key", "value"]⟩,
    ⟨"merge_site_e", "hash", ["key", "value"]⟩,
    ⟨"outer_array_site", "array", ["elem"]⟩,
    ⟨"outer_hash_site", "hash", ["key", "value"]⟩]
  alloc := [("keys", "atom:str"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("two", "atom:int"),
    ("nil", "atom:nil"), ("input_array", "input_array_site"), ("input_hash", "input_hash_site"), ("merge_arg_d", "literal_d"),
    ("merge_arg_e", "literal_e"), ("outer_array", "outer_array_site"), ("outer_hash", "outer_hash_site")]
  flow := [("TreesController/strkey", "TreesController/to_h.key"), ("TreesController/hash_block_ret", "TreesController/to_h.value"), ("TreesController/array_block_ret", "TreesController/map.elem"), ("one_and_x", "input_array_site.elem"),
    ("keys", "input_hash_site.key"), ("input_array", "input_hash_site.value"), ("keys", "literal_d.key"), ("two", "literal_d.value"),
    ("keys", "literal_e.key"), ("nil", "literal_e.value"), ("merged_e", "outer_array_site.elem"), ("merged_d", "outer_values"),
    ("outer_array", "outer_values"), ("keys", "outer_hash_site.key"), ("outer_values", "outer_hash_site.value")]
  load := [("TreesController/hash_recv", "key", "TreesController/block_k"), ("TreesController/hash_recv", "value", "TreesController/block_v"), ("TreesController/array_recv", "elem", "TreesController/block_elem")]
  filter := [("TreesController/P", "hash", "TreesController/hash_recv"), ("TreesController/P", "array", "TreesController/array_recv"), ("TreesController/P", "str", "TreesController/R"), ("TreesController/P", "int", "TreesController/R"),
    ("TreesController/P", "nil", "TreesController/R")]
  produce := [("TreesController/P", "hash", "TreesController/R", "TreesController/to_h"), ("TreesController/P", "array", "TreesController/R", "TreesController/map")]
  toStr := [("TreesController/block_k", "TreesController/strkey")]
  invoke := [("hash_value_call", "TreesController/block_v", "TreesController/hash_block_ret"), ("array_value_call", "TreesController/block_elem", "TreesController/array_block_ret"), ("inner_call", "input_hash", "inner"), ("outer_call", "outer_hash", "tree")]
  select := [("inner_call", "hash", "TreesController"), ("inner_call", "array", "TreesController"), ("inner_call", "str", "TreesController"), ("inner_call", "int", "TreesController"),
    ("inner_call", "nil", "TreesController"), ("outer_call", "hash", "TreesController"), ("outer_call", "array", "TreesController"), ("outer_call", "str", "TreesController"),
    ("outer_call", "int", "TreesController"), ("outer_call", "nil", "TreesController"), ("hash_value_call", "hash", "TreesController"), ("hash_value_call", "array", "TreesController"),
    ("hash_value_call", "str", "TreesController"), ("hash_value_call", "int", "TreesController"), ("hash_value_call", "nil", "TreesController"), ("array_value_call", "hash", "TreesController"),
    ("array_value_call", "array", "TreesController"), ("array_value_call", "str", "TreesController"), ("array_value_call", "int", "TreesController"), ("array_value_call", "nil", "TreesController")]
  formal := [("TreesController", "TreesController/P")]
  ret := [("TreesController", "TreesController/R")]
  merge := [("inner", "merge_arg_d", "merged_d", "merge_site_d"), ("inner", "merge_arg_e", "merged_e", "merge_site_e")]
  use := [("merge_d", "inner", "merge"), ("merge_e", "inner", "merge")]
  unsupported := [("merge", "array"), ("merge", "str"), ("merge", "int"), ("merge", "nil")]

/-- Case `f2_receiver_type`: model.py's solved `Pt` rows. -/
def c_f2_receiver_type_pt : List (String × String) := [("TreesController/P", "TreesController/map"), ("TreesController/P", "TreesController/to_h"), ("TreesController/P", "atom:int"), ("TreesController/P", "atom:nil"),
    ("TreesController/P", "atom:str"), ("TreesController/P", "input_array_site"), ("TreesController/P", "input_hash_site"), ("TreesController/P", "merge_site_d"),
    ("TreesController/P", "merge_site_e"), ("TreesController/P", "outer_array_site"), ("TreesController/P", "outer_hash_site"), ("TreesController/R", "TreesController/map"),
    ("TreesController/R", "TreesController/to_h"), ("TreesController/R", "atom:int"), ("TreesController/R", "atom:nil"), ("TreesController/R", "atom:str"),
    ("TreesController/array_block_ret", "TreesController/map"), ("TreesController/array_block_ret", "TreesController/to_h"), ("TreesController/array_block_ret", "atom:int"), ("TreesController/array_block_ret", "atom:nil"),
    ("TreesController/array_block_ret", "atom:str"), ("TreesController/array_recv", "TreesController/map"), ("TreesController/array_recv", "input_array_site"), ("TreesController/array_recv", "outer_array_site"),
    ("TreesController/block_elem", "TreesController/map"), ("TreesController/block_elem", "TreesController/to_h"), ("TreesController/block_elem", "atom:int"), ("TreesController/block_elem", "atom:nil"),
    ("TreesController/block_elem", "atom:str"), ("TreesController/block_elem", "merge_site_e"), ("TreesController/block_k", "atom:str"), ("TreesController/block_v", "TreesController/map"),
    ("TreesController/block_v", "TreesController/to_h"), ("TreesController/block_v", "atom:int"), ("TreesController/block_v", "atom:nil"), ("TreesController/block_v", "atom:str"),
    ("TreesController/block_v", "input_array_site"), ("TreesController/block_v", "merge_site_d"), ("TreesController/block_v", "outer_array_site"), ("TreesController/hash_block_ret", "TreesController/map"),
    ("TreesController/hash_block_ret", "TreesController/to_h"), ("TreesController/hash_block_ret", "atom:int"), ("TreesController/hash_block_ret", "atom:nil"), ("TreesController/hash_block_ret", "atom:str"),
    ("TreesController/hash_recv", "TreesController/to_h"), ("TreesController/hash_recv", "input_hash_site"), ("TreesController/hash_recv", "merge_site_d"), ("TreesController/hash_recv", "merge_site_e"),
    ("TreesController/hash_recv", "outer_hash_site"), ("TreesController/map.elem", "TreesController/map"), ("TreesController/map.elem", "TreesController/to_h"), ("TreesController/map.elem", "atom:int"),
    ("TreesController/map.elem", "atom:nil"), ("TreesController/map.elem", "atom:str"), ("TreesController/strkey", "atom:str"), ("TreesController/to_h.key", "atom:str"),
    ("TreesController/to_h.value", "TreesController/map"), ("TreesController/to_h.value", "TreesController/to_h"), ("TreesController/to_h.value", "atom:int"), ("TreesController/to_h.value", "atom:nil"),
    ("TreesController/to_h.value", "atom:str"), ("inner", "TreesController/map"), ("inner", "TreesController/to_h"), ("inner", "atom:int"),
    ("inner", "atom:nil"), ("inner", "atom:str"), ("input_array", "input_array_site"), ("input_array_site.elem", "atom:int"),
    ("input_array_site.elem", "atom:str"), ("input_hash", "input_hash_site"), ("input_hash_site.key", "atom:str"), ("input_hash_site.value", "input_array_site"),
    ("keys", "atom:str"), ("literal_d.key", "atom:str"), ("literal_d.value", "atom:int"), ("literal_e.key", "atom:str"),
    ("literal_e.value", "atom:nil"), ("merge_arg_d", "literal_d"), ("merge_arg_e", "literal_e"), ("merge_site_d.key", "atom:str"),
    ("merge_site_d.value", "TreesController/map"), ("merge_site_d.value", "TreesController/to_h"), ("merge_site_d.value", "atom:int"), ("merge_site_d.value", "atom:nil"),
    ("merge_site_d.value", "atom:str"), ("merge_site_e.key", "atom:str"), ("merge_site_e.value", "TreesController/map"), ("merge_site_e.value", "TreesController/to_h"),
    ("merge_site_e.value", "atom:int"), ("merge_site_e.value", "atom:nil"), ("merge_site_e.value", "atom:str"), ("merged_d", "merge_site_d"),
    ("merged_e", "merge_site_e"), ("nil", "atom:nil"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"),
    ("outer_array", "outer_array_site"), ("outer_array_site.elem", "merge_site_e"), ("outer_hash", "outer_hash_site"), ("outer_hash_site.key", "atom:str"),
    ("outer_hash_site.value", "merge_site_d"), ("outer_hash_site.value", "outer_array_site"), ("outer_values", "merge_site_d"), ("outer_values", "outer_array_site"),
    ("tree", "TreesController/map"), ("tree", "TreesController/to_h"), ("tree", "atom:int"), ("tree", "atom:nil"),
    ("tree", "atom:str"), ("two", "atom:int")]

/-- Case `f2_receiver_type`: model.py's `BadUse` rows. -/
def c_f2_receiver_type_bad : List (String × String) := [("merge_d", "array"), ("merge_d", "int"), ("merge_d", "nil"), ("merge_d", "str"),
    ("merge_e", "array"), ("merge_e", "int"), ("merge_e", "nil"), ("merge_e", "str")]

/-- Case `f2_receiver_type`: printed roots. -/
def c_f2_receiver_type_roots : List (String × String) := [("inner", "inner"), ("tree", "tree")]

/-- Case `f2_receiver_type_shared`: input relations. -/
def c_f2_receiver_type_shared : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"input_array_site", "array", ["elem"]⟩,
    ⟨"input_hash_site", "hash", ["key", "value"]⟩,
    ⟨"literal_d", "hash", ["key", "value"]⟩,
    ⟨"literal_e", "hash", ["key", "value"]⟩,
    ⟨"merge_site_d", "hash", ["key", "value"]⟩,
    ⟨"merge_site_e", "hash", ["key", "value"]⟩,
    ⟨"outer_array_site", "array", ["elem"]⟩,
    ⟨"outer_hash_site", "hash", ["key", "value"]⟩,
    ⟨"shared/map", "array", ["elem"]⟩,
    ⟨"shared/to_h", "hash", ["key", "value"]⟩]
  alloc := [("keys", "atom:str"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("two", "atom:int"),
    ("nil", "atom:nil"), ("input_array", "input_array_site"), ("input_hash", "input_hash_site"), ("merge_arg_d", "literal_d"),
    ("merge_arg_e", "literal_e"), ("outer_array", "outer_array_site"), ("outer_hash", "outer_hash_site")]
  flow := [("TreesController/strkey", "shared/to_h.key"), ("TreesController/hash_block_ret", "shared/to_h.value"), ("TreesController/array_block_ret", "shared/map.elem"), ("one_and_x", "input_array_site.elem"),
    ("keys", "input_hash_site.key"), ("input_array", "input_hash_site.value"), ("keys", "literal_d.key"), ("two", "literal_d.value"),
    ("keys", "literal_e.key"), ("nil", "literal_e.value"), ("merged_e", "outer_array_site.elem"), ("merged_d", "outer_values"),
    ("outer_array", "outer_values"), ("keys", "outer_hash_site.key"), ("outer_values", "outer_hash_site.value")]
  load := [("TreesController/hash_recv", "key", "TreesController/block_k"), ("TreesController/hash_recv", "value", "TreesController/block_v"), ("TreesController/array_recv", "elem", "TreesController/block_elem")]
  filter := [("TreesController/P", "hash", "TreesController/hash_recv"), ("TreesController/P", "array", "TreesController/array_recv"), ("TreesController/P", "str", "TreesController/R"), ("TreesController/P", "int", "TreesController/R"),
    ("TreesController/P", "nil", "TreesController/R")]
  produce := [("TreesController/P", "hash", "TreesController/R", "shared/to_h"), ("TreesController/P", "array", "TreesController/R", "shared/map")]
  toStr := [("TreesController/block_k", "TreesController/strkey")]
  invoke := [("hash_value_call", "TreesController/block_v", "TreesController/hash_block_ret"), ("array_value_call", "TreesController/block_elem", "TreesController/array_block_ret"), ("inner_call", "input_hash", "inner"), ("outer_call", "outer_hash", "tree")]
  select := [("inner_call", "hash", "TreesController"), ("inner_call", "array", "TreesController"), ("inner_call", "str", "TreesController"), ("inner_call", "int", "TreesController"),
    ("inner_call", "nil", "TreesController"), ("outer_call", "hash", "TreesController"), ("outer_call", "array", "TreesController"), ("outer_call", "str", "TreesController"),
    ("outer_call", "int", "TreesController"), ("outer_call", "nil", "TreesController"), ("hash_value_call", "hash", "TreesController"), ("hash_value_call", "array", "TreesController"),
    ("hash_value_call", "str", "TreesController"), ("hash_value_call", "int", "TreesController"), ("hash_value_call", "nil", "TreesController"), ("array_value_call", "hash", "TreesController"),
    ("array_value_call", "array", "TreesController"), ("array_value_call", "str", "TreesController"), ("array_value_call", "int", "TreesController"), ("array_value_call", "nil", "TreesController")]
  formal := [("TreesController", "TreesController/P")]
  ret := [("TreesController", "TreesController/R")]
  merge := [("inner", "merge_arg_d", "merged_d", "merge_site_d"), ("inner", "merge_arg_e", "merged_e", "merge_site_e")]
  use := [("merge_d", "inner", "merge"), ("merge_e", "inner", "merge")]
  unsupported := [("merge", "array"), ("merge", "str"), ("merge", "int"), ("merge", "nil")]

/-- Case `f2_receiver_type_shared`: model.py's solved `Pt` rows. -/
def c_f2_receiver_type_shared_pt : List (String × String) := [("TreesController/P", "atom:int"), ("TreesController/P", "atom:nil"), ("TreesController/P", "atom:str"), ("TreesController/P", "input_array_site"),
    ("TreesController/P", "input_hash_site"), ("TreesController/P", "merge_site_d"), ("TreesController/P", "merge_site_e"), ("TreesController/P", "outer_array_site"),
    ("TreesController/P", "outer_hash_site"), ("TreesController/P", "shared/map"), ("TreesController/P", "shared/to_h"), ("TreesController/R", "atom:int"),
    ("TreesController/R", "atom:nil"), ("TreesController/R", "atom:str"), ("TreesController/R", "shared/map"), ("TreesController/R", "shared/to_h"),
    ("TreesController/array_block_ret", "atom:int"), ("TreesController/array_block_ret", "atom:nil"), ("TreesController/array_block_ret", "atom:str"), ("TreesController/array_block_ret", "shared/map"),
    ("TreesController/array_block_ret", "shared/to_h"), ("TreesController/array_recv", "input_array_site"), ("TreesController/array_recv", "outer_array_site"), ("TreesController/array_recv", "shared/map"),
    ("TreesController/block_elem", "atom:int"), ("TreesController/block_elem", "atom:nil"), ("TreesController/block_elem", "atom:str"), ("TreesController/block_elem", "merge_site_e"),
    ("TreesController/block_elem", "shared/map"), ("TreesController/block_elem", "shared/to_h"), ("TreesController/block_k", "atom:str"), ("TreesController/block_v", "atom:int"),
    ("TreesController/block_v", "atom:nil"), ("TreesController/block_v", "atom:str"), ("TreesController/block_v", "input_array_site"), ("TreesController/block_v", "merge_site_d"),
    ("TreesController/block_v", "outer_array_site"), ("TreesController/block_v", "shared/map"), ("TreesController/block_v", "shared/to_h"), ("TreesController/hash_block_ret", "atom:int"),
    ("TreesController/hash_block_ret", "atom:nil"), ("TreesController/hash_block_ret", "atom:str"), ("TreesController/hash_block_ret", "shared/map"), ("TreesController/hash_block_ret", "shared/to_h"),
    ("TreesController/hash_recv", "input_hash_site"), ("TreesController/hash_recv", "merge_site_d"), ("TreesController/hash_recv", "merge_site_e"), ("TreesController/hash_recv", "outer_hash_site"),
    ("TreesController/hash_recv", "shared/to_h"), ("TreesController/strkey", "atom:str"), ("inner", "atom:int"), ("inner", "atom:nil"),
    ("inner", "atom:str"), ("inner", "shared/map"), ("inner", "shared/to_h"), ("input_array", "input_array_site"),
    ("input_array_site.elem", "atom:int"), ("input_array_site.elem", "atom:str"), ("input_hash", "input_hash_site"), ("input_hash_site.key", "atom:str"),
    ("input_hash_site.value", "input_array_site"), ("keys", "atom:str"), ("literal_d.key", "atom:str"), ("literal_d.value", "atom:int"),
    ("literal_e.key", "atom:str"), ("literal_e.value", "atom:nil"), ("merge_arg_d", "literal_d"), ("merge_arg_e", "literal_e"),
    ("merge_site_d.key", "atom:str"), ("merge_site_d.value", "atom:int"), ("merge_site_d.value", "atom:nil"), ("merge_site_d.value", "atom:str"),
    ("merge_site_d.value", "shared/map"), ("merge_site_d.value", "shared/to_h"), ("merge_site_e.key", "atom:str"), ("merge_site_e.value", "atom:int"),
    ("merge_site_e.value", "atom:nil"), ("merge_site_e.value", "atom:str"), ("merge_site_e.value", "shared/map"), ("merge_site_e.value", "shared/to_h"),
    ("merged_d", "merge_site_d"), ("merged_e", "merge_site_e"), ("nil", "atom:nil"), ("one_and_x", "atom:int"),
    ("one_and_x", "atom:str"), ("outer_array", "outer_array_site"), ("outer_array_site.elem", "merge_site_e"), ("outer_hash", "outer_hash_site"),
    ("outer_hash_site.key", "atom:str"), ("outer_hash_site.value", "merge_site_d"), ("outer_hash_site.value", "outer_array_site"), ("outer_values", "merge_site_d"),
    ("outer_values", "outer_array_site"), ("shared/map.elem", "atom:int"), ("shared/map.elem", "atom:nil"), ("shared/map.elem", "atom:str"),
    ("shared/map.elem", "shared/map"), ("shared/map.elem", "shared/to_h"), ("shared/to_h.key", "atom:str"), ("shared/to_h.value", "atom:int"),
    ("shared/to_h.value", "atom:nil"), ("shared/to_h.value", "atom:str"), ("shared/to_h.value", "shared/map"), ("shared/to_h.value", "shared/to_h"),
    ("tree", "atom:int"), ("tree", "atom:nil"), ("tree", "atom:str"), ("tree", "shared/map"),
    ("tree", "shared/to_h"), ("two", "atom:int")]

/-- Case `f2_receiver_type_shared`: model.py's `BadUse` rows. -/
def c_f2_receiver_type_shared_bad : List (String × String) := [("merge_d", "array"), ("merge_d", "int"), ("merge_d", "nil"), ("merge_d", "str"),
    ("merge_e", "array"), ("merge_e", "int"), ("merge_e", "nil"), ("merge_e", "str")]

/-- Case `f2_receiver_type_shared`: printed roots. -/
def c_f2_receiver_type_shared_roots : List (String × String) := [("inner", "inner"), ("tree", "tree")]

/-- Case `f2_call1`: input relations. -/
def c_f2_call1 : REDB where
  sites := [⟨"array_value_call/map", "array", ["elem"]⟩,
    ⟨"array_value_call/to_h", "hash", ["key", "value"]⟩,
    ⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"hash_value_call/map", "array", ["elem"]⟩,
    ⟨"hash_value_call/to_h", "hash", ["key", "value"]⟩,
    ⟨"inner_call/map", "array", ["elem"]⟩,
    ⟨"inner_call/to_h", "hash", ["key", "value"]⟩,
    ⟨"input_array_site", "array", ["elem"]⟩,
    ⟨"input_hash_site", "hash", ["key", "value"]⟩,
    ⟨"literal_d", "hash", ["key", "value"]⟩,
    ⟨"literal_e", "hash", ["key", "value"]⟩,
    ⟨"merge_site_d", "hash", ["key", "value"]⟩,
    ⟨"merge_site_e", "hash", ["key", "value"]⟩,
    ⟨"outer_array_site", "array", ["elem"]⟩,
    ⟨"outer_call/map", "array", ["elem"]⟩,
    ⟨"outer_call/to_h", "hash", ["key", "value"]⟩,
    ⟨"outer_hash_site", "hash", ["key", "value"]⟩]
  alloc := [("keys", "atom:str"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("two", "atom:int"),
    ("nil", "atom:nil"), ("input_array", "input_array_site"), ("input_hash", "input_hash_site"), ("merge_arg_d", "literal_d"),
    ("merge_arg_e", "literal_e"), ("outer_array", "outer_array_site"), ("outer_hash", "outer_hash_site")]
  flow := [("inner_call/strkey", "inner_call/to_h.key"), ("inner_call/hash_block_ret", "inner_call/to_h.value"), ("inner_call/array_block_ret", "inner_call/map.elem"), ("outer_call/strkey", "outer_call/to_h.key"),
    ("outer_call/hash_block_ret", "outer_call/to_h.value"), ("outer_call/array_block_ret", "outer_call/map.elem"), ("hash_value_call/strkey", "hash_value_call/to_h.key"), ("hash_value_call/hash_block_ret", "hash_value_call/to_h.value"),
    ("hash_value_call/array_block_ret", "hash_value_call/map.elem"), ("array_value_call/strkey", "array_value_call/to_h.key"), ("array_value_call/hash_block_ret", "array_value_call/to_h.value"), ("array_value_call/array_block_ret", "array_value_call/map.elem"),
    ("one_and_x", "input_array_site.elem"), ("keys", "input_hash_site.key"), ("input_array", "input_hash_site.value"), ("keys", "literal_d.key"),
    ("two", "literal_d.value"), ("keys", "literal_e.key"), ("nil", "literal_e.value"), ("merged_e", "outer_array_site.elem"),
    ("merged_d", "outer_values"), ("outer_array", "outer_values"), ("keys", "outer_hash_site.key"), ("outer_values", "outer_hash_site.value")]
  load := [("inner_call/hash_recv", "key", "inner_call/block_k"), ("inner_call/hash_recv", "value", "inner_call/block_v"), ("inner_call/array_recv", "elem", "inner_call/block_elem"), ("outer_call/hash_recv", "key", "outer_call/block_k"),
    ("outer_call/hash_recv", "value", "outer_call/block_v"), ("outer_call/array_recv", "elem", "outer_call/block_elem"), ("hash_value_call/hash_recv", "key", "hash_value_call/block_k"), ("hash_value_call/hash_recv", "value", "hash_value_call/block_v"),
    ("hash_value_call/array_recv", "elem", "hash_value_call/block_elem"), ("array_value_call/hash_recv", "key", "array_value_call/block_k"), ("array_value_call/hash_recv", "value", "array_value_call/block_v"), ("array_value_call/array_recv", "elem", "array_value_call/block_elem")]
  filter := [("inner_call/P", "hash", "inner_call/hash_recv"), ("inner_call/P", "array", "inner_call/array_recv"), ("inner_call/P", "str", "inner_call/R"), ("inner_call/P", "int", "inner_call/R"),
    ("inner_call/P", "nil", "inner_call/R"), ("outer_call/P", "hash", "outer_call/hash_recv"), ("outer_call/P", "array", "outer_call/array_recv"), ("outer_call/P", "str", "outer_call/R"),
    ("outer_call/P", "int", "outer_call/R"), ("outer_call/P", "nil", "outer_call/R"), ("hash_value_call/P", "hash", "hash_value_call/hash_recv"), ("hash_value_call/P", "array", "hash_value_call/array_recv"),
    ("hash_value_call/P", "str", "hash_value_call/R"), ("hash_value_call/P", "int", "hash_value_call/R"), ("hash_value_call/P", "nil", "hash_value_call/R"), ("array_value_call/P", "hash", "array_value_call/hash_recv"),
    ("array_value_call/P", "array", "array_value_call/array_recv"), ("array_value_call/P", "str", "array_value_call/R"), ("array_value_call/P", "int", "array_value_call/R"), ("array_value_call/P", "nil", "array_value_call/R")]
  produce := [("inner_call/P", "hash", "inner_call/R", "inner_call/to_h"), ("inner_call/P", "array", "inner_call/R", "inner_call/map"), ("outer_call/P", "hash", "outer_call/R", "outer_call/to_h"), ("outer_call/P", "array", "outer_call/R", "outer_call/map"),
    ("hash_value_call/P", "hash", "hash_value_call/R", "hash_value_call/to_h"), ("hash_value_call/P", "array", "hash_value_call/R", "hash_value_call/map"), ("array_value_call/P", "hash", "array_value_call/R", "array_value_call/to_h"), ("array_value_call/P", "array", "array_value_call/R", "array_value_call/map")]
  toStr := [("inner_call/block_k", "inner_call/strkey"), ("outer_call/block_k", "outer_call/strkey"), ("hash_value_call/block_k", "hash_value_call/strkey"), ("array_value_call/block_k", "array_value_call/strkey")]
  invoke := [("hash_value_call", "inner_call/block_v", "inner_call/hash_block_ret"), ("array_value_call", "inner_call/block_elem", "inner_call/array_block_ret"), ("hash_value_call", "outer_call/block_v", "outer_call/hash_block_ret"), ("array_value_call", "outer_call/block_elem", "outer_call/array_block_ret"),
    ("hash_value_call", "hash_value_call/block_v", "hash_value_call/hash_block_ret"), ("array_value_call", "hash_value_call/block_elem", "hash_value_call/array_block_ret"), ("hash_value_call", "array_value_call/block_v", "array_value_call/hash_block_ret"), ("array_value_call", "array_value_call/block_elem", "array_value_call/array_block_ret"),
    ("inner_call", "input_hash", "inner"), ("outer_call", "outer_hash", "tree")]
  select := [("inner_call", "hash", "inner_call"), ("inner_call", "array", "inner_call"), ("inner_call", "str", "inner_call"), ("inner_call", "int", "inner_call"),
    ("inner_call", "nil", "inner_call"), ("outer_call", "hash", "outer_call"), ("outer_call", "array", "outer_call"), ("outer_call", "str", "outer_call"),
    ("outer_call", "int", "outer_call"), ("outer_call", "nil", "outer_call"), ("hash_value_call", "hash", "hash_value_call"), ("hash_value_call", "array", "hash_value_call"),
    ("hash_value_call", "str", "hash_value_call"), ("hash_value_call", "int", "hash_value_call"), ("hash_value_call", "nil", "hash_value_call"), ("array_value_call", "hash", "array_value_call"),
    ("array_value_call", "array", "array_value_call"), ("array_value_call", "str", "array_value_call"), ("array_value_call", "int", "array_value_call"), ("array_value_call", "nil", "array_value_call")]
  formal := [("inner_call", "inner_call/P"), ("outer_call", "outer_call/P"), ("hash_value_call", "hash_value_call/P"), ("array_value_call", "array_value_call/P")]
  ret := [("inner_call", "inner_call/R"), ("outer_call", "outer_call/R"), ("hash_value_call", "hash_value_call/R"), ("array_value_call", "array_value_call/R")]
  merge := [("inner", "merge_arg_d", "merged_d", "merge_site_d"), ("inner", "merge_arg_e", "merged_e", "merge_site_e")]
  use := [("merge_d", "inner", "merge"), ("merge_e", "inner", "merge")]
  unsupported := [("merge", "array"), ("merge", "str"), ("merge", "int"), ("merge", "nil")]

/-- Case `f2_call1`: model.py's solved `Pt` rows. -/
def c_f2_call1_pt : List (String × String) := [("array_value_call/P", "array_value_call/to_h"), ("array_value_call/P", "atom:int"), ("array_value_call/P", "atom:str"), ("array_value_call/P", "merge_site_e"),
    ("array_value_call/R", "array_value_call/to_h"), ("array_value_call/R", "atom:int"), ("array_value_call/R", "atom:str"), ("array_value_call/block_k", "atom:str"),
    ("array_value_call/block_v", "atom:int"), ("array_value_call/block_v", "atom:nil"), ("array_value_call/block_v", "hash_value_call/map"), ("array_value_call/block_v", "hash_value_call/to_h"),
    ("array_value_call/hash_block_ret", "atom:int"), ("array_value_call/hash_block_ret", "atom:nil"), ("array_value_call/hash_block_ret", "hash_value_call/map"), ("array_value_call/hash_block_ret", "hash_value_call/to_h"),
    ("array_value_call/hash_recv", "array_value_call/to_h"), ("array_value_call/hash_recv", "merge_site_e"), ("array_value_call/strkey", "atom:str"), ("array_value_call/to_h.key", "atom:str"),
    ("array_value_call/to_h.value", "atom:int"), ("array_value_call/to_h.value", "atom:nil"), ("array_value_call/to_h.value", "hash_value_call/map"), ("array_value_call/to_h.value", "hash_value_call/to_h"),
    ("hash_value_call/P", "atom:int"), ("hash_value_call/P", "atom:nil"), ("hash_value_call/P", "hash_value_call/map"), ("hash_value_call/P", "hash_value_call/to_h"),
    ("hash_value_call/P", "input_array_site"), ("hash_value_call/P", "merge_site_d"), ("hash_value_call/P", "outer_array_site"), ("hash_value_call/R", "atom:int"),
    ("hash_value_call/R", "atom:nil"), ("hash_value_call/R", "hash_value_call/map"), ("hash_value_call/R", "hash_value_call/to_h"), ("hash_value_call/array_block_ret", "array_value_call/to_h"),
    ("hash_value_call/array_block_ret", "atom:int"), ("hash_value_call/array_block_ret", "atom:str"), ("hash_value_call/array_recv", "hash_value_call/map"), ("hash_value_call/array_recv", "input_array_site"),
    ("hash_value_call/array_recv", "outer_array_site"), ("hash_value_call/block_elem", "array_value_call/to_h"), ("hash_value_call/block_elem", "atom:int"), ("hash_value_call/block_elem", "atom:str"),
    ("hash_value_call/block_elem", "merge_site_e"), ("hash_value_call/block_k", "atom:str"), ("hash_value_call/block_v", "atom:int"), ("hash_value_call/block_v", "atom:nil"),
    ("hash_value_call/block_v", "hash_value_call/map"), ("hash_value_call/block_v", "hash_value_call/to_h"), ("hash_value_call/hash_block_ret", "atom:int"), ("hash_value_call/hash_block_ret", "atom:nil"),
    ("hash_value_call/hash_block_ret", "hash_value_call/map"), ("hash_value_call/hash_block_ret", "hash_value_call/to_h"), ("hash_value_call/hash_recv", "hash_value_call/to_h"), ("hash_value_call/hash_recv", "merge_site_d"),
    ("hash_value_call/map.elem", "array_value_call/to_h"), ("hash_value_call/map.elem", "atom:int"), ("hash_value_call/map.elem", "atom:str"), ("hash_value_call/strkey", "atom:str"),
    ("hash_value_call/to_h.key", "atom:str"), ("hash_value_call/to_h.value", "atom:int"), ("hash_value_call/to_h.value", "atom:nil"), ("hash_value_call/to_h.value", "hash_value_call/map"),
    ("hash_value_call/to_h.value", "hash_value_call/to_h"), ("inner", "inner_call/to_h"), ("inner_call/P", "input_hash_site"), ("inner_call/R", "inner_call/to_h"),
    ("inner_call/block_k", "atom:str"), ("inner_call/block_v", "input_array_site"), ("inner_call/hash_block_ret", "atom:int"), ("inner_call/hash_block_ret", "atom:nil"),
    ("inner_call/hash_block_ret", "hash_value_call/map"), ("inner_call/hash_block_ret", "hash_value_call/to_h"), ("inner_call/hash_recv", "input_hash_site"), ("inner_call/strkey", "atom:str"),
    ("inner_call/to_h.key", "atom:str"), ("inner_call/to_h.value", "atom:int"), ("inner_call/to_h.value", "atom:nil"), ("inner_call/to_h.value", "hash_value_call/map"),
    ("inner_call/to_h.value", "hash_value_call/to_h"), ("input_array", "input_array_site"), ("input_array_site.elem", "atom:int"), ("input_array_site.elem", "atom:str"),
    ("input_hash", "input_hash_site"), ("input_hash_site.key", "atom:str"), ("input_hash_site.value", "input_array_site"), ("keys", "atom:str"),
    ("literal_d.key", "atom:str"), ("literal_d.value", "atom:int"), ("literal_e.key", "atom:str"), ("literal_e.value", "atom:nil"),
    ("merge_arg_d", "literal_d"), ("merge_arg_e", "literal_e"), ("merge_site_d.key", "atom:str"), ("merge_site_d.value", "atom:int"),
    ("merge_site_d.value", "atom:nil"), ("merge_site_d.value", "hash_value_call/map"), ("merge_site_d.value", "hash_value_call/to_h"), ("merge_site_e.key", "atom:str"),
    ("merge_site_e.value", "atom:int"), ("merge_site_e.value", "atom:nil"), ("merge_site_e.value", "hash_value_call/map"), ("merge_site_e.value", "hash_value_call/to_h"),
    ("merged_d", "merge_site_d"), ("merged_e", "merge_site_e"), ("nil", "atom:nil"), ("one_and_x", "atom:int"),
    ("one_and_x", "atom:str"), ("outer_array", "outer_array_site"), ("outer_array_site.elem", "merge_site_e"), ("outer_call/P", "outer_hash_site"),
    ("outer_call/R", "outer_call/to_h"), ("outer_call/block_k", "atom:str"), ("outer_call/block_v", "merge_site_d"), ("outer_call/block_v", "outer_array_site"),
    ("outer_call/hash_block_ret", "atom:int"), ("outer_call/hash_block_ret", "atom:nil"), ("outer_call/hash_block_ret", "hash_value_call/map"), ("outer_call/hash_block_ret", "hash_value_call/to_h"),
    ("outer_call/hash_recv", "outer_hash_site"), ("outer_call/strkey", "atom:str"), ("outer_call/to_h.key", "atom:str"), ("outer_call/to_h.value", "atom:int"),
    ("outer_call/to_h.value", "atom:nil"), ("outer_call/to_h.value", "hash_value_call/map"), ("outer_call/to_h.value", "hash_value_call/to_h"), ("outer_hash", "outer_hash_site"),
    ("outer_hash_site.key", "atom:str"), ("outer_hash_site.value", "merge_site_d"), ("outer_hash_site.value", "outer_array_site"), ("outer_values", "merge_site_d"),
    ("outer_values", "outer_array_site"), ("tree", "outer_call/to_h"), ("two", "atom:int")]

/-- Case `f2_call1`: model.py's `BadUse` rows. -/
def c_f2_call1_bad : List (String × String) := []

/-- Case `f2_call1`: printed roots. -/
def c_f2_call1_roots : List (String × String) := [("inner", "inner"), ("tree", "tree")]

/-- Case `f2_call1_shared`: input relations. -/
def c_f2_call1_shared : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"input_array_site", "array", ["elem"]⟩,
    ⟨"input_hash_site", "hash", ["key", "value"]⟩,
    ⟨"literal_d", "hash", ["key", "value"]⟩,
    ⟨"literal_e", "hash", ["key", "value"]⟩,
    ⟨"merge_site_d", "hash", ["key", "value"]⟩,
    ⟨"merge_site_e", "hash", ["key", "value"]⟩,
    ⟨"outer_array_site", "array", ["elem"]⟩,
    ⟨"outer_hash_site", "hash", ["key", "value"]⟩,
    ⟨"shared/map", "array", ["elem"]⟩,
    ⟨"shared/to_h", "hash", ["key", "value"]⟩]
  alloc := [("keys", "atom:str"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("two", "atom:int"),
    ("nil", "atom:nil"), ("input_array", "input_array_site"), ("input_hash", "input_hash_site"), ("merge_arg_d", "literal_d"),
    ("merge_arg_e", "literal_e"), ("outer_array", "outer_array_site"), ("outer_hash", "outer_hash_site")]
  flow := [("inner_call/strkey", "shared/to_h.key"), ("inner_call/hash_block_ret", "shared/to_h.value"), ("inner_call/array_block_ret", "shared/map.elem"), ("outer_call/strkey", "shared/to_h.key"),
    ("outer_call/hash_block_ret", "shared/to_h.value"), ("outer_call/array_block_ret", "shared/map.elem"), ("hash_value_call/strkey", "shared/to_h.key"), ("hash_value_call/hash_block_ret", "shared/to_h.value"),
    ("hash_value_call/array_block_ret", "shared/map.elem"), ("array_value_call/strkey", "shared/to_h.key"), ("array_value_call/hash_block_ret", "shared/to_h.value"), ("array_value_call/array_block_ret", "shared/map.elem"),
    ("one_and_x", "input_array_site.elem"), ("keys", "input_hash_site.key"), ("input_array", "input_hash_site.value"), ("keys", "literal_d.key"),
    ("two", "literal_d.value"), ("keys", "literal_e.key"), ("nil", "literal_e.value"), ("merged_e", "outer_array_site.elem"),
    ("merged_d", "outer_values"), ("outer_array", "outer_values"), ("keys", "outer_hash_site.key"), ("outer_values", "outer_hash_site.value")]
  load := [("inner_call/hash_recv", "key", "inner_call/block_k"), ("inner_call/hash_recv", "value", "inner_call/block_v"), ("inner_call/array_recv", "elem", "inner_call/block_elem"), ("outer_call/hash_recv", "key", "outer_call/block_k"),
    ("outer_call/hash_recv", "value", "outer_call/block_v"), ("outer_call/array_recv", "elem", "outer_call/block_elem"), ("hash_value_call/hash_recv", "key", "hash_value_call/block_k"), ("hash_value_call/hash_recv", "value", "hash_value_call/block_v"),
    ("hash_value_call/array_recv", "elem", "hash_value_call/block_elem"), ("array_value_call/hash_recv", "key", "array_value_call/block_k"), ("array_value_call/hash_recv", "value", "array_value_call/block_v"), ("array_value_call/array_recv", "elem", "array_value_call/block_elem")]
  filter := [("inner_call/P", "hash", "inner_call/hash_recv"), ("inner_call/P", "array", "inner_call/array_recv"), ("inner_call/P", "str", "inner_call/R"), ("inner_call/P", "int", "inner_call/R"),
    ("inner_call/P", "nil", "inner_call/R"), ("outer_call/P", "hash", "outer_call/hash_recv"), ("outer_call/P", "array", "outer_call/array_recv"), ("outer_call/P", "str", "outer_call/R"),
    ("outer_call/P", "int", "outer_call/R"), ("outer_call/P", "nil", "outer_call/R"), ("hash_value_call/P", "hash", "hash_value_call/hash_recv"), ("hash_value_call/P", "array", "hash_value_call/array_recv"),
    ("hash_value_call/P", "str", "hash_value_call/R"), ("hash_value_call/P", "int", "hash_value_call/R"), ("hash_value_call/P", "nil", "hash_value_call/R"), ("array_value_call/P", "hash", "array_value_call/hash_recv"),
    ("array_value_call/P", "array", "array_value_call/array_recv"), ("array_value_call/P", "str", "array_value_call/R"), ("array_value_call/P", "int", "array_value_call/R"), ("array_value_call/P", "nil", "array_value_call/R")]
  produce := [("inner_call/P", "hash", "inner_call/R", "shared/to_h"), ("inner_call/P", "array", "inner_call/R", "shared/map"), ("outer_call/P", "hash", "outer_call/R", "shared/to_h"), ("outer_call/P", "array", "outer_call/R", "shared/map"),
    ("hash_value_call/P", "hash", "hash_value_call/R", "shared/to_h"), ("hash_value_call/P", "array", "hash_value_call/R", "shared/map"), ("array_value_call/P", "hash", "array_value_call/R", "shared/to_h"), ("array_value_call/P", "array", "array_value_call/R", "shared/map")]
  toStr := [("inner_call/block_k", "inner_call/strkey"), ("outer_call/block_k", "outer_call/strkey"), ("hash_value_call/block_k", "hash_value_call/strkey"), ("array_value_call/block_k", "array_value_call/strkey")]
  invoke := [("hash_value_call", "inner_call/block_v", "inner_call/hash_block_ret"), ("array_value_call", "inner_call/block_elem", "inner_call/array_block_ret"), ("hash_value_call", "outer_call/block_v", "outer_call/hash_block_ret"), ("array_value_call", "outer_call/block_elem", "outer_call/array_block_ret"),
    ("hash_value_call", "hash_value_call/block_v", "hash_value_call/hash_block_ret"), ("array_value_call", "hash_value_call/block_elem", "hash_value_call/array_block_ret"), ("hash_value_call", "array_value_call/block_v", "array_value_call/hash_block_ret"), ("array_value_call", "array_value_call/block_elem", "array_value_call/array_block_ret"),
    ("inner_call", "input_hash", "inner"), ("outer_call", "outer_hash", "tree")]
  select := [("inner_call", "hash", "inner_call"), ("inner_call", "array", "inner_call"), ("inner_call", "str", "inner_call"), ("inner_call", "int", "inner_call"),
    ("inner_call", "nil", "inner_call"), ("outer_call", "hash", "outer_call"), ("outer_call", "array", "outer_call"), ("outer_call", "str", "outer_call"),
    ("outer_call", "int", "outer_call"), ("outer_call", "nil", "outer_call"), ("hash_value_call", "hash", "hash_value_call"), ("hash_value_call", "array", "hash_value_call"),
    ("hash_value_call", "str", "hash_value_call"), ("hash_value_call", "int", "hash_value_call"), ("hash_value_call", "nil", "hash_value_call"), ("array_value_call", "hash", "array_value_call"),
    ("array_value_call", "array", "array_value_call"), ("array_value_call", "str", "array_value_call"), ("array_value_call", "int", "array_value_call"), ("array_value_call", "nil", "array_value_call")]
  formal := [("inner_call", "inner_call/P"), ("outer_call", "outer_call/P"), ("hash_value_call", "hash_value_call/P"), ("array_value_call", "array_value_call/P")]
  ret := [("inner_call", "inner_call/R"), ("outer_call", "outer_call/R"), ("hash_value_call", "hash_value_call/R"), ("array_value_call", "array_value_call/R")]
  merge := [("inner", "merge_arg_d", "merged_d", "merge_site_d"), ("inner", "merge_arg_e", "merged_e", "merge_site_e")]
  use := [("merge_d", "inner", "merge"), ("merge_e", "inner", "merge")]
  unsupported := [("merge", "array"), ("merge", "str"), ("merge", "int"), ("merge", "nil")]

/-- Case `f2_call1_shared`: model.py's solved `Pt` rows. -/
def c_f2_call1_shared_pt : List (String × String) := [("array_value_call/P", "atom:int"), ("array_value_call/P", "atom:str"), ("array_value_call/P", "merge_site_e"), ("array_value_call/P", "shared/to_h"),
    ("array_value_call/R", "atom:int"), ("array_value_call/R", "atom:str"), ("array_value_call/R", "shared/to_h"), ("array_value_call/block_k", "atom:str"),
    ("array_value_call/block_v", "atom:int"), ("array_value_call/block_v", "atom:nil"), ("array_value_call/block_v", "shared/map"), ("array_value_call/block_v", "shared/to_h"),
    ("array_value_call/hash_block_ret", "atom:int"), ("array_value_call/hash_block_ret", "atom:nil"), ("array_value_call/hash_block_ret", "shared/map"), ("array_value_call/hash_block_ret", "shared/to_h"),
    ("array_value_call/hash_recv", "merge_site_e"), ("array_value_call/hash_recv", "shared/to_h"), ("array_value_call/strkey", "atom:str"), ("hash_value_call/P", "atom:int"),
    ("hash_value_call/P", "atom:nil"), ("hash_value_call/P", "input_array_site"), ("hash_value_call/P", "merge_site_d"), ("hash_value_call/P", "outer_array_site"),
    ("hash_value_call/P", "shared/map"), ("hash_value_call/P", "shared/to_h"), ("hash_value_call/R", "atom:int"), ("hash_value_call/R", "atom:nil"),
    ("hash_value_call/R", "shared/map"), ("hash_value_call/R", "shared/to_h"), ("hash_value_call/array_block_ret", "atom:int"), ("hash_value_call/array_block_ret", "atom:str"),
    ("hash_value_call/array_block_ret", "shared/to_h"), ("hash_value_call/array_recv", "input_array_site"), ("hash_value_call/array_recv", "outer_array_site"), ("hash_value_call/array_recv", "shared/map"),
    ("hash_value_call/block_elem", "atom:int"), ("hash_value_call/block_elem", "atom:str"), ("hash_value_call/block_elem", "merge_site_e"), ("hash_value_call/block_elem", "shared/to_h"),
    ("hash_value_call/block_k", "atom:str"), ("hash_value_call/block_v", "atom:int"), ("hash_value_call/block_v", "atom:nil"), ("hash_value_call/block_v", "shared/map"),
    ("hash_value_call/block_v", "shared/to_h"), ("hash_value_call/hash_block_ret", "atom:int"), ("hash_value_call/hash_block_ret", "atom:nil"), ("hash_value_call/hash_block_ret", "shared/map"),
    ("hash_value_call/hash_block_ret", "shared/to_h"), ("hash_value_call/hash_recv", "merge_site_d"), ("hash_value_call/hash_recv", "shared/to_h"), ("hash_value_call/strkey", "atom:str"),
    ("inner", "shared/to_h"), ("inner_call/P", "input_hash_site"), ("inner_call/R", "shared/to_h"), ("inner_call/block_k", "atom:str"),
    ("inner_call/block_v", "input_array_site"), ("inner_call/hash_block_ret", "atom:int"), ("inner_call/hash_block_ret", "atom:nil"), ("inner_call/hash_block_ret", "shared/map"),
    ("inner_call/hash_block_ret", "shared/to_h"), ("inner_call/hash_recv", "input_hash_site"), ("inner_call/strkey", "atom:str"), ("input_array", "input_array_site"),
    ("input_array_site.elem", "atom:int"), ("input_array_site.elem", "atom:str"), ("input_hash", "input_hash_site"), ("input_hash_site.key", "atom:str"),
    ("input_hash_site.value", "input_array_site"), ("keys", "atom:str"), ("literal_d.key", "atom:str"), ("literal_d.value", "atom:int"),
    ("literal_e.key", "atom:str"), ("literal_e.value", "atom:nil"), ("merge_arg_d", "literal_d"), ("merge_arg_e", "literal_e"),
    ("merge_site_d.key", "atom:str"), ("merge_site_d.value", "atom:int"), ("merge_site_d.value", "atom:nil"), ("merge_site_d.value", "shared/map"),
    ("merge_site_d.value", "shared/to_h"), ("merge_site_e.key", "atom:str"), ("merge_site_e.value", "atom:int"), ("merge_site_e.value", "atom:nil"),
    ("merge_site_e.value", "shared/map"), ("merge_site_e.value", "shared/to_h"), ("merged_d", "merge_site_d"), ("merged_e", "merge_site_e"),
    ("nil", "atom:nil"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("outer_array", "outer_array_site"),
    ("outer_array_site.elem", "merge_site_e"), ("outer_call/P", "outer_hash_site"), ("outer_call/R", "shared/to_h"), ("outer_call/block_k", "atom:str"),
    ("outer_call/block_v", "merge_site_d"), ("outer_call/block_v", "outer_array_site"), ("outer_call/hash_block_ret", "atom:int"), ("outer_call/hash_block_ret", "atom:nil"),
    ("outer_call/hash_block_ret", "shared/map"), ("outer_call/hash_block_ret", "shared/to_h"), ("outer_call/hash_recv", "outer_hash_site"), ("outer_call/strkey", "atom:str"),
    ("outer_hash", "outer_hash_site"), ("outer_hash_site.key", "atom:str"), ("outer_hash_site.value", "merge_site_d"), ("outer_hash_site.value", "outer_array_site"),
    ("outer_values", "merge_site_d"), ("outer_values", "outer_array_site"), ("shared/map.elem", "atom:int"), ("shared/map.elem", "atom:str"),
    ("shared/map.elem", "shared/to_h"), ("shared/to_h.key", "atom:str"), ("shared/to_h.value", "atom:int"), ("shared/to_h.value", "atom:nil"),
    ("shared/to_h.value", "shared/map"), ("shared/to_h.value", "shared/to_h"), ("tree", "shared/to_h"), ("two", "atom:int")]

/-- Case `f2_call1_shared`: model.py's `BadUse` rows. -/
def c_f2_call1_shared_bad : List (String × String) := []

/-- Case `f2_call1_shared`: printed roots. -/
def c_f2_call1_shared_roots : List (String × String) := [("inner", "inner"), ("tree", "tree")]

/-- Case `f2_arg_head`: input relations. -/
def c_f2_arg_head : REDB where
  sites := [⟨"array/map", "array", ["elem"]⟩,
    ⟨"array/to_h", "hash", ["key", "value"]⟩,
    ⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"hash/map", "array", ["elem"]⟩,
    ⟨"hash/to_h", "hash", ["key", "value"]⟩,
    ⟨"input_array_site", "array", ["elem"]⟩,
    ⟨"input_hash_site", "hash", ["key", "value"]⟩,
    ⟨"int/map", "array", ["elem"]⟩,
    ⟨"int/to_h", "hash", ["key", "value"]⟩,
    ⟨"literal_d", "hash", ["key", "value"]⟩,
    ⟨"literal_e", "hash", ["key", "value"]⟩,
    ⟨"merge_site_d", "hash", ["key", "value"]⟩,
    ⟨"merge_site_e", "hash", ["key", "value"]⟩,
    ⟨"nil/map", "array", ["elem"]⟩,
    ⟨"nil/to_h", "hash", ["key", "value"]⟩,
    ⟨"outer_array_site", "array", ["elem"]⟩,
    ⟨"outer_hash_site", "hash", ["key", "value"]⟩,
    ⟨"str/map", "array", ["elem"]⟩,
    ⟨"str/to_h", "hash", ["key", "value"]⟩]
  alloc := [("keys", "atom:str"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("two", "atom:int"),
    ("nil", "atom:nil"), ("input_array", "input_array_site"), ("input_hash", "input_hash_site"), ("merge_arg_d", "literal_d"),
    ("merge_arg_e", "literal_e"), ("outer_array", "outer_array_site"), ("outer_hash", "outer_hash_site")]
  flow := [("hash/strkey", "hash/to_h.key"), ("hash/hash_block_ret", "hash/to_h.value"), ("hash/array_block_ret", "hash/map.elem"), ("array/strkey", "array/to_h.key"),
    ("array/hash_block_ret", "array/to_h.value"), ("array/array_block_ret", "array/map.elem"), ("str/strkey", "str/to_h.key"), ("str/hash_block_ret", "str/to_h.value"),
    ("str/array_block_ret", "str/map.elem"), ("int/strkey", "int/to_h.key"), ("int/hash_block_ret", "int/to_h.value"), ("int/array_block_ret", "int/map.elem"),
    ("nil/strkey", "nil/to_h.key"), ("nil/hash_block_ret", "nil/to_h.value"), ("nil/array_block_ret", "nil/map.elem"), ("one_and_x", "input_array_site.elem"),
    ("keys", "input_hash_site.key"), ("input_array", "input_hash_site.value"), ("keys", "literal_d.key"), ("two", "literal_d.value"),
    ("keys", "literal_e.key"), ("nil", "literal_e.value"), ("merged_e", "outer_array_site.elem"), ("merged_d", "outer_values"),
    ("outer_array", "outer_values"), ("keys", "outer_hash_site.key"), ("outer_values", "outer_hash_site.value")]
  load := [("hash/hash_recv", "key", "hash/block_k"), ("hash/hash_recv", "value", "hash/block_v"), ("hash/array_recv", "elem", "hash/block_elem"), ("array/hash_recv", "key", "array/block_k"),
    ("array/hash_recv", "value", "array/block_v"), ("array/array_recv", "elem", "array/block_elem"), ("str/hash_recv", "key", "str/block_k"), ("str/hash_recv", "value", "str/block_v"),
    ("str/array_recv", "elem", "str/block_elem"), ("int/hash_recv", "key", "int/block_k"), ("int/hash_recv", "value", "int/block_v"), ("int/array_recv", "elem", "int/block_elem"),
    ("nil/hash_recv", "key", "nil/block_k"), ("nil/hash_recv", "value", "nil/block_v"), ("nil/array_recv", "elem", "nil/block_elem")]
  filter := [("hash/P", "hash", "hash/hash_recv"), ("hash/P", "array", "hash/array_recv"), ("hash/P", "str", "hash/R"), ("hash/P", "int", "hash/R"),
    ("hash/P", "nil", "hash/R"), ("array/P", "hash", "array/hash_recv"), ("array/P", "array", "array/array_recv"), ("array/P", "str", "array/R"),
    ("array/P", "int", "array/R"), ("array/P", "nil", "array/R"), ("str/P", "hash", "str/hash_recv"), ("str/P", "array", "str/array_recv"),
    ("str/P", "str", "str/R"), ("str/P", "int", "str/R"), ("str/P", "nil", "str/R"), ("int/P", "hash", "int/hash_recv"),
    ("int/P", "array", "int/array_recv"), ("int/P", "str", "int/R"), ("int/P", "int", "int/R"), ("int/P", "nil", "int/R"),
    ("nil/P", "hash", "nil/hash_recv"), ("nil/P", "array", "nil/array_recv"), ("nil/P", "str", "nil/R"), ("nil/P", "int", "nil/R"),
    ("nil/P", "nil", "nil/R")]
  produce := [("hash/P", "hash", "hash/R", "hash/to_h"), ("hash/P", "array", "hash/R", "hash/map"), ("array/P", "hash", "array/R", "array/to_h"), ("array/P", "array", "array/R", "array/map"),
    ("str/P", "hash", "str/R", "str/to_h"), ("str/P", "array", "str/R", "str/map"), ("int/P", "hash", "int/R", "int/to_h"), ("int/P", "array", "int/R", "int/map"),
    ("nil/P", "hash", "nil/R", "nil/to_h"), ("nil/P", "array", "nil/R", "nil/map")]
  toStr := [("hash/block_k", "hash/strkey"), ("array/block_k", "array/strkey"), ("str/block_k", "str/strkey"), ("int/block_k", "int/strkey"),
    ("nil/block_k", "nil/strkey")]
  invoke := [("hash_value_call", "hash/block_v", "hash/hash_block_ret"), ("array_value_call", "hash/block_elem", "hash/array_block_ret"), ("hash_value_call", "array/block_v", "array/hash_block_ret"), ("array_value_call", "array/block_elem", "array/array_block_ret"),
    ("hash_value_call", "str/block_v", "str/hash_block_ret"), ("array_value_call", "str/block_elem", "str/array_block_ret"), ("hash_value_call", "int/block_v", "int/hash_block_ret"), ("array_value_call", "int/block_elem", "int/array_block_ret"),
    ("hash_value_call", "nil/block_v", "nil/hash_block_ret"), ("array_value_call", "nil/block_elem", "nil/array_block_ret"), ("inner_call", "input_hash", "inner"), ("outer_call", "outer_hash", "tree")]
  select := [("inner_call", "hash", "hash"), ("inner_call", "array", "array"), ("inner_call", "str", "str"), ("inner_call", "int", "int"),
    ("inner_call", "nil", "nil"), ("outer_call", "hash", "hash"), ("outer_call", "array", "array"), ("outer_call", "str", "str"),
    ("outer_call", "int", "int"), ("outer_call", "nil", "nil"), ("hash_value_call", "hash", "hash"), ("hash_value_call", "array", "array"),
    ("hash_value_call", "str", "str"), ("hash_value_call", "int", "int"), ("hash_value_call", "nil", "nil"), ("array_value_call", "hash", "hash"),
    ("array_value_call", "array", "array"), ("array_value_call", "str", "str"), ("array_value_call", "int", "int"), ("array_value_call", "nil", "nil")]
  formal := [("hash", "hash/P"), ("array", "array/P"), ("str", "str/P"), ("int", "int/P"),
    ("nil", "nil/P")]
  ret := [("hash", "hash/R"), ("array", "array/R"), ("str", "str/R"), ("int", "int/R"),
    ("nil", "nil/R")]
  merge := [("inner", "merge_arg_d", "merged_d", "merge_site_d"), ("inner", "merge_arg_e", "merged_e", "merge_site_e")]
  use := [("merge_d", "inner", "merge"), ("merge_e", "inner", "merge")]
  unsupported := [("merge", "array"), ("merge", "str"), ("merge", "int"), ("merge", "nil")]

/-- Case `f2_arg_head`: model.py's solved `Pt` rows. -/
def c_f2_arg_head_pt : List (String × String) := [("array/P", "array/map"), ("array/P", "input_array_site"), ("array/P", "outer_array_site"), ("array/R", "array/map"),
    ("array/array_block_ret", "atom:int"), ("array/array_block_ret", "atom:str"), ("array/array_block_ret", "hash/to_h"), ("array/array_recv", "array/map"),
    ("array/array_recv", "input_array_site"), ("array/array_recv", "outer_array_site"), ("array/block_elem", "atom:int"), ("array/block_elem", "atom:str"),
    ("array/block_elem", "hash/to_h"), ("array/block_elem", "merge_site_e"), ("array/map.elem", "atom:int"), ("array/map.elem", "atom:str"),
    ("array/map.elem", "hash/to_h"), ("hash/P", "hash/to_h"), ("hash/P", "input_hash_site"), ("hash/P", "merge_site_d"),
    ("hash/P", "merge_site_e"), ("hash/P", "outer_hash_site"), ("hash/R", "hash/to_h"), ("hash/block_k", "atom:str"),
    ("hash/block_v", "array/map"), ("hash/block_v", "atom:int"), ("hash/block_v", "atom:nil"), ("hash/block_v", "hash/to_h"),
    ("hash/block_v", "input_array_site"), ("hash/block_v", "merge_site_d"), ("hash/block_v", "outer_array_site"), ("hash/hash_block_ret", "array/map"),
    ("hash/hash_block_ret", "atom:int"), ("hash/hash_block_ret", "atom:nil"), ("hash/hash_block_ret", "hash/to_h"), ("hash/hash_recv", "hash/to_h"),
    ("hash/hash_recv", "input_hash_site"), ("hash/hash_recv", "merge_site_d"), ("hash/hash_recv", "merge_site_e"), ("hash/hash_recv", "outer_hash_site"),
    ("hash/strkey", "atom:str"), ("hash/to_h.key", "atom:str"), ("hash/to_h.value", "array/map"), ("hash/to_h.value", "atom:int"),
    ("hash/to_h.value", "atom:nil"), ("hash/to_h.value", "hash/to_h"), ("inner", "hash/to_h"), ("input_array", "input_array_site"),
    ("input_array_site.elem", "atom:int"), ("input_array_site.elem", "atom:str"), ("input_hash", "input_hash_site"), ("input_hash_site.key", "atom:str"),
    ("input_hash_site.value", "input_array_site"), ("int/P", "atom:int"), ("int/R", "atom:int"), ("keys", "atom:str"),
    ("literal_d.key", "atom:str"), ("literal_d.value", "atom:int"), ("literal_e.key", "atom:str"), ("literal_e.value", "atom:nil"),
    ("merge_arg_d", "literal_d"), ("merge_arg_e", "literal_e"), ("merge_site_d.key", "atom:str"), ("merge_site_d.value", "array/map"),
    ("merge_site_d.value", "atom:int"), ("merge_site_d.value", "atom:nil"), ("merge_site_d.value", "hash/to_h"), ("merge_site_e.key", "atom:str"),
    ("merge_site_e.value", "array/map"), ("merge_site_e.value", "atom:int"), ("merge_site_e.value", "atom:nil"), ("merge_site_e.value", "hash/to_h"),
    ("merged_d", "merge_site_d"), ("merged_e", "merge_site_e"), ("nil", "atom:nil"), ("nil/P", "atom:nil"),
    ("nil/R", "atom:nil"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("outer_array", "outer_array_site"),
    ("outer_array_site.elem", "merge_site_e"), ("outer_hash", "outer_hash_site"), ("outer_hash_site.key", "atom:str"), ("outer_hash_site.value", "merge_site_d"),
    ("outer_hash_site.value", "outer_array_site"), ("outer_values", "merge_site_d"), ("outer_values", "outer_array_site"), ("str/P", "atom:str"),
    ("str/R", "atom:str"), ("tree", "hash/to_h"), ("two", "atom:int")]

/-- Case `f2_arg_head`: model.py's `BadUse` rows. -/
def c_f2_arg_head_bad : List (String × String) := []

/-- Case `f2_arg_head`: printed roots. -/
def c_f2_arg_head_roots : List (String × String) := [("inner", "inner"), ("tree", "tree")]

/-- Case `f2_arg_head_shared`: input relations. -/
def c_f2_arg_head_shared : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"input_array_site", "array", ["elem"]⟩,
    ⟨"input_hash_site", "hash", ["key", "value"]⟩,
    ⟨"literal_d", "hash", ["key", "value"]⟩,
    ⟨"literal_e", "hash", ["key", "value"]⟩,
    ⟨"merge_site_d", "hash", ["key", "value"]⟩,
    ⟨"merge_site_e", "hash", ["key", "value"]⟩,
    ⟨"outer_array_site", "array", ["elem"]⟩,
    ⟨"outer_hash_site", "hash", ["key", "value"]⟩,
    ⟨"shared/map", "array", ["elem"]⟩,
    ⟨"shared/to_h", "hash", ["key", "value"]⟩]
  alloc := [("keys", "atom:str"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("two", "atom:int"),
    ("nil", "atom:nil"), ("input_array", "input_array_site"), ("input_hash", "input_hash_site"), ("merge_arg_d", "literal_d"),
    ("merge_arg_e", "literal_e"), ("outer_array", "outer_array_site"), ("outer_hash", "outer_hash_site")]
  flow := [("hash/strkey", "shared/to_h.key"), ("hash/hash_block_ret", "shared/to_h.value"), ("hash/array_block_ret", "shared/map.elem"), ("array/strkey", "shared/to_h.key"),
    ("array/hash_block_ret", "shared/to_h.value"), ("array/array_block_ret", "shared/map.elem"), ("str/strkey", "shared/to_h.key"), ("str/hash_block_ret", "shared/to_h.value"),
    ("str/array_block_ret", "shared/map.elem"), ("int/strkey", "shared/to_h.key"), ("int/hash_block_ret", "shared/to_h.value"), ("int/array_block_ret", "shared/map.elem"),
    ("nil/strkey", "shared/to_h.key"), ("nil/hash_block_ret", "shared/to_h.value"), ("nil/array_block_ret", "shared/map.elem"), ("one_and_x", "input_array_site.elem"),
    ("keys", "input_hash_site.key"), ("input_array", "input_hash_site.value"), ("keys", "literal_d.key"), ("two", "literal_d.value"),
    ("keys", "literal_e.key"), ("nil", "literal_e.value"), ("merged_e", "outer_array_site.elem"), ("merged_d", "outer_values"),
    ("outer_array", "outer_values"), ("keys", "outer_hash_site.key"), ("outer_values", "outer_hash_site.value")]
  load := [("hash/hash_recv", "key", "hash/block_k"), ("hash/hash_recv", "value", "hash/block_v"), ("hash/array_recv", "elem", "hash/block_elem"), ("array/hash_recv", "key", "array/block_k"),
    ("array/hash_recv", "value", "array/block_v"), ("array/array_recv", "elem", "array/block_elem"), ("str/hash_recv", "key", "str/block_k"), ("str/hash_recv", "value", "str/block_v"),
    ("str/array_recv", "elem", "str/block_elem"), ("int/hash_recv", "key", "int/block_k"), ("int/hash_recv", "value", "int/block_v"), ("int/array_recv", "elem", "int/block_elem"),
    ("nil/hash_recv", "key", "nil/block_k"), ("nil/hash_recv", "value", "nil/block_v"), ("nil/array_recv", "elem", "nil/block_elem")]
  filter := [("hash/P", "hash", "hash/hash_recv"), ("hash/P", "array", "hash/array_recv"), ("hash/P", "str", "hash/R"), ("hash/P", "int", "hash/R"),
    ("hash/P", "nil", "hash/R"), ("array/P", "hash", "array/hash_recv"), ("array/P", "array", "array/array_recv"), ("array/P", "str", "array/R"),
    ("array/P", "int", "array/R"), ("array/P", "nil", "array/R"), ("str/P", "hash", "str/hash_recv"), ("str/P", "array", "str/array_recv"),
    ("str/P", "str", "str/R"), ("str/P", "int", "str/R"), ("str/P", "nil", "str/R"), ("int/P", "hash", "int/hash_recv"),
    ("int/P", "array", "int/array_recv"), ("int/P", "str", "int/R"), ("int/P", "int", "int/R"), ("int/P", "nil", "int/R"),
    ("nil/P", "hash", "nil/hash_recv"), ("nil/P", "array", "nil/array_recv"), ("nil/P", "str", "nil/R"), ("nil/P", "int", "nil/R"),
    ("nil/P", "nil", "nil/R")]
  produce := [("hash/P", "hash", "hash/R", "shared/to_h"), ("hash/P", "array", "hash/R", "shared/map"), ("array/P", "hash", "array/R", "shared/to_h"), ("array/P", "array", "array/R", "shared/map"),
    ("str/P", "hash", "str/R", "shared/to_h"), ("str/P", "array", "str/R", "shared/map"), ("int/P", "hash", "int/R", "shared/to_h"), ("int/P", "array", "int/R", "shared/map"),
    ("nil/P", "hash", "nil/R", "shared/to_h"), ("nil/P", "array", "nil/R", "shared/map")]
  toStr := [("hash/block_k", "hash/strkey"), ("array/block_k", "array/strkey"), ("str/block_k", "str/strkey"), ("int/block_k", "int/strkey"),
    ("nil/block_k", "nil/strkey")]
  invoke := [("hash_value_call", "hash/block_v", "hash/hash_block_ret"), ("array_value_call", "hash/block_elem", "hash/array_block_ret"), ("hash_value_call", "array/block_v", "array/hash_block_ret"), ("array_value_call", "array/block_elem", "array/array_block_ret"),
    ("hash_value_call", "str/block_v", "str/hash_block_ret"), ("array_value_call", "str/block_elem", "str/array_block_ret"), ("hash_value_call", "int/block_v", "int/hash_block_ret"), ("array_value_call", "int/block_elem", "int/array_block_ret"),
    ("hash_value_call", "nil/block_v", "nil/hash_block_ret"), ("array_value_call", "nil/block_elem", "nil/array_block_ret"), ("inner_call", "input_hash", "inner"), ("outer_call", "outer_hash", "tree")]
  select := [("inner_call", "hash", "hash"), ("inner_call", "array", "array"), ("inner_call", "str", "str"), ("inner_call", "int", "int"),
    ("inner_call", "nil", "nil"), ("outer_call", "hash", "hash"), ("outer_call", "array", "array"), ("outer_call", "str", "str"),
    ("outer_call", "int", "int"), ("outer_call", "nil", "nil"), ("hash_value_call", "hash", "hash"), ("hash_value_call", "array", "array"),
    ("hash_value_call", "str", "str"), ("hash_value_call", "int", "int"), ("hash_value_call", "nil", "nil"), ("array_value_call", "hash", "hash"),
    ("array_value_call", "array", "array"), ("array_value_call", "str", "str"), ("array_value_call", "int", "int"), ("array_value_call", "nil", "nil")]
  formal := [("hash", "hash/P"), ("array", "array/P"), ("str", "str/P"), ("int", "int/P"),
    ("nil", "nil/P")]
  ret := [("hash", "hash/R"), ("array", "array/R"), ("str", "str/R"), ("int", "int/R"),
    ("nil", "nil/R")]
  merge := [("inner", "merge_arg_d", "merged_d", "merge_site_d"), ("inner", "merge_arg_e", "merged_e", "merge_site_e")]
  use := [("merge_d", "inner", "merge"), ("merge_e", "inner", "merge")]
  unsupported := [("merge", "array"), ("merge", "str"), ("merge", "int"), ("merge", "nil")]

/-- Case `f2_arg_head_shared`: model.py's solved `Pt` rows. -/
def c_f2_arg_head_shared_pt : List (String × String) := [("array/P", "input_array_site"), ("array/P", "outer_array_site"), ("array/P", "shared/map"), ("array/R", "shared/map"),
    ("array/array_block_ret", "atom:int"), ("array/array_block_ret", "atom:str"), ("array/array_block_ret", "shared/to_h"), ("array/array_recv", "input_array_site"),
    ("array/array_recv", "outer_array_site"), ("array/array_recv", "shared/map"), ("array/block_elem", "atom:int"), ("array/block_elem", "atom:str"),
    ("array/block_elem", "merge_site_e"), ("array/block_elem", "shared/to_h"), ("hash/P", "input_hash_site"), ("hash/P", "merge_site_d"),
    ("hash/P", "merge_site_e"), ("hash/P", "outer_hash_site"), ("hash/P", "shared/to_h"), ("hash/R", "shared/to_h"),
    ("hash/block_k", "atom:str"), ("hash/block_v", "atom:int"), ("hash/block_v", "atom:nil"), ("hash/block_v", "input_array_site"),
    ("hash/block_v", "merge_site_d"), ("hash/block_v", "outer_array_site"), ("hash/block_v", "shared/map"), ("hash/block_v", "shared/to_h"),
    ("hash/hash_block_ret", "atom:int"), ("hash/hash_block_ret", "atom:nil"), ("hash/hash_block_ret", "shared/map"), ("hash/hash_block_ret", "shared/to_h"),
    ("hash/hash_recv", "input_hash_site"), ("hash/hash_recv", "merge_site_d"), ("hash/hash_recv", "merge_site_e"), ("hash/hash_recv", "outer_hash_site"),
    ("hash/hash_recv", "shared/to_h"), ("hash/strkey", "atom:str"), ("inner", "shared/to_h"), ("input_array", "input_array_site"),
    ("input_array_site.elem", "atom:int"), ("input_array_site.elem", "atom:str"), ("input_hash", "input_hash_site"), ("input_hash_site.key", "atom:str"),
    ("input_hash_site.value", "input_array_site"), ("int/P", "atom:int"), ("int/R", "atom:int"), ("keys", "atom:str"),
    ("literal_d.key", "atom:str"), ("literal_d.value", "atom:int"), ("literal_e.key", "atom:str"), ("literal_e.value", "atom:nil"),
    ("merge_arg_d", "literal_d"), ("merge_arg_e", "literal_e"), ("merge_site_d.key", "atom:str"), ("merge_site_d.value", "atom:int"),
    ("merge_site_d.value", "atom:nil"), ("merge_site_d.value", "shared/map"), ("merge_site_d.value", "shared/to_h"), ("merge_site_e.key", "atom:str"),
    ("merge_site_e.value", "atom:int"), ("merge_site_e.value", "atom:nil"), ("merge_site_e.value", "shared/map"), ("merge_site_e.value", "shared/to_h"),
    ("merged_d", "merge_site_d"), ("merged_e", "merge_site_e"), ("nil", "atom:nil"), ("nil/P", "atom:nil"),
    ("nil/R", "atom:nil"), ("one_and_x", "atom:int"), ("one_and_x", "atom:str"), ("outer_array", "outer_array_site"),
    ("outer_array_site.elem", "merge_site_e"), ("outer_hash", "outer_hash_site"), ("outer_hash_site.key", "atom:str"), ("outer_hash_site.value", "merge_site_d"),
    ("outer_hash_site.value", "outer_array_site"), ("outer_values", "merge_site_d"), ("outer_values", "outer_array_site"), ("shared/map.elem", "atom:int"),
    ("shared/map.elem", "atom:str"), ("shared/map.elem", "shared/to_h"), ("shared/to_h.key", "atom:str"), ("shared/to_h.value", "atom:int"),
    ("shared/to_h.value", "atom:nil"), ("shared/to_h.value", "shared/map"), ("shared/to_h.value", "shared/to_h"), ("str/P", "atom:str"),
    ("str/R", "atom:str"), ("tree", "shared/to_h"), ("two", "atom:int")]

/-- Case `f2_arg_head_shared`: model.py's `BadUse` rows. -/
def c_f2_arg_head_shared_bad : List (String × String) := []

/-- Case `f2_arg_head_shared`: printed roots. -/
def c_f2_arg_head_shared_roots : List (String × String) := [("inner", "inner"), ("tree", "tree")]

/-- Case `reembed`: input relations. -/
def c_reembed : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"inner", "record_b", ["b"]⟩,
    ⟨"outer", "record_a", ["a"]⟩]
  alloc := [("R", "atom:nil"), ("R", "outer"), ("inner_result", "inner")]
  flow := [("inner_result", "outer.a"), ("projection", "inner.b")]
  load := [("R", "a", "projection")]
  use := [("recursive_index", "R", "[]")]
  unsupported := [("[]", "nil")]

/-- Case `reembed`: model.py's solved `Pt` rows. -/
def c_reembed_pt : List (String × String) := [("R", "atom:nil"), ("R", "outer"), ("inner.b", "inner"), ("inner_result", "inner"),
    ("outer.a", "inner"), ("projection", "inner")]

/-- Case `reembed`: model.py's `BadUse` rows. -/
def c_reembed_bad : List (String × String) := [("recursive_index", "nil")]

/-- Case `reembed`: printed roots. -/
def c_reembed_roots : List (String × String) := [("b", "inner_result"), ("r", "R")]

/-- Case `reembed_safe`: input relations. -/
def c_reembed_safe : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"inner", "record_b", ["b"]⟩,
    ⟨"outer", "record_a", ["a"]⟩]
  alloc := [("R", "atom:nil"), ("R", "outer"), ("inner_result", "inner")]
  flow := [("inner_result", "outer.a"), ("projection", "inner.b")]
  load := [("R", "a", "projection")]
  filter := [("R", "nil", "projection")]

/-- Case `reembed_safe`: model.py's solved `Pt` rows. -/
def c_reembed_safe_pt : List (String × String) := [("R", "atom:nil"), ("R", "outer"), ("inner.b", "atom:nil"), ("inner.b", "inner"),
    ("inner_result", "inner"), ("outer.a", "inner"), ("projection", "atom:nil"), ("projection", "inner")]

/-- Case `reembed_safe`: model.py's `BadUse` rows. -/
def c_reembed_safe_bad : List (String × String) := []

/-- Case `reembed_safe`: printed roots. -/
def c_reembed_safe_roots : List (String × String) := [("b", "inner_result"), ("r", "R")]

/-- Case `acyclic_shared_site`: input relations. -/
def c_acyclic_shared_site : REDB where
  sites := [⟨"atom:float", "float", []⟩,
    ⟨"atom:int", "int", []⟩,
    ⟨"atom:model_u", "model_u", []⟩,
    ⟨"atom:model_var", "model_var", []⟩,
    ⟨"atom:nil", "nil", []⟩,
    ⟨"atom:str", "str", []⟩,
    ⟨"atom:sym", "sym", []⟩,
    ⟨"box", "array", ["elem"]⟩]
  alloc := [("i", "atom:int"), ("s", "atom:str"), ("first", "box"), ("second", "box")]
  flow := [("i", "box.elem"), ("s", "box.elem")]

/-- Case `acyclic_shared_site`: model.py's solved `Pt` rows. -/
def c_acyclic_shared_site_pt : List (String × String) := [("box.elem", "atom:int"), ("box.elem", "atom:str"), ("first", "box"), ("i", "atom:int"),
    ("s", "atom:str"), ("second", "box")]

/-- Case `acyclic_shared_site`: model.py's `BadUse` rows. -/
def c_acyclic_shared_site_bad : List (String × String) := []

/-- Case `acyclic_shared_site`: printed roots. -/
def c_acyclic_shared_site_roots : List (String × String) := [("first", "first"), ("second", "second")]

/-- Every case: name, inputs, expected `Pt`, expected `BadUse`, roots. -/
def all : List (String × REDB × List (String × String) × List (String × String) ×
    List (String × String)) := [
  ("self", c_self, c_self_pt, c_self_bad, c_self_roots),
  ("cycle2", c_cycle2, c_cycle2_pt, c_cycle2_bad, c_cycle2_roots),
  ("cycle3", c_cycle3, c_cycle3_pt, c_cycle3_bad, c_cycle3_roots),
  ("merge2", c_merge2, c_merge2_pt, c_merge2_bad, c_merge2_roots),
  ("param", c_param, c_param_pt, c_param_bad, c_param_roots),
  ("argument_tree", c_argument_tree, c_argument_tree_pt, c_argument_tree_bad, c_argument_tree_roots),
  ("chain64", c_chain64, c_chain64_pt, c_chain64_bad, c_chain64_roots),
  ("f2_mono", c_f2_mono, c_f2_mono_pt, c_f2_mono_bad, c_f2_mono_roots),
  ("f2_mono_shared", c_f2_mono_shared, c_f2_mono_shared_pt, c_f2_mono_shared_bad, c_f2_mono_shared_roots),
  ("f2_receiver_type", c_f2_receiver_type, c_f2_receiver_type_pt, c_f2_receiver_type_bad, c_f2_receiver_type_roots),
  ("f2_receiver_type_shared", c_f2_receiver_type_shared, c_f2_receiver_type_shared_pt, c_f2_receiver_type_shared_bad, c_f2_receiver_type_shared_roots),
  ("f2_call1", c_f2_call1, c_f2_call1_pt, c_f2_call1_bad, c_f2_call1_roots),
  ("f2_call1_shared", c_f2_call1_shared, c_f2_call1_shared_pt, c_f2_call1_shared_bad, c_f2_call1_shared_roots),
  ("f2_arg_head", c_f2_arg_head, c_f2_arg_head_pt, c_f2_arg_head_bad, c_f2_arg_head_roots),
  ("f2_arg_head_shared", c_f2_arg_head_shared, c_f2_arg_head_shared_pt, c_f2_arg_head_shared_bad, c_f2_arg_head_shared_roots),
  ("reembed", c_reembed, c_reembed_pt, c_reembed_bad, c_reembed_roots),
  ("reembed_safe", c_reembed_safe, c_reembed_safe_pt, c_reembed_safe_bad, c_reembed_safe_roots),
  ("acyclic_shared_site", c_acyclic_shared_site, c_acyclic_shared_site_pt, c_acyclic_shared_site_bad, c_acyclic_shared_site_roots)
]

end ProofLean.Cases
