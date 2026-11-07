# Hand-back 199-r3: Bridges real cgroup bind diagnostic

Agent: worker. Status: handed-back. Independent review is required before a new diagnostic.

## What changed

New diagnostic `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/preflight-r3`; manifest SHA-256 `4a096d2c1eb020da99853959a3c26e4948a9c240618958accea0b80e553997d5`. Original r2 manifest `9b538a5cedd5b26cd689edfc5ca156b82d3d172405306daf8f8e83b790efce6f` and all its members remain intact. Its allocation helper is byte-identical. Exact job-component, normalized fixed evidence-root and no-bytecode protections are retained.

The host first records and requires real job-scoped, readable counters, then chooses an explicit read-only bind of the actual controller: v1 `/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro`, or v2 `/sys/fs/cgroup:/sys/fs/cgroup:ro`. The container uses the same worker path, actual membership and mount mapping; it requires `samefile` agreement with the frozen worker's fixed path and real counters. No counter is copied or synthesized. The collector now emits memory-controller membership lines, relevant cgroup mount lines and per-candidate errors even when mount resolution or file reads fail. No general environment or arbitrary mountinfo dump is added. A future genuine adapter must use the same reviewed real read-only controller bind and still pass the unchanged worker's own job/counter guards.

The actual failed 50309188 host evidence showed v1 membership `/slurm/uid_105853/job_50309188/step_batch/task_0` and readable peak/failcnt/oom_control at the matching real host path. The r2 contained process exited 1 with `actual cgroup memory mount unavailable` and emitted no JSON; overall job was reported failed `2:0`. Its observed command contained no cgroup bind. This supports testing the explicit bind; it does not prove the next contained run can mount or read it. All old evidence is preserved.

For root after review and transfer, set H to `/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment`, B to `$H/Deception-Circuit/.claude/worktrees/specificity-ladder`, P to `$B/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/preflight-r3`, S to `$B/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime`, and E to `$B/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/root-cgroup199-r3`. E must be pre-created and owned by the job user without symlink ancestors, and E/execution must not exist. Root-only test shape:

```bash
sbatch --test-only --parsable --account=cis260361p --partition=RM-shared --qos=rm --nodes=1 --ntasks=1 --cpus-per-task=26 --mem=48G --time=00:05:00 --no-requeue --export=ALL,CUDA_VISIBLE_DEVICES= --chdir="$S" --output="$E/job-%j.log" "$P/launch.sh" "$E/execution" 4a096d2c1eb020da99853959a3c26e4948a9c240618958accea0b80e553997d5
```

After review root may use the same arguments without `--test-only` for one deliberate diagnostic. The output is visibility evidence only; the blocked genuine proof needs its separate corrected supervisor and review.

## How verified

A semantic RED using the unmodified r2 collector produced the same missing-mount assertion before returning membership evidence; raw `red-observation.log` is preserved. After the fix, `test_preflight test_bind_failures` passed 9 tiny tests under each supported interpreter, including actual read-only bind argument construction, v1/v2 paths, missing mount evidence, membership, missing counters, confinement and spool/no-bytecode protections. Host files parse with Python 3.6 grammar; wrappers pass `bash -n`. No real controller or host was probed by these tests.

## Execution evidence

Local synthetic tests only: semantic RED exited 1 and both GREEN suites exited 0, 9 tests each. Existing real job 50309188 was reported failed with exit `2:0`; its preserved host/container observations are described above. No new job, graph, model, scientific rows or baseline. Manifest above pins this diagnostic, not a scientific source change.

## What is NOT done

No remote call, transfer, scheduler action, new job, RS/git, model, effects, or 194 worker/schema change. The proposed bind has not been proven on Bridges. Zero is never substituted for absent counters. No scientific/resource proof or full-score admission is asserted.

## Open questions

Independent review must check bind scope, diagnostic error capture, path matching, actual allocation and closure. Default: do not launch until reviewed and staged; if the container still cannot mount/read the controller, preserve the new structured failure and stop for a fresh ruling.
