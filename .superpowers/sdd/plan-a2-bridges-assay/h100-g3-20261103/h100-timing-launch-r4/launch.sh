#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual Bridges GPU allocation required}"
exec python3 "$(dirname "$0")/host-launch.py"
