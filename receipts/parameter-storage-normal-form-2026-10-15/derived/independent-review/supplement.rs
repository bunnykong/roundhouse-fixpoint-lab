
#[test]
#[ignore = "breaker: independent debug equality and split fold on the registered 36 samples"]
fn rv_normalized-composition_debug_and_split_fold() {
    assert!(on());
    assert!(super::norm_on());
    let ts = storage_samples();
    assert_eq!(ts.len(), 36);
    let fp = |t: &Ty| format!("{t:?}");
    let key = (ClassId(Symbol::from("RvOwner")), Symbol::from("call"), MethodReceiver::Instance);
    let batch = |obs: &[&Ty]| {
        let mut rows = HashMap::new();
        fold_param_observations(&mut rows, obs.iter().map(|t| (key.clone(), vec![(*t).clone()])).collect());
        rows[&key][0].clone()
    };
    let mut counts: std::collections::BTreeMap<&str, u64> = Default::default();
    let mut examples: std::collections::BTreeMap<&str, String> = Default::default();
    let mut bad = |law: &'static str, ids: &[usize]| {
        *counts.entry(law).or_default() += 1;
        examples.entry(law).or_insert_with(|| format!("{ids:?}"));
    };
    for (i, a) in ts.iter().enumerate() {
        let na = super::normalize(a.clone());
        if fp(&super::normalize(na.clone())) != fp(&na) { bad("n_idem", &[i]); }
        for (j, b) in ts.iter().enumerate() {
            let ab = unify_param_ty(a.clone(), b.clone());
            let ab_fp = fp(&ab);
            let ba = unify_param_ty(b.clone(), a.clone());
            if ab_fp != fp(&ba) { bad("comm", &[i,j]); }
            if ab_fp != fp(&super::normalize(ab.clone())) { bad("join_not_normal", &[i,j]); }
            if ab_fp != fp(&unify_param_ty(ab.clone(), ab.clone())) { bad("output_idem", &[i,j]); }
            if ab_fp != fp(&unify_param_ty(ab.clone(), a.clone())) { bad("replay", &[i,j]); }
            if ab_fp != fp(&ba) && crate::wire_ty::storage_types(&[ab.clone()], &[ba]) {
                bad("storage_equality_masks_difference", &[i,j]);
            }
            for (k, c) in ts.iter().enumerate() {
                let left = unify_param_ty(ab.clone(), c.clone());
                let right = unify_param_ty(a.clone(), unify_param_ty(b.clone(), c.clone()));
                if fp(&left) != fp(&right) { bad("assoc", &[i,j,k]); }
                let batched = batch(&[a,b,c]);
                let separate = storage_fold(&[a.clone(),b.clone(),c.clone()]);
                if fp(&batched) != fp(&separate) { bad("batch_split", &[i,j,k]); }
                if fp(&batched) != fp(&super::normalize(batched.clone())) { bad("stored_not_normal", &[i,j,k]); }
                if fp(&batched) != fp(&batch(&[c,b,a])) { bad("reverse_fold", &[i,j,k]); }
            }
        }
    }
    println!("RV-protocol-DEBUG {}", json!({"samples":ts.len(),"pairs":ts.len().pow(2),
        "triples":ts.len().pow(3),"audit":audit::on(),"counts":counts,"examples":examples}));
    assert!(counts.is_empty(), "independent observer or split fold found counterexamples: {counts:?}");
}
