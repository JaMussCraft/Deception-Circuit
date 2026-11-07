#!/usr/bin/env bash
# Run the reviewed twin-training wrapper inside one explicitly reserved allocation.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
TWIN_STAGE=run
if [[ ${1:-} == --dry-run ]]; then
  TWIN_STAGE=dry-run
  shift
fi
for TWIN_ARG in "$@"; do
  case "$TWIN_ARG" in
    --stage|--stage=*) echo 'Use the launcher --dry-run switch; stage override is not allowed.' >&2; exit 2 ;;
  esac
done
if [[ $TWIN_STAGE == run && -z ${SLURM_JOB_ID:-} ]]; then
  echo 'Training requires a Slurm allocation.' >&2; exit 1
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
export DC_RUN_MANIFEST_GIT=0
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec "$DC_PYTHON" -m scripts.twin_training --stage "$TWIN_STAGE" "$@"
