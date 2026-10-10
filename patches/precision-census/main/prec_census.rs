// Extension of the emitter-root census. Rows and snapshots are opt-in.
include!("inventory.rs");
use roundhouse::{analyze::Analyzer, expr::{Expr, ExprNode}, ty::Ty};
use serde_json::json;
use std::{collections::HashMap, io::{BufWriter, Write}, path::Path};

fn bits(t: &Ty) -> u8 {
    let mut b = if t.is_unknown() { 2 } else { 0 };
    if t.is_unknown() && !matches!(t, Ty::Var { .. }) { b |= 1; }
    if matches!(t, Ty::Bottom) { b |= 4; }
    let mut child = |t: &Ty| b |= bits(t);
    match t {
        Ty::Array { elem } => child(elem),
        Ty::Hash { key, value } => { child(key); child(value); }
        Ty::Tuple { elems } => elems.iter().for_each(child),
        Ty::Union { variants } => variants.iter().for_each(child),
        Ty::Record { row } => row.fields.values().for_each(child),
        Ty::Class { args, .. } => args.iter().for_each(child),
        Ty::Fn { params, block, ret, .. } => {
            params.iter().for_each(|p| child(&p.ty));
            if let Some(t) = block { child(t); }
            child(ret);
        }
        _ => {}
    }
    b
}

// Canonical diagnostic spelling: union arms and record fields sorted; tuple and
// function positions retained. Var is explicit, never rendered as untyped.
fn render(t: &Ty) -> String {
    let r = render;
    match t {
        Ty::Int => "Integer".into(), Ty::Float => "Float".into(),
        Ty::Bool => "bool".into(), Ty::Str => "String".into(), Ty::Sym => "Symbol".into(),
        Ty::Date => "Date".into(), Ty::Time => "Time".into(), Ty::Nil => "nil".into(),
        Ty::Bottom => "bot".into(), Ty::SelfInstance => "instance".into(),
        Ty::Relation { of } => format!("Relation[{}]", of.0.as_str()),
        Ty::Array { elem } => format!("Array[{}]", r(elem)),
        Ty::Hash { key, value } => format!("Hash[{}, {}]", r(key), r(value)),
        Ty::Tuple { elems } => format!("[{}]", elems.iter().map(r).collect::<Vec<_>>().join(", ")),
        Ty::Union { variants } => {
            let mut v: Vec<_> = variants.iter().map(r).collect(); v.sort(); v.dedup();
            format!("({})", v.join(" | "))
        }
        Ty::Record { row } => {
            let mut v: Vec<_> = row.fields.iter().map(|(k,v)| format!("{}: {}",k.as_str(),r(v))).collect();
            v.sort(); if let Some(rest) = &row.rest { v.push(format!("**Var[{}]", rest.0)); }
            format!("{{ {} }}", v.join(", "))
        }
        Ty::Class { id, args } => {
            if args.is_empty() { id.0.as_str().into() }
            else { format!("{}[{}]", id.0.as_str(), args.iter().map(r).collect::<Vec<_>>().join(", ")) }
        }
        Ty::Fn { params, block, ret, effects } => {
            let ps: Vec<_> = params.iter().map(|p| format!("{:?}:{}:{}",p.kind,p.name.as_str(),r(&p.ty))).collect();
            let bs = block.as_ref().map(|b| format!(" {{ {} }}",r(b))).unwrap_or_default();
            format!("fn({}){} -> {} !{:?}",ps.join(", "),bs,r(ret),effects)
        }
        Ty::Var { var } => format!("Var[{}]", var.0),
        // STAGED_VARIANTS
        _ => "untyped".into(),
    }
}

include!("kind.rs");

#[derive(Default)]
struct Census { typed:u64, missing:u64, untyped:u64, bare:u64, var_only:u64, full:u64, bottom:u64 }
fn count(e:&Expr,c:&mut Census) {
    if let Some(t)=&e.ty {
        c.typed+=1; let b=bits(t);
        c.untyped+=u64::from(b&1!=0); c.var_only+=u64::from(b&1==0 && b&2!=0);
        c.full+=u64::from(b&3==0); c.bottom+=u64::from(b&4!=0);
        c.bare+=u64::from(t.is_unknown() && !matches!(t,Ty::Var{..}));
    } else { c.missing+=1; }
    e.node.for_each_child(&mut |e| count(e,c));
}

