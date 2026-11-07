#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual Bridges CPU allocation required}"
P=/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/a3-green-bridges-transport229-r3
exec python3 -B "$P/host.py" --config "$1" --config-sha256 "$2" --manifest-sha256 "$3"
