#!/bin/bash
# Print the evaluate_circuit.py arguments of one format-control job (shell-quoted).
# usage: bash outputs/_launch_format_control/cell_cmd.sh <suite> <job>
#   e.g. bash outputs/_launch_format_control/cell_cmd.sh format-control-far-nls0.3 D_and_F__far
# Jobs and cells are listed in suite_manifest.json (`fc_launch.py plan` rewrites it).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec python outputs/_launch_format_control/fc_launch.py args "$@"
