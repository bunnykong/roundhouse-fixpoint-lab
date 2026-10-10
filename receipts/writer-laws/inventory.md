# Carried-slot writer inventory


`+` means pass, `-` means fail. Result vectors spell out every property; an ignored test's passing properties are still measured in the generated run.

- **B:** C, G, I, L, R, D, P = commutativity, regrouping/associativity, idempotence, pending-left, pending-right, duplicate replay, permutation.
- **T:** I, E, G, P, M = repeated-transfer idempotence, pending preservation, join preservation, union-arm permutation, monotonicity.
- **U:** I, E, W = bound idempotence, pending preservation, identity within the limits.
- **S:** once/pair, P-once, G-pair = one cut versus pairwise cuts, permutation with one cut, regrouping with pairwise cuts.
- **Q:** P+D = actual batch writer versus one cut after all contributions, with permutation and replay.
- **F:** bounded = actual reflective storage versus the bounded incoming type.

| Slot | Writer | Operation | Laws |
|---|---|---|---|
| ivar | W01 `join_ivar_slot` | normalized join | `B:+++++++` |
| ivar | W02 `extract_ivar_assignments: plain` | join; batch cut | `B:+++++++` |
| ivar Hash value | W03 `widen_hash_ivar_value` | spine join | `B:+++++++` |
| reflective ivar | W04 `harvest_ivar_set` | join; open gate | `B:+++++++` |
| reflective ivar | W05 `narrow_to_named_model` | model projection | `T:++-+-` |
| parameter | W06 `unify_param_ty` | normalized join | `B:+++++++` |
| parameter row | W07 `fold_param_observations` | join; batch cut | `B:+++++++` |
| parameter seed | W08 `param_ty_with_default` | join default | `B:+++++++` |
| method return | W09 `decide_harvested_return` | replace; stabilize; untie | `B:--+++--` |
| method return | W10 `insert_inferred_return` | cut new; return policy | `B:--+++--` |
| method return | W11 `register_method_return` | unknown fallback; return policy | `B:-------` |
| method return | W12 `fold_concern_surfaces` | ordered copy | `B:-+++---` |
| class return | W13 `fold_extended_modules` | ordered copy | `B:-+++---` |
| class return | W14 `fold_current_attribute_forwarders` | replace from instance | `B:-+++---` |
| view helper | W15 `harvest_returns_to_registry: helper` | first owner | `B:-++-++-` |
| module return | W16 `fold_host_surfaces` | known-host agreement | `B:++---++` |
| constant | W17 `record_const` | last write | `B:-+++---` |
| several maps | W18 `union_of` | raw union | `B:+++--++` |
| controller ivar | W19 `union_ivar_maps` | raw union | `B:+++--++` |
| filter ivar | W20 `merge_alternative_branches` | union; absent = Nil | `B:+++--++` |
| Current attribute | W21 `collect_const_attr_writes` | open gate; union | `T:+++++` |
| controller seed | W22 `is_clean_binding` | clean gate | `T:++-+-` |
| class attribute | W23 `is_uninformative` | evidence gate | `T:++-++` |
| layout ivar | W24 `type_views_and_tests: layout` | noise selection; union | `B:-+++---` |
| partial ivar | W25 `type_views_and_tests: partial` | noise selection; union | `B:-++-++-` |
| partial local | W26 `extract_partial_render_sites` | last write | `B:-+++---` |
| assignment target | W27 `multiassign_target_ty: position 0` | shape projection | `T:++-+-` |
| local and ivar | W28 `apply_narrowing: non-nil` | remove_nil | `T:++-+-` |
| local and ivar | W29 `apply_narrowing: nil` | intersect Nil | `T:+-+++` |
| local and ivar | W30 `apply_narrowing: is_a Int` | intersection | `T:+-+++` |
| local and ivar | W31 `apply_narrowing: not Int` | exclusion | `T:++-+-` |
| local and ivar | W32 `apply_narrowing: is_a Array` | intersection | `T:+--+-` |
| local and ivar | W33 `apply_narrowing: is_a Hash` | intersection | `T:+--+-` |
| local and ivar | W34 `apply_narrowing: not Array` | exclusion | `T:++-+-` |
| local and ivar | W35 `apply_narrowing: not Hash` | exclusion | `T:++-+-` |
| reader local | W36 `narrow_binding: Reader` | conditional shadow | `T:++-+-` |
| closure params | W37 `block_ctx_for: each` | receiver projection | `T:++---` |
| closure params | W38 `block_ctx_for: each_with_index` | receiver projection | `T:++---` |
| closure params | W39 `block_ctx_for: then` | receiver projection | `T:++-+-` |
| closure Array | W40 `collect_array_pushes` | open gate; collect | `T:+++++` |
| closure Hash | W41 `collect_hash_index_writes` | open gate; collect | `T:+++++` |
| closure local | W42 `collect_local_assignment_tys` | open gate; collect | `T:+++++` |
| condition local | W43 `collect_var_assignments_into` | last write | `B:-+++---` |
| pattern local | W44 `propagate_match_bindings: required` | replace | `B:-+++---` |
| pattern local | W45 `propagate_match_bindings: conditional` | raw union | `B:+++--++` |
| IR type | W46 `BodyTyper::analyze_expr` | recompute; overwrite | `B:-+++---` |
| IR empty Array | W47 `propagate_expected_to_empty_container` | overwrite; read back | `B:-++++--` |
| IR empty Hash | W48 `propagate_expected_to_empty_container` | overwrite; read back | `B:-++++--` |
| IR class Hash | W49 `seed_empty_hashes` | overwrite | `B:-+++---` |
| carried Ty | W50 `fixpoint_bound::bound` | size/depth widening | `U:+++` |
| bounded ivar | W51 `bound after join_ivar_slot` | once vs each pair | `S:-+-` |
| bounded param | W52 `bound after unify_param_ty` | once vs each pair | `S:-+-` |
| bounded ivar | W53 `extract_ivar_assignments: batch` | join all; one cut | `Q:+` |
| bounded row | W54 `fold_param_observations: batch` | join all; one cut | `Q:+` |
| reflective ivar | W55 `harvest_ivar_set: bound coverage` | storage vs bound | `F:-` |

