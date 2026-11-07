#!/bin/bash
# Root binds the actual host interpreter/script and submits all resources separately.
set -euo pipefail
if [[ "${1:-}" == --dry-run ]]; then
 exec "${A3_HOST_PYTHON:-python3}" -B "${A3_CANDIDATE311_HOST:-/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/candidate-producer311/host.py}" --dry-run
fi
: "${SLURM_JOB_ID:?actual CPU job required}"
: "${A3_CANDIDATE311_HOST:?root must bind the absolute host.py path}"
[[ "$A3_CANDIDATE311_HOST" == /* ]] || exit 2
export A3_WRAPPER_START_SECONDS="$(date +%s.%N)"
exec "${A3_HOST_PYTHON:-python3}" -B "$A3_CANDIDATE311_HOST" --config "$1" --config-sha256 "$2"
