#!/bin/bash
set -euo pipefail
export CUDA_VISIBLE_DEVICES=
export A3_HOST_PYTHON=/usr/bin/python3
export A3_CANDIDATE311_HOST=/ocean/projects/cis260361p/swong2/specificity-ladder-a3-producer-2ba697d7f5fd/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/candidate-producer311/host.py
exec bash /ocean/projects/cis260361p/swong2/specificity-ladder-a3-producer-2ba697d7f5fd/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/candidate-producer311/launch.sh /ocean/projects/cis260361p/swong2/specificity-ladder-a3-producer-2ba697d7f5fd/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/producer-deployment320/config.json "$(cat /ocean/projects/cis260361p/swong2/specificity-ladder-a3-producer-2ba697d7f5fd/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/producer-deployment320/config.sha256)"
