#!/bin/bash
# instructed-route B2 P1 capture (plans/B2-plan.md sections 1 and 4, ticket T8): one GPU job that runs
# scripts/falsity_probe_capture.py over a capture plan and writes the Readout residuals, item logits, per-token DLA
# and run_manifest.json. Patterned on scripts/analyze_components.sbatch (cluster profile, mgnp) and
# scripts/jobs/run_sdr_cue_probe.sh (cwd guard, offline HF, BLAS threads 1).
#
# Submit from the instructed-route worktree root, after `mkdir -p logs`, with --time on the command line (this
# header sets none on purpose) and the partition and account chosen at submit time:
#
#   sbatch --time=00:45:00 --partition=gpuH200x8-interactive --account=bimc-delta-gpu \
#       scripts/jobs/run_b2_capture.sbatch
#
# With no arguments it runs the real plan into outputs/_analyses/instructed-route-b2/p1. With arguments they pass
# through unchanged, so the smoke job names its own plan and output directory:
#
#   sbatch --time=00:30:00 ... scripts/jobs/run_b2_capture.sbatch \
#       --plan docs/research/instructed-route/jobs/B2-p1-smoke.json \
#       --output-dir outputs/_analyses/instructed-route-b2/p1-smoke
#
# Login check first (no model, no GPU):
#   python scripts/falsity_probe_capture.py --plan docs/research/instructed-route/jobs/B2-p1-plan.json \
#       --output-dir <scratch dir> --dry-run --check-encoding
#SBATCH --job-name=b2-p1-capture
#SBATCH --account=bimc-delta-gpu
#SBATCH --partition=gpuA100x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --output=logs/b2_p1_capture_%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"

WORKTREE="/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route"
if [[ ! -f scripts/falsity_probe_capture.py || "$(pwd -P)" != "$WORKTREE" ]]; then
    echo "Run from the instructed-route worktree root ($WORKTREE); cwd is $(pwd -P)." >&2
    exit 1
fi
mkdir -p logs

if [ "$#" -eq 0 ]; then
    set -- --plan docs/research/instructed-route/jobs/B2-p1-plan.json \
        --output-dir outputs/_analyses/instructed-route-b2/p1
fi

profile="scripts/cluster/${DC_CLUSTER:-delta}.env"
if [ ! -f "$profile" ]; then
    echo "unknown cluster profile: $profile (DC_CLUSTER=${DC_CLUSTER:-})" >&2
    exit 2
fi
source "$profile"

set +u
eval "$DC_ACTIVATE" || { echo "environment activation failed: $DC_ACTIVATE" >&2; exit 1; }
set -u
export HF_HOME="$DC_HF_HOME"
# The model is already in HF_HOME; the capture never downloads.
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1

echo "b2-p1-capture: host $(hostname), job ${SLURM_JOB_ID:-none}, python $(command -v python)"
exec python scripts/falsity_probe_capture.py "$@"
