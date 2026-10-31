# Shared brief for ticket-implementing subagents (mechanism-datasets)

You are implementing one ticket of the mechanism-datasets feature in the `Deception-Circuit` repo. The
orchestrator gives you the ticket path. Read this whole file before starting, then the ticket, then
`Alignment/.scratch/mechanism-datasets/spec.md` (binding), then `reports/00-dataset-audit.md`.

## Implement instructions

> Implement the work described by the ticket. Use /tdd at the seams the spec names. Run single test files
> regularly and the full suite once at the end, in both environments. Once done, run /code-review against
> the branch base. Do not commit: hand the orchestrator an absolute file list to commit.

Invoke `mattpocock-skills:tdd` before writing code and `mattpocock-skills:code-review` at the end. If the
review skill cannot spawn sub-agents from where you run, do both axes (Standards, Spec) yourself and say so.

## Must-read files (in order)

1. Your ticket. Its checkboxes are the acceptance criteria.
2. `/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/spec.md`. Sections 6 (acceptance rule),
   10 (hard stops) and 11 (budget) are binding and may not be reinterpreted.
3. `/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/00-dataset-audit.md`.
4. `/projects/beto/swong2/Alignment/project_context/prompts/deception_tasks_shared.md` and the three task
   specs `deception_task_{far,sdr,ser}.md` (clause flavor rules).
5. `CONTEXT.md` in the worktree. Use its vocabulary (Scaffold, Pressure Clause, Predicate, Designation
   Polarity, Item Polarity, Template Variant, Honest Twin, Format Circuit, Behavioral Filter, Readout). Avoid
   the terms it says to avoid ("control", "template" for the Scaffold).

## Where you may work

- Code: only `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets`
  (branch `mechanism-datasets`). The session is pinned there.
- Docs: your own ticket file, `/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/`, and
  `/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/compute-ledger.json`.
- Read-only: the main checkout `/projects/beto/swong2/Alignment/Deception-Circuit` (live experiments) and
  every other worktree (`format-control`, `selective-deception`, ...). Never write there.
- Never edit v1 behaviour: `dc.SPECS`, `dataset/build_deception_dataset.py`, `dataset/pilot_deception.py`,
  `data/datasets/{far,sdr,ser}*`, `DECEPTION_TASKS`, existing task ids, anything under `outputs/` that you
  did not create. Edits to shared files (`tasks/__init__.py`, `config.py`, `evaluation/context.py`,
  `evaluation/circuits.py`, `CONTEXT.md`) are additive and minimal.
- **No git, no EnterWorktree, no worktree creation.** The orchestrator commits by explicit file list.

## Shell rules (the worktree-isolation hook enforces them)

- Literal absolute paths in every command. No `$VAR` or `$(...)` that computes a program, path or option;
  the hook refuses such commands. No `cd <elsewhere> && ...`.
- Call interpreters by path. Login base env: `/sw/external/python/anaconda3/bin/python` (py3.9,
  transformers 4.57.3). Job env mgnp: `/u/swong2/.conda/envs/mgnp/bin/python` (py3.12, transformers 5.13).
  Do not `source conda.sh` in interactive commands.
- Base-env pytest needs `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`; delete any `core.*`
  dump it leaves in the worktree.
- Run the full suite with `run_in_background` and a generous timeout; Lustre can stall IO for minutes.
- Anything that builds an OpenRouter client (clause screening, purity judge) runs under mgnp; the base
  env's openai 1.3.5 fails with a `proxies` TypeError.

## Tests

