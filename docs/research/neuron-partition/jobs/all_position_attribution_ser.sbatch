#!/bin/bash
# neuron-partition, SER (the secondary task of START item 10): the all-position attribution rankings of ruling R11
# (atp_all_mean, atp_all_absmean, rev_atp_all_*), the SER copy of all_position_attribution_far.sbatch (job 23478550,
# 482 s on an A40). The same ten output directories in six python calls:
#   full train+validation: dh and in forward, then dh and in with --reverse (H as clean, D as twin);
#   the stratified halves A and B: dh and in forward, then dh with --reverse, per half.
# Two differences from FAR, both from W10's hand-back (reports/11-w10-ser-prep-handback.md):
#   - SER's clause-form filter is a ruling, so it is the second argument: `predicate` (wording-matched to SER's
#     predicate-naming I request) or `all` (every clause form). It picks W10's rank file
#     ser_<form>_rank_ids.json, and it is the --tag of every output directory.
#   - A form filter drops ranking rows, so the full ranking passes --ids <rank file> --ids-key rank_all (FAR's
#     omitted --ids because every train and validation row was eligible). I and user-neutral rows are kept when their
#     id is in the list, as for the halves.
# Pools: W10's sha256-checked copies, data/pools/ser_v2_user_{inversion,neutral} (pools_manifest_ser.json).
# Submit from the worktree root with the committed short sha and the form:
#
#   sbatch --account=beto-delta-gpu --partition=gpuH200x8-interactive,gpuA40x4-interactive --time=00:30:00 \
#       docs/research/neuron-partition/jobs/all_position_attribution_ser.sbatch <commit> <predicate|all>
#
# Login-node dry run (no GPU, no model; loads the tokenizer and the paired rows, prints counts and an estimate):
#
#   bash docs/research/neuron-partition/jobs/all_position_attribution_ser.sbatch <commit> <predicate|all> --dry-run
#
# Outputs: outputs/_analyses/neuron-partition/attribution/ser_v2_{dh,in}_train+validation_<form>_<commit>[_rev]/,
#          ser_v2_{dh,in}_train+validation_<form>_half{1,2}_<commit>/ and ser_v2_dh_..._<form>_half{1,2}_<commit>_rev/
# Not the 40 GB A100s: the 8B backward does not fit there.
#
#SBATCH --job-name=nrn-allpos-atp-ser
#SBATCH --account=beto-delta-gpu
#SBATCH --partition=gpuH200x8-interactive,gpuA40x4-interactive
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=logs/neuron_partition_all_position_ser_%j.out

set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-.}"

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ] || { [ "$#" -eq 3 ] && [ "$3" != "--dry-run" ]; }; then
    echo "usage: sbatch ... all_position_attribution_ser.sbatch <commit> <predicate|all> [--dry-run]" >&2
    exit 2
fi
COMMIT="$1"
FORM="$2"
DRY=()
if [ "$#" -eq 3 ]; then
    DRY=(--dry-run)
fi
case "$FORM" in
    predicate|all) ;;
    *) echo "form must be predicate or all, not: $FORM" >&2; exit 2 ;;
esac

profile="scripts/cluster/${DC_CLUSTER:-delta}.env"
if [ ! -f "$profile" ]; then
    echo "unknown cluster profile: $profile (DC_CLUSTER=${DC_CLUSTER:-})" >&2
    exit 2
fi
source "$profile"

set +eu
eval "$DC_ACTIVATE"
set -eu
export HF_HOME="$DC_HF_HOME"
if [ "$DC_HF_OFFLINE" = "1" ]; then
    export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
fi
export RESEARCH_DIRECTION=neuron-partition
nvidia-smi --query-gpu=name,memory.total --format=csv || [ "${#DRY[@]}" -eq 1 ]

DATA=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/data
RANK="$DATA/ser_${FORM}_rank_ids.json"
if [ ! -f "$RANK" ]; then
    echo "no rank file: $RANK (scripts/neuron_partition_data.py sample --task ser --clause-form $FORM)" >&2
    exit 2
fi
common=(--task ser_v2 --split train,validation --batch-size 4 --pool-dir "$DATA/pools" --commit "$COMMIT" "${DRY[@]}")
python scripts/neuron_attribution.py "${common[@]}" --ids "$RANK" --ids-key rank_all --tag "$FORM" --pair dh in
python scripts/neuron_attribution.py "${common[@]}" --ids "$RANK" --ids-key rank_all --tag "$FORM" --pair dh in --reverse
python scripts/neuron_attribution.py "${common[@]}" --ids "$RANK" --ids-key halves.A --tag "${FORM}_half1" --pair dh in
python scripts/neuron_attribution.py "${common[@]}" --ids "$RANK" --ids-key halves.A --tag "${FORM}_half1" --pair dh --reverse
python scripts/neuron_attribution.py "${common[@]}" --ids "$RANK" --ids-key halves.B --tag "${FORM}_half2" --pair dh in
python scripts/neuron_attribution.py "${common[@]}" --ids "$RANK" --ids-key halves.B --tag "${FORM}_half2" --pair dh --reverse
