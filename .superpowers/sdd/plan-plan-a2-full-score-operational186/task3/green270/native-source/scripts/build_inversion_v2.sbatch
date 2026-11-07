#!/bin/bash
# Score the Instructed-Inversion Condition rows (<task>_inversion) on one GPU (mechanism-analysis ticket 08):
# dataset/build_inversion_v2.py --stage score. Every argument is passed through to the builder
# (default: all three tasks, the committed pool and clause-form table).
#
# Proposed path: scripts/build_inversion_v2.sbatch (scripts/ is ticket 01's area, so the
# orchestrator places it). It is profile-aware like scripts/evaluate_circuit.sbatch: Delta by
# default, Bridges-2 with DC_CLUSTER=bridges2, which scripts/remote/b2.sh submit passes.
#
#   scripts/remote/b2.sh submit --dry --time 00:30:00 --script scripts/build_inversion_v2.sbatch \
#       --job-name build-inv-v2
#
# Dry path first, on the login node (CPU, no weights, writes nothing):
#   python -I dataset/build_inversion_v2.py --stage score --no-model
# Then, on Delta after `b2.sh fetch outputs/_build_inversion_v2`:
#   python -I dataset/build_inversion_v2.py --stage assemble
#
#SBATCH --job-name=build-inversion-v2
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --output=logs/build_inversion_v2_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

profile="scripts/cluster/${DC_CLUSTER:-delta}.env"
if [ ! -f "$profile" ]; then
    echo "unknown cluster profile: $profile (DC_CLUSTER=${DC_CLUSTER:-})" >&2
    exit 2
fi
source "$profile"

set +u
eval "$DC_ACTIVATE"
set -u
export HF_HOME="$DC_HF_HOME" TQDM_DISABLE=1
if [ "$DC_HF_OFFLINE" = "1" ]; then
    export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
fi
echo "build_inversion_v2: job ${SLURM_JOB_ID:-local} on ${SLURM_JOB_PARTITION:-unknown} ($(hostname)), cluster ${DC_CLUSTER:-delta}, args: $*"
python -I dataset/build_inversion_v2.py --stage score "$@"