- Both suites, both envs, from the worktree root:
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python -m pytest tests -q`
  and `/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests -q`.
- Compare failures **by name** against `reports/00-baseline-failures.md` (ticket 01's first step records it on
  the branch base before any edit, both envs, names only; from a worktree expect the MASK repo-root test plus
  the 7 main-checkout names). Results differ by about one fp32 ulp across the envs; that is not a regression.
- CPU tests only: `tests/fakes.py` (`FakeWordTokenizer`, `ScriptedModel`) and the 2-layer random Llama in
  `tests/helpers.py`. Tests that need the real Llama tokenizer load it from the HF cache and skip cleanly
  when it is unavailable.

## Slurm

- No GPU on the login node. Accounts `beto-delta-gpu`, `bimc-delta-gpu`, `bgrb-delta-gpu`; compare with
  `sshare -u swong2 -o Account,FairShare` and `sbatch --test-only`. Standing permission: a PENDING job may be
  cancelled and resubmitted identically under a fresher account; log the replacement in the ledger.
- Inference (pilots, builds): `gpuA40x4`, `gpuA100x4`, `gpuA100x8`, `gpuH200x8` and their `-interactive`
  twins (1 h cap, one job per user per partition, usually start within a minute). Training: `gpuH200x8`
  (preferred) or `gpuA40x4` only; 8B training OOMs on the 40 GB A100s.
- Before every submission: run the script's CPU dry path (`--no-model`) through the actual sbatch wrapper's
  command line on the login node, then `sbatch --test-only`. Put `--account`, `--partition` and `--time` on
  the command line. `mkdir -p /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/logs`
  first and submit from the worktree root.
- Wrappers activate mgnp as `source ~/.bashrc && conda activate mgnp || { echo "Environment initialization failed" >&2; exit 1; }`
  inside a `set +u` block. A bare `source ~/.bashrc` under errexit exits silently with a blank log.
- Poll with `sacct -X -j <id> -o JobID,State,Elapsed` (squeue can transiently return nothing under load).

## Compute ledger (`compute-ledger.json`)

- Before submitting, add a reservation: `reservation_id`, `ticket`, `purpose`, `job_id` (after submit),
  `account`, `partition`, `gpus`, `time_limit`, `reserved_gpu_hours` (= time limit x GPUs), `status`,
  `submitted_at`, `output_dir`, `source_sha256` of the scripts the job runs. Check that reconciled usage +
  in-flight reservations + this one stay within your ticket's allocation and the 60 h cap; if not, stop
  and hand back.
- After the job ends: set `status`, `actual_seconds` and `actual_gpu_hours` from `sacct`, and lower
  `reserved_gpu_hours` to the actual elapsed rounded up to 0.25 h. Update the `totals` block.
- OpenRouter: one entry per batch in `openrouter_calls` (`ticket`, `purpose`, `model`, `n_calls`,
  `approx_usd`).
- Read-modify-write the file immediately before each edit and keep it valid JSON; other tickets' entries
  are never removed.

## Hard stops (hand back to the orchestrator, do not proceed)

- Any proposal to drop a mechanism or report a two-way result, a purity failure, or a mechanism still
  failing after round 3.
- Any circuit evaluation: no `evaluate_circuit.py` (not even `--dry-run`), no suites, knockouts,
  compositions or EVAL 5, no `outputs/llama-8b-instruct_sdr_coarse/_launch/postprocess.sh` (it submits
  evaluations). `outputs/_launch_format_control/postprocess_coarse.sh` (backup + mask expansion only) is
  allowed.
- A projected or actual cost beyond your ticket's allocation.

## Ticket bookkeeping and reporting

- At start set the ticket's `**Status:**` to `claimed`. Tick each checkbox as you verify it; leave unticked
  what you could not do and say why under `## Comments`.
- At the end append `## Comments`: what was built, files touched (absolute paths, as the commit list), test
  results per env with new failure names, Slurm job ids with outcomes, ledger delta, open questions for the
  researcher, and the review outcome. Write the review to `reports/<NN>-<slug>-review.md` and a longer
  narrative, if needed, to `reports/<NN>-implementer-report.md`. Set `**Status:**` to `resolved`, or leave
  `claimed` with a blocker note.
- Final message to the orchestrator: ticket status, the file list to commit, tests per env, Slurm jobs and
  verdicts, ledger usage, unresolved review findings, decisions the researcher must make. Lead with any
  hard stop.
- The orchestrator's commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Design rules for every ticket

- v2 is a side build. New names, new paths, new output dirs; nothing v1 changes behaviour.
- Every non-pressure condition is derived from the pressure prompt by clause surgery
  (`dataset/clause_surgery.py`), never by re-templating.
- One scaffold for three tasks: anything that differs between tasks beyond the predicate pair, the user
  question/stem and the clause pool is a bug.
- Thresholds in spec section 6 are pre-registered. Report numbers at other thresholds if useful; never
  decide with them.
