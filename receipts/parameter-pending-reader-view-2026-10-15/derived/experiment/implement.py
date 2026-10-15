from pathlib import Path
import re
D = Path(__file__).resolve().parent
C = D / 'week/evidence/sources/probe-source'

def edit(relative, old, new):
    p = C / relative
    text = p.read_text()
    assert text.count(old) == 1, (relative, text.count(old), old)
    p.write_text(text.replace(old, new))

edit('src/analyze/parameter_conservation.rs',
'''/// provenance L2: an `untyped` whose only reason is Pending is the identity beside any other arm.''',
'''fn pident() -> bool {
    static ON: OnceLock<bool> = OnceLock::new();
    *ON.get_or_init(|| std::env::var("RH_PROVENANCE_PIDENT").as_deref() != Ok("0"))
}

/// provenance L2: an `untyped` whose only reason is Pending is the identity beside any other arm.''')
edit('src/analyze/parameter_conservation.rs',
'''    join(Ty::pending_untyped(), observed)
}''',
'''    if pident() {
        join(Ty::pending_untyped(), observed)
    } else if matches!(observed, Ty::Bottom) {
        Ty::pending_untyped()
    } else {
        observed
    }
}''')
edit('src/analyze/parameter_conservation.rs',
'''    if variants.iter().any(|t| !pending_only(t)) {''',
'''    if pident() && variants.iter().any(|t| !pending_only(t)) {''')
edit('src/ty.rs',
'''    pub fn union(self, other: Self) -> Self { Self(self.0 | other.0) }''',
'''    pub fn union(self, other: Self) -> Self {
        static LIFT: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
        let b = self.0 | other.0;
        let lift = *LIFT.get_or_init(|| std::env::var("RH_PROVENANCE_LIFT").as_deref() == Ok("1"));
        Self(if lift && b & 6 != 0 { b & !1 } else { b })
    }''')
edit('src/analyze/mod.rs',
'''    pub fn inferred_param_types(&self, class: &ClassId, method: &Symbol) -> Option<&[Ty]> {
        self.params_row(class, method).map(|v| v.as_slice())
    }

    // Instance side first: a caller asking by name alone reads the `def` an instance runs, as it did before rows were keyed by side.
    fn params_row(&self, class: &ClassId, method: &Symbol) -> Option<&Vec<Ty>> {
        [MethodReceiver::Instance, MethodReceiver::Class]
            .into_iter()
            .find_map(|side| self.inferred_params.get(&(class.clone(), method.clone(), side)))
    }''',
'''    pub fn inferred_param_types(&self, class: &ClassId, method: &Symbol) -> Option<std::borrow::Cow<'_, [Ty]>> {
        self.params_row(class, method)
    }

    // Instance side first: a caller asking by name alone reads the `def` an instance runs, as it did before rows were keyed by side.
    fn params_row(&self, class: &ClassId, method: &Symbol) -> Option<std::borrow::Cow<'_, [Ty]>> {
        [MethodReceiver::Instance, MethodReceiver::Class]
            .into_iter()
            .find_map(|side| self.inferred_params.get(&(class.clone(), method.clone(), side)))
            .map(|row| provenance_reader_row(row))
    }''')
edit('src/analyze/mod.rs',
'''self.params_row(c, m)?.clone()''',
'''self.params_row(c, m)?.into_owned()''')
edit('src/analyze/mod.rs',
'''                let inferred = self.inferred_params.get(&key);''',
'''                let inferred = self.inferred_params.get(&key).map(|row| provenance_reader_row(row));''')
edit('src/analyze/mod.rs',
'''                let has_params = inferred
                    .is_some_and''',
'''                let has_params = inferred.as_ref()
                    .is_some_and''')
edit('src/analyze/mod.rs',
'''param_ty_with_default(inferred.and_then(|v| v.get(i)).cloned(), p)''',
'''param_ty_with_default(inferred.as_ref().and_then(|v| v.get(i)).cloned(), p)''')
edit('src/analyze/mod.rs',
'''        let observed = self.inferred_params.get(&key);''',
'''        let observed = self.inferred_params.get(&key).map(|row| provenance_reader_row(row));''')
edit('src/analyze/mod.rs',
'''let from_sites = observed.and_then(|v| v.get(i)).cloned();''',
'''let from_sites = observed.as_ref().and_then(|v| v.get(i)).cloned();''')
edit('src/analyze/mod.rs',
'''        let own = self.inferred_params.get(&(class_id.clone(), action_name.clone(), MethodReceiver::Instance));
        let from_origin = origin
            .and_then(|m| self.inferred_params.get(&(m.clone(), action_name.clone(), MethodReceiver::Instance)));''',
'''        let own = self.inferred_params.get(&(class_id.clone(), action_name.clone(), MethodReceiver::Instance))
            .map(|row| provenance_reader_row(row));
        let from_origin = origin
            .and_then(|m| self.inferred_params.get(&(m.clone(), action_name.clone(), MethodReceiver::Instance)))
            .map(|row| provenance_reader_row(row));''')
