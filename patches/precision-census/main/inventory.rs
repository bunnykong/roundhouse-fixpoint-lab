fn for_each_hook_body_ref(
    app: &roundhouse::app::App,
    f: &mut impl FnMut(&roundhouse::expr::Expr),
) {
    fn visit_param_defaults(
        params: &[roundhouse::dialect::Param],
        f: &mut impl FnMut(&roundhouse::expr::Expr),
    ) {
        for p in params {
            if let Some(default) = &p.default {
                f(default);
            }
        }
    }
    for model in &app.models {
        for item in &model.body {
            match item {
                roundhouse::dialect::ModelBodyItem::Method { method, .. } => {
                    visit_param_defaults(&method.params, f);
                    f(&method.body)
                }
                roundhouse::dialect::ModelBodyItem::Scope { scope, .. } => {
                    visit_param_defaults(&scope.params, f);
                    f(&scope.body)
                }
                roundhouse::dialect::ModelBodyItem::Callback { callback, .. } => {
                    if let Some(cond) = &callback.condition {
                        f(cond);
                    }
                }
                roundhouse::dialect::ModelBodyItem::Unknown { expr, .. } => f(expr),
                roundhouse::dialect::ModelBodyItem::Association {
                    assoc: roundhouse::dialect::Association::HasMany { extension, .. },
                    ..
                } => {
                    for m in extension {
                        visit_param_defaults(&m.params, f);
                        f(&m.body);
                    }
                }
                _ => {}
            }
        }
        for default in model.class_attr_defaults.values() {
            f(default);
        }
    }
    for lc in &app.library_classes {
        for method in &lc.methods {
            visit_param_defaults(&method.params, f);
            f(&method.body);
        }
        for (_name, value) in &lc.constants {
            f(value);
        }
        for call in &lc.unknown_calls {
            f(call);
        }
        for initializer in &lc.class_ivar_initializers {
            f(initializer);
        }
    }
    // Same set as the mutable twin — see the note there.
    if let Some(lc) = &app.rails_application {
        for method in &lc.methods {
            visit_param_defaults(&method.params, f);
            f(&method.body);
        }
        for (_name, value) in &lc.constants {
            f(value);
        }
        for call in &lc.unknown_calls {
            f(call);
        }
        for initializer in &lc.class_ivar_initializers {
            f(initializer);
        }
    }
    for controller in &app.controllers {
        for item in &controller.body {
            match item {
                roundhouse::dialect::ControllerBodyItem::Action { action, .. } => {
                    for (_name, default) in &action.opt_params {
                        f(default);
                    }
                    f(&action.body)
                }
                roundhouse::dialect::ControllerBodyItem::ClassMethod { method, .. } => {
                    visit_param_defaults(&method.params, f);
                    f(&method.body)
                }
                roundhouse::dialect::ControllerBodyItem::Unknown { expr, .. } => f(expr),
                roundhouse::dialect::ControllerBodyItem::Filter { filter, .. } => {
                    if let Some(c) = &filter.if_cond_expr {
                        f(c);
                    }
                    if let Some(c) = &filter.unless_cond_expr {
                        f(c);
                    }
                }
                _ => {}
            }
        }
    }
    if let Some(seeds) = &app.seeds {
        f(seeds);
    }
}

// One inventory for the extra emit-bound roots the hook walker intentionally
// excludes. Keep the mutable projection and immutable survey in lockstep.
macro_rules! forwarding_roots {
    ($app:ident, $f:ident, $iter:ident, $option:ident $(, $mutable:tt)?) => {
        for view in & $($mutable)? $app.views { $f(& $($mutable)? view.body); }
        for tm in & $($mutable)? $app.test_modules {
            if let Some(setup) = tm.setup.$option() { $f(setup); }
            for test in & $($mutable)? tm.tests { $f(& $($mutable)? test.body); }
            for (_, value) in & $($mutable)? tm.constants { $f(value); }
            for method in & $($mutable)? tm.helpers {
                $f(& $($mutable)? method.body);
                for default in method.params.$iter().filter_map(|p| p.default.$option()) { $f(default); }
            }
            for class in & $($mutable)? tm.inner_classes {
                for method in & $($mutable)? class.methods {
                    $f(& $($mutable)? method.body);
                    for default in method.params.$iter().filter_map(|p| p.default.$option()) { $f(default); }
                }
                for (_, value) in & $($mutable)? class.constants { $f(value); }
                for call in & $($mutable)? class.unknown_calls { $f(call); }
                for initializer in & $($mutable)? class.class_ivar_initializers { $f(initializer); }
            }
        }
    }
}


fn for_each_forwarding_body_ref(app: &roundhouse::App, f: &mut impl FnMut(&roundhouse::expr::Expr)) {
    for_each_hook_body_ref(app, f);
    forwarding_roots!(app, f, iter, as_ref);
}

/// Survey every emit-bound expression root, including defaults and fixture
/// expressions outside the forwarding pass's narrower inventory. Callers walk
/// children themselves, so each root is visited exactly once.
fn for_each_emit_body_ref(app: &roundhouse::App, f: &mut impl FnMut(&roundhouse::expr::Expr)) {
    for_each_forwarding_body_ref(app, f);
    for association in app.models.iter().flat_map(|model| model.associations()) {
        match association {
            roundhouse::dialect::Association::BelongsTo { default: Some(e), .. }
            | roundhouse::dialect::Association::HasMany { scope: Some(e), .. } => f(e),
            _ => {}
        }
    }
    for action in app.controllers.iter().flat_map(|c| c.actions()) {
        for default in action.kw_params.iter().filter_map(|(_, e)| e.as_ref()) { f(default); }
    }
    for view in &app.views {
        for default in view.strict_locals.iter().flatten().filter_map(|p| p.default.as_ref()) { f(default); }
    }
    for fixture in &app.fixtures {
        for e in &fixture.preamble { f(e); }
        for value in fixture.records.values().flat_map(|record| record.values()) {
            if let roundhouse::dialect::FixtureValue::Ruby(e) = value { f(e); }
        }
    }
    for helper in &app.routes.direct_helpers { f(&helper.body); }
    for function in &app.sql_functions {
        let mut visit_method = |method: &roundhouse::dialect::MethodDef| {
            f(&method.body);
            for default in method.params.iter().filter_map(|p| p.default.as_ref()) { f(default); }
        };
        match &function.kind {
            roundhouse::app::SqlFunctionKind::Scalar { method } => visit_method(method),
            roundhouse::app::SqlFunctionKind::Aggregate { step, finalize } => {
                visit_method(step);
                visit_method(finalize);
            }
        }
    }
}
