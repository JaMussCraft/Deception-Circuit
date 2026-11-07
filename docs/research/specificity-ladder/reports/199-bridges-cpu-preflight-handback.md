# Hand-back 199: Bridges CPU visibility preflight and inventory

Agent: worker. Status: handed-back. Preflight requires independent review; the genuine proof adapter is blocked pending the reviewed corrected 194 successor.

## What changed

Directory `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199` preserves root's existing `bridges-cpu-forecast-01.json`. New `preflight/` manifest SHA-256 `ef89c8ec44a659e73f39ce6c95c2b9557eb88c83304d0332f4a06867d1c6dc9c`; `transfer-inventory.json` SHA-256 `f5634973c7be281dbb9ad6f6d571d2cea08c8a4c3f9730bfacd8f13e149db38a`. Draft `proof-adapter/` manifest is `c867593c4db71c741a1f5404d89cb6086f4d3c95a9b0759328513f9ba3d433` and is **not authorized for a genuine run**: it carries the inherited `finished <= deadline` equality and does not tighten after reap to the fresh end time. Root requires a separately reviewed corrected 194 successor before any proof launch; this draft must be revised or replaced after that review.

The inventory enumerates 511 source file hashes, 422 ordinary input paths/bytes/hashes, all 11 namespace aliases (including the original four source links), 20 fixed 194 input pins including report187, four mutable current protection catalogues, 15 new packet files, and existing SIF/packed interpreter/cache references. Entries distinguish historical staging evidence from new transfer or required fresh remote verification. No current remote existence is asserted. Root must transfer exact missing new/fixed inputs, refresh all four catalogues and recheck the old closure and literal aliases. No credentials, weights or agent metadata are proposed for copying.

The separately labeled preflight captures actual host Slurm allocation and actual host and contained-process `/proc/self/cgroup` membership and readable memory counters. It uses the proposed same physical-to-virtual project bind, `/ocean` read-only bind, HF cache bind, SIF, 26-CPU/48-GiB environment, Bridges activation and one-thread settings; it builds no graph and loads no model. Frozen `proof_worker.py:cgroup()` recognizes v2 `memory.current`, `memory.peak`, `memory.events` and v1 `memory.usage_in_bytes`, `memory.max_usage_in_bytes`, `memory.failcnt`, `memory.oom_control`. It requires the actual job ID in the cgroup path and a readable job-scoped peak; it compares v2 OOM/kill events or v1 failcnt across the run. The preflight conservatively requires the v2 peak plus events or v1 peak plus failcnt and oom_control to be readable. Missing actual information fails; no proxy or inferred peak is substituted.

For root only, after exact preflight review and transfer, set H to `/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment`, B to `$H/Deception-Circuit/.claude/worktrees/specificity-ladder`, P to `$B/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/preflight`, S to `$B/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime`, and E to a fresh physical output parent under B. Root's test-only shape is:

```bash
sbatch --test-only --parsable --account=cis260361p --partition=RM-shared --qos=rm --nodes=1 --ntasks=1 --cpus-per-task=26 --mem=48G --time=00:05:00 --no-requeue --export=ALL,CUDA_VISIBLE_DEVICES= --chdir="$S" --output="$E/job-%j.log" "$P/launch.sh" "$E/execution" ef89c8ec44a659e73f39ce6c95c2b9557eb88c83304d0332f4a06867d1c6dc9c
```

The physical scheduler WorkDir is checked separately from the container's virtual cwd. Root may use the same reviewed arguments without `--test-only` for a single short visibility probe; `$E/execution` must not exist. The probe's exit 2 or missing counter is a visibility failure, not a scientific proof or a reason to patch the worker. No proof admission follows automatically.

## How verified

`proof_worker.py`, `proof_schema.py`, `proof_guards.py`, `input-pins.json` and `native-schema-contract.json` were byte-compared against immutable 194 manifest `6c6bed2a3738846f008daa42454eac104ba4bfc43f3765aa41da9c47ac584f70`. Host allocation and container path fakes passed four tiny tests on both base and mgnp. These test actual acceptance/rejection logic and path mapping, not the Bridges scheduler or container. Host Python files parse with Python 3.6 grammar; all four shell wrappers passed `bash -n`. Packet manifests rehash. Initial RED was missing adapter module setup, not a behavioral regression.

## Execution evidence

Local tiny tests only: four per interpreter exited 0. No actual Bridges preflight, job, real cgroup, graph, model or scientific proof ran. No scientific rows or baseline claimed. The immutable scientific source is commit `50e947bb852613e3a270082651f2bd1b7bb0c525`; preflight and inventory are pinned above.

## What is NOT done

No SSH, transfer, scheduler call, submission, RS, git, source edit, effect read or model. Current remote bytes and real container cgroup visibility remain unverified. The draft proof supervisor has the two noted deadline blockers and must not be run. No host/memory/timing/storage acceptance is established.

## Open questions

Independent reviewer should examine the preflight bindings, real Slurm fact checks, host and container counter paths, manifest closure and exact inventory before root runs it. Root must separately obtain and review the corrected 194 successor; default is no genuine proof launch until both the corrected deadline contract and real job-scoped cgroup visibility pass.
