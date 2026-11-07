#!/bin/bash
set -euo pipefail
packet=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2
exec python3 "$packet/runner.py" "$@"
