#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual CPU allocation required}"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export HF_HUB_CACHE=/work/nvme/beto/swong2 TRANSFORMERS_CACHE=/work/nvme/beto/swong2
timeout --signal=TERM --kill-after=15 840 /u/swong2/.conda/envs/mgnp/bin/python -B "$(dirname "$0")/shape.py" --output "$1" --manifest-sha256 "$2"
