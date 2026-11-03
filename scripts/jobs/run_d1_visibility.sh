#!/bin/bash
# deception-divergence D1 (START.md item D1, spec.md R1 to R4): one GPU job that scores the listener-knowledge
# arms and the role-matched operator-turn inversion on the D1 sample of far_v2, sdr_v2 and ser_v2.
# Patterned on scripts/jobs/run_b2_capture.sbatch (cluster profile, cwd guard, offline HF, BLAS threads 1).
#
# Stages: `sample` (CPU, deterministic; reuses an identical sample.jsonl and refuses a different one), then either
# `build --dry-run` (with --dry-run: CPU only, writes build_report.json and stops) or `score` and `read`.
# Every other argument passes through to every stage (for example --tasks far_v2, --max-ids 200 with
# --out-root <dir> for a smoke, --max-seq-length N).
#
# Login-node dry run (no GPU, no sbatch):
#   bash scripts/jobs/run_d1_visibility.sh --dry-run
#
# Delta (from the worktree root, after `mkdir -p logs`; --time on the command line, none in this header):
#   sbatch --time=HH:MM:SS --partition=gpuA100x4 --account=bgrb-delta-gpu scripts/jobs/run_d1_visibility.sh
#
# Bridges-2 (from Delta, after pushing the branch and `scripts/remote/b2.sh sync-code --branch deception-divergence`;
# b2.sh adds --export=ALL,DC_CLUSTER=bridges2 and --gpus-per-node=h100-80:1; the job regenerates the sample):
#   scripts/remote/b2.sh submit --time HH:MM:SS --script scripts/jobs/run_d1_visibility.sh --job-name d1-visibility
#   scripts/remote/b2.sh fetch outputs/_analyses/deception-divergence
#
# DD_COMMIT is the worktree HEAD (`git rev-parse HEAD`, read-only, skipped under --dry-run, kept when already set);
# the score stage refuses to run without a 40-hex value.
#SBATCH --job-name=d1-visibility
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --output=logs/d1_visibility_%j.out

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
if [[ ! -f scripts/d1_visibility.py || "$(pwd -P)" != "$(cd "$expected" && pwd -P)" ]]; then
    echo "Run from $expected (cluster ${DC_CLUSTER_NAME}); cwd is $(pwd -P)." >&2
    exit 1
fi
mkdir -p logs

DRY=0
ARGS=()
for a in "$@"; do
    if [ "$a" = "--dry-run" ]; then DRY=1; else ARGS+=("$a"); fi
done

if [ -z "${D1_PYTHON:-}" ]; then
    set +u
    eval "$DC_ACTIVATE" || { echo "environment activation failed: $DC_ACTIVATE" >&2; exit 1; }
    set -u
    D1_PYTHON=python
fi
export HF_HOME="$DC_HF_HOME"
# The model and tokenizer are already in HF_HOME; nothing downloads.
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1

# The score stage needs the commit; the CPU dry run does not, so it never reads it.
if [ "$DRY" = 0 ]; then
    DD_COMMIT="${DD_COMMIT:-$(git rev-parse HEAD)}"
    export DD_COMMIT
fi
echo "d1-visibility: host $(hostname), cluster ${DC_CLUSTER_NAME}, job ${SLURM_JOB_ID:-none}, commit ${DD_COMMIT:-none}," \
     "python $(command -v "$D1_PYTHON"), dry-run $DRY"

run() { "$D1_PYTHON" -I scripts/d1_visibility.py "$@"; }

run sample ${ARGS[@]+"${ARGS[@]}"}
if [ "$DRY" = 1 ]; then
    run build --dry-run ${ARGS[@]+"${ARGS[@]}"}
    exit 0
fi
run score ${ARGS[@]+"${ARGS[@]}"}
run read ${ARGS[@]+"${ARGS[@]}"}
