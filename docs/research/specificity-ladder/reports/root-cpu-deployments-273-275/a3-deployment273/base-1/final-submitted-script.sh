#!/bin/bash
set -euo pipefail
root=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-deployment273/base-1
read -r config_sha < "$root/config.sha256"
[[ "$config_sha" =~ ^[0-9a-f]{64}$ ]]
exec bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-r2-sharded/cpu.sbatch "$root/config.json" "$config_sha" 46d52e51eefcde1b59147e59750651f44e156607dac1e95a40d814360e64e96c
