#!/usr/bin/env bash
# Submit only after orchestrator reservation/registration; this wrapper never submits.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
LADDER_DRY_RUN=0
if [[ ${1:-} == --dry-run ]]; then LADDER_DRY_RUN=1; shift; fi
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
if [[ $LADDER_DRY_RUN == 1 ]]; then
  exec "$DC_PYTHON" -m component_analysis.specificity_ladder --dry-run "$@"
fi
exec "$DC_PYTHON" -m component_analysis.specificity_ladder "$@"
