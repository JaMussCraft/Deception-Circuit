#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual CPU allocation required}"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
exec /sw/external/python/anaconda3/bin/python3.9 "$(dirname "$0")/supervisor.py" "$@"
