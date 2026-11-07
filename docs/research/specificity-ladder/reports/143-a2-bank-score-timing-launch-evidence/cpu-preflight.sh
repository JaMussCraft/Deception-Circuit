#!/usr/bin/env bash
set -euo pipefail
: "${SLURM_JOB_ID:?Real CPU allocation required}"
: "${A2_TIMING_PREFLIGHT_OUTPUT:?Root supplies fresh preflight output}"
source /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/real-input-readiness/bank-scoring-timing/launch/environment.sh
export CUDA_VISIBLE_DEVICES=''
exec "$DC_PYTHON" /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/real-input-readiness/bank-scoring-timing/launch/preflight.py
