#!/usr/bin/env bash
# Root-owned future command template, not admission and not executed by CPU preparation.
# Existing mask job 23444798 retains its original immutable reservation/mapping.
set -euo pipefail
source /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/environment.sh
: "${A3_EDGE_LEDGER:?Root must provide a fresh successor ledger mapping bound to this source/output/inventory}"
: "${A3_EDGE_RESERVATION:?Root must provide the matching original edge M1 reservation admission}"
: "${SLURM_JOB_ID:?Root must arrange an actual H200 allocation before model work}"
export SPECIFICITY_A3_EDGE_REPO_ROOT="$B"
cd "$B"
exec bash "$B/scripts/jobs/specificity_a3_edges.sh" --stage pilot --measure-stage fit --steps 8 --design "$O/canonical/design.json" --commit "$C" --work-dir "$O/edge" --prepared "$O/edge/prepared" --inventory "$O/edge/inventory-pilot" --ledger-snapshot "$A3_EDGE_LEDGER" --reservation "$A3_EDGE_RESERVATION" --registry "$W/docs/research/held_out.json"
