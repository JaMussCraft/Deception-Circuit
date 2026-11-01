# Hand-back 23: independent review of the B2 P2 result, the SDR wish test

Agent: independent reviewer (Claude Opus 5.5), session claude-230e4716. Brief: the team lead's review request for job
23412228. Status: done.

## What changed

I wrote `docs/research/instructed-route/reviews/02-p2-review.md`, the verdict, five checks and a proposed F-rte-002
row. No code, results or outputs were changed. Throwaway check scripts live in the job's temporary directory only.

## How verified

I recomputed f for all 29 groups in all six cells from `knockout/groups_instances.json`, with my own clustered
bootstrap over the wish dataset's `instructed_inversion_id` and `pressure_id` columns. Every f matches the reader's
`p2_wish.json` exactly, and every interval end agrees to within 0.002. I checked ids, counts, clusters and the 20 null
quartets against their seed rule. I compared per-row margins with the dataset values to bound the A100 drift, and
checked file mtimes against the job window. `research-session lint` passes on the review and on this file.

## Execution evidence

Not applicable: no runs. CPU-only reads with the mgnp interpreter. The reviewed job's own evidence (23412228 COMPLETED
0:0, n 618, 0 unpaired, means 3.1445 and -2.9214, commit a7827d4) is in section 5 of the review.

## What is NOT done

- I did not confirm with git that `component_analysis/` is identical across a7827d4, 0ac1c17, e885200 and 384e387.
  The mtime and single-process evidence says the code that ran was fixed at 14:30:56.
- No cross-patch from the SDR D stream into the wish stream was run. Only that would show the quartet carries the same
  content for the wish and the instruction.

## Open questions

- The manifest fingerprints git per cell at write time, and hashes neither `component_analysis/` nor the task and twin
  datasets the wish cells read. The orchestrator should decide whether to file that as a manifest ticket before any
  "replicated" status.
- Whether the plan's reading ("a selector, not deception machinery") goes into the synthesis is the orchestrator's
  call. The proposed FINDINGS row leaves it out.
