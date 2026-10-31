# Shared brief for ticket-implementing subagents (mechanism-analysis)

You are implementing one ticket of the mechanism-analysis feature in the `Deception-Circuit` repo. The orchestrator
gives you the ticket path. Read this whole file first, then the ticket, then
`/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/spec.md` (binding), then
`reports/00-plan-handback.md` (verified facts with file:line evidence) and `reports/00-plan-review.md` (why the
rules are built the way they are).

Tickets: 01 infrastructure; 02a v2 component analysis for phase 1; 02b neutral twin in attention and path patching,
criteria amendment; 03 phase 1; 04 phase 2; 05 phase 3; 06 synthesis; 07 seeds (conditional, R5); 08 the
instructed-inversion control condition.

## Implement instructions

> Implement the work described by the ticket. Use /tdd at the seams the spec names. Run single test files regularly
> and the full suite once at the end, in both environments. Once done, run /code-review against the branch base. Do
> not commit: hand the orchestrator an absolute file list to commit.

Invoke `mattpocock-skills:tdd` before writing code and `mattpocock-skills:code-review` at the end. If the review
skill cannot spawn sub-agents from where you run, do both axes (Standards, Spec) yourself and say so. Tickets that
only run jobs and read results (03-07) still review their result scripts and readings.

## Must-read files (in order)

1. Your ticket. Its checkboxes are the acceptance criteria.
2. `spec.md`. Binding and not to be reinterpreted: §2 (pre-registered rules and predictions), §5 (phase order and
   the phase gate), §6 (budget and records), §9 (rulings R0-R17).
3. `reports/00-plan-handback.md`, then `reports/00-plan-review.md`.
4. In the worktree:
   - `CONTEXT.md`. Use its vocabulary: Scaffold, Pressure Clause, Predicate, Designation Polarity, Item Polarity,
     Template Variant, Honest Twin, Neutral-Clause Twin, Format Circuit, Readout, Component, Segment, Component
     Role, Positive Control, Comparison Set, Contingent Survivor. Avoid the terms it says to avoid: "control" for the
     Honest Condition, "template" for the Scaffold. In this feature "the inversion control condition" names
     `<t>_v2_inversion` only.
   - `docs/component-roles.md` and ADR-0001 / ADR-0002. Read the sign conventions before reading any number.
   - `docs/bridges2.md`.
5. The prior cell of record: `outputs/_analyses/sdr-dh-core/dh_core__leaf/sdr/result_summary.md` in the main
   checkout. It shows the command shape, checks and write-up style.
6. mechanism-datasets readings: `/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/06-*.md`.

## Where you may work

- Code: only `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis` (branch
  `mechanism-analysis`).
- Docs: your own ticket file, `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports/`,
  `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/compute-ledger.json` (under its lock), and, in the
  worktree, `docs/research/mechanism-analysis/` (curated records, R6).
- Read-only:
  - the main checkout `/projects/beto/swong2/Alignment/Deception-Circuit` (live experiments, the v1 cells of
    record under `outputs/_analyses/`);
  - every other worktree (`mechanism-datasets`, `selective-*`, ...);
  - every existing output.
- Never edit:
  - the existing v2 datasets (`data/datasets/<t>_v2`, `_v2_honest`, `_v2_nopressure`, `comparison_set_v2.json`) or
    their provenance-pinned builders (`build_deception_v2.py`, `deception_v2.py`, `clause_surgery.py`,
    `contingency.py`; `tests/test_v2_reproducibility.py` fails by design if you do). Ticket 08 imports them and
    writes the new `<t>_v2_inversion` condition beside them;
  - v1 behaviour (`dc.SPECS`, `DECEPTION_TASKS`, v1 segmentation);
  - any output you did not create.
  Edits to shared files (`component_analysis/*`, `analyze_components.py`, `evaluation/*`, `scripts/remote/b2.sh`,
  `scripts/*.sbatch`, `scripts/cluster/*.env`, `CONTEXT.md`) are additive and minimal, and keep v1 behaviour
  byte-identical, tested.
- `docs/component-roles.md` is edited only by ticket 02b, with the v2 amendment of R1 and R7: the text goes first
  into `reports/02b-criteria-amendment.md`; the orchestrator reports it to the user (R10); after the orchestrator's
  go, 02b writes it into the doc as a dated amendment with its change-log entry, before any v2 roles pass. Any other
  criteria change needs the user.
- **No git, no EnterWorktree, no worktree creation.** The orchestrator commits by explicit file list and pushes.

## Shell rules (the worktree-isolation hook enforces them)

