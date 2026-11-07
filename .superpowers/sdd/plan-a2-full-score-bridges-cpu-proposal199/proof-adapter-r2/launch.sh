#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual Bridges CPU allocation required}"
P=/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/proof-adapter-r2
PY=python3
if [[ ${SLURM_JOB_ID} == 1 && -z ${SLURM_CLUSTER_NAME:-} && -n ${ADAPTER201_TEST_PYTHON:-} ]]; then PY=$ADAPTER201_TEST_PYTHON; fi
exec "$PY" "$P/host_supervisor.py" --output "$1" --manifest-sha256 "$2" --bindings "$3" --bindings-sha256 "$4"
