# A2 Bridges2 portability: read-only assessment

The existing launcher accepts `DC_CLUSTER=bridges2` and an actual single H100,
but the current frozen application is not independently relocatable by that switch.
No source, data, config, reservation, job or remote system was changed for this note.
Source-cost implementation remains held for independent plan review.

## Smallest reviewed transfer set

Use the intact application archive and snapshot, not an unaudited import subset:
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/application.tar` and sibling `snapshot.json`, with its declared
source inventory and the original `outputs`, `data`, `logs` and protected-registry links.
The archive includes the actual wrapper `scripts/jobs/specificity_twin_training.sh`,
`scripts/twin_training.py`, frozen default config, training/model/data code and Bridges2
profile. The accepted auditor requires the complete declared inventory, ordinary source
files and exact archive/snapshot hashes: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a2_mask_comparison.py`.

For an SDR-only move, the exact data/reference closure is:

| Item | Required bytes/reference |
|---|---|
| Operational config | Unchanged `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-timing-h200-config.json`; the wrapper's frozen default config ships in the source archive. |
| Build | Entire unchanged `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json`. |
| Matched task | All files in `a2-matched-77b6487-m07/D/sdr_v2` AND `I/sdr_v2`: root `dataset_config.json`, `dataset_dict.json`; each train/validation/test split's Arrow file, `dataset_info.json`, `state.json`. |
| Authoritative task sources | Every file named by the SDR source manifest's `file_hashes`, under W/data/datasets/`sdr_v2`, `sdr_v2_honest`, and W/outputs/_analyses/specificity-ladder/a1-control-77b6487-m07/`sdr_v2_user_inversion`, `sdr_v2_user_neutral`. Do not select only used rows or Arrow files: source directory inventories/row hashes must match exactly. |
| Registries | Current primary `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/held_out.json` AND W/docs/research/held_out.json, plus every referenced protected-set file if present at transfer/launch. Current inspected registries use inline sets. |
| Source audit | Original `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-fleet-6bd8bf5-h200/fleet-plan.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/a2-cohort-ruling.json`, snapshot/archive, and accepted source-record schema; use current `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a2_mask_comparison.py` for returned-artifact audit. It is not in the older training archive. |
| H200 comparison reference | SDR D/I timing receipts and logs under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200`, and each receipt's native config/results/history/active_nodes/run_manifest files. Preserve associated accepted audit calculations and add genuine paired reference-control artifacts once root defines them. No need to transfer unrelated full training outputs or entire study trees. |
| Runtime/cache | Packed mgnp environment with audited package/CUDA identity; complete Llama tokenizer/model cached snapshot, index, all indexed shards and referenced blobs, with refs/main still identifying `0e9e39f249a16976918f6564b8830bc894c89659`. The frozen loader does not pass a revision explicitly, so an arbitrary existing HF cache is insufficient. |

Derived from the unchanged manifest/file inventories, an individual task needs
58 authoritative source files, 22 matched-task files and one build manifest: 81 data
files. All source kinds are checked for either training arm. D sources include their
filter/provenance JSON, H its dataset metadata, and I/neutral sources their assembly,
filter/scoring provenance and score JSONL files, even though those are not all direct
training inputs. For another task substitute its task names; do not transfer only the
training arm selected for that job. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json`
and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/runtime/scripts/twin_training.py`.

## Absolute-path and audit blockers

`_stored_rows` opens each `manifest.tasks[task].sources[kind].path` verbatim, and private
configs must contain exactly those source-provenance objects. They point to Delta's
absolute W paths. The primary protected registry is also hardcoded outside W.
The frozen runtime has absolute live-link targets. Merely moving the build or setting
a remote `data_root` cannot resolve these references.

The clean byte-preserving option is a genuine remote filesystem namespace/bind mapping
that provides the original `/projects/.../Deception-Circuit` primary and nested W paths,
with local remote data/log/output storage behind them. An unprivileged container bind
is only a possible mechanism; availability/policy must be checked by root. It must
preserve the snapshot's root/link relationships and audit-visible paths. Ordinary
symlinks under `/ocean` alone do not create the missing `/projects` namespace.

Otherwise a separately reviewed relocation adapter/derivative lineage is needed.
Changing manifest `sources.path`, private `source_provenance`, snapshot root/live links
or fleet records changes authenticated identities; do not edit originals or recompute
hashes while claiming the old artifacts are unchanged.

The training wrapper permits an output-root change, but accepted `audit_source` requires
exact frozen config INCLUDING `outputs/_training_specificity_ladder/a2-h200`, exact
snapshot/archive/fleet-plan bindings, cell cwd/receipt/config paths and complete native
file inventories. A renamed H100 output config therefore needs an explicit audited
operational-relocation contract; it will not pass the current intake unchanged.
Keeping the old directory label in an honest namespace-preserving run is operationally
possible, but actual H100/Bridges2 identity must remain explicit in new raw receipts.
Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a2_mask_comparison.py` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/runtime/scripts/twin_training.py`.

`--chdir` must be the actual frozen runtime because the shell wrapper sources its cluster
profile relatively. Root must pass the Bridges2 environment through Slurm exports,
use the typed H100 GPU request from the profile, and set the remote HF_HUB_CACHE explicitly
rather than inherit a Delta cache variable. Confirm that the wrapper sees exactly one
GPU in its actual allocation. No remote prerequisite is assumed from local inspection.

## Timing, equivalence and coherent grouping

Before scientific cells: CPU plan/preflight against the transferred bytes, then actual
H100 timing-only runs for BOTH SDR arms using the unchanged training parameters and
periodic validation; include true environment/model-load/outer-job costs and memory peak.
The accepted H200 timing receipts used 20 epochs of the frozen 500-epoch schedule.
H200 SDR observed peak is 52.222 binary GiB (legacy log field says GB), which makes fit
plausible but proves neither H100 fit nor runtime. H200 audit/projection reuse explicitly
requires the same hardware, and its audit script hardcodes H200/Delta checks. Sources:
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/sdr_v2-D-seed42.json`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/sdr_v2-I-seed42.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/tools/62-a2-complete-timing-audit.py` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/92-a2-full-timing-refinement-handback.md`.

Require a root-reviewed, same-source paired H200/H100 numerical reference control on
fixed already-permitted validation rows, exact token/mask/readout/label order, same
native backend/BF16 profile and declared nonempty pruning state, alongside the ordinary
unpruned reference. Record margins/argmax, drift tolerances, environment and source/data
hashes before scientific dispatch. Existing H200 timing success, or the different-assay
`component_analysis/sweep_drift.py` precedent, does not supply this A2-specific control.
No new efficacy filter or held-out set is proposed.

Conditional grouping recommendation: move the entire still-unstarted SDR task, both D/I
and all registered seeds, if root's live check confirms that status. Its local receipt
inventory has no accepted full SDR source audit; completed FAR/SER cells remain H200.
This preserves within-task arm/seed hardware consistency, while task-level hardware
remains an explicit limitation. Do not split only a convenient SDR arm or seed across
devices. Keep every Delta job intact until the remote path/audit contract, real H100
controls, cost/storage budget and reviewed replacement plan are concrete. Root owns any
later cancellation, new reservations, transfer, launch and return-audit; old charges
cannot silently refund.
