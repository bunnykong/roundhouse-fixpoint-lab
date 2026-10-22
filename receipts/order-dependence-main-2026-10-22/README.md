# Order dependence on main

Unscored research reference: five small Rails programs whose types on upstream Roundhouse main change with the
order of two methods, files or filters. Each comes in two orders, with CRuby or ActionPack witnesses and a check that
runs both orders. An independent reproduction confirmed the first test.

## Fact F80

On upstream main at `2cd9e5d9` and the current head `958b48fa`, bare Roundhouse gives different types for five small Rails programs when only the order of two methods, files or filters changes. Each of 30 variants ran three times on both commits, and all 180 runs were deterministic. A code audit predicted ten such shapes; a first test of 108 programs and an independent reproduction with its own minimal programs confirmed the same five. (2) One method writes an ivar Hash with `[]=` and another assigns it a Hash literal. With the `[]=` method first, the getter's keys are `String | Symbol`; with the literal first, only `Symbol`, which matches CRuby. A class's methods share one map, `extract_ivar_assignments(&method.body, &mut flow_ivars);` (`src/analyze/mod.rs:3923`; `:2540` for models), so the `[]=` write finds no entry and takes `// No prior entry — seed a fresh Hash[Str, incoming].` (`:8687`). (5) A model method returns nil or another model's nil-returning method. If the caller's file sorts first, the call types `untyped?` and `.zzz` only warns; if the callee's file sorts first, it types `nil` and `.zzz` is an error, as in CRuby. Each model file is harvested inside the model loop, `self.harvest_one_model(model);` (`src/analyze/mod.rs:2581`), and a nil return seen with an unknown arm stays gradual: `if existing.has_unknown_arm() || new.has_unknown_arm() {` … `return Some(gradual_nil());` (`src/analyze/harvest_return.rs:49-50`). It needs a nil-returning callee: with `7`, both orders give `Integer?`. (6) The same holds inside one model split across two files, since each file becomes its own model entry, `app.models.push(model);` (`src/ingest/app.rs:586`): `untyped?` with the caller's file first, `nil`, CRuby's answer, with the callee's. In one file both orders give `untyped?`, wrong but stable. (7) Two controllers declare `helper_method :who` with different return types. Both views get the first controller's type, `.find_map(|c| c.instance_methods.get(name).cloned());` (`src/analyze/mod.rs:4856`), while Rails calls each controller's own method, so one view is wrong in either order. (9) Two `before_action` filters write the same view ivar. The view gets the first filter's type, `ivars.entry(k.clone()).or_insert_with(|| v.clone());` (`src/analyze/mod.rs:3378`; `:3594` for inherited actions), while Rails renders the last write, so the view is wrong in either order. For 2, 5 and 6 the swapped order matches CRuby 4.0.7; for 7 and 9 neither order matches ActionPack 8.1.4, so they are correctness bugs that also vary with order. The 1,272 generated programs behind the milestone-3 comment (https://github.com/rubys/roundhouse/issues/617#issuecomment-6330116782) found none because each is a single service class without these shapes; this corrects that comment's "1,272 generated programs found none yet".

## Condition

