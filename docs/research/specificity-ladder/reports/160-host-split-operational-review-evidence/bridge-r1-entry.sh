#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual CPU allocation required}"
exec python3 "$(dirname "$0")/supervisor.py" --config "$1" --config-sha256 "$2"
