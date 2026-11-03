#!/bin/bash
# neuron-partition N1: the full FAR attribution ranking (scripts/neuron_attribution.py) on the train and validation
# splits (item 10 of START.md): D vs its Neutral-Clause Twin H (400 rows) and the user-turn I vs its user-neutral
# twin (354 rows, W3's verified copy of the unmerged Codex pool), batch 4, first forward only, then with --reverse
# (H as clean, D as twin; the forward keys are recomputed in that run too). Pilot 23475874 measured 0.098 and 0.084
# seconds per row on an A40, so the four passes are a few minutes plus two model loads.
# Submit from the worktree root (the cluster profile path is relative):
#
#   sbatch --account=beto-delta-gpu --partition=gpuH200x8-interactive,gpuA40x4-interactive --time=00:30:00 \
#       docs/research/neuron-partition/jobs/full_attribution_far.sbatch
#
# Outputs: outputs/_analyses/neuron-partition/attribution/far_v2_{dh,in}_train+validation_7386fd3[_rev]/
# Not the 40 GB A100s: the 8B backward does not fit there.
#
#SBATCH --job-name=nrn-full-atp-far
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuH200x8-interactive,gpuA40x4-interactive
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=logs/neuron_partition_full_far_%j.out

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

POOLS=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/data/pools
common=(--task far_v2 --pair dh in --split train,validation --batch-size 4 --pool-dir "$POOLS" --commit 7386fd3)
python scripts/neuron_attribution.py "${common[@]}" "$@"
python scripts/neuron_attribution.py "${common[@]}" --reverse "$@"
