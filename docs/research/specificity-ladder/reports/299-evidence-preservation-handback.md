# Hand-back 299: Completed evidence preservation inventory

Agent: Terra inventory worker. Status: handed-back.

## What changed

Created `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-evidence-preservation299/inventory.json`. Its 410 regular files total 8,453,270 bytes and each has an absolute source, unique proposed relative destination, byte count, SHA-256 and role. It includes the 36 receipt-listed files for each Bridges job, 34 receipt-listed timing files, 12 terminal files for each Task 3 run and their Slurm logs, deployment/control files, named correction and review packets, source files and review hand-backs.

## How verified

Compared the local A3 and timing artifacts against their receipt byte counts and hashes: no missing files or mismatches. All proposed destinations are unique. Task 3 terminal files were listed directly from each run's top level; the accepted run's receipt is also included. No temporary fixture directories were traversed. The inventory's missing and mismatch lists are empty for the selected files.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No evidence was copied or committed. Shallow named-packet inventories are not a complete frozen source export or proof that every transitive scientific input is included; the manifest explicitly records this limitation. In particular, candidate287's full tree and Task 3's full closure are not inventoried wholesale. The orchestrator must assess any additional source closure needed for the intended preservation scope before copying.

## Open questions

- Whether complete source exports or only the named correction files and controls are required for durable reproduction remains for root to decide. Default: preserve the selected evidence and extend the explicit manifest if a full closure is required.
