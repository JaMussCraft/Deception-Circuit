# Hand-back 199-r2: Bridges cgroup diagnostic guards

Agent: worker. Status: handed-back. Scoped independent 200-r2 review is required before transfer or execution.

## What changed

Distinct diagnostic `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/preflight-r2`; manifest SHA-256 `9b538a5cedd5b26cd689edfc5ca156b82d3d172405306daf8f8e83b790efce6f`. The original preflight and its manifest `ef89c8ec44a659e73f39ce6c95c2b9557eb88c83304d0332f4a06867d1c6dc9c` remain intact, as does the original transfer inventory. The helper is included locally in the new diagnostic closure as `allocation_helper.py`, byte-identical to reviewed draft helper SHA-256 `c08c99de710a08dde1082d2954c3c535576840b911570b4665c5284520094c6f`; its proof adapter main is not called.

Cgroup scope now requires an exact numeric `job_123` or `job123` component, rejects different/prefix/nested foreign jobs, resolves actual v1/v2 controller mount roots from `/proc/self/mountinfo`, and requires the resolved counter path to be the same actual directory the unchanged 194 worker would read. Missing job scope, required peak/events or v1 failcnt/oom_control fails; no substituted peak. The host launcher uses `python3 -B` and disables bytecode. Output must be the exact normalized physical `$B/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/root-cgroup199-r2/execution`, with its pre-existing evidence parent owned by the job user, no symlink ancestors, and no existing or dangling leaf.

For root only after scoped review and exact transfer of every manifest member plus manifest, H is `/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment`, B is `$H/Deception-Circuit/.claude/worktrees/specificity-ladder`, P is `$B/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/preflight-r2`, S is `$B/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime`, and E is `$B/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/root-cgroup199-r2`. Root must create and own E with no symlink ancestry and leave E/execution absent. Test-only shape:

```bash
sbatch --test-only --parsable --account=cis260361p --partition=RM-shared --qos=rm --nodes=1 --ntasks=1 --cpus-per-task=26 --mem=48G --time=00:05:00 --no-requeue --export=ALL,CUDA_VISIBLE_DEVICES= --chdir="$S" --output="$E/job-%j.log" "$P/launch.sh" "$E/execution" 9b538a5cedd5b26cd689edfc5ca156b82d3d172405306daf8f8e83b790efce6f
```

After review, root may perform a single visibility probe using the same command with `--test-only` removed. It is not a genuine resource proof, model or GPU admission.

## How verified

Original semantics RED in `red-regressions.log`: three tests failed for substring prefix matching, lexical traversal, and lack of host `-B`. Successor `test_preflight` passed 6 tiny tests on each supported interpreter, including exact own job v1/v2, prefix/different job, missing events/failcnt, mount-root mapping, normalized/occupied/dangling/symlink output rejection, copied spool launch, and real helper import with no bytecode. Host Python files parse using Python 3.6 grammar; both shell wrappers passed `bash -n`. These are local synthetic fixtures only; no actual controller facts are asserted.

## Execution evidence

Local pure tests only: original semantics RED exited 1 with three failures; base and mgnp GREEN exited 0 with six tests each. No Slurm job, model or scientific rows. The diagnostic manifest above pins its helper and all executable scripts; no new scientific source commit is claimed.

## What is NOT done

No scheduler/SSH/transfer/RS/git action, model, graph, real cgroup probe, source/schema change or genuine proof. Actual job-scoped counters and container visibility remain unknown until root's reviewed diagnostic run. The genuine proof adapter remains separately blocked on corrected 194 deadline review.

## Open questions

Independent review should check exact job component semantics, controller mount mapping versus the frozen worker, path confinement, bytecode behavior, physical-to-virtual binds and the complete new seven-file manifest closure. Default: no probe until review and root transfer checks pass.
