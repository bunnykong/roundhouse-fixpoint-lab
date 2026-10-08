# Runtime shape oracle

The recorder samples public Ruby values; the checker tests recursive type membership and unused productions.
Use CRuby 4.0.7 and Python 3.9+. All dependencies are standard libraries. From the repository root:

```sh
python3 -B models/control/run.py
python3 -B -m unittest discover -s oracle -p 'test_*.py'
ruby oracle/record.rb --source reproductions/f2_merge/app/controllers/trees_controller.rb \
  --entry 'TreesController#index' --returns canonical --params canonical:value \
  --fuzz 'TreesController#canonical' --seed 20261007 --count 256 --depth 6 --output oracle/demo.jsonl
python3 oracle/check.py oracle/demo.jsonl models/control/evidence/canonical.rbs \
  --slots models/control/evidence/canonical.slots.json --json
```

The control command first creates a grammar and the exact slot-to-alias map used above.
Repeat `--source` and `--stub` to load more files. ApplicationController is stubbed automatically.
`Class#method` uses an instance; `Module#method` extends an Object; `Class.method` calls a class method.
`--args '[3,null]'` supplies entry arguments. `--prefix-args '[6]'` precedes a fuzzed payload.

Supported types are atoms, unions, recursive aliases, Array, Hash, tuples, records, and parentheses.
Tuples require exact length. Records require their named Symbol keys and allow extra keys. Alias-only cycles
are input errors. Tagged JSONL preserves snapshots, repeated references, and object cycles. Paths in records
are relative to this repository; an external input is represented by its basename and content hash.

Exit 0 means the sampled values fit; exit 1 reports counterexamples; exit 2 means invalid, incomplete,
unsupported, or empty input. All matching union arms count as witnesses, including overlap. Unused arms
are candidates for investigation. Sampling cannot prove exactness or general runtime soundness.
