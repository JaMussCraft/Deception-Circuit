#!/bin/bash
set -euo pipefail
root=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-deployment293/base-1
read -r config_sha < "$root/config.sha256"
[[ "$config_sha" =~ ^[0-9a-f]{64}$ ]]
exec bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r8-sharded/cpu.sbatch "$root/config.json" "$config_sha" d471c56a4548bb5fc39cd7a635a0426e1f22b769dee5fae058244e1a052f0797