The following inventory expands the wrappers and snapshot paths. It identifies where the policy is used; these composition paths are not counted as additional independent generated passes.

| Slot | Writer path | Operation | Coverage |
|---|---|---|---|
| registry seeds | C01 | source/catalog insert; own priority | bootstrap; not a round join |
| model attributes | C02 | schema row replacement | immutable source seed |
| model methods | C03 | source insert or first write | bootstrap priority; not independently measured |
| method returns | C04 | return policy; relation-tail specialization; unknown/open gates | W09-W11; caller selectors not generated |
| constant values | C05 | DeclarationId overwrite; rebuild snapshot; ambiguous bare name removal | W17 overwrite kind; ID/ambiguity composition not measured |
| constant scopes | C06 | record_const; own-name overlay | W17; scope resolution not generated |
| parameter rows | C07 | rebuild or clone; fold observations; batch bound | W06-W08, W52, W54; routing selectors not generated |
| parameter seeds | C08 | declared priority; default join; position replacement | W06-W08, W37-W39; declaration/arity catalog not exhausted |
| ivar harvest | C09 | join; destructure; raw index collection; Hash widening; touched-slot bound | W01-W05, W27, W53, W55 |
| filter ivars | C10 | union; branch Nil; ordered filter overlay; first-write fallback | W18-W20; overlay is W17/W15 policy kind |
| controller state | C11 | cache snapshot replace; own overlay; open gate; union; strip_nil; clean-gated overwrite | W18, W19, W22, W28; dirty/cache composition not measured |
| Current types | C12 | contribution gate and union; return publication; copy | W21, W09-W11, W14 |
| view seeds | C13 | noise-select union; open gate; first/last overlay; snapshot replace | W18, W24-W26; snapshot/rebuild not independently generated |
| mailer params | C14 | bare-Var gate; raw union by field; view overlay | W18 raw union kind; full mailer path not generated |
| partial state | C15 | depth-capped noise-select union; last local write; shape projection | W25, W26; edge discovery and depth cap not proved |
| local/ivar flow | C16 | replace; raw union; projection; branch transfer | W18, W27-W49; whole compute operator matrix not exhausted |
| closure refinements | C17 | open-gated collection; raw union; seed refinement; retro-stamp | W40-W43; complete outer-scope/refinement composition not measured |
| IR type stamps | C18 | compute overwrite; parameter-value override; empty literal readback; retro-stamp | W46-W49; node kinds not exhausted |
| method signatures | C19 | replace configuration Fn; post-fixpoint fill-only signature | overwrite/first-owner kinds W46/W15; signature composition not generated |
| block verdicts | C20 | clear/rebuild name sets | non-Ty metadata; no Var identity |
| relation verdicts | C21 | insert relation_derived/materializing_scopes names | non-Ty metadata; not independently generated |
| copy markers | C22 | record copied names; remove/rebuild host loans | W12/W13/W16 value policies; marker identity not proved |
| IR metadata | C23 | recompute decisions, diagnostics and effects | non-Ty payloads; outside this lattice universe |

