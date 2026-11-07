#!/usr/bin/env bash
# Executes one admitted stage; never reserves resources or submits a job.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
A2_DRY_RUN=0
if [[ ${1:-} == --dry-run ]]; then A2_DRY_RUN=1; shift; fi
if [[ $A2_DRY_RUN == 0 ]]; then
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
fi
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
if [[ $A2_DRY_RUN == 1 ]]; then
  exec "${DC_PYTHON:-python}" -m component_analysis.a2_pipeline --dry-run "$@"
fi
exec "$DC_PYTHON" -m component_analysis.a2_pipeline "$@"
