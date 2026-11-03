#!/bin/bash
# deception-divergence D1 follow-up (spec.md ruling R6): one GPU job that scores the phrasing-4 arms (L4_visible,
# L4_hidden: one sentence appended at the end of the user turn) on the D1 job's live ids of far_v2, sdr_v2 and
# ser_v2, plus D again on the 1,000 anchors per task as the cross-job control, then runs the CPU read.
# Patterned on scripts/jobs/run_d1_visibility.sh (cluster profile, cwd guard, offline HF, BLAS threads 1).
#
# Inputs: the D1 outputs under outputs/_analyses/deception-divergence/d1/<task>/ (sample.jsonl,
# sample_report.json, scores.jsonl, run_manifest.json), which every stage hash-checks against D1's own records.
# There is no sample stage: the ids are D1's.
#
# Stages: `build --dry-run` (with --dry-run: CPU only, writes build_report_l4.json and stops) or `score` and
# `read`. Every other argument passes through to every stage (for example --tasks far_v2, --max-ids 200 with a
# copy of the D1 inputs under --out-root <dir> for a smoke).
#
# Login-node dry run (no GPU, no sbatch):
#   bash scripts/jobs/run_d1_followup.sh --dry-run
#
# Delta (from the worktree root, after `mkdir -p logs`; --time on the command line, none in this header):
#   sbatch --time=HH:MM:SS --partition=gpuA100x4 --account=bgrb-delta-gpu scripts/jobs/run_d1_followup.sh
#
# Bridges-2 (from the Bridges-2 clone, after syncing the branch; the D1 outputs of job 50145353 must be present
# there unchanged):
#   sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=<alloc> -A <alloc> -p GPU-shared \
#       --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t HH:MM:SS --job-name=d1-followup \
#       scripts/jobs/run_d1_followup.sh
#
# DD_COMMIT is the worktree HEAD (`git rev-parse HEAD`, read-only, skipped under --dry-run, kept when already set);
# the score stage refuses to run without a 40-hex value.
#SBATCH --job-name=d1-followup
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --output=logs/d1_followup_%j.out

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
if [[ ! -f scripts/d1_followup.py || "$(pwd -P)" != "$(cd "$expected" && pwd -P)" ]]; then
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
echo "d1-followup: host $(hostname), cluster ${DC_CLUSTER_NAME}, job ${SLURM_JOB_ID:-none}, commit ${DD_COMMIT:-none}," \
     "python $(command -v "$D1_PYTHON"), dry-run $DRY"

run() { "$D1_PYTHON" -I scripts/d1_followup.py "$@"; }

if [ "$DRY" = 1 ]; then
    run build --dry-run ${ARGS[@]+"${ARGS[@]}"}
    exit 0
fi
run score ${ARGS[@]+"${ARGS[@]}"}
run read ${ARGS[@]+"${ARGS[@]}"}
