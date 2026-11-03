#!/bin/bash
# neuron-partition N1 pilot: attribution patching over every MLP hidden neuron (scripts/neuron_attribution.py) on
# 64 validation rows of FAR D vs its Neutral-Clause Twin H, then 64 validation rows of the user-turn I vs its
# user-neutral twin (unmerged Codex pool, read in place), batch 4, to measure seconds per row and size the full run.
# Submit from the worktree root (the cluster profile path is relative):
#
#   sbatch --account=beto-delta-gpu --partition=gpuH200x8-interactive,gpuA40x4-interactive --time=00:45:00 \
#       docs/research/neuron-partition/jobs/pilot_attribution.sbatch
#
# Login-node check first (same arguments plus --dry-run):
#
#   python scripts/neuron_attribution.py --task far_v2 --pair dh in --split validation --limit 64 --batch-size 4 --dry-run
#
# Not the 40 GB A100s: the 8B backward does not fit there.
#
#SBATCH --job-name=nrn-pilot-atp
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuH200x8-interactive,gpuA40x4-interactive
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=00:45:00
#SBATCH --output=logs/neuron_partition_pilot_%j.out

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
export HF_HOME="$DC_HF_HOME"
if [ "$DC_HF_OFFLINE" = "1" ]; then
    export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
fi
export RESEARCH_DIRECTION=neuron-partition
nvidia-smi --query-gpu=name,memory.total --format=csv
python scripts/neuron_attribution.py --task far_v2 --pair dh in --split validation --limit 64 --batch-size 4 "$@"
