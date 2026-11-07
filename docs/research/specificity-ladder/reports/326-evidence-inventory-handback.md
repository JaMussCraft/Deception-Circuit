# Evidence preservation inventory hand-back

Status: handed-back

## What changed

Created `.superpowers/sdd/plan-evidence-preservation326/inventory.json` in the specificity-ladder worktree. It lists 356 files, 7,666,114 bytes, with source, destination relative to `reports/cpu-evidence-326`, SHA-256 and size. It includes the requested completed job receipts, source and control evidence, reviews, receiver constraints and selected root helpers.

## How verified

The inventory was generated from selected named directories and each included regular file was read and hashed. No scientific acceptance is asserted.

## Execution evidence

The manifest records the exact sources and hashes. The original sandbox command runner failed to launch; scoped escalated commands allowed the read and manifest write.

## What is NOT done

No files were copied and no Git, jobs, tests, SSH or RS commands were run. Excluded candidate source export and isolated index, temporary fixture trees, large scientific inputs, producer source-tree and live producer output, and deployment324 run-01 and its potentially live Slurm log. Producer monitor snapshots were also omitted.

## Open questions

The orchestrator should recheck hashes when copying and assess whether any new terminal evidence has appeared since this inventory. Receiver constraints are included without claiming receiver placement or acceptance.
