#!/usr/bin/env bash
set -euo pipefail
: "${SLURM_JOB_ID:?Actual Slurm CPU job required}"
: "${A3_CPU_PREPARATION_RELEASE:?Root exact-source accepted-review CPU release required}"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="" DC_RUN_MANIFEST_GIT=0
exec /sw/external/python/anaconda3/bin/python3.9 "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/n5-mask-genuine-preparation-861f84a3938a/run-cpu-preparation.py"
