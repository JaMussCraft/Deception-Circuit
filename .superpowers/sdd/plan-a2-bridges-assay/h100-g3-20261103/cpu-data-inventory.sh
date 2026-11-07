#!/bin/bash
set -euo pipefail
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 DC_RUN_MANIFEST_GIT=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export HF_HOME=/work/nvme/beto/swong2 HF_HUB_CACHE=/work/nvme/beto/swong2 TRANSFORMERS_CACHE=/work/nvme/beto/swong2
exec /u/swong2/.conda/envs/mgnp/bin/python "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/prepare-data-inventory.py"
