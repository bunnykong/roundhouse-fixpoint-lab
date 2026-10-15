
#[test]
#[ignore = "provenance factorial protocol: lineage factorial; counts every counterexample"]
fn provenance_breaker_all_examples() {
    assert!(on(), "run with RH_PARAMETER_REASON_CONSERVE=1");
    let arm = (std::env::var("RH_PROVENANCE_PIDENT").expect("set RH_PROVENANCE_PIDENT"),
               std::env::var("RH_PROVENANCE_LIFT").expect("set RH_PROVENANCE_LIFT"));
    let st = |a: &Ty, b: &Ty| crate::wire_ty::storage_types(&[a.clone()], &[b.clone()]);
    let key = (ClassId(Symbol::from("LawOwner")), Symbol::from("call"), MethodReceiver::Instance);
    let fold = |obs: &[&Ty]| {
        let mut rows = HashMap::new();
        fold_param_observations(&mut rows, obs.iter().map(|t| (key.clone(), vec![(*t).clone()])).collect());
        rows[&key][0].clone()
    };
    let (ts, p) = (samples(), Ty::pending_untyped());
    let mut n: std::collections::BTreeMap<&str, u64> = Default::default();
    let mut ex: std::collections::BTreeMap<&str, Vec<String>> = Default::default();
    let mut bad = |law: &'static str, case: String| {
        *n.entry(law).or_default() += 1;
        let e = ex.entry(law).or_default();
        e.push(case);
    };
    for a in &ts {
        for b in &ts {
            let ab = unify_param_ty(a.clone(), b.clone());
            if !st(&ab, &unify_param_ty(b.clone(), a.clone())) { bad("comm", format!("{a:?} | {b:?}")) }
            if !st(&unify_param_ty(ab.clone(), a.clone()), &ab) { bad("idem", format!("{a:?} | {b:?}")) }
            if !st(&fold(&[a, b]), &fold(&[b, a])) { bad("fold2", format!("{a:?} | {b:?}")) }
            let want: BTreeSet<String> = evidence(&origins(a)).union(&evidence(&origins(b))).cloned().collect();
            if evidence(&origins(&ab)) != want { bad("evidence", format!("{a:?} | {b:?}")) }
            for c in &ts {
                let left = unify_param_ty(ab.clone(), c.clone());
                let right = unify_param_ty(a.clone(), unify_param_ty(b.clone(), c.clone()));
                if !st(&left, &right) { bad("assoc", format!("{a:?} | {b:?} | {c:?}")) }
                let f = fold(&[a, b, c]);
                if [[a, c, b], [b, a, c], [b, c, a], [c, a, b], [c, b, a]].iter().any(|o| !st(&f, &fold(o))) {
                    bad("fold3", format!("{a:?} | {b:?} | {c:?}"))
                }
            }
        }
    }
    for x in &ts {
        let want = if matches!(x, Ty::Bottom) { p.clone() } else { unify_param_ty(x.clone(), x.clone()) };
        if !st(&unify_param_ty(p.clone(), x.clone()), &want) { bad("pid", format!("{x:?}")) }
    }
    let seed_ok = st(&fold(&[&Ty::Bottom, &Ty::Int]), &fold(&[&Ty::Int, &Ty::Bottom]));
    let no_early_never = !matches!(fold(&[&Ty::Bottom]), Ty::Bottom);
    println!("provenance-BREAKER-ALL {}", json!({"arm": arm, "counts": n, "examples": ex,
        "seed_ok": seed_ok, "no_early_never": no_early_never}));
}

#[test]
#[ignore = "provenance factorial protocol: lineage factorial; counts every counterexample"]
fn provenance_breaker_debug_oracle() {
    assert!(on(), "run with RH_PARAMETER_REASON_CONSERVE=1");
    let arm = (std::env::var("RH_PROVENANCE_PIDENT").expect("set RH_PROVENANCE_PIDENT"),
               std::env::var("RH_PROVENANCE_LIFT").expect("set RH_PROVENANCE_LIFT"));
    let st = |a: &Ty, b: &Ty| format!("{a:?}") == format!("{b:?}");
    let key = (ClassId(Symbol::from("LawOwner")), Symbol::from("call"), MethodReceiver::Instance);
    let fold = |obs: &[&Ty]| {
        let mut rows = HashMap::new();
        fold_param_observations(&mut rows, obs.iter().map(|t| (key.clone(), vec![(*t).clone()])).collect());
        rows[&key][0].clone()
    };
    let (ts, p) = (samples(), Ty::pending_untyped());
    let mut n: std::collections::BTreeMap<&str, u64> = Default::default();
    let mut ex: std::collections::BTreeMap<&str, Vec<String>> = Default::default();
    let mut bad = |law: &'static str, case: String| {
        *n.entry(law).or_default() += 1;
        let e = ex.entry(law).or_default();
        if e.len() < 5 { e.push(case) }
    };
    for a in &ts {
        for b in &ts {
            let ab = unify_param_ty(a.clone(), b.clone());
            if !st(&ab, &unify_param_ty(b.clone(), a.clone())) { bad("comm", format!("{a:?} | {b:?}")) }
            if !st(&unify_param_ty(ab.clone(), a.clone()), &ab) { bad("idem", format!("{a:?} | {b:?}")) }
            if !st(&fold(&[a, b]), &fold(&[b, a])) { bad("fold2", format!("{a:?} | {b:?}")) }
            let want: BTreeSet<String> = evidence(&origins(a)).union(&evidence(&origins(b))).cloned().collect();
            if evidence(&origins(&ab)) != want { bad("evidence", format!("{a:?} | {b:?}")) }
            for c in &ts {
                let left = unify_param_ty(ab.clone(), c.clone());
                let right = unify_param_ty(a.clone(), unify_param_ty(b.clone(), c.clone()));
                if !st(&left, &right) { bad("assoc", format!("{a:?} | {b:?} | {c:?}")) }
                let f = fold(&[a, b, c]);
                if [[a, c, b], [b, a, c], [b, c, a], [c, a, b], [c, b, a]].iter().any(|o| !st(&f, &fold(o))) {
                    bad("fold3", format!("{a:?} | {b:?} | {c:?}"))
                }
            }
        }
    }
    for x in &ts {
        let want = if matches!(x, Ty::Bottom) { p.clone() } else { unify_param_ty(x.clone(), x.clone()) };
        if !st(&unify_param_ty(p.clone(), x.clone()), &want) { bad("pid", format!("{x:?}")) }
    }
    let seed_ok = st(&fold(&[&Ty::Bottom, &Ty::Int]), &fold(&[&Ty::Int, &Ty::Bottom]));
    let no_early_never = !matches!(fold(&[&Ty::Bottom]), Ty::Bottom);
    println!("provenance-BREAKER-DEBUG {}", json!({"arm": arm, "counts": n, "examples": ex,
        "seed_ok": seed_ok, "no_early_never": no_early_never}));
}
