# Ticket 04 hand-back (progress log; the final summary is at the top once all three datasets exist)

## Progress

- 2026-10-21 10:24. Score jobs were submitted on the interactive partitions, account beto-delta-gpu:
  - 23099684: far_v2 test split, gpuA100x8-interactive.
  - 23099685: ser_v2, all splits, gpuA100x4-interactive.
  - 23099686: sdr_v2, all splits, gpuA40x4-interactive.
- 2026-10-21 11:00.
  - 23099685 (SER) COMPLETED in 43 min.
  - 23099684 (FAR test) and 23099686 (SDR) hit the 1 h cap. Every finished chunk was saved atomically, so
    nothing was lost:
    - FAR test: 7 of 9 chunks, 140,000 of 162,500 instances.
    - SDR: train, validation and 2 of 3 test chunks, 61,668 of 75,836 instances.
  - Throughput: about 8 min per 20,000-instance chunk on an A100, about 19 min on an A40.
  - Yield matches the pilot projection; the 1.3x overgeneration margin turned out unnecessary. The selection
    check, run on CPU with the builder's own `select_split`, fills every SER and SDR split and FAR's test split
    from the finished chunks: 200/200/1000, no shortfall, variant cells balanced, caps respected. Per the lead's
    instruction (2026-10-21), overgeneration is capped at what 200/200/1000 needs: FAR test chunks 7-8 and SDR
    test chunk 2 are not run. The filter reports count only the instances actually scored.
- 2026-10-21 11:15. `ser_v2` and `sdr_v2` were assembled (D/H/F, 200/200/1000 each), and the reproducibility
  test passes on both. Sanity check: the build's train list starts with the pilot's instances, and the build
  reproduces the pilot's contingent survivors exactly, SDR 133/133 and SER 70/70, with none extra.
- 2026-10-21 11:07. Job 23100970 was submitted: far_v2 train + validation, 65,000 instances,
  gpuA100x8-interactive, 1 h. Its dry path through the wrapper passed. Ledger entry `04-build-far-trainval`.
- Ledger after reconciling the three finished jobs: ticket 04 at 3.5 GPU-h reserved of 16, plus 1.0 in flight.

## Final hand-back (2026-10-21)

**Ticket 04 is `in-review`. All nine v2 dataset directories are built:** far_v2, sdr_v2 and ser_v2, each with
`_honest` and `_nopressure`, at 200/200/1000 with identical instance ids and row order.
- **Construction checks (§14.G11)** pass on every selected row and on every full-build survivor.
- **Selection.** Strata are exactly 25% each, variants 50/50, clause caps at `cap_used` (FAR and SER 0.15, SDR
  0.10), maximum length 106 tokens.
- **Length.** The cross-task D band is 12 (94-106) and the median gap is 5.
- **Reproducibility.** The test passes in both envs.
- **Comparison set.** 5 / 0 / 8 rows (train / validation / test). The shared-clause subset is empty.
- **Pilot match.** The build reproduces the pilot's contingent survivors exactly (FAR 71, SDR 133, SER 70).

Tests:
- base: 8 failed, 1665 passed, 58 skipped. The failures are exactly the 8 baseline names.
- mgnp: 8 failed, 1818 passed, 19 skipped. The failures are exactly the 8 baseline names.

Compute and spend:
- GPU: ticket 04 reserved 4.0 of 16 GPU-h after reconciliation, 3.27 GPU-h actual, across 5 jobs (two hit the 1 h
  interactive cap; their saved chunks were kept). The feature total is 11.25 of 60.
- OpenRouter: 969 calls, about 2.15 USD.

Files to commit (absolute paths):
- Modified since c18a8ef (commit these exact versions; `provenance.json` pins the builder's sha256
  `60597332ae2953bbbf2517ca39629bb0b6e64509176c4dbd5910614879e4a4a2`):
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/dataset/build_deception_v2.py
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/tests/test_build_v2.py
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/CONTEXT.md
- Datasets (new):
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/data/datasets/far_v2/
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/data/datasets/far_v2_honest/
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/data/datasets/far_v2_nopressure/
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/data/datasets/sdr_v2/
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/data/datasets/sdr_v2_honest/
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/data/datasets/sdr_v2_nopressure/
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/data/datasets/ser_v2/
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/data/datasets/ser_v2_honest/
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/data/datasets/ser_v2_nopressure/
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/data/datasets/comparison_set_v2.json
- Already committed in c18a8ef; check they are unchanged:
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/dataset/mechanism_purity_v2.py
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/dataset/purity_judge_v2.py
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/build_v2.sbatch
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/tests/test_purity_v2.py
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/tests/test_purity_judge_v2.py
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/tests/test_v2_reproducibility.py
- Do NOT commit:
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/_build_v2/ (425 MB scoring work dir)
  - /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/logs/
- Docs outside the repo:
  - /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/spec.md (§14.G11 added)
  - /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/issues/04-purity-judge-full-build-and-reproducibility.md
  - /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/compute-ledger.json
  - /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/04-ticket-04-report.md
  - /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/04-handback.md
  - /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/04-purity-diagnostics.md
  - /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/04-purity-judge-full-build-and-reproducibility-review.md
  - /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/purity-hard-stop.md
  - /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/purity/ (v1 and v2 judge outputs, pre-registration, diagnostics, construction checks)
  - /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports/pilots/topup04/

Open issues:
1. LLM judges do not support the SDR and SER mechanism labels. Judge v2 failed both under both raters, with kappa
   0.00 and 0.08, and reads their answers as contradicting the suffix sentence. Purity is construction-defined and
   recorded as a limitation.
2. The three-way comparison set is tiny (5 / 0 / 8), and the shared-clause matched-pressure subset is empty,
   because shared clauses never produced a contingent survivor.
3. The wording confound between FAR's act-naming pool and the unified SDR/SER pool stands (CONTEXT.md). So does
   SDR's lower honest-instruction accuracy (0.90; item_2 share 0.41).
4. `provenance.json` pins the sha256 of four source files. Editing `dataset/build_deception_v2.py`,
   `deception_v2.py`, `clause_surgery.py` or `contingency.py` will fail the reproducibility test by design.
5. FAR test (140,000 of 162,500) and SDR test (40,000 of 54,168) were scored partially, with overgeneration capped
   at need. The filter reports count only scored instances.
