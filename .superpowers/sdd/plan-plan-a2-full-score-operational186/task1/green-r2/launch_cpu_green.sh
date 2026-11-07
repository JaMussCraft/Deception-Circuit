#!/bin/bash
set -euo pipefail
# Slurm spools $0; preserve the independently pinned absolute packet path.
PACKET=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2
exec /sw/external/python/anaconda3/bin/python3.9 "$PACKET/run_cpu_green.py" "$@"
