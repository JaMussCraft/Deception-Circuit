#!/bin/bash
set -euo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ "${1:-}" == --dry-run ]]; then
    exec "${A3_HOST_PYTHON:-python3}" -B "$SCRIPT_DIR/host.py" --dry-run
fi
: "${SLURM_JOB_ID:?actual CPU allocation required}"
exec "${A3_HOST_PYTHON:-python3}" -B "$SCRIPT_DIR/host.py" --config "$1" --config-sha256 "$2" --manifest-sha256 "$3"
