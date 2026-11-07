#!/usr/bin/env bash
set -euo pipefail
: "${SLURM_JOB_ID:?Actual root-admitted allocation required}"
: "${A2_SCORE_ROOT_RELEASE:?Root fresh release/output required}"
: "${A2_SCORE_EXECUTION_OUTPUT:?Fresh operational output required}"
source "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/full-score-H200-40fe-v2-proposal/launch/environment.sh"
exec "$DC_PYTHON" "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/full-score-H200-40fe-v2-proposal/launch/controller.py"
