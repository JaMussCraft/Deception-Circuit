# RESUME — mechanism-datasets orchestration (written 2026-10-21, before context compaction)

Role: Fable is the orchestrator; Opus subagents do the work. User wants concise, high-level updates only,
trusts the orchestrator's decisions, and must be asked before (a) any circuit evaluation, (b) dropping a
mechanism. Keep every ruling in `spec.md` §13/§14 (G1–G11) and every decision in the shared memory file
`/projects/beto/swong2/Alignment/.agents/memory/mechanism-datasets-plan.md`.

## Where things are

- Worktree (session is pinned here; agents never run git; orchestrator commits by file list):
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets`, branch
  `mechanism-datasets`, HEAD **48df320** (datasets committed). Untracked, do not commit: `outputs/_build_v2/`
  (425 MB scoring work dir), `logs/`.
- Spec, brief, tickets, reports, ledger: `/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/`
  (`spec.md`, `agent-brief.md`, `issues/01..05`, `reports/`, `compute-ledger.json`).
- Tickets 01–04 DONE and committed. **Ticket 05 (train v2 circuits) NOT started**; user said "wait" right
  after the dataset commit and has not yet given the go for training.
- Datasets: `data/datasets/{far,sdr,ser}_v2{,_honest,_nopressure}` (200/200/1000 each; D/H/F share instance
  ids and row order), `data/datasets/comparison_set_v2.json` (5/0/8). Provenance pins sha256 of
  `build_deception_v2.py`, `deception_v2.py`, `clause_surgery.py`, `contingency.py` — editing them fails
  `tests/test_v2_reproducibility.py` by design.
- Final pilot selection: `reports/pilot-selection.json` — family `rule_instructed`, suffix ON, SER wording B
  original predicates; FAR cell r8_far_strong_on (strong/act-naming pool), SDR r9_sdr_unified_on, SER
  r9_ser_unified_on_B. Residual confound (CONTEXT.md): FAR pool is all act-naming; SDR/SER use the unified
  (act-naming + relational) pool.
- Purity: construction-based (user decision §14.G11). LLM judges (v1 and v2, sonnet-4.5 + gemini-2.5-pro)
  pass FAR (100/100) but do not separate SDR/SER (kappa 0.00/0.08); recorded as a stated limitation in
  CONTEXT.md and the ticket-04 report. Do not re-run judges.
- Budget: 60 GPU-h cap, **11.25 reserved used** (ledger). OpenRouter ~5 USD so far (credits topped up).
- Other session's jobs may appear in the queue (`sel-v4-*`, `run_sdr_native_controls*`): ignore them.

## Next step (after the user says go)

Ticket 05: `/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/issues/05-train-v2-circuits-and-hand-back.md`.
Train D and H circuits for far_v2/sdr_v2/ser_v2 at fine nls0.3 and coarse heads-only nls0.3 (match
`outputs/llama-8b-instruct_sdr` fine config and `outputs/llama-8b-instruct_sdr_coarse/.../config.coarse.json`;
pass `--deception-margin-loss 0.7` deliberately; train only on gpuA40x4 or gpuH200x8, never A100 40 GB;
post-process coarse runs only with format-control's `postprocess_coarse.sh`, never the coarse wave's
`postprocess.sh` which submits evaluations). Spawn an Opus agent `impl-05` with the same brief pattern as
impl-01..04 (read agent-brief.md, spec.md, the ticket, reports/04-ticket-04-report.md; no git; ledger;
both-env tests; write progress to `reports/05-handback.md` because agent hand-back messages have dropped
several times — when the queue goes quiet, read the reports directly). Ticket 05 budget 20 GPU-h.
**HARD STOP after training: no faithfulness suites, knockouts, compositions or EVAL 5 until the user reviews.**

## Known gotchas this session

- Agent messages crossed/dropped ~5 times; always also check `reports/*handback*.md` and `squeue`/`sacct`.
- Interactive partitions have a 1 h cap: builds timed out once; use non-interactive with `--time` for >45 min.
- Bash commands that compute program/args from variables, or loops with python inside, are refused by the
  worktree-isolation hook: write a script to `/u/swong2/.claude/jobs/6e1f64bd/tmp/` and run it by literal path
  with `/u/swong2/.conda/envs/mgnp/bin/python -I`.
- Lustre git can exceed 120 s: use `timeout 300` on git add/commit; a trailing `git status` may time out
  after a successful commit (check `git log -1`).
- `component_analysis/dataloaders.py` MECHANISM_TASKS still lists only v1 ids (extend before any v2
  component analysis).

## Summary to give the user on resume (one paragraph)

All three v2 mechanism datasets (FAR, SDR, SER) are built, verified and committed on branch
`mechanism-datasets` (48df320): one shared scaffold, one instruction family, same-instance honest twins,
construction-based purity with the LLM-judge disagreement recorded as a limitation. 11.25 of 60 GPU-h used.
Waiting on the user's go to train the circuits (ticket 05); evaluations need a separate review.

## Update 2026-10-22: ticket 05 done (coarse-only, G12), HEAD bd67758

Six coarse heads-only circuits trained, post-processed and committed; see `reports/05-training-summary.md` and
`reports/05-handback.md`. Ledger 22.75 of 60 GPU-h. Fine runs deferred. Next: user review of the size table, then
(only with the user's explicit go) evaluations: faithfulness suites, knockouts, compositions, EVAL 5. Before any
v2 component analysis extend `component_analysis/dataloaders.py` MECHANISM_TASKS. Slurm: use bjhz-delta-gpu while
its fairshare is fresh; account moves/QOS changes on queued jobs need the user to run scontrol themselves.

## Update 2026-10-24: evaluation + Bridges-2 plan proposed, awaiting user answers

Recon report: `reports/06-recon-evals-and-bridges2.md`. Proposed to the user (not yet approved, nothing started):
- Evals, no EVAL 5, two stages: stage 1 = 24 cells (suff + heads-only KO per circuit; D&H suff/KO, D-H KO, H-D KO
  per task); stage 2 = 33 cells (cross-task D transfer, 31-head shared D core, XOR/exclusives, H-on-D-test and
  D-on-nopressure controls). ~27 A40 GPU-h or ~5.5 H100 GPU-h. Prereqs: rebuild MLP operand from a v2 run; config-only
  nopressure stand-in; one Delta reference cell re-run on Bridges-2 as drift control.
- Bridges-2 (PSC, user swong2): push branch to origin (needs user OK); ~/.ssh/config ControlMaster for
  bridges2.psc.edu and data.bridges2.psc.edu (user enters password once per host via `!`); rsync from Delta to the DTN:
  HF snapshot 15 GB + wikitext cache (offline mode, no token), conda-pack of mgnp 9 GB (fallback pinned pip); cluster
  profile for sbatch (GPU-shared, h100-80 recommended, V100 unusable); dispatch helper on Delta; Delta canonical;
  do not copy ~/.bashrc (API keys). Open questions for the user: push OK, allocation id, GPU type, stage plan yes.

## Update 2026-10-25: tickets 06 and 07 DONE; feature complete up to evaluations. HEAD c24b5d9 (pushed)

- Ticket 07: Bridges-2 (PSC) is a second cluster dispatched from Delta. See `docs/bridges2.md` in the repo and the
  shared memory `bridges2-cluster.md`. SSH aliases `bridges2` / `b2dtn`; the masters were opened by the user on
  dt-login04 (ControlPersist yes). The Delta key `~/.ssh/id_psc` is registered on the PSC key form but was still
  rejected at 07:33 CDT on 10-25 (propagation pending); re-test with
  `ssh -o ControlMaster=no -o ControlPath=none -o BatchMode=yes bridges2 hostname`. If the masters drop before the
  key works, the user must reopen them from a real terminal on the same login node.
- Ticket 06: 65 evaluation cells (drift control, stage 1, stage 2) on Bridges-2 h100-80, fetched to Delta under
  `outputs/_suites/mechanism-v2-coarse/{control,stage1,stage2}/`. Reports: `reports/06-stage1-results.md`,
  `reports/06-stage2-results.md`, `reports/06-evaluation-reading.md` (combined verdict), `.json` beside each.
  Suite tooling: `outputs/_launch_mechanism_v2/evals/` (suite_v2.json, gen_cells.py, stage{1,2}_results.py).
- Verdict: coarse heads-only v2 circuits are mostly shared answer machinery (31-head core in all D and H; every
  D/H/core knockout removes deception on all tasks AND inverts no-pressure answers). Mechanism-specific heads are
  small/partial: exclusives 8/14/10 (far/sdr/ser), far's D-H (26 heads) most deception-leaning. See the reading.
- Budget: Delta 22.75/60 GPU-h; Bridges-2 ticket 06 11.0/20 H100 GPU-h reserved (7.4 actual), ticket 07 0.5/1.
- Spec rulings up to G16 in `spec.md` §14. Not done: fine circuits (deferred, G12), EVAL 5 (user: not now),
  component analysis (needs `component_analysis/dataloaders.py` MECHANISM_TASKS extended to v2 ids), mean/zero
  ablation replication of core + exclusive cells (suggested, ~1-2 GPU-h).
- Branch mechanism-datasets is a fast-forward of main (aef064a); the user may merge it to main themselves.
- NEXT PHASE (user, 2026-10-25): circuit-level analysis of the v2 circuits and compositions for a publishable
  paper, run as a NEW feature/session (suggested slug `mechanism-analysis`).
