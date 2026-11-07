#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?actual Bridges CPU allocation required}"
[[ "$SLURM_JOB_ID" =~ ^[0-9]+$ ]]
PHYSICAL=/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment
REL=Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199
PACKET="$PHYSICAL/$REL/proof-adapter-r3"
JOB="$PHYSICAL/$REL/root-genuine-proof-r2/job-$SLURM_JOB_ID"
MANIFEST_SHA=4e4b4bcf1ddcd6481fac1eccd966a2a1cbfa385b2bd16a9a00504cfaa05def3f
[[ -d "$JOB" && ! -L "$JOB" && "$(stat -c %u "$JOB")" == "$(id -u)" ]]
p="$JOB"
while [[ "$p" != / ]]; do [[ ! -L "$p" ]]; p="$(dirname "$p")"; done
[[ "$(realpath -e "$JOB")" == "$JOB" ]]
[[ -f "$JOB/bindings.json" && ! -L "$JOB/bindings.json" ]]
[[ -f "$JOB/bindings.sha256" && ! -L "$JOB/bindings.sha256" ]]
IFS= read -r BINDING_SHA < "$JOB/bindings.sha256" || [[ -n "$BINDING_SHA" ]]
[[ "$BINDING_SHA" =~ ^[0-9a-f]{64}$ ]]
cmp -s "$JOB/bindings.sha256" <(printf '%s\n' "$BINDING_SHA") || cmp -s "$JOB/bindings.sha256" <(printf '%s' "$BINDING_SHA")
[[ "$(sha256sum "$JOB/bindings.json" | cut -d' ' -f1)" == "$BINDING_SHA" ]]
[[ -f "$PACKET/manifest.json" && ! -L "$PACKET/manifest.json" ]]
[[ "$(sha256sum "$PACKET/manifest.json" | cut -d' ' -f1)" == "$MANIFEST_SHA" ]]
exec bash "$PACKET/launch.sh" "$JOB/execution" "$MANIFEST_SHA" "$JOB/bindings.json" "$BINDING_SHA"
