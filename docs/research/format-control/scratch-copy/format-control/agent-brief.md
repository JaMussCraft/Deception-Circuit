# Shared brief for ticket-implementing subagents (format-control)

You are implementing one ticket of the format-control feature in the
`Deception-Circuit` repo. The orchestrator tells you the ticket path, the
worktree path and the branch. Read this whole file before starting.

## Implement instructions

> Implement the work described by the ticket. Use /tdd at the seams the spec
> names. Run single test files regularly and the full suite once at the end,
> in both environments. Once done, run /code-review against the branch base.
> Commit your work to the current branch.

Invoke `mattpocock-skills:tdd` before writing code and
`mattpocock-skills:code-review` at the end. If the review skill cannot spawn
sub-agents from where you run, do both axes (Standards, Spec) yourself and say
so in the report.

## Must-read files (in this order)

1. The ticket file. Its checkboxes are the acceptance criteria.
2. `Alignment/.scratch/format-control/spec.md` (Pre-registered outcomes,
   Implementation Decisions and Testing Decisions are binding).
3. `Deception-Circuit/CONTEXT.md`: task-structure terms (Scaffold, Pressure
   Clause, Honest Twin, Honest Condition, Readout, Corruption, Behavioral
   Filter). Use that vocabulary in code, tests and docs; do not use the terms
   it says to avoid ("control" is one of them: the thing you build is the
   Format Circuit and the `nopressure` condition).
4. Prior art named in the spec's Testing Decisions.

## Where you may work

- Only inside the worktree the orchestrator gives you
  (`Deception-Circuit/.claude/worktrees/format-control`, branch
  `format-control`, cut from the main checkout's current HEAD), plus the
  ticket file and `Alignment/.scratch/format-control/reports/`.
- Never edit the main checkout at `Alignment/Deception-Circuit` (the
  researcher runs live experiments there; a coarse SDR seed-stability wave is
  in flight) or any other worktree. Do not touch the `component-analysis`
  branch or worktree.
- Commit to the current branch. Do not push, rebase or merge.
- Commit messages: imperative subject that says why, ending with
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Data and run directories (main checkout, read-only for you)

| handle | path |
| --- | --- |
| FAR D (fine nls0.3) | `outputs/llama-8b-instruct_far/nls0.3_noedge_260819-083914` |
| FAR H | `outputs/llama-8b-instruct_far/nls0.3_honest_noedge_260819-084020` |
| SDR D (fine nls0.3) | `outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414` |
| SDR H | `outputs/llama-8b-instruct_sdr/nls0.3_honest_noedge_260819-083525` |
| SDR coarse heads-only D | `outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742` |
| SDR coarse heads-only H | `outputs/llama-8b-instruct_sdr_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_260922-092743` |
| datasets | `data/datasets/{far,far_honest,sdr,sdr_honest}` (arrow DatasetDict, tracked) |
| coarse recipes | `outputs/llama-8b-instruct_sdr_coarse/_launch/{submit_train.sh,submit_headsko.sh,submit_eval5.sh,postprocess.sh}` |
| cross-task launch | `outputs/_suites/_launch_260922/{cell_cmd.sh,submit.sh,merge_shards.py,write_suite_summary.py}` |
| eval 5 settings | `outputs/_eval5_launch/eval5_args.sh` |

`outputs/` is untracked: reference these by absolute path into
`/projects/beto/swong2/Alignment/Deception-Circuit/...`; never copy large files
into the worktree. New datasets and outputs you produce go under the worktree's
own `data/datasets/` and `outputs/`.

## Environments and scheduling

Identical to `Alignment/.scratch/component-analysis/agent-brief.md`, section
"Environments (two, both matter)": login base (python 3.9, transformers
4.57.3) and `mgnp` (python 3.12, transformers 5.13); activate mgnp with
`source /sw/external/python/anaconda3/etc/profile.d/conda.sh && conda activate mgnp`;
run the base suite with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`;
record baseline failing test names on the branch base in both envs and judge
"no new failures" by name.

Slurm: no GPU on the login node. Any account (`beto-delta-gpu`,
`bimc-delta-gpu`, `bgrb-delta-gpu`) and any partition (`gpuA40x4`,
`gpuA100x4`, `gpuA100x8`, `gpuH200x8`) is allowed; pick by queue length and
fairshare (`sbatch --test-only`, `sprio`). No job-length cap. Always
`--dry-run` on the login node first; put `--time` on the command line; submit
from the worktree root; poll `squeue -u $USER` in the background. Lustre can
hang git for minutes: run git and the suites in the background with timeouts
and delete any `core.*` dump.

## Ticket bookkeeping

- At start: set `**Status:**` to `claimed`.
- Tick each checkbox as you verify it; leave unticked what you could not do and
  say why under `## Comments`.
- At the end: append `## Comments` with what was built, files touched, test
  results per env (counts plus new failure names), Slurm job ids and what their
  outputs showed, open questions for the researcher, and the review outcome.
  Write the review to `reports/<NN>-<slug>-review.md`. Then set `**Status:**`
  to `resolved`, or leave `claimed` with a blocker note.

## Design rules for every ticket

- The Format Circuit is the `nopressure` condition of a mechanism task; it is
  not a new task. Everything that already works for `honest` must work for
  `nopressure` with no special casing.
- Prompts for the `nopressure` and `honest_instruction` conditions are derived
  from the stored prompt string by clause surgery, never by re-templating
  through `dc.SPECS`. Predicate words come from each record's `desig` /
  `desig_inv`.
- Keep changes to shared files (`train.py`, `tasks/deception.py`,
  `evaluation/variants.py`, `evaluation/circuits.py`, the sbatch scripts)
  minimal and additive; tickets 03 to 06 may run in parallel on sibling
  branches.
- Nothing from EVAL 5 is launched without the researcher's explicit go-ahead.

## Final report to the orchestrator

Ticket status, commits (hash and subject), test results per env with new
failure names, Slurm jobs and verdicts, shared files changed, unresolved review
findings, decisions the researcher must make.

## Researcher decisions so far

- 2026-10-13 (grilling): no-pressure is the primary format condition, honest
  instruction is evaluation-only; honest labels with a both-streams filter and
  an argmax flip; threshold steps 0.7 / 0.5 / 0.3 to reach 150 train and 500
  test, floor 0.3; strict pairing by instance id with the deceptive splits,
  honest-split instances only as a tagged fallback subset; FAR and SDR now,
  SER deferred; pair with fine nls0.3 (FAR, SDR) and coarse heads-only nls0.3
  (SDR); same NLS, one retune step of 0.1 if sizes differ by more than 25
  percent; full 3 by 3 faithfulness, knockouts, overlap and the deltas D-F,
  D&F, F-D, xor(D,H,F) at both granularities for fine (head primary), head
  only for coarse; eval 2 gate (wikitext KL <= 0.66) before eval 5; eval 5
  needs explicit permission; grader caveats stay; any account or partition
  for speed; six tickets implemented in a fresh session.
