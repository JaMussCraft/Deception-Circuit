#!/usr/bin/env bash
set -euo pipefail
: "${SLURM_JOB_ID:?Actual root-admitted GPU allocation required}"
: "${A2_TIMING_ROOT_RELEASE:?Root new job/reservation/mapping admission required}"
: "${A2_TIMING_EXECUTION_OUTPUT:?Root supplies fresh timing receipt namespace}"
source /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/real-input-readiness/bank-scoring-timing/launch-g2/environment.sh
# Keep Slurm's actual CUDA_VISIBLE_DEVICES and all actual Slurm variables.
exec "$DC_PYTHON" /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/real-input-readiness/bank-scoring-timing/launch-g2/controller.py
