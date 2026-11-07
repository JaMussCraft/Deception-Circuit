#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1 DC_RUN_MANIFEST_GIT=0 DC_CLUSTER=delta
export DC_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python
export HF_HOME=/work/nvme/beto/swong2 HF_HUB_CACHE=/work/nvme/beto/swong2
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 WANDB_MODE=disabled
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH="/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-runtime-40fe57289405/runtime"
exec "$DC_PYTHON" "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/real-input-readiness/comparison-freeze-driver.py"
