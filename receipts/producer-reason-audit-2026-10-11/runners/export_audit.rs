// Extra observational output for the lab's selected-type exporter.
fn producer_reason_audit(t: Option<&Ty>) -> serde_json::Value {
    fn walk(t: &Ty, tags: &mut std::collections::BTreeSet<String>, unsupported: &mut bool) {
        match t {
            Ty::Untyped { why } => { for reason in why.reasons() { tags.insert(reason.to_owned()); } }
            Ty::Var { .. } => { tags.insert("Var".into()); }
            Ty::Array { elem } => walk(elem, tags, unsupported),
            Ty::Hash { key, value } => { walk(key, tags, unsupported); walk(value, tags, unsupported); }
            Ty::Tuple { elems } | Ty::Union { variants: elems } => {
                for e in elems { walk(e, tags, unsupported); }
            }
            Ty::Record { row } => {
                for e in row.fields.values() { walk(e, tags, unsupported); }
                if row.rest.is_some() { *unsupported = true; }
            }
            Ty::Fn { ret, .. } => walk(ret, tags, unsupported),
            Ty::Int | Ty::Float | Ty::Bool | Ty::Str | Ty::Sym | Ty::Nil | Ty::Bottom => {}
            _ => { *unsupported = true; }
        }
    }
    let mut tags = std::collections::BTreeSet::new();
    let mut unsupported = false;
    if let Some(t) = t { walk(t, &mut tags, &mut unsupported); }
    serde_json::json!({
        "present": t.is_some(), "tags": tags,
        "origins": t.map(roundhouse::analyze::producer_evidence::origins), "unsupported_by_exporter": unsupported,
        "debug": t.map(|t| format!("{t:?}"))
    })
}
