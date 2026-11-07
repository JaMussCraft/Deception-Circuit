#!/bin/bash
set -euo pipefail
source "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/runtime/scripts/cluster/bridges2.env"
set +u
eval "$DC_ACTIVATE"
set -u
export HF_HOME="$DC_HF_HOME" HF_HUB_CACHE=/work/nvme/beto/swong2 TRANSFORMERS_CACHE=/work/nvme/beto/swong2
export CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
exec python "/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/deployment/early-cache-probe.py"
