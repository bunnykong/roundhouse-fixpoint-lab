# Arena ownership and reset boundaries

Source investigation at public `96519abf042435d4cfefe5a05d7450b042275fa7` on `fixpoint-arena`,
activated with `RH_ARENA=1`. [source-lines.json](source-lines.json) retains the exact file hash
and relevant lines; the complete source is `src/ty_arena.rs` at that pin.

```sh
git show 96519abf:src/ty_arena.rs
git grep -n 'ty_arena::reset\|ty_arena::boundary' 96519abf -- src
```

The address index retains Arc payload owners; shared-payload identities refresh on mutation.
Arena and dependent memo reset together at analysis entry and the 262,144-entry boundary between
operations. Registry entries, IR stamps and fold values still hold `Ty`. Persistent IDs require
arena lifetime ownership before replacing those holders; the disposable memo reset cannot survive
while IDs remain stored. This is a lifetime constraint, with no new speed claim.
