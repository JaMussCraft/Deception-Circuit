#!/usr/bin/env bash
set -euo pipefail
export REVIEW134_RUNTIME="/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-runtime-40fe57289405/runtime"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 DC_RUN_MANIFEST_GIT=0
exec /sw/external/python/anaconda3/bin/python3.9 "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/134-source-refresh-batch-review-evidence/run_review.py"
