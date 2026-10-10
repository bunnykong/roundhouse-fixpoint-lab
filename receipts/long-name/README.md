# Long literal dispatch name

The [fixture](../../reproductions/long_name_dispatch/) has a 94-byte ASCII method name.
The historical scanner's `String::len()` cutoff was 80 bytes, while dispatch accepted the literal.
`unfixed.rbs`, `repaired.rbs`, `verify.txt` and `shuffles.txt` retain the signature, extra-round
movement and shuffled digest observations. [condition.json](condition.json) pins the code and flags.
Public staged [`92844f68`](https://github.com/bunnykong/roundhouse/tree/92844f68ea0bef9bfb6d8a8f1b0fc4cad4fff51b) includes the scanner repair.

```sh
python3 -B receipts/long-name/recompute.py
python3 -B receipts/long-name/rerun.py
```

For the historical shuffled probe, start at the shared-type snapshot in `condition.json`
and apply [long-name-probe.diff](../../patches/long-name-probe.diff). Build with four Cargo jobs,
then, from the lab root, run `roundhouse check --continue reproductions/long_name_dispatch` with the six S3 flags,
`RH_DET=1 RH_C1_DIGEST=1` and `RH_SHUFFLE=0`, `1`, `2` in separate processes.
Run the extra-round check separately with `RH_FOLD_VERIFY=1`: it changes the state whose digest is printed.
The patch includes the committed probe's semantics; comments use public descriptions.

The five public apps at [the lab pins](../public-app-pins.json) contained no string-literal
`send`, `public_send`, `__send__` or `try` names over 80 bytes. The defect's presence on this
constructed fixture therefore does not change their recorded results.

The scan can be repeated after fetching the pinned apps:

```sh
ruby receipts/long-name/literal-scan.rb corpus/apps
```

`public-app-scan.json` retains the zero-hit output, Ruby and Prism versions, and the app/lib scope.
`scanned-inputs.json` verifies the complete source inventories against the pinned public trees.
Fresh shuffled runs and the extra-round movement are retained separately in `release-*-recheck.json`.