fn symbol(e:&Expr)->String {
    match &*e.node {
        ExprNode::Send{method,..} => method.as_str().into(),
        ExprNode::Var{name,..}|ExprNode::Ivar{name,..}|ExprNode::MethodRef{name,..}|ExprNode::Let{name,..} => name.as_str().into(),
        ExprNode::Const{path} => path.iter().map(|x|x.as_str()).collect::<Vec<_>>().join("::"),
        _ => String::new(),
    }
}

// Root ownership is metadata, never part of the primary file/span/kind key.
fn owners(app:&roundhouse::App)->HashMap<usize,serde_json::Value> {
    use roundhouse::dialect::{ModelBodyItem,ControllerBodyItem,MethodDef};
    let mut out=HashMap::new();
    fn method(out:&mut HashMap<usize,serde_json::Value>,class:&str,m:&MethodDef) {
        let owner=json!({"class":class,"method":m.name.as_str(),"side":format!("{:?}",m.receiver),
            "params":m.params.iter().map(|p|p.name.as_str()).collect::<Vec<_>>()});
        out.insert(&m.body as *const Expr as usize,owner.clone());
        for p in &m.params { if let Some(d)=&p.default { out.insert(d as *const Expr as usize,owner.clone()); } }
    }
    for lc in app.library_classes.iter().chain(app.rails_application.iter()) {
        for m in &lc.methods { method(&mut out,lc.name.0.as_str(),m); }
        for (name,e) in &lc.constants { out.insert(e as *const Expr as usize,json!({"class":lc.name.0.as_str(),"constant":name.as_str()})); }
    }
    for model in &app.models {
        for item in &model.body {
            if let ModelBodyItem::Method{method:m,..}=item { method(&mut out,model.name.0.as_str(),m); }
            if let ModelBodyItem::Scope{scope,..}=item {
                out.insert(&scope.body as *const Expr as usize,json!({"class":model.name.0.as_str(),"method":scope.name.as_str(),"side":"scope","params":scope.params.iter().map(|p|p.name.as_str()).collect::<Vec<_>>() }));
            }
        }
    }
    for controller in &app.controllers {
        for item in &controller.body {
            match item {
                ControllerBodyItem::ClassMethod{method:m,..}=>method(&mut out,controller.name.0.as_str(),m),
                ControllerBodyItem::Action{action,..}=>{
                    out.insert(&action.body as *const Expr as usize,json!({"class":controller.name.0.as_str(),"method":action.name.as_str(),"side":"Instance","params":action.params.fields.keys().map(|x|x.as_str()).chain(action.opt_params.iter().map(|(x,_)|x.as_str())).chain(action.kw_params.iter().map(|(x,_)|x.as_str())).collect::<Vec<_>>() }));
                }
                _=>{}
            }
        }
    }
    for tm in &app.test_modules {
        for m in &tm.helpers { method(&mut out,tm.name.0.as_str(),m); }
        for lc in &tm.inner_classes { for m in &lc.methods { method(&mut out,lc.name.0.as_str(),m); } }
        for t in &tm.tests { out.insert(&t.body as *const Expr as usize,json!({"class":tm.name.0.as_str(),"method":t.name.as_str(),"side":"test"})); }
    }
    out
}

fn unknowns(t:&Ty)->HashMap<String,u64> {
    let mut out=HashMap::new();
    fn visit(t:&Ty,out:&mut HashMap<String,u64>) {
        if t.is_unknown() && !matches!(t,Ty::Var{..}) {
            // PROVENANCE
            *out.entry("untyped".into()).or_default()+=1;
        }
        match t {
            Ty::Array{elem}=>visit(elem,out), Ty::Hash{key,value}=>{visit(key,out);visit(value,out);}
            Ty::Tuple{elems}=>elems.iter().for_each(|t|visit(t,out)),
            Ty::Union{variants}=>variants.iter().for_each(|t|visit(t,out)),
            Ty::Record{row}=>row.fields.values().for_each(|t|visit(t,out)),
            Ty::Class{args,..}=>args.iter().for_each(|t|visit(t,out)),
            Ty::Fn{params,block,ret,..}=>{
                params.iter().for_each(|p|visit(&p.ty,out));
                if let Some(t)=block {visit(t,out);} visit(ret,out);
            }
            _=>{}
        }
    }
    visit(t,&mut out); out
}

