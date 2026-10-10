# Recorded limits of the Discourse trace

The passages below retain the trace report's wording for coverage and interpretation.
The public-copy hostname redaction and operational metadata normalization are recorded separately
in [recorded-files.json](recorded-files.json); they preserve every membership decision.

> Across P, E and I there are 127 observations and 27 distinct reads: main accepts 127 and rejects 0;
> S3 accepts 91 and rejects 36. These totals describe the declared union of three runtime settings.
> Every observation maps to one fixed static slot; **no-slot observations = 0**, **missing selected types = 0**.

> These are reads of the receiver itself, including the receiver of `[]=`. The wrapper snapshots the
> Hash immediately before that particular read's surrounding operation. It evaluates `@data` once and
> returns the same object. Samples after a write or at a method return cannot stand for these earlier reads.
> Three reads on line 95 and two on line 145 retain separate identities.

> The remaining unobserved read is the conditional pending-duration assignment at **145:9**.
> A longer-running job test with an interval tick is needed to observe that branch; starting and final logging
> alone do not execute it.

> All accepted observations in these app comparisons involve at least one uncertain or unsupported component.
> The paired census adds no new opaque selected alias/category, but neither arm establishes all-execution soundness.

> The earlier observed S3 app graph accepts/rejects exactly the same values as its final grammar for
> P, E and I: 17/7, 54/21 and 20/8. Selected final types, raw categories and loop endings match the
> unmodified S3 export. This is selected-slot parity, not whole-state parity: the two app runs' full
> structural telemetry differs (universe sizes 575858 and 575860, with different structural digests).
> That structure snapshot precedes the observer hook, but no cause is assigned to the difference.

> The earlier `*-instrumented` observer builds are retained as pre-review references. Their temporary
> Ty union construction touched the sharing cache. The committed `*-observed` version constructs JSON only.
> The final observer was built and rechecked on F17. Its extra app repeat was cancelled while waiting
> for the shared lock. The actual app graph check used the earlier observer: 28 roots, zero reachable
> fold nodes, so its temporary-union branch was not exercised by these selected app reads.
> No final-observer app repeat or fresh app verification is claimed.

> The main app export hits its production and absorb caps; views settles at round 1.
> S3 app loops settle at production/views/absorb rounds 5/1/2. A fresh app extra-round control was not run;
> its queued job was cancelled. The only fresh zero-movement claim here is for the settling reproduction.

> `graph.rbs` is checked separately. Original main and unmodified S3 exports identify their graph stage as
> `final-only`; that file repeats the final grammar. The observed S3 reference provides actual pre-expansion
> `graph-raw.json`, reachable graph nodes and a graph uncertainty census. A repeated final grammar is never
> reported as a recovered folded graph.

> F17's corrected final exports still contain uncertainty in both selected slots;
> its actual graph retains uncertainty in one. Zero rejection is qualified by that coverage.

> The expression exporter currently searches named library-class method bodies, not every Ruby metaprogramming form.
> An unsupported location must be reported as missing; expanding the selector's coverage is a separate adapter change.

> The seed catches a missing `node_modules/.pnpm/lock.yaml` frontend/theme error. The selected backend tests pass;
> broader tests may need the app's frontend setup. This is not a complete Discourse development installation.

> The synchronous enqueue test at line 149 bypasses JobInstrumenter and passes with zero selected observations.
> The recorder now exits 2 and emits an error marker for it; it is not a passing oracle trace.

> Enabling interval logging on the logging assertion at line 169 changes the first log status to `starting`,
> so that test fails. Use the separate own test at line 74; do not rewrite assertions to rescue a trace.

> Preserve Time and exception tags explicitly. Unsupported runtime objects must fail recording;
> unsupported static rendering must remain in the coverage census.

> Hash snapshots contain changing PID, timestamps, duration and GC counters. The seed fixes test ordering;
> it does not make raw values byte-identical. Stable source slots and tag-membership counts repeat.

> Fixed selection coverage is independent of the observed domain. Missing unobserved static slots still fail the gate;
> no-slot observations and partial/error traces are separate failure categories.

> These are single process observations on a shared host, not speed comparisons. Shared analyzer-lock waiting
> has been much longer than execution and is excluded from exporter process times.

> No full analyzer test suite or 105-pair emission gate was rerun; this work is observation infrastructure,
> not an inference implementation candidate or its acceptance certificate.

> these are solo re-executions,
> not independent verification.