Composition writer paths (C numbers refer to the preceding table):

- C01, registry seeds: `Analyzer::with_adapter; registry::{ar,stdlib,library,view,gem_boundary}::register; data::register; test_module::register`.
- C02, model attributes: `Analyzer::with_adapter`.
- C03, model methods: `register_has_secure_password; register_generates_token_for; register_has_rich_text; register_plain_text_attr; register_attr_accessors; register_ar_attributes; register_has_json; register_serialized_columns; register_typed_store`.
- C04, method returns: `harvest_one_model; harvest_method_returns; class_configuration::analyze_class_configuration`.
- C05, constant values: `build_constant_registry; run_typing_passes; test_module::type_tests_only`.
- C06, constant scopes: `extract_const_assignments; extract_controller_const_assignments; ConstScope::with_own; type_test_modules`.
- C07, parameter rows: `unify_params_from_call_sites; apply_param_sites; fold_concern_param_sites; unify_test_params_onto; overlay_test_params`.
- C08, parameter seeds: `seed_method_params; seed_action_params; type_direct_helper_bodies; block_ctx_for; compute Lambda`.
- C09, ivar harvest: `extract_ivar_assignments_in; walk_ivar_assignments: Assign, OpAssign, MultiAssign, Send, []=`.
- C10, filter ivars: `collect_transitive_filter_ivars; union_ivar_maps; merge_alternative_branches; merged_before_seed; bind_framework_assigned_ivars`.
- C11, controller state: `type_production_bodies: Phase A cache, ancestor layer, two seed sweeps, Phase B refinements`.
- C12, Current types: `collect_const_attr_writes; harvest_method_returns; fold_current_attribute_forwarders`.
- C13, view seeds: `type_production_bodies: action, layout, content partial, inherited action, mailer; view_seeds assignment`.
- C14, mailer params: `harvest_mailer_with_params; type_production_bodies mailer views`.
- C15, partial state: `type_views_and_tests; extract_partial_render_sites; render::interpret_render_call`.
- C16, local/ivar flow: `BodyTyper::compute: Seq, assignments, OpAssign, MultiAssign, If, Case, rescue, Lambda; collect_var_assignments_into; propagate_match_bindings; apply_narrowing`.
- C17, closure refinements: `compute Seq; collect_array_pushes; collect_hash_index_writes; collect_local_assignment_tys`.
- C18, IR type stamps: `BodyTyper::analyze_expr; compute Send/Seq; propagate_expected_to_empty_container; seed_empty_hashes`.
- C19, method signatures: `analyze_class_configuration; stamp_inferred_method_signatures`.
- C20, block verdicts: `harvest_block_value_methods`.
- C21, relation verdicts: `with_adapter; harvest_one_model`.
- C22, copy markers: `fold_concern_surfaces; fold_extended_modules; fold_host_surfaces`.
- C23, IR metadata: `BodyTyper::analyze_expr; Analyzer::collect_effects; Analyzer::analyze include-diagnostic block; diagnostics::diagnose`.

Carried state is defined by `src/analyze/fixpoint_check.rs:24`: method returns, constants, attribute rows, block/relation verdicts, parameter rows, refined controller bindings, controller caches, view seeds, copy markers, and typed IR. Source-only seeds are listed because they initialize those slots. Temporary Ctx and render maps are listed where they feed carried IR or the next round's channel.

The main wrapper paths are in `src/analyze/mod.rs:1823` (constants), `src/analyze/mod.rs:2012` (production/controller channel), `src/analyze/mod.rs:3776` (views), `src/analyze/mod.rs:4491` (return harvest), `src/analyze/mod.rs:5229` (parameters), and `src/analyze/mod.rs:7845` (ivar harvest). Transfer and stamp paths are in `src/analyze/body/mod.rs:430`, `src/analyze/body/narrowing.rs:286`, `src/analyze/body/send.rs:339`, `src/analyze/render.rs:42`, and `src/analyze/class_configuration.rs:16`. The tests live in the corresponding `writer_law_tests` modules and `src/analyze/writer_laws.rs:1`.
