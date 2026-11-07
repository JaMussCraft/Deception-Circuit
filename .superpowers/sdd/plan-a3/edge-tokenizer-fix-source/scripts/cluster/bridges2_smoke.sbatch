#!/bin/bash
# Bridges-2 smoke job (ticket 07): GPU visible, model + wikitext load offline, evaluate_circuit parses.
# Submit from Delta, which puts account, partition, GPU and time on the command line:
#
#   scripts/remote/b2.sh submit --script scripts/cluster/bridges2_smoke.sbatch --time 00:15:00
#
# Login-node dry path on Delta (CPU only, no model):
#
#   DC_CLUSTER=delta bash scripts/cluster/bridges2_smoke.sbatch --no-model
#
#SBATCH --job-name=b2-smoke
#SBATCH --nodes=1
#SBATCH --output=logs/b2_smoke_%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"
mkdir -p logs

profile="scripts/cluster/${DC_CLUSTER:-bridges2}.env"
[ -f "$profile" ] || { echo "unknown cluster profile: $profile" >&2; exit 2; }
source "$profile"
set +u
eval "$DC_ACTIVATE" || { echo "Environment initialization failed" >&2; exit 1; }
set -u
export HF_HOME="$DC_HF_HOME"
if [ "$DC_HF_OFFLINE" = "1" ]; then
    export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
fi
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1

echo "host=$(hostname) cluster=$DC_CLUSTER_NAME job=${SLURM_JOB_ID:-none}"
command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv || true
python scripts/cluster/smoke_check.py "$@"
