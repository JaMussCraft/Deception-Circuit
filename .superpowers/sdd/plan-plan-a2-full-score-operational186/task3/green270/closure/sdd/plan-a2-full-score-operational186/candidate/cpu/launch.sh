#!/bin/bash
set -euo pipefail
packet=${A2_FULL_SCORE_CPU_PACKET:?absolute immutable CPU packet required}
[[ "$packet" == /* && -f "$packet/supervisor.py" && ! -L "$packet/supervisor.py" ]]
exec python3 "$packet/supervisor.py" "$@"