- Literal absolute paths in every command. No `$VAR` or `$(...)` that computes a program, path or option; the hook
  refuses them. No `cd <elsewhere> && ...`. Heredocs and loops with python inside are refused too: write a script to
  your job's tmp dir with the Write tool and run it by literal path.
- Interpreters by path:
  - login base env: `/sw/external/python/anaconda3/bin/python` (py3.9, transformers 4.57.3, nnsight 0.5.12);
  - job env mgnp: `/u/swong2/.conda/envs/mgnp/bin/python` (py3.12, transformers 5.13, nnsight 0.7.0).
  Use `-I` for scripts that read datasets. Do not `source conda.sh` in interactive commands.
- Base-env pytest needs `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`. Delete any `core.*` dump it
  leaves in the worktree.
- Run the full suite with `run_in_background` and a generous timeout; Lustre can stall IO and git for minutes.
- The base env's user-site transformers calls the HF API under `HF_HUB_OFFLINE=1` unless Python runs with `-I`.

## Tests

- Both suites, both envs, from the worktree root:
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python -m pytest tests -q`
  and `/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests -q`.
- Before any edit, ticket 01 records the failing test names on the branch base in both envs in
  `reports/00-baseline-failures.md`; later tickets compare against it. Memory says main has 7 baseline names, plus
  the MASK repo-root test from a worktree. Results differ by about one fp32 ulp across the envs; that is not a
  regression.
- CPU tests only: `tests/fakes.py` (`FakeWordTokenizer`, `ScriptedModel`) and the 2-layer random Llama in
  `tests/helpers.py`. nnsight-dependent tests run on mgnp and skip cleanly on base (the pin is 0.7.0). Tests needing
  the real tokenizer load it from the HF cache and skip when it is unavailable.

## GPU jobs

**Bridges-2 is the default route** (spec §5, §6). Use only GPU-shared, one h100-80 per job, and keep one GPU type per
suite.

- Dispatch from the worktree with `scripts/remote/b2.sh` (`sync-code`, `sync-data`, `submit`, `status`, `fetch`),
  after ticket 01's branch support. Every subcommand takes `--dry`; use it first.
- SSH masters live on one Delta login node. Run b2.sh on that node. A closed master is an error: hand back. The
  orchestrator reopens it (key auth works from Delta) or asks the user.
- Every Bridges-2 submission carries `--export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p`, which b2.sh writes,
  and `--gpus-per-node=h100-80:1`, never `--gpus=`.
- Code reaches Bridges-2 only through the pushed branch (R3). The orchestrator pushes; ask before a wave if your code
  is not pushed yet.
- Model load is about 10.5 min cold, so pack cells per job within the ticket's allocation.
- Fetch results to Delta after every wave. Analysis cells are git-ignored (`outputs/_analyses/`), so they come back
  only by fetch. Anything still only on `/ocean` is at risk: Bridges-2 is expected offline about 2026-11-09.

**Delta fallback** only with the orchestrator's approval per wave, inside R2's 12 GPU-h fallback cap:

- bjhz-delta-gpu first (compare `sshare -u swong2 -o Account,FairShare` and `sbatch --test-only`);
- phase 1 (and tickets 02a, 02b, 08): A40 or H200; phases 2-3 (tickets 04, 05): H200 only (R16); ticket 07: H200
  only; for anything under an hour, interactive partitions first (1 h cap, one job per user per partition);
- never A100 for training.

**Every submission:**

1. Run the CLI's `--dry-run` through the actual sbatch wrapper's command line on the login node.
2. Run `sbatch --test-only` (Delta) or `b2.sh submit --test-only` (Bridges-2).
3. Put `--time` on the command line. Size it from observed runtime + a reasonable buffer (x1.5, quarter hours), not
   an extreme worst case (memory `slurm-job-policy`, user feedback 2026-10-25).
4. `mkdir -p /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/logs` before
   any Delta submission, and submit from the worktree root.

**Wrappers** activate the env through the cluster profile (`DC_ACTIVATE`). On Delta that is
`source ~/.bashrc && conda activate mgnp` inside a `set +u` block; a bare `source ~/.bashrc` under errexit exits
silently with a blank log.

**Polling:** `sacct -X -j <id> -o JobID,State,Elapsed` on Delta, `b2.sh status <id>` on Bridges-2. Do not poll in
tight loops.

## Compute ledger (`compute-ledger.json`)

- Two sections, `delta` and `bridges2`. Bridges-2 H100 GPU-hours cost 2 SU each. Allocations per ticket: spec §6.
- **Lock (R16).** Tickets run concurrently, so every read-modify-write of the ledger holds a lock:
  1. `mkdir /projects/beto/swong2/Alignment/.scratch/mechanism-analysis/compute-ledger.lock` (atomic; it fails if
     the lock is held);
  2. write your ticket id and the time to
     `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/compute-ledger.lock/owner`;
  3. read the ledger, edit it, keep it valid JSON;
  4. `rm /projects/beto/swong2/Alignment/.scratch/mechanism-analysis/compute-ledger.lock/owner`, then
     `rmdir /projects/beto/swong2/Alignment/.scratch/mechanism-analysis/compute-ledger.lock`.
  If the lock is held, wait a few minutes and retry. If it is older than 15 minutes, hand back; never break it.
- Before submitting, add a reservation to the right section with:
  - `reservation_id`, `ticket`, `purpose`;
  - `job_id` (after submit), `account`, `partition`, `gpu_spec`, `gpus`, `time_limit`;
  - `reserved_gpu_hours` (= time limit x GPUs), `status`, `submitted_at`, `output_dir`;
  - `source_sha256` of the scripts the job runs.
  Check that reconciled + in-flight + this reservation stay within your ticket's allocation and the section's cap.
  If not, stop and hand back.
- After the job ends, set `status`, `actual_seconds`, `actual_gpu_hours` from sacct, and lower `reserved_gpu_hours`
  to the actual elapsed rounded up to 0.25 h. Update `totals` (and `committed_su` for `bridges2`).
- Never remove other tickets' entries.

## Records (R6)

- Analysis cells stay untracked under the worktree's `outputs/_analyses/mechanism-analysis-*/` on Delta (canonical,
  fetched from Bridges-2). Nothing under `outputs/_analyses/` is un-ignored.
- Each ticket puts a curated copy of what the paper needs (head tables as CSV, `roles.json`, readings JSON) under
  `docs/research/mechanism-analysis/` in the worktree and lists it for the orchestrator to commit.
- `.scratch` reports are the working record.
- Removing the worktree deletes git-ignored files: the orchestrator moves the cells to the main checkout's
  `outputs/_analyses/` first.

## The phase gate and when you hand back

The phase gate is the orchestrator's, and it is the only stop rule between phases:

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

You hand back to the orchestrator, and do not proceed, at the end of your ticket and on any of:

- any EVAL 5 (`--evals benchmarks`), any merge to main, any training outside ticket 07, any proposal to drop a
  mechanism or report a two-way result;
- a drift control outside its pre-registered tolerance;
- a projected or actual cost beyond your ticket's allocation, or a grid that needs the cap raise of R14;
- any change to a pre-registered rule or threshold in spec §2, or to `docs/component-roles.md` criteria beyond 02b's
  amendment. Report numbers at other thresholds if useful; never decide with them;
- a closed SSH master or a held ledger lock older than 15 minutes.

## Ticket bookkeeping and reporting

- At start, set the ticket's `**Status:**` to `claimed`. Tick each checkbox as you verify it. Leave unticked what you
  could not do and say why under `## Comments`.