edit('src/analyze/mod.rs',
'''            let observed = [own, from_origin]''',
'''            let observed = [own.as_deref(), from_origin.as_deref()]''')
edit('src/analyze/mod.rs',
'''        self.settle_pending(app);''',
'''        if std::env::var("RH_PROVENANCE_ROWDUMP").as_deref() == Ok("1")
            && std::env::var("RH_PUBLIC_INPUT").as_deref() == Ok("1")
        {
            let rows: std::collections::BTreeMap<String, serde_json::Value> = self.inferred_params.iter()
                .map(|(k, row)| (format!("{}|{}|{:?}", k.0.0.as_str(), k.1.as_str(), k.2), serde_json::json!({
                    "ref": fold::in_reference_mode(&k.0, &k.1),
                    "full": row.iter().map(|t| format!("{t:?}")).collect::<Vec<_>>(),
                    "known": row.iter().map(|t| format!("{:?}", t.clone().strip_unknown())).collect::<Vec<_>>(),
                })))
                .collect();
            eprintln!("rh-parameter-rows: {}", serde_json::json!(rows));
        }
        self.settle_pending(app);''')
edit('src/analyze/mod.rs',
'''fn unify_param_ty_raw(stored: Ty, observed: Ty) -> Ty {''',
'''// The stored row retains contributions; only designated typing reads use this view.
fn provenance_reader_row(row: &[Ty]) -> std::borrow::Cow<'_, [Ty]> {
    static VIEW: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    if *VIEW.get_or_init(|| std::env::var("RH_PROVENANCE_READER_VIEW").as_deref() == Ok("1")) {
        std::borrow::Cow::Owned(row.iter().map(|t| unify_param_ty_raw(t.clone(), t.clone())).collect())
    } else {
        std::borrow::Cow::Borrowed(row)
    }
}

fn unify_param_ty_raw(stored: Ty, observed: Ty) -> Ty {''')
edit('src/ide.rs',
'''ty: inferred.and_then(|ts| ts.get(i)).cloned().unwrap_or(Ty::gradual()).into(),''',
'''ty: inferred.as_ref().and_then(|ts| ts.get(i)).cloned().unwrap_or(Ty::gradual()).into(),''')
edit('examples/producer_reason_sound_types.rs',
    '                let ty = if let Some(index) = spec[2].as_u64() {',
    '                let param_row;\n                let ty = if let Some(index) = spec[2].as_u64() {')
edit('examples/producer_reason_sound_types.rs',
    '                    analyzer.inferred_param_types(&class, &method).and_then(|row| row.get(index as usize))',
    '                    param_row = analyzer.inferred_param_types(&class, &method);\n                    param_row.as_deref().and_then(|row| row.get(index as usize))')
edit('examples/producer_reason_sound_types.rs',
    'analyzer.inferred_param_types(&class, m).unwrap_or(&[])',
    'analyzer.inferred_param_types(&class, m).unwrap_or_default()')
edit('examples/parameter_reason_sound_types.rs',
    '            let ty = if s.is_array() {',
    '            let param_row;\n            let ty = if s.is_array() {')
edit('examples/parameter_reason_sound_types.rs',
    '                    analyzer.inferred_param_types(&class, &method).and_then(|r| r.get(index as usize))',
    '                    param_row = analyzer.inferred_param_types(&class, &method);\n                    param_row.as_deref().and_then(|r| r.get(index as usize))')
card = (D/'protocol.md').read_text()
harness = re.search(r'```rust\n(fn evidence\(o:.*?\n})\n```', card, re.S).group(1)
p = C/'src/analyze/parameter_conservation/tests.rs'
p.write_text(p.read_text() + '\n' + harness + '\n')
print('Applied advance_prediction flags, reader view, row dump and verbatim harness.')
