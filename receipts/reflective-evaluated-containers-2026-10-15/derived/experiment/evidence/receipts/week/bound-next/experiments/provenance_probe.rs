//! Read-only characterization of the pinned analyzer; not a semantic repair.
use super::*;
use crate::ty::Provenance;
use serde_json::{json, Value};

fn describe(t: &Ty) -> Value {
    json!({"debug": format!("{t:?}"), "wire": serde_json::to_value(t).unwrap()})
}

#[test]
fn producer_reason_provenance_observe() {
    let p = Ty::pending_untyped();
    let g = Ty::gradual();
    let u = Ty::unresolved();
    let classes = HashMap::new();
    let typer = BodyTyper::new(&classes);
    let ghost = Ty::Class { id: ClassId(Symbol::from("EvidenceExternal")), args: vec![].into() };
    let miss = typer.dispatch(Some(&ghost), &Symbol::from("producer_reason_unmodeled"), None, &[]);
    let pg = union_of(p.clone(), g.clone());
    let gp = union_of(g.clone(), p.clone());
    let roundtrip: Ty = serde_json::from_value(serde_json::to_value(&u).unwrap()).unwrap();
    let (guard_true, guard_false) = narrowing::head_split(&u, &Ty::Str);
    println!("producer_reason: {}", json!({
        "condition": "producer_reason-provenance-38403140-characterization-v1",
        "fold": std::env::var("RH_FOLD").ok(),
        "union_pending_gradual": describe(&pg),
        "union_gradual_pending": describe(&gp),
        "ordinary_equality_of_reordered_joins": pg == gp,
        "storage_equality_of_reordered_joins": crate::wire_ty::storage_types(
            std::slice::from_ref(&pg), std::slice::from_ref(&gp)),
        "parameter_int_gradual": describe(&super::super::unify_param_ty(Ty::Int, g)),
        "ivar_nil_tagged_pending": describe(&join_ivar_slot(Ty::Nil, p)),
        "missing_dispatch": describe(&miss),
        "ivar_nil_missing_dispatch": describe(&join_ivar_slot(Ty::Nil, miss)),
        "unresolved_json_roundtrip": describe(&roundtrip),
        "string_guard_true": describe(&guard_true),
        "string_guard_false": describe(&guard_false)
    }));
}

/// Proposed conservation gate: run explicitly, and expect failure on the pin.
/// It is a design requirement, not an existing Roundhouse guarantee.
#[test]
#[ignore = "proposed provenance contract; deliberately fails on 38403140"]
fn producer_reason_provenance_contract() {
    for (a, b) in [(Ty::pending_untyped(), Ty::gradual()), (Ty::unresolved(), Ty::gradual())] {
        for (left, right) in [(a.clone(), b.clone()), (b, a)] {
            assert_eq!(union_of(left, right).provenance(), Some(Provenance::Gradual),
                       "merging unknown tags must retain the gradual possibility");
        }
    }
    // This is only the scalar policy minimum. A reason-set prototype must add
    // assertions for all input origins; this test alone cannot certify that.
    // Ordinary serialized type output must stay unchanged in this first trial.
    for (a, b, c) in [
        (Ty::pending_untyped(), Ty::unresolved(), Ty::gradual()),
        (Ty::gradual(), Ty::pending_untyped(), Ty::unresolved()),
        (Ty::unresolved(), Ty::gradual(), Ty::pending_untyped()),
    ] {
        let left = union_of(union_of(a.clone(), b.clone()), c.clone());
        let right = union_of(a, union_of(b, c));
        assert_eq!(left.provenance(), Some(Provenance::Gradual));
        assert_eq!(right.provenance(), Some(Provenance::Gradual));
        assert_eq!(serde_json::to_value(left).unwrap(), serde_json::to_value(Ty::gradual()).unwrap());
    }
}

#[test]
#[ignore = "proposed producer distinction; deliberately fails on 38403140"]
fn producer_reason_pending_contract() {
    let classes = HashMap::new();
    let typer = BodyTyper::new(&classes);
    let ghost = Ty::Class { id: ClassId(Symbol::from("EvidenceExternal")), args: vec![].into() };
    let miss = typer.dispatch(Some(&ghost), &Symbol::from("producer_reason_unmodeled"), None, &[]);
    assert_eq!(miss.provenance(), Some(Provenance::Unresolved),
               "a missing external method is not an unevaluated slot");
    assert_ne!(join_ivar_slot(Ty::Nil, miss), Ty::Nil,
               "a modeling gap must not certify nil-only");
    assert_eq!(join_ivar_slot(Ty::Nil, Ty::pending_untyped()), Ty::Nil,
               "a verified pending seed contributes no value evidence");
}

#[test]
#[ignore = "proposed positive guard bound; deliberately fails on 38403140"]
fn producer_reason_guard_contract() {
    // This asserts the type projection of the true branch. A provenance-aware
    // implementation must retain its origin separately, not erase the cause.
    for unknown in [Ty::gradual(), Ty::unresolved()] {
        let receiver = union_of(Ty::Int, unknown);
        let (yes, no) = narrowing::head_split(&receiver, &Ty::Str);
        assert_eq!(yes, Ty::Str, "a successful String test bounds this occurrence");
        assert!(no.mentions_unknown(), "the negative branch still admits other unknown values");
        assert!(receiver.mentions_unknown(), "branch refinement must not mutate the carried slot");
    }
}
