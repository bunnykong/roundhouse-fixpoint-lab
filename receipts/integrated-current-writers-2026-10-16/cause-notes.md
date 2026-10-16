# Mutation losses in the sampled rows

Condition `integrated-current-writers-20261016-four-apps-v0a0`, unset V0A0. The census assigns 35 of 54 new sampled losses to array contents,
14 to hash contents, and five to missing caller/writer contributions. These are row counts; one source defect
can affect several rows. The two targeted Slack rows are outside the samples and rates.

The [array transfer](https://github.com/bunnykong/roundhouse/blob/991ec4b356a21cf53271737124533c617e01e847/src/analyze/body/send.rs) returns the receiver's old element type for
append operations. Later sequence refinement does not repair the append result or every loop-carried value.
The [hash transfer](https://github.com/bunnykong/roundhouse/blob/991ec4b356a21cf53271737124533c617e01e847/src/analyze/body/mod.rs) preserves old keys on the current-writer path;
merge handling also omits input contributions. Runtime witnesses show additions missing from the inferred containers.
This source correspondence supports the sampled families; individual flag causality was not isolated.

Chatwoot C1431/C1432 read Slack sender hashes after unchanged name/avatar insertions. A finite Slack/request/database
boundary executes the original method and expressions. Every control schedule admits the nonempty Symbol-keyed
hashes; every candidate schedule rejects them with Bottom keys. Each row varies in control and becomes equal in
the candidate. C134 and C1007 independently lose nonempty String arrays. The light check freshly executes all
23 Chatwoot observations and verifies those four rows against exact native identities.

Array/hash losses dominate this sample. That is not proof of dominance among the 6,096 unadjudicated rows,
nor evidence that a proposed mutation-writer repair works. Soundness and general order independence remain open.
