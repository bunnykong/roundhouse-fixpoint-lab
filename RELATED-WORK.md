# Related work

The ideas behind the RFC are classical. This list credits where each one comes from. Items marked † were read in abstract or summary only.

## Upstream (Roundhouse and Spinel)

- **Roundhouse:**
  - [#518](https://github.com/rubys/roundhouse/issues/518), [#584](https://github.com/rubys/roundhouse/pull/584) and [#589](https://github.com/rubys/roundhouse/pull/589): the growth report, the stored-type bound, and loop reporting (thomasklemm);
  - [#521](https://github.com/rubys/roundhouse/pull/521) and [#524](https://github.com/rubys/roundhouse/pull/524): stabilization and the dirty frontier (thomasklemm);
  - [#505](https://github.com/rubys/roundhouse/pull/505): the provenance split, deferred;
  - [#528](https://github.com/rubys/roundhouse/pull/528) and [#551](https://github.com/rubys/roundhouse/pull/551) (dai199);
  - [#565](https://github.com/rubys/roundhouse/pull/565) (eddygarcas);
  - [#72](https://github.com/rubys/roundhouse/issues/72): the typed call graph and per-unit analysis;
  - commits `68f4d828`, `16e1ead2` and `ccbafad6` (rubys).
- **Spinel:**
  - [fixpoint convergence notes](https://github.com/matz/spinel/blob/master/docs/internals/fixpoint-convergence.md) and commit `933266361` (matz);
  - [matz/spinel#4113](https://github.com/matz/spinel/issues/4113): the cap canary;
  - [matz/spinel#7236](https://github.com/matz/spinel/issues/7236) and [matz/spinel#7237](https://github.com/matz/spinel/issues/7237): change-driven scheduling (thomasklemm);
  - [matz/spinel#7697](https://github.com/matz/spinel/pull/7697) and [matz/spinel#7699](https://github.com/matz/spinel/pull/7699) (FrancescoK).

## Set-based analysis and inferred recursive types

- Heintze, *Set-based analysis of ML programs*, LFP 1994, [doi:10.1145/182409.182495](https://doi.org/10.1145/182409.182495). Heintze and Jaffar, *A finite presentation theorem for approximating logic programs*, POPL 1990, [doi:10.1145/96709.96729](https://doi.org/10.1145/96709.96729).
- Aiken, Wimmers and Lakshman, *Soft typing with conditional types*, POPL 1994, [doi:10.1145/174675.177847](https://doi.org/10.1145/174675.177847).
- Wright and Cartwright, *A practical soft type system for Scheme*, TOPLAS 1997, [doi:10.1145/239912.239917](https://doi.org/10.1145/239912.239917).
- Flanagan et al., *Catching bugs in the web of program invariants* (MrSpidey), PLDI 1996, [doi:10.1145/231379.231387](https://doi.org/10.1145/231379.231387). Flanagan and Felleisen, *Componential set-based analysis*, TOPLAS 1999, [doi:10.1145/316686.316703](https://doi.org/10.1145/316686.316703).
- Palsberg and O'Keefe, *A type system equivalent to flow analysis*, TOPLAS 1995, [doi:10.1145/210184.210187](https://doi.org/10.1145/210184.210187).
- Chaudhuri et al., *Fast and precise type checking for JavaScript* (Flow), OOPSLA 2017, [doi:10.1145/3133872](https://doi.org/10.1145/3133872).
- Castagna, Laurent and Nguyễn, *Polymorphic type inference for dynamic languages*, POPL 2024, [doi:10.1145/3632882](https://doi.org/10.1145/3632882) †.

## Ruby

- **TypeProf** ([ruby/typeprof](https://github.com/ruby/typeprof), Endoh): v2's origin-keyed container vertices; commit `e68384616` removed union-argument expansion from the prototype.
- Furr, An, Foster and Hicks: [DRuby](https://www.cs.umd.edu/projects/PL/druby/papers/druby-oops09.pdf) (OOPSLA 2009), [DRails](https://www.cs.umd.edu/projects/PL/druby/papers/drails-ase09.pdf) (ASE 2009) and Rubydust (POPL 2011, [doi:10.1145/1926385.1926437](https://doi.org/10.1145/1926385.1926437)).
- Kazerounian et al.: InferDL ([doi:10.1145/3426422.3426985](https://doi.org/10.1145/3426422.3426985)) and SimTyper ([doi:10.1145/3485483](https://doi.org/10.1145/3485483)) †.
- Matsumoto and Minamide, [IPSJ](https://ipsj.ixsq.nii.ac.jp/records/16465) †.

## Industrial checkers

- **Pyright** separates *not computed yet* from `Unknown`.
- **ty's** divergence marker, and its structural recursive types ([astral-sh/ruff#28425](https://github.com/astral-sh/ruff/pull/28425)).
- **TypeScript's** recursion identity, and **Luau's** printed cyclic types.
- **Elixir's** `dynamic()`, which carries an upper bound.

## Solving, sharing and precision

- Kildall; Kam and Ullman; Cousot and Cousot; Nielson, Nielson and Hankin.
- Bourdoncle, *Efficient chaotic iteration strategies with widenings*, FMPA 1993 (LNCS 735).
- Amato et al., [arXiv:1503.00883](https://arxiv.org/abs/1503.00883) †, and Apinis, Seidl and Vojdani, on non-monotone systems. Salsa, Adapton, PIKOS and DRed for incremental and parallel solving.
- Abiteboul, Hull and Vianu, [Foundations of Databases, ch. 13–14](http://webdam.inria.fr/Alice/pdfs/Chapter-13.pdf): inflationary fixpoints.
- Filliâtre and Conchon, hash-consing; Bryant, BDDs.
- Agesen, CPA. Plevyak and Chien, [precise concrete type inference](https://www.cs.cornell.edu/courses/cs612/2000SP/papers/plevyak-type-inf.pdf).
- Giacobazzi, Ranzato and Scozzari, [*Making abstract interpretations complete*](https://www.math.unipd.it/~ranzato/papers/jacm00.pdf), JACM 2000. Clarke et al., [CEGAR](https://web.stanford.edu/class/cs357/cegar.pdf).

## Mechanized fixpoints

- Klein and Nipkow, [Isabelle bytecode verifier](https://www21.in.tum.de/~nipkow/pubs/tcs03.pdf); Cachera et al.; Benzaken et al.; Hofmann, Karbyshev and Seidl; Stade, Tilscher and Seidl.
- La Spina, Demange and Blazy ([doi:10.1007/978-3-031-91121-7_4](https://doi.org/10.1007/978-3-031-91121-7_4)) †.
- Mathlib's [fixed points](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Order/FixedPoints.html).