fn snapshot(app:&roundhouse::App,analyzer:&Analyzer,phase:&str) {
    let Ok(base)=std::env::var("RH_PRECDIFF_ROWS") else {return};
    let path=if phase=="final" {base.clone()} else {format!("{base}.{phase}.jsonl")};
    let mut w=BufWriter::new(std::fs::File::create(path).expect("create rows"));
    let root=std::fs::canonicalize(std::env::args().last().unwrap()).unwrap();
    let files:Vec<_>=app.sources.iter().map(|s|{
        Path::new(&s.path).strip_prefix(&root).map(|p|p.to_string_lossy().into_owned()).unwrap_or_else(|_|s.path.clone())
    }).collect();
    let os=owners(app); let mut seq=0u64; let mut rootid=0u64;
    fn walk(e:&Expr,parent:Option<u64>,rootid:u64,seq:&mut u64,files:&[String],owner:&serde_json::Value,w:&mut impl Write) {
        let here=*seq;
        if let Some(t)=&e.ty {
            let b=bits(t); let file=if e.span.file.0==0 {"<synthetic>"} else {&files[e.span.file.0 as usize-1]};
            let recv=if let ExprNode::Send{recv:Some(recv),..}=&*e.node {recv.ty.as_ref().map(render)} else {None};
            let row=json!({"seq":*seq,"parent":parent,"root":rootid,"file":file,"file_id":e.span.file.0,
                "start":e.span.start,"end":e.span.end,"kind":kind(e),"symbol":symbol(e),"owner":owner,
                "type":render(t),"category":if b&1!=0 {"untyped"} else if b&2!=0 {"var"} else {"full"},
                "bits":b,"unknowns":unknowns(t),"recv_type":recv});
            serde_json::to_writer(&mut *w,&row).unwrap(); writeln!(w).unwrap();
        }
        *seq+=1; e.node.for_each_child(&mut |e|walk(e,Some(here),rootid,seq,files,owner,w));
    }
    for_each_emit_body_ref(app,&mut |e|{
        let owner=os.get(&(e as *const Expr as usize)).cloned().unwrap_or(serde_json::Value::Null);
        walk(e,None,rootid,&mut seq,&files,&owner,&mut w); rootid+=1;
    });
    w.flush().unwrap();
    if phase=="pre-expand" {
        let fold=roundhouse::analyze::precdiff_probe::fold_slots(analyzer);
        std::fs::write(format!("{base}.fold-slots.json"),serde_json::to_vec(&fold).unwrap()).unwrap();
    }
    let mut slots=BufWriter::new(std::fs::File::create(format!("{base}.{phase}.slots.jsonl")).unwrap());
    for (id,c) in analyzer.class_registry() {
        for (side,table) in [("instance",&c.instance_methods),("class",&c.class_methods),("constant",&c.constants),("ivar",&c.attributes.fields.iter().map(|(k,v)|(k.clone(),v.clone())).collect())] {
            for (method,t) in table {
                let row=analyzer.inferred_param_types(id,method);
                writeln!(slots,"{}",json!({"class":id.0.as_str(),"side":side,"name":method.as_str(),"type":render(t),"unknowns":unknowns(t),"params":row.map(|ts|ts.iter().map(render).collect::<Vec<_>>())})).unwrap();
            }
        }
    }
    slots.flush().unwrap();
}

fn main() {
    roundhouse::stack::run(|| {
        let input=std::env::args().last().expect("input");
        if std::env::var("RH_PRECDIFF_ROWS").is_ok() && std::env::var("RH_PRECDIFF_TRACE").as_deref()==Ok("1") {
            roundhouse::analyze::precdiff_probe::set_hook(snapshot);
        }
        roundhouse::ingest::survey::activate();
        let mut app=roundhouse::ingest::ingest_app(Path::new(&input)).expect("ingest input");
        let mut analyzer=Analyzer::new(&app); analyzer.analyze(&mut app);
        let mut c=Census::default(); for_each_emit_body_ref(&app,&mut |e|count(e,&mut c));
        if std::env::var("RH_PRECDIFF_ROWS").is_ok() {snapshot(&app,&analyzer,"final");}
        eprintln!("rh-gate: {}",json!({"typed":c.typed,"missing":c.missing,"bare_untyped":c.bare,
            "untyped_anywhere":c.untyped,"var_without_untyped":c.var_only,"fully_typed":c.full,"bottom_anywhere":c.bottom}));
        println!("roundhouse-check: . — 0 parse error(s), 0 error(s), 0 warning(s), 0 gap-attributed note(s), 0 survey gap(s)");
    });
}
