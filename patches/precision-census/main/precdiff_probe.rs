// Public-only opt-in observation hooks for expression census.
use super::Analyzer;
use crate::App;
use std::cell::Cell;
type Hook = fn(&App, &Analyzer, &str);
thread_local! { static HOOK: Cell<Option<Hook>> = const { Cell::new(None) }; }
pub fn set_hook(hook: Hook) { HOOK.with(|h| h.set(Some(hook))); }
pub(super) fn snapshot(app: &App, analyzer: &Analyzer, phase: &str) {
    HOOK.with(|h| { if let Some(hook) = h.get() { hook(app, analyzer, phase); } });
}

use std::{collections::{HashMap,HashSet},sync::LazyLock,cell::RefCell,io::{BufWriter,Write}};
use crate::{expr::{Expr,ExprNode},ty::Ty};
use super::body::{Ctx,ClassInfo};
static FLOW: LazyLock<bool> = LazyLock::new(|| std::env::var("RH_PRECDIFF_FLOW").is_ok());
static SELECT: LazyLock<HashSet<[u32;3]>> = LazyLock::new(|| {
    std::env::var("RH_PRECDIFF_SELECT").ok().and_then(|p|std::fs::read_to_string(p).ok())
        .and_then(|s|serde_json::from_str::<Vec<[u32;3]>>(&s).ok()).unwrap_or_default().into_iter().collect()
});
thread_local! {
    static LAST: RefCell<HashMap<String,serde_json::Value>> = RefCell::new(HashMap::new());
    static EVENTS: RefCell<Option<BufWriter<std::fs::File>>> = RefCell::new(None);
    static HARVEST: RefCell<Option<(usize,String)>> = RefCell::new(None);
}
pub(super) fn flow(e:&Expr,t:&Ty,ctx:&Ctx,classes:&HashMap<crate::ident::ClassId,ClassInfo>) {
    if !*FLOW || !SELECT.contains(&[e.span.file.0,e.span.start,e.span.end]) { return; }
    let mut data=serde_json::json!({"span":[e.span.file.0,e.span.start,e.span.end],"type":t,
        "self_type":ctx.self_ty,"class_side":ctx.class_side,
        "discriminant":format!("{:?}",std::mem::discriminant(&*e.node))});
    let (kind,name)=match &*e.node {
        ExprNode::Var{name,..}=>{
            data["binding"]=serde_json::json!(ctx.local_bindings.get(name));
            ("Var",name.as_str().to_string())
        }
        ExprNode::Ivar{name}=>{
            data["binding"]=serde_json::json!(ctx.ivar_bindings.get(name));
            ("Ivar",name.as_str().to_string())
        }
        ExprNode::Send{recv,method,block,..}=>{
            data["recv"]=serde_json::json!(recv.as_ref().and_then(|e|e.ty.as_ref()));
            data["block"]=serde_json::json!(block.as_ref().and_then(|e|e.ty.as_ref()));
            let mut targets=Vec::new();
            fn candidates(t:&Ty,ids:&mut Vec<crate::ident::ClassId>) {
                match t {
                    Ty::Class{id,..}=>ids.push(id.clone()),
                    Ty::Relation{of}=>ids.push(of.clone()),
                    Ty::Union{variants}=>variants.iter().for_each(|t|candidates(t,ids)),
                    _=>{}
                }
            }
            let mut ids=Vec::new();
            if let Some(t)=recv.as_ref().and_then(|e|e.ty.as_ref()).or(ctx.self_ty.as_ref()) {candidates(t,&mut ids);}
            let mut seen=HashSet::new();
            while let Some(id)=ids.pop() {
                if !seen.insert(id.clone()) {continue;}
                if let Some(c)=classes.get(&id) {
                    for (side,table) in [("instance",&c.instance_methods),("class",&c.class_methods)] {
                        if let Some(ty)=table.get(method) { targets.push(serde_json::json!({"class":id.0.as_str(),"side":side,"method":method.as_str(),"type":ty})); }
                    }
                    ids.extend(c.includes.iter().cloned());ids.extend(c.parent.iter().cloned());
                }
            }
            data["targets"]=serde_json::json!(targets);
            ("Send",method.as_str().to_string())
        }
        ExprNode::Const{path}=>("Const",path.iter().map(|p|p.as_str()).collect::<Vec<_>>().join("::")),
        _=>("Other",String::new()),
    };
    data["kind"]=serde_json::json!(kind);data["symbol"]=serde_json::json!(name);
    let key=format!("{:?}:{kind}:{name}:{:?}:{}",e.span,ctx.self_ty,ctx.class_side);
    LAST.with(|s|{s.borrow_mut().insert(key,data);});
}
pub(super) fn flush_flow() {
    if !*FLOW {return;}
    let p=std::env::var("RH_PRECDIFF_FLOW").unwrap();
    let mut w=BufWriter::new(std::fs::File::create(p).unwrap());
    LAST.with(|s|{for v in s.borrow().values() {writeln!(w,"{v}").unwrap();}});
    w.flush().unwrap(); EVENTS.with(|e|{if let Some(w)=&mut *e.borrow_mut(){w.flush().unwrap();}});
}
pub(super) fn harvest_context(table:usize,method:&str) {
    if *FLOW {HARVEST.with(|s|*s.borrow_mut()=Some((table,method.into())));}
}
pub(super) fn event(rule:&str,data:impl FnOnce()->serde_json::Value) {
    if !*FLOW {return;}
    let data=data();
    let context=HARVEST.with(|s|s.borrow().clone());
    EVENTS.with(|s|{
        let mut s=s.borrow_mut();
        if s.is_none() {
            let p=std::env::var("RH_PRECDIFF_FLOW").unwrap()+".events.jsonl";
            *s=Some(BufWriter::new(std::fs::File::create(p).unwrap()));
        }
        writeln!(s.as_mut().unwrap(),"{}",serde_json::json!({"rule":rule,"context":context,"data":data})).unwrap();
    });
}
pub fn fold_slots(_analyzer:&Analyzer)->serde_json::Value {serde_json::Value::Null}
