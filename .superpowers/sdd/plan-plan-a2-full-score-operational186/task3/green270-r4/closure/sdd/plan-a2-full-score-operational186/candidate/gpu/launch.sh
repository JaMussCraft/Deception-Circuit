#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual Bridges GPU allocation required}"
: "${A2_FULL_SCORE_PACKET:?absolute immutable packet path required}"
case "$A2_FULL_SCORE_PACKET" in
  /*) ;;
  *) echo 'Absolute packet path required.' >&2; exit 1 ;;
esac
case "/$A2_FULL_SCORE_PACKET/" in
  */../*) echo 'Parent traversal forbidden.' >&2; exit 1 ;;
esac
# Slurm spools $0; the root supplies the separately hash-validated packet path.
export PYTHONDONTWRITEBYTECODE=1
exec python3 "$A2_FULL_SCORE_PACKET/host-launch.py"
