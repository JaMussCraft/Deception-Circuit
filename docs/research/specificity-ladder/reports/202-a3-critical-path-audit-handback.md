# Hand-back 202: A3 state and shortest credible path

Agent: Astra decision reviewer. Status: resolved as a decision audit; execution remains with root. Snapshot: November 6, 2026, 4:38 pm EST.

## What changed

Created this report and a small source/evidence index. No source, scheduler, ledger, admission, or scientific setting changed.

- Primary hand-back: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/202-a3-critical-path-audit-handback.md`.
- Identical worktree copy for the orchestrator: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/202-a3-critical-path-audit-handback.md`.
- Audit evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/a3-critical-path-audit202/audit-evidence.json`.

**Verdict for the user:** A3 has not reached its direction GPU experiment. Most recent progress is infrastructure and validation, with no A3 specificity result. Real CPU and queue costs matter, but the workflow has also become unnecessarily expensive: it expands a huge metadata graph, repeatedly authenticates it, and serializes many small implementation/review steps behind scheduler waits. Concentrate the hard work on one direction pilot, stop adding unrelated A2 work to its critical path, and measure whether the existing pilot allowance can actually accommodate the receiver before further expansion. An edge pilot is independent, but is not currently a ready shortcut.

**Actual state and scientific work remaining.** A1 is complete with a negative specificity finding. A3 direction fitting/selection/assessment on the pretrained model has not begun. The cancelled mask attempt used no GPU time; the replacement failed after 2,342 GPU-seconds without a complete timing receipt. Each retains its 0.75 GPU-hour charge, and a third mask attempt is unauthorized. This is not a scientific mask null. Edge source preparation exists, but no completed edge GPU experiment is established.

The direction metadata optimization has genuine full-output equivalence in mgnp. The original BASE reference is complete; its candidate comparison remains pending. The metadata-preallocation implementation has only Task 1 helpers in place, with corrected dual-environment validation pending; Tasks 2–4 remain. Even after code completion, fresh source-bound preparation, the nine prefit numerical cases and complete aggregation/reconciliation, measured receiver resources, paired timing feasibility, and actual root admission remain. A timing pilot is then followed by fitting, validation selection, the later selected-site pilot, and the actual three-seed direction/null/steering/control panel and power report. These are substantial remaining steps, not an imminent scientific answer.

**Why it has taken so long.** The real compute is metadata, not training: original BASE construction plus serialization took about 60 minutes, with 3,748.8 seconds child elapsed; the mgnp optimization cut total time about 25 percent but retained roughly 123 GB peak memory. Both current CPU jobs still queue. The November 4–6 usage stop also contributed. Avoidable costs include giant repeated row metadata, model loading before target construction, repeated authentication, small changes split across scheduler/review rounds, and documented wrong-directory, wrapper, transfer, timeout and test-contract mistakes. Independent review caught real defects, but its granularity and root attention split across A2/A3 have added latency. See WORKLOG and indexed source/receipts; no broad transcript reconstruction was performed.

**A specific overengineering concern.** The original oracle declares 5.916 TB of output, of which 5.882 TB is `publication_metadata`. In `derive_storage_requirements`, `identity` includes `len(captures)*1024`, and that quantity is multiplied by `captures + shards + jobs`. Thus a global capture-count allowance is charged across the publication count. This is a conservative implementation envelope, not measured output and not a lower bound imposed by the experiment. The host 1.396 TB and cache 322.5 GB are also full-target M2 envelopes, not the initial pilot's measured RAM requirement. Do a narrow actual-writer-versus-bound audit before provisioning against these numbers; do not simply lower the guard. Source inspection is enough to identify this concern, not enough to claim the entire bound can be removed.

The present preallocation design is a sensible near-term repair: it moves construction off GPU time and preserves the existing scientific workload. It still retains the large format and plans three full receiver reads, one parse/freeze, and an entry-bound final check. Those costs and JSON alias expansion need actual measurement. Replacing repeated records with a compact, authenticated recipe could preserve the science, but is a larger engineering change. Do not start that second architecture merely because it looks cleaner. Make it the explicit fallback if the measured prepared receiver cannot meet the allowance, or if the actual-writer audit demonstrates that full M2 remains impractical.

**Decisive recommendation and effort bound.** Finish accepted 183 Tasks 2–4 as designed; do not put a compact-format rewrite ahead of them. This is the shortest known route because the transport seam and scientific semantics are already reviewed, whereas a new representation would reopen reconstruction and provenance contracts. Budget one focused implementation/review cycle, on the order of hours of active engineering, rather than another multi-day architecture effort; this is a planning allowance, not a completion forecast. Queue delays and defects remain uncertain. Reconsider only if the genuine receiver measurement shows that this route cannot fit the paired allowance.

In parallel, cap the actual-writer/storage audit at 30–45 minutes of source inspection and small fixtures. It should not block Tasks 2–4 or trigger another full-target build. Trace the actual per-publication identity/completion payloads: a change is justified if they contain fixed-size references or shard-local fields while the bound charges the global capture-count allowance on every publication. Derive a conservative replacement from those exact schemas and test representative largest shapes plus scaling. If the writer really embeds global metadata, lowering the bound alone is wrong; deduplication needs a reviewed implementation change. The finding gates full M2 resource provisioning, not the present M1 preallocation repair.

**Shortest credible direction path.**

1. Consume the two already-queued results once terminal; preserve failures and existing oracles. Do not rebuild a completed baseline for another reviewer. Corrected Task 1 acceptance and BASE equality are separate branches and can proceed independently.
2. Keep one Sol implementer on Tasks 2–3, with one scoped reviewer maintaining context across them. Preserve task ownership and source pinning. Use early brief pure tests and static feedback, then one coherent dual-environment regression pass per stable integration revision where the accepted plan permits. Root can explicitly revise redundant operational checkpoints; no silent skip of required coverage.
3. Finish Task 4 closure and publish the integrated source once. Prepare final-source CPU producer/receiver measurement and fresh nine-case numerical work as independent jobs once their actual shared prerequisites exist. The native aggregate waits for its required cases; the receiver measurement waits for the real prepared target. Do not serialize independent work merely because one report number precedes another.
4. Combine genuine target production and its first receiver/profile consumer in the same suitable CPU allocation when source and receipt boundaries are fixed. Preserve separate completed artifacts and actual resource observations. This avoids an extra queue wait and duplicate production. Record warm/cache limitations and retain any required cold/new-process check. Do not run two 130 GB builders concurrently in one 192 GiB allocation.
5. Decide paired direction M1 feasibility before spending. The total is 1,800 GPU-seconds across prefit and selected pilots, including both startup/finish/proof costs; the two 90-second finish reserves alone leave 1,620 seconds. The old optimized build nearly consumed that allowance by itself, so preallocation is necessary but does not establish fit. Later selected coverage needs real fit/selection backing; it cannot be replaced by the old 63-case proofs. If measured receiver plus bounded remaining work cannot fit, present a concrete operational or cap decision promptly instead of beginning another open-ended proof chain.
6. With actual feasibility, fresh source/numerical acceptance, and root reservation/mapping/allocation checks complete, run the unchanged validation-only prefit timing experiment. Call this timing evidence. It does not answer whether a deception-specific direction exists. Proceed to the scientific panel only under its own measured admission.

**Edge alternative.** Report 117 and current `cached_pilot_stability` show that edge initial execution does not depend on the direction runtime. However, it enumerates 9,664 stability keys, with at least 9,667 guard refreshes, and the fit/select/assessment timing stages share 0.75 GPU-hours. The newer compute-host evidence in report 142 is more relevant than the obsolete 36-second refresh: even the improved source-only stability scenarios span roughly 114–185 minutes, before native attribution/loading/other costs. These are same-rate scenarios, not a portable impossibility theorem. A bounded source/count review may identify a feasible repair, but spending the whole allowance on the first pilot would leave later required timing unfunded. Do not divert the main direction implementer to an unbounded edge rewrite or launch it on the assumption that independent means ready.

**Testing and coordination.** The transport RED job took 139 seconds including dual interpreter setup and a native 6 MB fixture; first GREEN took 86 seconds through 54 passes and one bad test. Use bounded 10–30-second pure local subsets for cheap feedback, but keep the full dual-environment suite, native cases, giant comparisons and profiling on compute nodes. Consolidate stable-revision checks into available or one appropriately sized short CPU allocation where permitted; preserve exact source pins and separate receipts. Review static code while jobs queue. Reuse accepted unchanged-source oracles by hash. Terra/Luna can package and monitor; Sol implements and reviews semantics. Do not turn this Astra consultation into another standing approval gate. Let independent A2 work finish, but give the next actionable hard implementation/review slot to A3.

**CPU placement and Bridges.** Keep the queued BASE comparison intact unless a measured replacement clearly wins. Bridges currently lacks the required Python 3.9 environment. First make one short packaging/resource estimate; stage it only if transfer plus environment verification plus expected execution beats the remaining Delta wait across multiple planned jobs, especially given the reported November 9 outage. Do not spend hours porting BASE to save one comparison, substitute mgnp for BASE, or duplicate a running job. Already-staged mgnp work may use Bridges after actual cgroup/account/resource checks. The A2 cgroup fix is infrastructure, not A3 science. More CPUs will not obviously accelerate the largely Python/JSON path. Favor adequate RAM and eligible queues; preserve age and running jobs rather than repeatedly chasing forecasts.

**Decisions versus authorized fixes.** Existing scope authorizes finishing the accepted preallocation repair, focused tests/reviews, source-preserving CPU placement, paired-feasibility measurement, correct root admission, and reprioritizing implementation effort. A compact representation or tighter proved storage bound can also be an operational revision when exact science and authority guarantees are retained, but needs a concrete reviewed delta. User decisions are required for a cap change, another mask attempt, reduced controls/seeds/nulls/rows, dropping/defering a promised research arm, registered held-out scoring, or merger to main. Do not ask for generic permission to continue authorized operational work. Do not present an infeasible pilot as a reason to quietly weaken controls. If feasibility fails, give the user measured options and the exact requested change.

## How verified

Read the original START and accepted A3 plan; primary RESUME and recent WORKLOG; preallocation 175/183 and execution ledger; runtime/workload/edge source; original BASE oracle and child receipt; mgnp independent comparison; edge reviews 117, 128 and 142. The small evidence index records exact paths and hashes. No giant stream was regenerated or rehashed.

```bash
/u/swong2/.local/bin/codex-usage --pause-at 80
```

Observed: 15 percent used, 85 percent remaining, `should_pause=false`, reset November 13 at 16:18:29 UTC. Root was notified that its next session checkpoint is at 17 percent.

```bash
squeue -j 23613149,23613360 -o '%.18i %.9P %.8T %.10M %.30R'
```

Observed: both pending, reason `None`; the short job permits CPU and CPU-interactive, the BASE comparison CPU only. This audit did not independently remeasure global scheduler depth or Bridges availability.

```bash
sed -n '203,345p' /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_workload.py
```

Observed: publication-count multiplication and full-reader retention assumptions described above. Source inspection does not establish a smaller safe replacement bound.

## Execution evidence

Not applicable: no runs.

Historical execution observations are attributed to existing raw receipts, not reproduced here: BASE job `23608994`, child exit 0, 3,748.804658 seconds, full stream digest in the indexed `COMPLETE_ORACLE.json`, frozen source `861f84a3938a5e22fa329af0c469b2dd812fe68a`; mgnp original `23491516` and candidate `23605794`, accepted by review 171. These are metadata execution receipts, not scientific effect estimates. Queue and usage commands above are read-only diagnostics.

## What is NOT done

No new experiment, tests, job, source fix, reservation, authority change, remote deployment, or comprehensive re-audit of historical evidence. No promise of a launch time or full A3 completion date. The precise receiver time/RAM and paired feasibility are unknown. The compact-format alternative and lower M2 publication bound are proposed investigations, not implemented or established solutions. No scientific null is inferred from engineering failure. No git or subagents were used.

## Open questions

Root should make one immediate execution decision: prioritize completing direction preallocation and its feasibility measurement over additional A2 controller/resource expansion. Default recommendation: yes, while preserving independent running work. A narrow actual-writer/storage-bound audit can proceed in parallel without blocking the first pilot unless it reveals a shared feasibility problem. No new user approval is needed solely for these operational priorities.

If paired M1 feasibility fails, or the user prefers an exploratory GPU diagnostic with a smaller scientific scope, root must present that as a concrete new choice. Default: preserve the existing scope/caps and report the measured blocker; do not silently relabel a reduced experiment as A3 completion.