- **Write progress to `reports/<NN>-handback.md` as you go.** Agent messages have dropped several times; the
  orchestrator reads the hand-back files when the queue is quiet.
- At the end, append `## Comments` with:
  - what was built and run;
  - the files touched (absolute paths, as the commit list), including `docs/research/mechanism-analysis/` copies;
  - test results per env, with new failure names;
  - job ids per cluster with outcomes;
  - the ledger delta;
  - open questions for the researcher;
  - the review outcome.
  Write the review to `reports/<NN>-review.md`. Set `**Status:**` to `resolved`, or leave `claimed` with a blocker
  note.
- Final message to the orchestrator: lead with any hand-back trigger. Then the ticket status, the file list to
  commit, tests per env, jobs and verdicts, ledger usage, unresolved review findings, and the decisions the
  researcher must make.
- The orchestrator's commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Design rules for every ticket

- v1 behaviour is untouched; every v2 extension is additive and tested against a v1 snapshot.
- Every number names its file. A number computed from files is marked "derived".
- Read each analysis in its native sign and state it (ADR-0002). On H and F cells the knockout drop means "supports
  the honest answer".
- Paired columns say `paired` in the name. Coverage (n, instance set, sample seed) goes into the head-table meta.
- Selection uses the seed-0 sample; tests of selected sets use the seed-1 held-out sample (R11(b)).
- Pre-registered rules decide; everything else is labelled exploratory. R-lens is exploratory (R12).
