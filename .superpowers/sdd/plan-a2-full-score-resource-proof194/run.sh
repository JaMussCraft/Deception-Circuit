#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual CPU allocation required}"
P=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-resource-proof194
export DC_RUN_MANIFEST_GIT=0 DC_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 HF_HUB_CACHE=/work/nvme/beto/swong2 TRANSFORMERS_CACHE=/work/nvme/beto/swong2
PY=/u/swong2/.conda/envs/mgnp/bin/python
if [[ ${PROOF194_WRAPPER_TEST:-0} == 1 ]]; then [[ "$SLURM_JOB_ID" == 1 && -z ${SLURM_CLUSTER_NAME:-} ]]; PY=${PROOF194_PYTHON:?test interpreter}; fi
exec "$PY" -B "$P/supervisor.py" --output "$1" --manifest-sha256 "$2"
