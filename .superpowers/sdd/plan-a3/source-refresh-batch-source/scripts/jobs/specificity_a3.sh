#!/usr/bin/env bash
# Root alone reserves/submits; this wrapper only validates or executes its stage.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export A3_WRAPPER_START_SECONDS="$(date +%s.%N)"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
a3_checkout_valid() {
  [[ -n ${1:-} && -f "$1/component_analysis/a3_pipeline.py" && -f "$1/scripts/cluster/${DC_CLUSTER:-delta}.env" ]]
}
A3_SCRIPT_CANDIDATE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ -n ${A3_REPO_ROOT:-} ]]; then
  a3_checkout_valid "$A3_REPO_ROOT" || { echo 'A3_REPO_ROOT is not a complete checkout.' >&2; exit 1; }
  A3_WRAPPER_ROOT="$A3_REPO_ROOT"
elif a3_checkout_valid "$A3_SCRIPT_CANDIDATE"; then
  A3_WRAPPER_ROOT="$A3_SCRIPT_CANDIDATE"
elif a3_checkout_valid "$PWD"; then
  A3_WRAPPER_ROOT="$PWD"
elif a3_checkout_valid "${SLURM_SUBMIT_DIR:-}"; then
  A3_WRAPPER_ROOT="$SLURM_SUBMIT_DIR"
else
  echo 'Set A3_REPO_ROOT or submit with --chdir pointing to the complete checkout.' >&2
  exit 1
fi
cd -- "$A3_WRAPPER_ROOT"
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
printf 'A3 command:'
printf ' %q' "$DC_PYTHON" -m component_analysis.a3_pipeline "$@"
printf '\n'
exec "$DC_PYTHON" -m component_analysis.a3_pipeline "$@"
