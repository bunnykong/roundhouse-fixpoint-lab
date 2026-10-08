# Executable models

Python 3.9+ standard library only; runtime seed experiments also require CRuby 4.0.7.
Each subdirectory has a runnable example. These are explicit abstractions and hand-lowered relations,
so their counters measure solver work rather than Ruby execution or analyzer speed.

```sh
python3 -B models/datalog/run.py
python3 -B models/control/run.py
python3 -B -m unittest models.cyclic_eq.test_cyclic_eq models.cyclic_eq.test_permutation
```

Origin-aware regular equations and site grammars use different abstractions for projections and correlated arms.
The graph reifier has an exponential determinization worst case. A finite site solver does not require that
reification. The examples retain those distinctions so an apparent speedup cannot silently change the question.
