#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual held/released Delta CPU job required}"
[[ "$SLURM_JOB_ID" =~ ^[0-9]+$ ]]
ROOT=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/root-Delta-model-preflight
JOB="$ROOT/job-$SLURM_JOB_ID"
[[ -f "$JOB/config.json" && ! -L "$JOB/config.json" ]]
[[ -f "$JOB/config.sha256" && ! -L "$JOB/config.sha256" ]]
read -r CONFIG_SHA < "$JOB/config.sha256"
[[ "$CONFIG_SHA" =~ ^[0-9a-f]{64}$ ]]
[[ "$(sha256sum "$JOB/config.json" | cut -d' ' -f1)" == "$CONFIG_SHA" ]]
[[ "$(sha256sum /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/delta-model-phase-preflight-r2/implementation-manifest.json | cut -d' ' -f1)" == "6c0fa366c2176f61999c86240b8d3049608eb5ce3c833fc817a241962215c42a" ]]
[[ "$(sha256sum /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/h100-timing-launch-r5/manifest.json | cut -d' ' -f1)" == "661d16c5f38149b4d258fa372472dd5aab57cd0afe0a131aa6b5683b735657bc" ]]
exec bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/delta-model-phase-preflight-r2/launch.sh "$JOB/config.json" "$CONFIG_SHA"
