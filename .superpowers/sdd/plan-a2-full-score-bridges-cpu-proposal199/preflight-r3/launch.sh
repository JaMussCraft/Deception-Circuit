#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual Bridges CPU allocation required}"
P=/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/preflight-r3
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B "$P/host_probe.py" --output "$1" --manifest-sha256 "$2"
