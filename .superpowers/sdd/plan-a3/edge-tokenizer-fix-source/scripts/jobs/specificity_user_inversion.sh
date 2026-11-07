#!/usr/bin/env bash
# Caller submits with explicit account/partition/time and prior ledger reservation.
# The same profile and activation run in CPU preflight and allocation scoring.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
SPECIFICITY_DRY_RUN=0
if [[ ${1:-} == --dry-run ]]; then
  SPECIFICITY_DRY_RUN=1
  shift
fi
if [[ $SPECIFICITY_DRY_RUN == 0 && -z ${SLURM_JOB_ID:-} ]]; then
  echo 'Scoring requires a Slurm allocation.' >&2; exit 1
fi
case ${DC_CLUSTER:-delta} in
  delta|bridges2) source "scripts/cluster/${DC_CLUSTER:-delta}.env" ;;
  *) echo 'Unsupported DC_CLUSTER.' >&2; exit 1 ;;
esac
if [[ -z ${DC_PYTHON:-} ]]; then
  set +u
  eval "$DC_ACTIVATE" || { echo 'Environment initialization failed.' >&2; exit 1; }
  set -u
  DC_PYTHON=python
fi
export HF_HOME="$DC_HF_HOME"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
if [[ $SPECIFICITY_DRY_RUN == 1 ]]; then
  echo 'CPU dry-run (no model, submission, or output writes):'
  exec "$DC_PYTHON" -m dataset.build_user_inversion_v2 --stage score --dry-run "$@"
fi
exec "$DC_PYTHON" -m dataset.build_user_inversion_v2 --stage score "$@"