- Upstream [rubys/roundhouse](https://github.com/rubys/roundhouse) main at `2cd9e5d9` (the commit of the milestone-3
  comment) and `958b48fa` (main's head on October 22), each built with `cargo build --release --locked`, with no
  research flags. `src/analyze/mod.rs` and `src/analyze/harvest_return.rs` are byte-identical at both commits;
  `src/ingest/app.rs` gains one `use` line, so its line numbers below are one higher than at `2cd9e5d9`.
- Each program was read three ways: `roundhouse check --continue --no-hotspots .`, the RBS from
  `roundhouse --target ruby --allow-unsupported . -o OUT`, and the MCP `type_at` tool. [check.py](check.py) uses
  the first two.
- Each of 30 variants, these pairs and a few more forms, ran three times on each commit. All 180 runs gave the same
  output for the same variant, on both commits.
- Witnesses: CRuby 4.0.7 for shapes 2, 5 and 6, over empty `ActiveRecord::Base` and `ActionController::Base`
  classes; ActionPack 8.1.4 on Ruby 3.3.2 for shapes 7 and 9, because 4.0.7 had no Rails gems installed.

## The five shapes

Each pair under [repros/](repros) has an `as-written` and a `swapped` app that differ only in the order named.

| Shape | As written | Swapped | Right answer |
| --- | --- | --- | --- |
| 2: `[]=` and a literal write one ivar | getter `Hash[(String \| Symbol), …]?` | `Hash[Symbol, …]?` | swapped: CRuby gives `{s: "v", n: 2}` |
| 5: model caller and nil callee in two files | `untyped?`, a warning | `nil`, an error | swapped: CRuby raises on nil |
| 6: one model split across two files | `untyped?`, a warning | `nil`, an error | swapped: CRuby raises on nil |
| 7: `helper_method :who` in two controllers | both views `Integer` | both views `String` | neither: each view calls its own `who` |
| 9: two `before_action` filters write `@x` | view `Integer` | view `String` | neither: the view sees the last write |

### 2. `[]=` ivar writes across methods

`class Bag; def put = @t[:n] = 2; def reset = @t = { s: "v" }; def t = @t; end`, swapped by putting `reset` first.
All methods of a class share one ivar map, and the deferred `[]=` join covers one body only. So when `put` comes
first, its write finds no `@t` and seeds a String-keyed Hash.

```rust
// src/analyze/mod.rs:3923 (and :2540 for models), in type_production_bodies
extract_ivar_assignments(&method.body, &mut flow_ivars);
// src/analyze/mod.rs:8687, in widen_hash_ivar_value
// No prior entry — seed a fresh Hash[Str, incoming]. Matches
```

Both orders also type `put` as `nil`, while CRuby returns 2. That bug does not depend on order.

### 5. Model caller and callee in different files

`Alpha.f(c) = c ? nil : Zulu.g` in `alpha.rb`, `Zulu.g = nil` in `zulu.rb`, and a controller calling
`Alpha.f(true).zzz`. Swapped, `g` is in `alpha.rb` and `f` in `zulu.rb`. The model loop harvests each file's returns
before it types the next, so a caller typed first stores a nil return with an unknown arm, which then stays gradual.

```rust
// src/analyze/mod.rs:2427 and 2581, in type_production_bodies
for model in &mut app.models {
    self.harvest_one_model(model);
// src/analyze/harvest_return.rs:48-50
if matches!(core_e, Ty::Nil) {
    if existing.has_unknown_arm() || new.has_unknown_arm() {
        return Some(gradual_nil());
```

### 6. One model split across files

`class Gamma` with `f` in `gamma_a.rb` and `g` in `gamma_b.rb`, swapped by exchanging the two bodies. The app reader
sorts the paths, and each file becomes its own model entry, so the split model behaves like shape 5.

```rust
// src/ingest/app.rs:6847, in read_rb_files
out.sort();
// src/ingest/app.rs:586
app.models.push(model);
```

### 7. `helper_method` in two controllers

`AController` and `BController` both declare `helper_method :who`, returning `1` and `"b"`; each view renders
`<%= who.zzz %>`. The registry copies one type per helper name onto the shared `ActionView::Base` and takes the first
owner's. In ActionPack each view calls its own controller's `who`, so B's view is wrong in both orders.

```rust
// src/analyze/mod.rs:4847 and 4856, in harvest_returns_to_registry
let view_ctx = ClassId(Symbol::from("ActionView::Base"));
    .find_map(|c| c.instance_methods.get(name).cloned());
```

### 9. A view ivar written by two `before_action` filters

`before_action :one, :two`, with `one` setting `@x = 1` and `two` setting `@x = "s"`, and a view rendering
`<%= @x.zzz %>`; swapped, `before_action :two, :one`. The per-view ivar map keeps the first filter's write, while
ActionPack renders the last. Two `before_action` calls behave the same, `def` order has no effect, and an action body
that reads `@x` gets `String`, the last write.

```rust
// src/analyze/mod.rs:3376-3378 (again at 3592-3594 for inherited actions), in type_production_bodies
if let Some(fivars) = chained_bindings.get(&filter.target) {
    for (k, v) in fivars {
        ivars.entry(k.clone()).or_insert_with(|| v.clone());
```

Line numbers are at `958b48fa`; [the files on GitHub](https://github.com/rubys/roundhouse/tree/958b48fa0971719f75afddcb3e283f65bef2b53b/src).

## Scope

- Shape 5 needs a nil-returning callee. With `def self.g = 7`, both orders give `Integer?`
  ([repros/5-scope-integer-callee](repros/5-scope-integer-callee)).
- Shape 6 shows only when the model is split across files. In one file both method orders give `untyped?`
  ([repros/6-scope-one-file](repros/6-scope-one-file)): stable, but wrong, since CRuby returns nil.
- Shape 2 holds for a model too, with the same two types.

## The earlier search

The [milestone-3 comment](https://github.com/rubys/roundhouse/issues/617#issuecomment-6330116782) ends: "The guard
itself changes only once a small program shows main depending on order; 1,272 generated programs found none yet."
Those programs are all one `Probe` class in `app/services`, in one file or split across reopened files. None has an
ivar `[]=` write, a model, a controller, `helper_method`, `before_action` or a call into another class. Rerun through
the same commands on `2cd9e5d9`, their 1,152 order comparisons are all equal. A code audit of main then predicted
ten order-dependent shapes. A first test of 108 programs, run in every method order in one file and across reopened
files, confirmed five, and this reproduction confirmed the same five with its own programs. So main does depend on
order in small programs, and this corrects the comment's "none yet".

## Limits

- These are small programs. How often the shapes occur in the four apps was not measured.
- [check.py](check.py) reads diagnostics and RBS; it does not query `type_at`.
- The Rails witnesses use ActionPack 8.1.4 on Ruby 3.3.2.
- No fix is proposed here.

## Reproduce

Build upstream main, for example at `958b48fa`, with `cargo build --release --locked`. Then, from the lab root, with
Python 3.9 or later:

```sh
python3 -B receipts/order-dependence-main-2026-10-22/check.py /path/to/roundhouse/target/release/roundhouse
```

It copies each pair to a temporary directory, runs both orders, prints what differs, and compares every result with
[recorded.json](recorded.json); `2cd9e5d9` and `958b48fa` both match it. The witnesses need CRuby 4.0.7 and a Ruby
with the actionpack and actionview 8.1.4 gems:

```sh
RUBY=ruby RAILS_RUBY=ruby sh receipts/order-dependence-main-2026-10-22/witness/run.sh
```

It compares their output with [witness/recorded.txt](witness/recorded.txt).
