# 180 — Eight remaining fixed paid split templates

Prepared eight unreviewed per-split argv/receipt templates and actual CPU dry-run evidence only under `transfer-v5/fixed-paid-batch/`. No reservations, submissions, GPU/model/API work, source changes, cache/ledger edits, original178/harm-template edits or original receipt edits. Controller/manifest ownership remains with179worker; this report supplies a separate preparation index.

Index: `fixed-paid-batch/preparation-index.json`; all exact paths, ordered recipient IDs, ordered unique native donor IDs, per-recipient partner IDs/index, output/checkpoint/result roots, immutable source hashes, planned account/partition/command shapes, cost assumptions and dry-run evidence are recorded there. IndexSHA256 `6343e3e22d4793edbad9dad1f8a2a90145cfbb7778c2b9a67208ff3cd553f22a`.

|Order/split|Recipients|Used donors|Original batches|NEWstop|Response-only planningUSD|
|---|---:|---:|---:|---:|---:|
|1 lb:harm-pressure-knowledge-report|50|50|42|43|0.317–0.364|
|2 lb:convincing-game|50|50|42|43|2.641–2.974|
|3 mask:continuations|28|28|24|25|1.487–2.072|
|4 mask:disinformation|11|9|12|13|0.591–0.828|
|5 mask:doubling_down_known_facts|29|14|22|23|1.347–1.759|
|6 mask:known_facts|37|34|30|31|1.670–2.149|
|7 mask:provided_facts|50|50|42|43|2.341–3.073|
|8 mask:statistics|16|16|12|13|0.553–3.871|

All eight preserve native512, all five frozen states, original masks/recipients/donors, exact version2 expected argv and existing per-split output/checkpoint prefixes. Every receipt remains reviewed=false, rootdecisionempty and reservationnull. Each plans1H200/3600seconds under account+qosbjhz-delta-gpu, partitiongpuH200x8-interactive; command shapes explicitly include `--time=01:00:00` and require ROOT_FINAL_RECEIPT_REQUIRED. They are not executable launch approvals.

Batch counts are `5*ceil(Nrecipient/8)+ceil(NuniqueUsedDonors/8)`; NEWstop is one greater so the last raw batch permits final stock scoring/coherence. Sourceinspection confirms `gen_engine.generate_bucketed` uses stable descending prompt-length sort then contiguous batch8 slices. Frozen KVcache path keeps batch8; sorting changes exact bucket contents but not ceilcounts. Native donor message identities are unique and distinct from recipient message identities; pool_items exactly match the used unique donor IDs. Total226original generation batches/1606physicalgenerations/1355maximum response-judge requests before caching and retries. No rebucketing was introduced.

All eight actual shell→version2runner→public evaluator CPUdryruns exited0 sequentially, totaling151.372seconds. Each verifies frozen source/argv/policy/cohort bindings, exact fixedcase/donorcount/native512, allfive states and the public “Nothing was written” marker. Each passed credential_names_passed=[]; no content guard was created. All eight preflight snapshots remained190globalattempts/USD0.219921. Logs and per-split statusJSON are listed byindex; aggregate `fixed-paid-batch/cpu-dryrun-summary.json` reports all_eight_passed=true. Final templates were also revalidated using the required mgnp interpreter. An initial verification command used basePython and was correctly refused by the interpreter gate; rerunning under mgnp passed without changing any template.

Cost estimates reuse167's historical-prompt proxies: five times selected full-row prompt chars divided by4(lower) or2(upper), plus576inputtokens per response; frozen price/output metadata is unchanged. Numericalstatistics assumes1000–10000reasoning/outputtokens percall as a planning sensitivity, not a bound. Sum response-only estimates10.946–17.091USD excludes repeatedstartuphealth, retries and cache effects. First instructed's observed globalsettled0.219921 is context only; do not extrapolate its low cost to numericalMASK. Full-context reservation sum~1857USD is a pessimistic exposure bound across requests, not an expected bill. The shared reviewed20USD/5000attempt guard still governs every physical paid attempt; pending/unknown costs retain reserves and can stop work before expected coverage.

The new fixed batch plans8GPUhours, matching root's requested36.6/40cumulative reservation scenario after finalization; no reservation was made by this worker. One-hour limits are bounded attempts, not completion guarantees. Every remaining dataset keeps original strict classification/completion semantics; the explicitINVALID exception remains instructed-only. Any incomplete/error/budget/unknown-settlement outcome must halt the sequential controller for root review rather than silently skipping, retrying, filtering or reclassifying.

Controller reuse contracts supplied directly: import version2runner and call validate(receipt,dry_run=True) for CPU preparation, validate(...,False) for finalized rootauthorization (still no model/GPU/API); complete_result(dataset,previous_mtime_ns,receiptpath) checks the fresh strict result for these eight datasets. Controller must separately associate receiptcontent guard with the submitted job and record freshness. Authoritative global settlement snapshot/parser are strict175 snapshot(ledger,lock=True) and budget_audit(rows), which distinguish knownsettled, pending and unknownretainedreserve; avoid attributing arbitrary future globalappends to one block.

Hash convention: index argv_sha256/argv_file_sha256 hash argv JSONfilebytes; argv_canonical_sha256 and receipt.argv_sha256 use the legacy canonical argv digest. No preparation file or original artifact should be rewritten during controller finalization: root creates distinct final receipts/manifest, rechecks exact source/input/policy bindings and live budgets/scheduler, and completes181review before any submission.
