#!/usr/bin/env bash
set -euo pipefail
: "${SLURM_JOB_ID:?Actual Slurm CPU job required; do not run preparation on login}"
: "${A3_CPU_PREPARATION_RELEASE:?Root must provide exact CPU-only review release}"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=""
exec /sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/source-refresh-batch-real-input-cpu-proposal/run-cpu-preparation.py
