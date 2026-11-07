#!/bin/bash
# Root supplies the authenticated existing supervisor, interpreter and all resources.
# Absolute adapter path remains valid after a scheduler relocates this shell file.
set -euo pipefail
packet=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/prepared-resource-runner278
if [[ "${1:-}" == --dry-run ]]; then
    exec "${MEASUREMENT_PYTHON:-/sw/external/python/anaconda3/bin/python3.9}" -B "$packet/runner.py" --dry-run
fi
: "${MEASUREMENT_PYTHON:?unbound: root must supply the actual interpreter}"
: "${MEASUREMENT_SUPERVISOR:?unbound: root must supply the authenticated existing supervisor}"
[[ "$MEASUREMENT_PYTHON" == /* && "$MEASUREMENT_SUPERVISOR" == /* ]] || exit 2
exec "$MEASUREMENT_PYTHON" -B "$MEASUREMENT_SUPERVISOR" "$@"
