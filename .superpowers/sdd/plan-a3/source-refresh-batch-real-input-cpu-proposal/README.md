# Fresh batching successor: Slurm CPU preparation proposal

Status: handed-back proposal only; not submitted or executed. The reserved results handback follows actual execution after root submission.

## What changed

External operational harness only, bound to immutable commit `40fe57289405fd53a3fce02e5d4e47a0ebf78b64`. No runtime source, old artifacts, science, registry, scheduler, RS or job changes. New output will be `W/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-40fe57289405`, created by the CPU job only. Existing/partial output causes a stop; there is no automatic retry or re-signing.

## How verified

Proposal Python syntax is compiled in memory and shell syntax checked only. No producer, validator, source context, test or timing is executed on login. Final file hashes are in `proposal-manifest.json`; `config.json` pins runtime/snapshot/output and original inputs. Root's external CPU-only release must bind that manifest and exact source/output, confirming independent134 acceptance. This is coordination only and grants no model, reservation or execution authority.

The original earlier successful sequence totaled 1341.568 seconds, approximately 22m22s. [Timing basis](duration-basis.json) records every phase; [resource configuration](config.json) records the exact limits. Actual f5 compute job `23454781` took 156 seconds for the source comparison, versus the earlier 152.792-second benchmark step; no compute-node speedup is assumed. Request 35 minutes, four CPUs, 32 GiB on `beto-delta-cpu/cpu`, constraint `projects`, zero GPUs. All work is serial and thread-limited. The internal deadline is 2010 seconds with 90 seconds left for cleanup. This allows roughly twelve minutes above the prior successful sequence for initial/final bindings, oracle/audit agreement and two copied-input negative contexts. Filesystem/cache variability can still cause a timeout; preserve partial evidence and stop. No coverage is reduced to meet the queue window.

## Execution evidence

The exact phase commands are in `commands.json`, in this order:

- Actual canonical directions prepare/freeze with the original A1 design/selected/mandatory sidecar, matched build, history, unchanged ruling and settings.
- Actual new-source mask settings publisher, mask prepare/freeze and complete pilot/full inventories through the frozen wrapper.
- Actual edge prepare through the frozen wrapper, followed by owning full-fit-target and pilot inventory producers. Both complete owning inventory validators remain.
- Both nonauthorizing wrapper pilot dry-runs, full owner artifact/inventory validation, original scientific row/utility/assessment equivalence, source/input bindings.
- Each owner's real cold context plus three clean full-byte refreshes, CPU/wall/peak/retained/transient RAM and actual consumed startup/host fields. Real Slurm environment/job/node/account/resources are retained. Model lease/reservation hooks remain unchanged and unexercised because this is source-only CPU work.
- Outside clean timings: original oracle and batch full rows/order agreement on the same new inputs, plus one audited fresh guard proving every original complete file occurrence was read. No reader or guard is monkeypatched. New file sizes need not equal f5.
- Separate byte-identical copies of each newly prepared owner artifact. Add an empty supplemental explicit registry while retaining every original default/explicit registry; mint genuine context, then prove real current protected overlap rejects, safe atomic reset revalidates, and changed copied prepared bytes reject. Originals/catalogs remain untouched; no checksum marker is re-signed.
- Observational comparison against hash-bound f5 CPU job `23454781` raw results. Nodes, accounts and caches may differ; cache control and causal speedup attribution remain false. Final source/static-input/artifact hashes and actual CPU allocation are published.

Two operational adaptations to122 are explicit: job/node/allocation fields are actual Slurm CPU provenance; historical catalog hashes in scientific metadata are treated as recorded provenance while actual current owner protection/grader validators remain mandatory. Unrelated legitimate catalog updates do not freeze parent directory timestamps or rewrite scientific bytes. The script only changes copied negative artifacts and its new output.

Root submission command (not executed by this proposal):

```bash
A3_CPU_PREPARATION_RELEASE=/absolute/root-written-release.json sbatch --parsable --export=ALL --account=beto-delta-cpu --partition=cpu --constraint=projects --ntasks=1 --cpus-per-task=4 --mem=32G --time=00:35:00 --job-name=lad-a3-batch-prep --chdir=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder --output=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/source-refresh-batch-real-input-cpu-proposal/logs/slurm-%j.out /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/source-refresh-batch-real-input-cpu-proposal/cpu-preparation.sh
```

Root copies `cpu-release.template.json` to an external path, sets the actual proposal-manifest hash and accepted CPU-only review flags, then submits. No release fields may authorize model work. No Slurm variable is fabricated, erased or overwritten. Allocation checks require a genuine RUNNING beto CPU job on its allocated node with no GPU TRES. Source-only observers additionally require no CUDA device.

## What is NOT done

No submission, preparation, local heavy validation, test, source/data mutation, model/large weights, GPU, scientific pilot, reservation/ledger/cap exception, remote/API/notebook/subagent or production code change. Source-frozen numeric/scientific metadata remains H200 as originally specified; CPU host diagnostics record the real CPU separately.

## Open questions

Root reviews exact hashes/resources and owns submission/accounting. The original pinned offline `/work/nvme/beto/swong2/hub` cache must be accessible on the allocated node; a cache or genuine source/protection rejection stops without a workaround. Complete outputs, observed timings and independent readiness remain future evidence; no performance/admission claim follows from this proposal. Root's parallel native CPU case may share cluster/storage load; the comparison remains observational with actual node/resource provenance.
