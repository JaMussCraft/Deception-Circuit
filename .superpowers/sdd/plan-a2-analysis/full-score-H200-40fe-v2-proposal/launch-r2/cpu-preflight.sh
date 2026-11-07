#!/usr/bin/env bash
set -euo pipefail
: "${SLURM_JOB_ID:?Actual root-admitted allocation required}"
: "${A2_SCORE_PREFLIGHT_OUTPUT:?Root fresh release/output required}"
export CUDA_VISIBLE_DEVICES=""
source "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/full-score-H200-40fe-v2-proposal/launch-r2/environment.sh"
exec "$DC_PYTHON" "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/full-score-H200-40fe-v2-proposal/launch-r2/preflight.py"
