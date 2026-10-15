
#[test]
#[ignore = "breaker: reproduce the recorded nested-union coverage failure"]
fn residual_witness_nested_union_loss() {
    use crate::analyze::absorption_residual;
    assert!(!on() && audit::on() && absorption_residual::on());
    audit::reset(&[]);
    let key = (ClassId(Symbol::from("BreakerNestedUnion")), Symbol::from("call"), MethodReceiver::Instance);
    let stored = Ty::Var { var: TyVar(0) };
    let observed = Ty::Union { variants: vec![
        Ty::Union { variants: vec![Ty::Str, Ty::Var { var: TyVar(0) }, Ty::unresolved()].into() },
        Ty::Nil,
    ].into() };
    let result = {
        let _context = audit::parameter_context(&key, 1, "join");
        unify_param_ty(stored.clone(), observed.clone())
    };
    let expected = Ty::Union { variants: vec![Ty::Str, Ty::Nil].into() };
    assert!(crate::wire_ty::storage_types(&[result.clone()], &[expected]));
    assert!(origins(&observed).contains("$:Unresolved"));
    assert!(!origins(&result).contains("$:Unresolved"));
    assert_eq!(absorption_residual::hidden(&stored, &observed, &result, false), 0);
    let report = absorption_residual::report(true);
    assert_eq!(report["map"]["BreakerNestedUnion|call|Instance|param=1"].as_u64().unwrap_or(0) & 4, 0);
    let ledger = audit::snapshot();
    assert!(ledger["parameter_native_events"].as_array().unwrap().iter().any(|e|
        e["destination"] == "BreakerNestedUnion|call|Instance|param=1" &&
        e["lost_kinds"].as_array().unwrap().contains(&json!("Unresolved"))));

    let flat = Ty::Union { variants: vec![Ty::Str, Ty::Var { var: TyVar(0) }, Ty::unresolved(), Ty::Nil].into() };
    let flat_result = unify_param_ty(stored.clone(), flat.clone());
    assert!(crate::wire_ty::storage_types(&[result.clone()], &[flat_result.clone()]));
    assert_eq!(absorption_residual::hidden(&stored, &flat, &flat_result, false) & 4, 4);
    println!("RESIDUAL-WITNESS-NESTED {}", json!({
        "stored":format!("{stored:?}"), "observed":format!("{observed:?}"),
        "output":format!("{result:?}"), "input_origins":origins(&observed),
        "output_origins":origins(&result), "hidden_nested":0,
        "hidden_flat":absorption_residual::hidden(&stored, &flat, &flat_result, false),
        "same_visible_output":true, "ledger":ledger,
    }));
}

#[test]
#[ignore = "breaker: isolate cumulative residual order dependence on registered Var and Int samples"]
fn residual_witness_row_residual_order() {
    use crate::analyze::absorption_residual;
    assert!(!on() && audit::on() && absorption_residual::on());
    audit::reset(&[]);
    let fold = |owner: &str, contributions: Vec<Ty>| {
        let key = (ClassId(Symbol::from(owner)), Symbol::from("call"), MethodReceiver::Instance);
        let mut rows = HashMap::new();
        fold_param_observations(&mut rows, contributions.into_iter().map(|t| (key.clone(), vec![t])).collect());
        rows[&key][0].clone()
    };
    let first = fold("BreakerVarFirst", vec![Ty::Var { var: TyVar(0) }, Ty::Int]);
    let last = fold("BreakerVarLast", vec![Ty::Int, Ty::Var { var: TyVar(0) }]);
    assert!(crate::wire_ty::storage_types(&[first.clone()], &[last.clone()]));
    assert_eq!(first, Ty::Int);
    let map = absorption_residual::report(true)["map"].clone();
    let first_bits = map["BreakerVarFirst|call|Instance|param=0"].as_u64().unwrap_or(0);
    let last_bits = map["BreakerVarLast|call|Instance|param=0"].as_u64().unwrap_or(0);
    assert_eq!(first_bits, 0);
    assert_eq!(last_bits, 8);
    println!("RESIDUAL-WITNESS-ROW {}", json!({"var_first_visible":format!("{first:?}"),
        "var_last_visible":format!("{last:?}"), "var_first_residual":first_bits,
        "var_last_residual":last_bits, "same_storage":true,
        "scope":"supplementary production-hook counterexample, not the abstract cell-law harness"}));
}
