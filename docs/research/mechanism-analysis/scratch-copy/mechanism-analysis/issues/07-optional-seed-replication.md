# 07 (conditional, R5) — Seed replication of the three D circuits and the stability of the exclusives

**What to do:** only if R5's condition holds after the phase-1 reading: a headline claim rests on exclusive-head
identities (R-own, C-reads or C-v1). Then train D_far, D_sdr and D_ser coarse heads-only at NLS 0.3 with seeds 1 and
123 on Delta, matching ticket 05's config otherwise. Measure the seed stability of the core, exclusives and D-H, and
evaluate the seed exclusives' knockouts. Answers RQ-D. If the condition does not hold, the ticket is dropped and
single seed is stated as a limitation (spec §7 item 1).

**Status:** ready-for-agent (conditional: launches only when the orchestrator records that R5's condition holds)
**Type:** task
**Blocked by:** the phase-1 reading (`reports/03-phase1-reading.md`, its R5 statement). Can run in parallel with 04
and 05.
**GPU allocation:** Delta 6.0 GPU-h, H200 only: training 6 x 0.75 on gpuH200x8-interactive, KO cells 1.5 in one H200
job. A40 training (~2.5 h per run) does not fit and needs a cap raise; never A100 (8B training OOMs at 40 GB).
bjhz-delta-gpu first.

## Facts to build on

- Ticket 05 of mechanism-datasets: config to match (`config.coarse.json` of the seed-42 runs, `--deception-margin-loss
  0.7`, the four coarse flags), `outputs/_launch_format_control/postprocess_coarse.sh` only (never the SDR wave's
  `postprocess.sh`, which submits evaluations). Timings: H200 interactive ~30 min per run.
- Seed-wave precedent: coarse SDR seeds 1 and 123, `_launch/seed_stability.py` (chance-corrected Jaccard), memory
  `coarse-sdr-seed-wave`.
- `scripts/train_deception.sbatch` has no cluster profile, so training stays on Delta.
- Delta interactive partitions: 1 h cap, one job per user per partition (memory `interactive-partitions`).
- Delta accounts: bjhz-delta-gpu first (memory `slurm-account-priority`, `delta-account-fairshare`).

## Acceptance criteria

- [ ] 6 runs trained, post-processed, sizes by `evaluation/masks.count_masks`, in-run gate read (not acted on).
- [ ] Pairwise and three-seed Jaccard (chance-corrected) for D, core, exclusives and D-H per task. Median layer of each
      exclusive set per seed. RQ-D prediction marked confirmed, refuted or inconclusive.
- [ ] KO cells (interchange, `--evals knockout`, 20-set null) of each seed's exclusives and of the seed-intersection
      exclusives on the home D test set, in one Delta H200 job.
- [ ] `reports/07-seeds-results.md` and reading; curated copies under `docs/research/mechanism-analysis/seeds/` (R6).
      Ledger `delta` section reconciled under the lock. Review in `reports/07-review.md`.

## Hand-back

The stability table and reading. It feeds ticket 06.

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

## Comments
