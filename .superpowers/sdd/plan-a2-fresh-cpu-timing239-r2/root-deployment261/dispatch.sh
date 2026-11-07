#!/bin/bash
set -euo pipefail
root=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/root-deployment261
read -r config_sha < "$root/config.sha256"
[[ "$config_sha" =~ ^[0-9a-f]{64}$ ]]
exec bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/launch.sh --config "$root/config.json" --config-sha256 "$config_sha"
