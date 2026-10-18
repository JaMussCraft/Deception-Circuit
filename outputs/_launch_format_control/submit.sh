#!/bin/bash
# Submit one Slurm job per ready format-control job (dry-run passed, inputs
# configured, not yet submitted), alternating accounts; records job ids in
# suite_manifest.json. --dry prints the exact sbatch lines and submits nothing.
#
# usage: bash outputs/_launch_format_control/submit.sh [--dry]
#            [--accounts bgrb-delta-gpu bimc-delta-gpu ...]
#            [--partition gpuA40x4,gpuA100x4,gpuA100x8] [--time HH:MM:SS]
#            [--suite <suite>]... [--job <job>]... [--resubmit]
#
# Any account (beto/bimc/bgrb-delta-gpu) and partition is allowed; check
# fairshare first (sprio, sbatch --test-only). Without --time, each job gets its
# dry-run estimate x 1.5 in quarter hours (at least one hour).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec python outputs/_launch_format_control/fc_launch.py submit "$@"
