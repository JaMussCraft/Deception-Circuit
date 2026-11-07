#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual Bridges H100 allocation required}"
[[ "$SLURM_JOB_ID" =~ ^[0-9]+$ ]]
PHYSICAL=/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment
VIRTUAL=/projects/beto/swong2/Alignment
REL=Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103
JOB="$PHYSICAL/$REL/root-H100-R5/job-$SLURM_JOB_ID"
[[ -f "$JOB/config.json" && ! -L "$JOB/config.json" ]]
[[ -f "$JOB/config.sha256" && ! -L "$JOB/config.sha256" ]]
read -r CONFIG_SHA < "$JOB/config.sha256"
[[ "$CONFIG_SHA" =~ ^[0-9a-f]{64}$ ]]
[[ "$(sha256sum "$JOB/config.json" | cut -d' ' -f1)" == "$CONFIG_SHA" ]]
[[ "$(sha256sum "$PHYSICAL/$REL/h100-timing-launch-r5/manifest.json" | cut -d' ' -f1)" == "661d16c5f38149b4d258fa372472dd5aab57cd0afe0a131aa6b5683b735657bc" ]]
export A2_H100_BOUND_CONFIG="$JOB/config.json"
export A2_H100_BOUND_CONFIG_SHA256="$CONFIG_SHA"
export A2_TIMING_EXECUTION_OUTPUT="$VIRTUAL/$REL/root-H100-R5/job-$SLURM_JOB_ID/execution"
export A2_H100_RELEASE_DIRECTORY="$VIRTUAL/$REL/root-H100-R5/job-$SLURM_JOB_ID/releases"
exec bash "$PHYSICAL/$REL/h100-timing-launch-r5/launch.sh"
