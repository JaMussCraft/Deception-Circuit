#!/bin/bash
# neuron-partition: set ablation of MLP hidden neurons under the twin, mean and zero references
# (spec.md item 10 "Ablation"), one GPU job over every set of a sets file. Runs
# scripts/neuron_set_ablation.py, which loads the model once and loops over sets and references, and writes
# summary.json, rows.jsonl and run_manifest.json into the output dir.
#
# Arguments: <sets.json> <ids.json> <output_dir> [extra args passed to neuron_set_ablation.py]
#
# Submit from the repository root (the Bridges-2 clone or the Delta worktree), with --time on the command line
# (this header sets none on purpose; size it from the CLI's --dry-run estimate plus a buffer) and `logs/` present.
#
# Bridges-2 (first choice; login nodes set SBATCH_EXPORT=NONE, so export explicitly; DC_B2_ALLOC names the clone
# path and must stay cis260361p, -A picks the charge):
#
#   sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260372p -p GPU-shared \
#       --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 02:30:00 --job-name=np-ablate \
#       docs/research/neuron-partition/jobs/ablation_cells.sbatch \
#       outputs/_analyses/neuron-partition/sets/far_sets.json \
#       outputs/_analyses/neuron-partition/ids/far_test_seed2.json \
#       outputs/_analyses/neuron-partition/ablation/far-cell1 --max-length 128
#
# Delta (A40, H100 or H200 only; 8B activations and the twin capture do not fit a 40 GB A100):
#
#   sbatch --account=bimc-delta-gpu --partition=gpuH200x8 --gpus-per-node=1 -t <from the pilot timing> \
#       docs/research/neuron-partition/jobs/ablation_cells.sbatch <sets.json> <ids.json> <output_dir>
#
# Pilot first, to measure seconds per forward (summary.json `timing`) before sizing the full cell's walltime:
# `--limit 16` is 2 batches per condition (IOI's 100 rows and the 400-row mean bank are not limited): 7,354
# forwards for 84 sets, about 4.5 min of forwards plus the model load by the dry run, so it fits a Delta
# interactive partition's one-hour slot:
#
#   sbatch --account=bimc-delta-gpu --partition=gpuH200x8-interactive --gpus-per-node=1 -t 00:30:00 \
#       docs/research/neuron-partition/jobs/ablation_cells.sbatch <sets.json> <ids.json> <pilot_dir> \
#       --max-length 128 --limit 16
#
# Every finished cell is appended to <output_dir>/cells_partial.jsonl as it completes, so a job killed at its
# walltime keeps the cells it finished; summary.json and rows.jsonl are written only at the end.
#
# The user-turn I and user-neutral pools are untracked HF dataset dicts inside the Codex worktree on Delta. On
# Bridges-2 they must be copied first (read-only, sha256 recorded by run_manifest.json on the host that runs).
# Their location: NP_I_DIR and NP_N_DIR when set; else, on Bridges-2,
# outputs/_inputs/neuron-partition/<task>_v2_user_{inversion,neutral} under the repository root; on Delta, the
# specificity-ladder A1 control cell (read only, never written). NP_TASK picks the task (default far).
#
# Login-node check first (no GPU, no model; builds every batch with the tokenizer and prints the estimate):
#   bash docs/research/neuron-partition/jobs/ablation_cells.sbatch <sets.json> <ids.json> <scratch_dir> --dry-run
#
#SBATCH --job-name=np-ablate
#SBATCH --account=bimc-delta-gpu
#SBATCH --partition=gpuH200x8
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --output=logs/np_ablate_%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"

if [[ ! -f scripts/neuron_set_ablation.py ]]; then
    echo "Run from the Deception-Circuit repository root; cwd is $(pwd -P)." >&2
    exit 1
fi
if [ "$#" -lt 3 ]; then
    echo "usage: sbatch [options] $0 <sets.json> <ids.json> <output_dir> [extra args]" >&2
    exit 2
fi
SETS="$1"
IDS="$2"
OUT="$3"
shift 3
for path in "$SETS" "$IDS"; do
    if [[ ! -f "$path" ]]; then
        echo "no such file: $path" >&2
        exit 2
    fi
done
mkdir -p logs

profile="scripts/cluster/${DC_CLUSTER:-delta}.env"
if [ ! -f "$profile" ]; then
    echo "unknown cluster profile: $profile (DC_CLUSTER=${DC_CLUSTER:-})" >&2
    exit 2
fi
source "$profile"

# ~/.bashrc (Delta's activation) is not errexit- or nounset-clean, so both are off while it runs.
set +eu
eval "$DC_ACTIVATE"
activated=$?
set -eu
if [ "$activated" -ne 0 ]; then
    echo "environment activation failed: $DC_ACTIVATE" >&2
    exit 1
fi
export HF_HOME="$DC_HF_HOME"
# The model is already in HF_HOME; this job never downloads.
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export RESEARCH_DIRECTION=neuron-partition

TASK="${NP_TASK:-far}"
if [ "${DC_CLUSTER_NAME:-delta}" = "bridges2" ]; then
    pools="outputs/_inputs/neuron-partition"
else
    pools="/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a1-control-77b6487-m07"
fi
I_DIR="${NP_I_DIR:-${pools}/${TASK}_v2_user_inversion}"
N_DIR="${NP_N_DIR:-${pools}/${TASK}_v2_user_neutral}"
for path in "$I_DIR" "$N_DIR"; do
    if [[ ! -d "$path" ]]; then
        echo "user-turn pool not found: $path (copy it, or set NP_I_DIR / NP_N_DIR)" >&2
        exit 2
    fi
done

echo "np-ablate: cluster ${DC_CLUSTER_NAME:-delta}, host $(hostname), job ${SLURM_JOB_ID:-none}," \
     "python $(command -v python), task ${TASK}"
echo "  sets $SETS  ids $IDS  out $OUT"
echo "  I $I_DIR"
echo "  N $N_DIR"
exec python scripts/neuron_set_ablation.py --task "$TASK" --sets "$SETS" --ids "$IDS" \
    --i-dir "$I_DIR" --n-dir "$N_DIR" --output-dir "$OUT" "$@"
