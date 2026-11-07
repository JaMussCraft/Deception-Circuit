#!/bin/bash
set -euo pipefail
TASK2_PACKET=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r3
exec /sw/external/python/anaconda3/bin/python3.9 "$TASK2_PACKET/run_cpu_green.py" "$@"
