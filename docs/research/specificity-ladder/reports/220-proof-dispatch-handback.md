# Held CPU proof dispatch

Status: handed-back

## What changed

Added `root-proof-dispatch220/dispatch.sh` and its fixture tests under the specificity-ladder worktree's `.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/`. The spooled Bash wrapper derives the per-job path from numeric `SLURM_JOB_ID`, checks the user-owned nonsymlink directory and resolved ancestry, validates the complete sidecar as a lowercase SHA-256 against the raw bindings bytes, checks the fixed reviewed adapter manifest, and passes those exact arguments to its unchanged launch script. Dispatch SHA-256 is `8abf86b1295addd5cd8b41f13176199fb0fcf753cf6f1c40c044a073fa05e6aa`; fixture SHA-256 is `47855038052b2ffc3f14365df70858fac1e1cd6493ee69c756dbca6d90076afe`.

The frozen adapter confines output to `root-genuine-proof-r2`; the coordinator ruled that this existing operational namespace must be used for the fresh job directory, while the pinned manifest identifies the r3 adapter. No frozen packet was changed.

## How verified

The positive spool regression first failed against an empty dispatch implementation. Nine local fixture tests then passed on each of base Python 3.9 and mgnp, including exact arguments, missing and partial leaves, incorrect and split digests, job ID rejection, symlinked leaves and ancestry, and wrong manifest. `bash -n` passed. Python 3.6 was unavailable locally; the dispatch is Bash and the test source uses Python 3.6-compatible syntax.

## Execution evidence

No scheduler, remote system, container, GPU, model or proof was run. The checked adapter manifest is `4e4b4bcf1ddcd6481fac1eccd966a2a1cbfa385b2bd16a9a00504cfaa05def3f`. The fixtures substitute only their temporary physical root and fixture manifest pin when exercising the spooled script; they do not establish actual host behavior.

## What is NOT done

Independent review, held-job submission, sealing the actual per-job bindings and release remain with the coordinator. The sidecar must be created from the actual root-authorized bindings after the real job ID is known; a computed current digest alone is not an independent authority.

## Open questions

Actual host operation and allocation remain untested. The reviewed adapter must enforce its own packet, binding contents and allocation checks after dispatch.
