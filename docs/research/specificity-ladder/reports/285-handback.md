# Hand-back 285: Actual A2 local CPU timing review

Agent: independent result reviewer, gpt-6.1-sol. Ticket: actual timing diagnostic 23624978. Status: resolved for local timing facts only.

## What changed

**Verdict: ACCEPT LOCAL COMPONENT TIMING FACTS ONLY.** No blocking inconsistency was found in the measured evidence. Operational feasibility remains undetermined, exactly as `operational_feasible: null` and `LOCAL_COMPONENTS_MEASURED_ONLY` state. This verdict grants no GPU admission, automatic retry or synthetic-marker authority.

Only `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-timing-result-review285/check_evidence.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-timing-result-review285/checks.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/285-handback.md` were written. No source, state, job, remote or Git action occurred. No author narrative was used. Root should run handback lint centrally; this worker was prohibited from RS commands.

Accepted observations:

| Stage | Distinct child PID | Child internal wall, seconds | Parent pipeline through evidence, seconds | Child process peak RSS, bytes |
| --- | --- | --- | --- | --- |
| Prime | 3649297 | 212.391776 | 221.204894 | 1949282304 |
| Fresh | 3652266 | 186.876922 | 193.165566 | 1955831808 |

Both child processes exited zero without TERM, before their original deadlines. Fresh completed the measured pipeline within the 240-second cap. Each reconstructed exactly 59,652 unique domain rows and 3,396 positive-control keys, matching the genuine shape proof, including support/reason mask `73002c8b74d13947aeb9bf1f6e09d50544b549ea51ab00a50b9510bd6404ffd8`. This is data-domain reconstruction and authentication, not scoring rows or numerical/model execution. Native bank and tokenizer/context validation ran; no model loaded, freeze executed or GPU admitted.

Scope/source evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/data_path.py:8` calls the unchanged Task 2 helpers, compares G2/G3 science fields, validates the authentic bank payload and native numeric environment, reconstructs the whole domain and rechecks live source/protection context. `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-operational186/candidate/cpu/validate-phase.py:184` requires exact row/control set equality and the complete support/reason mask, so unsupported diagnostic rows and controls are not silently dropped. Both actual child observations record source `50e947bb852613e3a270082651f2bd1b7bb0c525`, module origins entirely inside its frozen runtime, equal before/after source/input/G3/bank/catalogue identities and four exact saved catalogue captures. The job/packet-bound current witness matches those captures. Its remote catalogue entries are historical readbacks, never continuous Delta truth.

Clock interpretation: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/runner.py:181` starts the pipeline clock before allocation lookup, output setup, parent pin checks, parameters and process launch. It includes the new interpreter, native data path, child serialization/exit and the parent's independent source/input/catalogue/bank checks, final allocation checks, metrics and pipeline-evidence write through `:230`. The child clock starts inside `main` after top-level imports and ends before its final guard/serialization; it is not the full path. The larger parent observation is the accepted component timing. The recorded wall fields use monotonic seconds; Unix timestamps separately enforce original, only-shortenable deadlines. The tiny through-evidence increment is retained in the report, while `pipeline-observation.json` stores the earlier pre-write wall value.

Local publication took 0.394136 seconds, measured from before allocation re-observation through local serialize/readback, packet recheck and exclusive hard-link publication (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/runner.py:256`). It is local diagnostic evidence publication, not a GPU release. The report's approximately 417.10-second runner total excludes batch/bootstrap overhead outside `main` and precedes final report serialization/check; the accounting duration is 428 seconds. Those clocks need not coincide.

Memory/CPU interpretation: child RSS uses Linux `ru_maxrss * 1024`, in bytes, for that child process's lifetime. The cgroup path labelled process is actually the batch task cgroup shared with the parent/children, not isolated child RSS; the distinct job ancestor is the aggregate job scope. Final observed job peak was 3,092,062,208 bytes, current 1,502,920,704 bytes, with a 34,359,738,368-byte job limit and zero recorded OOM events. These are observed cumulative peaks/snapshots, not prospective resource bounds. Pipeline child CPU fields are deltas of parent `RUSAGE_CHILDREN`, which can include its other reaped subprocesses; internal child CPU fields provide the narrower process observation. CPU seconds are not interchangeable with elapsed wall seconds.

The arithmetic 193.165566 + proposed 45 = 238.165566 seconds, leaving 61.834434 seconds of a hypothetical 300-second window, is orientation only. One primed-followed-by-fresh pair cannot attribute the difference solely to cache effects or establish future tail latency.

## How verified

Read actual code, job/config/witness pins, child and parent observations, metrics, catalogue snapshots, local-publication evidence and terminal accounting inventory directly. Accepted Task 2 fixture results were retained as dependencies; no suite was rerun.

```bash
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-timing-result-review285/check_evidence.py
```

Observed exit zero in approximately 1.25 seconds: all 34 sealed actual files matched byte counts/hashes; all 577 packet members matched hashes; supplied manifest/config digests matched; distinct PIDs, normal exits, deadline ordering, full counts, pinned import origins, four catalogue snapshots per stage, immutable before/after identities and orientation arithmetic passed. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-timing-result-review285/checks.json`.

## Execution evidence

- Job and cluster: 23624978 on Delta, cn099, four CPUs, 32 GiB, fifteen-minute allocation.
- Exit/state: terminal inventory records COMPLETED, 0:0, elapsed 428 seconds; both child observations and empty logs support normal completion. Final parent allocation still observes the same running job/resources, with zero requeues/restarts.
- Row counts: both observed 59,652 reconstructed against 59,652 expected domain rows, and 3,396 reconstructed against 3,396 expected positive controls.
- Baseline comparison: prime and fresh independently match the same 59,652-row / 3,396-control reference; no scientific baseline accuracy, scoring result or replication is claimed.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/root-deployment261/terminal-evidence285/root-terminal-inventory.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/root-deployment261/execution/DIAGNOSTIC-REPORT.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/root-deployment261/execution/prime/child-observation.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/root-deployment261/execution/fresh/child-observation.json`; source commit `50e947bb852613e3a270082651f2bd1b7bb0c525`. This diagnostic has no new scientific `run_manifest.json`; source/config/packet identities are carried by those sealed artifacts. Packet manifest digest is `c43d084973d38dbb2367b269879f23cc2d42383784f65d9abde937d4232573e6`, config digest `77457adc29fb92488a79c215e0a16c9755ff97c9dcca37dc71afb80cccc31ebc`.

## What is NOT done

No request-acquisition or cross-cluster transfer timing, real GPU WAITING/READY/COMPLETE exchange, remote root publication, GPU identity observation, score execution or operational feasibility proof. Historical H100 bank provenance in the observations belongs to bank job 50189932; it is not a GPU assigned to this CPU diagnostic. No other active validation job is covered by this review.

Root's next gate is an independently reviewed, bounded measurement/feasibility closure for the complete actual request-to-publication path: request acquisition, local owning proof production and supervision, current stable captures/native ledger closure, transfer and remote readback/cache/source/allocation rechecks, final usage/protection checks and once-only publication. Use actual resource/source/job bindings and the minimum original/current deadline, account for variability and all margins, retain failed evidence, and preserve every operational/GPU admission gate. The unused orientation headroom cannot substitute for those missing costs.

## Open questions

No question blocks accepting the local timing observations. Default: retain them as measured inputs to the remaining feasibility review; keep operational admission closed and do not authorize a retry from this diagnostic.
