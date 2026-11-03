#!/bin/bash
# deception-divergence D2 premise (plans/D2-plan.md, spec.md rulings R7 to R13): one GPU job that computes the
# elicitation features, selects and ablates the refusal direction, and generates the acts-on-it replies for
# far_v2, sdr_v2 and ser_v2, then reads the classifier arm. The judge runs afterwards on the login node, by the
# orchestrator, after freeze G-D2 (`scripts/d2_premise.py judge --judge-stage ...`), followed by `read --labels`.
# Patterned on scripts/jobs/run_d1_visibility.sh (cluster profile, cwd guard, offline HF, BLAS threads 1).
#
# Stages: with --dry-run, `build --dry-run` only (CPU, no GPU, writes build reports); otherwise
# `features direction generate` in one process (one model load), then `read`. Every other argument passes through
# (for example --tasks far_v2, or --max-test-ids 150 as the pre-registered fallback cap).
#
# Login-node dry run (no GPU, no sbatch):
#   bash scripts/jobs/run_d2_premise.sh --dry-run
#
# Bridges-2 (from Delta, after pushing the branch and `scripts/remote/b2.sh sync-code --branch deception-divergence`):
#   sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260361p -p GPU-shared \
#       --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 01:00:00 --job-name=d2-premise \
#       scripts/jobs/run_d2_premise.sh
#   scripts/remote/b2.sh fetch outputs/_analyses/deception-divergence
#
# Delta (from the worktree root; --time on the command line, none in this header):
#   sbatch --time=01:00:00 --partition=gpuA100x4 --account=bgrb-delta-gpu scripts/jobs/run_d2_premise.sh
#
# DD_COMMIT is the worktree HEAD (`git rev-parse HEAD`, read-only, skipped under --dry-run, kept when already set);
# the GPU stages refuse to run without a 40-hex value.
#SBATCH --job-name=d2-premise
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --output=logs/d2_premise_%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"

DELTA_WORKTREE="/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence"
profile="scripts/cluster/${DC_CLUSTER:-delta}.env"
if [ ! -f "$profile" ]; then
    echo "unknown cluster profile: $profile (DC_CLUSTER=${DC_CLUSTER:-})" >&2
    exit 2
fi
source "$profile"
if [ "${DC_CLUSTER_NAME}" = "delta" ]; then
    expected="$DELTA_WORKTREE"
else
    expected="$DC_REPO_ROOT"
fi
if [[ ! -f scripts/d2_premise.py || "$(pwd -P)" != "$(cd "$expected" && pwd -P)" ]]; then
    echo "Run from $expected (cluster ${DC_CLUSTER_NAME}); cwd is $(pwd -P)." >&2
    exit 1
fi
mkdir -p logs

DRY=0
ARGS=()
for a in "$@"; do
    if [ "$a" = "--dry-run" ]; then DRY=1; else ARGS+=("$a"); fi
done

if [ -z "${D2_PYTHON:-}" ]; then
    set +u
    eval "$DC_ACTIVATE" || { echo "environment activation failed: $DC_ACTIVATE" >&2; exit 1; }
    set -u
    D2_PYTHON=python
fi
export HF_HOME="$DC_HF_HOME"
# The model and tokenizer are already in HF_HOME; nothing downloads.
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1

if [ "$DRY" = 0 ]; then
    DD_COMMIT="${DD_COMMIT:-$(git rev-parse HEAD)}"
    export DD_COMMIT
fi
echo "d2-premise: host $(hostname), cluster ${DC_CLUSTER_NAME}, job ${SLURM_JOB_ID:-none}, commit ${DD_COMMIT:-none}," \
     "python $(command -v "$D2_PYTHON"), dry-run $DRY"

run() { "$D2_PYTHON" -I scripts/d2_premise.py "$@"; }

if [ "$DRY" = 1 ]; then
    run build --dry-run ${ARGS[@]+"${ARGS[@]}"}
    exit 0
fi
if [ ! -f data/d2/d2_inputs.json ]; then
    echo "data/d2/d2_inputs.json is missing; it is committed with the branch" >&2
    exit 1
fi
run features direction generate ${ARGS[@]+"${ARGS[@]}"}
run read ${ARGS[@]+"${ARGS[@]}"}
