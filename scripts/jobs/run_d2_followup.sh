#!/bin/bash
# deception-divergence D2 follow-up (plans/D2-followup-plan.md, spec.md ruling R15): one GPU job that recomputes the
# drift anchor (D2's train D rows), computes the HI, DT, HT and IH elicitation features and the ablated HI features
# with D2's stored refusal direction on the full-sequence path of record (R14), then reads the result. No direction
# stage, no generation, no judge. Patterned on scripts/jobs/run_d2_premise.sh (cluster profile, cwd guard, offline
# HF, BLAS threads 1).
#
# Stages: with --dry-run, `build --dry-run` only (CPU, no GPU, writes the build report; exit status 1 when anything
# blocks submission); otherwise `features` (one model load), then `read`. Every other argument passes through.
#
# Login-node dry run (no GPU, no sbatch):
#   bash scripts/jobs/run_d2_followup.sh --dry-run \
#       --report docs/research/deception-divergence/results/d2_followup/build_report.json
#
# Bridges-2 (from Delta, after pushing the branch and `scripts/remote/b2.sh sync-code --branch deception-divergence`;
# D2's outputs/_analyses/deception-divergence/d2 must already be in the Bridges-2 clone, as job 50155519 wrote them):
#   sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260361p -p GPU-shared \
#       --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 00:45:00 --job-name=d2-followup \
#       scripts/jobs/run_d2_followup.sh
#   scripts/remote/b2.sh fetch outputs/_analyses/deception-divergence/d2_followup
#
# DD_COMMIT is the worktree HEAD (`git rev-parse HEAD`, read-only, skipped under --dry-run, kept when already set);
# the features stage refuses to run without a 40-hex value.
#SBATCH --job-name=d2-followup
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --output=logs/d2_followup_%j.out

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
if [[ ! -f scripts/d2_followup.py || "$(pwd -P)" != "$(cd "$expected" && pwd -P)" ]]; then
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
echo "d2-followup: host $(hostname), cluster ${DC_CLUSTER_NAME}, job ${SLURM_JOB_ID:-none}, commit ${DD_COMMIT:-none}," \
     "python $(command -v "$D2_PYTHON"), dry-run $DRY"

run() { "$D2_PYTHON" -I scripts/d2_followup.py "$@"; }

if [ "$DRY" = 1 ]; then
    run build --dry-run ${ARGS[@]+"${ARGS[@]}"}
    exit 0
fi
for f in data/d2/d2_inputs.json data/d2/d2_followup_clauses.json \
         outputs/_analyses/deception-divergence/d2/refusal_direction.pt; do
    if [ ! -f "$f" ]; then
        echo "$f is missing" >&2
        exit 1
    fi
done
run features ${ARGS[@]+"${ARGS[@]}"}
run read ${ARGS[@]+"${ARGS[@]}"}
