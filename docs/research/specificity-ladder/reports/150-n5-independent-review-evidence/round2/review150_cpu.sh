#!/usr/bin/env bash
set -euo pipefail
: "${SLURM_JOB_ID:?Root must submit independent probes as Slurm CPU}"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
exec /sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/150-n5-independent-review-evidence/round2/run_review.py
