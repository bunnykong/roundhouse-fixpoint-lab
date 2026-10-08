//! Export the merged-back normalizer's final types and loop endings.
use roundhouse::{analyze::{Analyzer, LoopEnd}, ident::{ClassId, Symbol}, ty::Ty};
use std::path::Path;

fn render(t: &Ty) -> String {
    match t {
        Ty::Int => "Integer".into(),
        Ty::Float => "Float".into(),
        Ty::Bool => "bool".into(),
        Ty::Str => "String".into(),
        Ty::Sym => "Symbol".into(),
        Ty::Nil => "nil".into(),
        Ty::Array { elem } => format!("Array[{}]", render(elem)),
        Ty::Hash { key, value } => format!("Hash[{}, {}]", render(key), render(value)),
        Ty::Tuple { elems } => format!("[{}]", elems.iter().map(render).collect::<Vec<_>>().join(", ")),
        Ty::Union { variants } => variants.iter().map(render).collect::<Vec<_>>().join(" | "),
        Ty::Fn { ret, .. } => render(ret),
        Ty::Bottom => "{ __bottom__: nil }".into(),
        _ => "untyped".into(),
    }
}

fn end(e: LoopEnd) -> serde_json::Value {
    match e {
        LoopEnd::Settled(n) => serde_json::json!({"end": "settled", "round": n}),
        LoopEnd::RanToCap => serde_json::json!({"end": "ran_to_cap"}),
        LoopEnd::NotRun => serde_json::json!({"end": "not_run"}),
    }
}

fn main() {
    roundhouse::stack::run(|| {
        let path = std::env::args().nth(1).expect("usage: settle-probe APP");
        roundhouse::ingest::survey::activate();
        let mut app = roundhouse::ingest::app::ingest_app(Path::new(&path)).unwrap();
        let mut analyzer = Analyzer::new(&app);
        analyzer.analyze(&mut app);
        let class = ClassId(Symbol::from("TreesController"));
        let method = Symbol::from("canonical");
        let arg = analyzer.inferred_param_types(&class, &method)
            .and_then(|row| row.first()).expect("missing canonical parameter");
        let ret = analyzer.class_registry().get(&class)
            .and_then(|c| c.instance_methods.get(&method)).expect("missing canonical return");
        let rounds = analyzer.fixpoint_rounds();
        println!("{}", serde_json::json!({
            "types": {
                "trees_controller_canonical_arg0": render(arg),
                "trees_controller_canonical_ret": render(ret)
            },
            "loops": {
                "production": end(rounds.production),
                "views_and_tests": end(rounds.views_and_tests),
                "absorb": end(rounds.absorb)
            }
        }));
    });
}
