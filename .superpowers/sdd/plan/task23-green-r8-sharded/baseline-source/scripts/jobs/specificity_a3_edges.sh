#!/usr/bin/env bash
# Root reserves jobs; this wrapper never submits or mutates a ledger.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export SPECIFICITY_A3_EDGE_WRAPPER_STARTED_UNIX="$(date +%s.%N)"
if [[ -n ${SPECIFICITY_A3_EDGE_REPO_ROOT:-} ]]; then
  EDGE_ROOT="$SPECIFICITY_A3_EDGE_REPO_ROOT"
elif [[ -n ${SLURM_JOB_ID:-} && -f component_analysis/a3_edge_pipeline.py ]]; then
  EDGE_ROOT="$PWD"
else
  EDGE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
fi
cd "$EDGE_ROOT"
if [[ -z ${DC_PYTHON:-} ]]; then
  case ${DC_CLUSTER:-delta} in
    delta|bridges2) source "scripts/cluster/${DC_CLUSTER:-delta}.env" ;;
    *) echo 'Unsupported DC_CLUSTER.' >&2; exit 1 ;;
  esac
  set +u
  eval "$DC_ACTIVATE" || { echo 'Environment initialization failed.' >&2; exit 1; }
  set -u
  DC_PYTHON=python
  export HF_HOME="$DC_HF_HOME"
fi
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
exec "$DC_PYTHON" -m component_analysis.a3_edge_pipeline "$@"
