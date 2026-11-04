#!/bin/bash
set -euo pipefail
: "${G3_RUNTIME:?accepted runtime required}"
: "${G3_VALIDATOR:?reviewed validator required}"
: "${G3_PARAMETERS:?actual parameters required}"
: "${G3_PARAMETERS_SHA:?actual parameter digest required}"
cd "$G3_RUNTIME"
source "$G3_RUNTIME/scripts/cluster/bridges2.env"
set +u
eval "$DC_ACTIVATE"
set -u
export DC_CLUSTER=bridges2 DC_B2_ALLOC=cis260361p
export HF_HOME="$DC_HF_HOME" HF_HUB_CACHE=/work/nvme/beto/swong2 TRANSFORMERS_CACHE=/work/nvme/beto/swong2
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$G3_RUNTIME"
: "${SLURM_JOB_ID:?actual job identity required}"
exec /ocean/projects/cis260361p/swong2/envs/mgnp/bin/python "$(dirname "$G3_VALIDATOR")/entry-guard.py" "$G3_ENTRY_CONTEXT"
