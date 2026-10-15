# The storage reason contract

The codec follows producer reason audit's representation at `d83849d3` and the native parameter reason seeds starting tree:
`Pending = 1`, `Gradual = 2`, `Unresolved = 4`. All seven nonempty subsets are valid. Reason union is
bitwise union; the effective legacy tag prioritizes Gradual, then Unresolved, then Pending. Storage
preserves the complete subset, never just that effective tag. Unknown bits and empty sets are rejected.

Schema 3 has identity
`rh-warm-native-v1:pending=1,gradual=2,unresolved=4;row=ordered-pairs`.
Every native `Untyped` stores `why` as the complete integer mask. Record fields store ordered pairs;
union operands, function parameters and type arguments retain their native array order. Ordinary IR
serialization keeps its legacy field shape, and its reader still ignores the skipped reason field.

The API is `storage_codec::WarmCodec`, used by actual expression and fold-write persistence and by
read/input fingerprints. Source spans and recursive-slot keys continue through warm's existing wire
mapping. Chronological records retain unit/source/receiver-side/occurrence identity, root, guards,
fold writes and actual scheduler reads. This clone has no persisted production return accumulator
or per-writer completion table to convert. It does not repair parameter absorption or joins.

The native reason-only control exercises the actual production evaluation guard and body typer with
an unchanged reader and changed constant evidence. It distinguishes read invalidation from input/body
invalidation and proves the reader is typed again. It also checks reason withdrawal and subsequent
replay. The standalone control publishes one body record without a whole-program shadow; native CLI
fixtures and the Mastodon profile independently retain mandatory shadow and separate cold validation.

The integration test selects the same codec API as production. The private reader-guard control lives
in library tests, so its command uses `--lib warm_provenance_invalidation` instead of `--test warm_check`.
All subprocesses that clear inherited experimental variables explicitly pass the candidate switch.
