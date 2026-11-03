#!/bin/bash
# neuron-partition N3: split-half FAR attribution rankings (scripts/neuron_attribution.py --ids). The halves are W3's
# pressure-cluster-stratified halves of the train+validation ranking ids (far_rank_ids.json, halves.A and halves.B;
# 200 D ids each, matching 174 and 180 I/N rows by id). Per half: dh and in forward, then dh with --reverse (six
# runs), batch 4, pools from W3's sha256-checked copy. The full ranking (job 23476096) took 252 s for twice the rows.
# Submit from the worktree root with the committed short sha as the only argument:
#
#   sbatch --account=beto-delta-gpu --partition=gpuH200x8-interactive,gpuA40x4-interactive --time=00:30:00 \
#       docs/research/neuron-partition/jobs/split_half_attribution_far.sbatch <commit>
#
# Outputs: outputs/_analyses/neuron-partition/attribution/far_v2_{dh,in}_train+validation_half{1,2}_<commit>/ and
#          far_v2_dh_train+validation_half{1,2}_<commit>_rev/
# Not the 40 GB A100s: the 8B backward does not fit there.
#
#SBATCH --job-name=nrn-half-atp-far
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuH200x8-interactive,gpuA40x4-interactive
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=logs/neuron_partition_split_half_far_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

if [ "$#" -ne 1 ]; then
    echo "usage: sbatch ... split_half_attribution_far.sbatch <commit>" >&2
    exit 2
fi
COMMIT="$1"

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

DATA=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/data
common=(--task far_v2 --split train,validation --batch-size 4 --pool-dir "$DATA/pools" --ids "$DATA/far_rank_ids.json"
        --commit "$COMMIT")
python scripts/neuron_attribution.py "${common[@]}" --ids-key halves.A --tag half1 --pair dh in
python scripts/neuron_attribution.py "${common[@]}" --ids-key halves.A --tag half1 --pair dh --reverse
python scripts/neuron_attribution.py "${common[@]}" --ids-key halves.B --tag half2 --pair dh in
python scripts/neuron_attribution.py "${common[@]}" --ids-key halves.B --tag half2 --pair dh --reverse
