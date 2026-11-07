#!/bin/bash
set -euo pipefail
: "${A2_H100_RUNTIME:?}" "${A2_H100_PACKET:?}" "${A2_H100_BOUND_CONFIG:?}" "${A2_H100_BOUND_CONFIG_SHA256:?}"
cd "$A2_H100_RUNTIME"
export DC_B2_ALLOC=cis260361p
source scripts/cluster/bridges2.env
set +u
eval "$DC_ACTIVATE"
set -u
export DC_CLUSTER=bridges2 DC_PYTHON=/ocean/projects/cis260361p/swong2/envs/mgnp/bin/python
export HF_HUB_CACHE=/work/nvme/beto/swong2 TRANSFORMERS_CACHE=/work/nvme/beto/swong2
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$A2_H100_RUNTIME" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec "$DC_PYTHON" "$A2_H100_PACKET/controller.py"
