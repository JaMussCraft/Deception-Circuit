# Actual A2 CPU comparison and prospective group freeze

Status: handed-back

## What changed

**CPU comparison and prospective freeze completed successfully.** All 18 canonical full scientific sources passed the accepted comparison path, and all nine per-seed D-minus-I aliases are frozen in a fresh namespace. The required seed-stability component fails for every task; functional specificity has not been measured. No A3 plan or scientific threshold changes follow from this result. [Actual manifest](139-a2-comparison-freeze-evidence/run_manifest.json).

Analysis execution is `40fe57289405fd53a3fce02e5d4e47a0ebf78b64`; original training execution remains `6bd8bf5334f2e83613a129d2fcfeacf83e762191`, with original A1 ancestor `5f450dc93dac707af649dee8c8ca60888b2831db`. The frozen input packet and driver hashes are unchanged. Output: [all18 prospective analysis](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-analysis/all18-40fe57289405-v1/COMPLETE.json).

## How verified

Read actual allocation, terminal accounting, owning freeze command and completion metadata. The CPU driver ran `compare_masks`/`write_comparison`, then the owning freeze CLI, which independently recomputed current source comparison and validated original A1 design/selection/sidecar, current source/protection/grader and model-config metadata. It validated the published receipt, exact default operations and references, checked immutable source before/after and rejected project imports outside the bundle. [Completion](139-a2-comparison-freeze-evidence/COMPLETE.json), [executed freeze](139-a2-comparison-freeze-evidence/freeze-command.json).

Independently performed a brief standard-library metadata/set check: every bound receipt/config/active-node hash matches the completed comparison; native binary exports reconstruct the exact frozen D/I/X/Y/intersection/union sets. Recomputed mixed pairwise Jaccards and head/MLP containment match the output. No source-audit replay, model execution or assay-outcome inspection occurred locally. Native training-test metrics were not inspected. [Independent recomputation](139-a2-comparison-freeze-evidence/membership-recomputation.json).

## Execution evidence

CPU job `23459504` on `cn061` completed exit `0:0` after 95 seconds, with four CPUs, thirty-two GiB and no GPU. The driver measured its own inner duration separately. No retry was needed. [Accounting and exact resources](139-a2-comparison-freeze-evidence/run_manifest.json), [batch log](139-a2-comparison-freeze-evidence/slurm-23459504.log).

| [Task](139-a2-comparison-freeze-evidence/membership-recomputation.json) | Mixed Jaccard: seeds 42/1 | 42/123 | 1/123 | Minimum |
|---|---:|---:|---:|---:|
| [FAR](139-a2-comparison-freeze-evidence/membership-recomputation.json) | 25/101 | 24/97 | 29/96 | 24/97 |
| [SDR](139-a2-comparison-freeze-evidence/membership-recomputation.json) | 37/104 | 37/99 | 34/97 | 34/97 |
| [SER](139-a2-comparison-freeze-evidence/membership-recomputation.json) | 49/119 | 33/120 | 36/121 | 33/120 |

Every pair is below the predeclared 0.5 threshold. Therefore no task can satisfy the unchanged robust seed-stable task-pass conjunction, regardless of later assay results. This is a membership-stability result, not a functional specificity null. [Exact numerators, denominators and ratios](139-a2-comparison-freeze-evidence/membership-recomputation.json), [frozen thresholds](139-a2-comparison-freeze-evidence/run_manifest.json).

| Task | Head containment: seed42 | seed1 | seed123 |
|---|---:|---:|---:|
| FAR | 82/142 | 76/140 | 78/136 |
| SDR | 42/112 | 51/116 | 52/113 |
| SER | 49/127 | 55/138 | 73/141 |

All individual ratios are below 0.9, so no task meets the predeclared head-containment result. [Frozen threshold](139-a2-comparison-freeze-evidence/run_manifest.json). D-minus-I total component counts in seed order remain FAR 61/65/60, SDR 73/68/63 and SER 82/86/71; all aliases are nonempty and remain retained without efficacy or stability filtering. Head and whole-MLP counts remain separate in evidence. [Exact containment/counts](139-a2-comparison-freeze-evidence/membership-recomputation.json).

## What is NOT done

No original source/data mutation, Git, reviewer submission/RS mutation, retry, pretrained weights, model forward, GPU job, H-bank collection or functional assay scoring. Root submitted the job and owns RS updates; reviewer scheduler queries were read-only. No change to A1 frozen assessment/utility membership, donor maps, seeds, controls or required floors.

The CPU artifact retains audited native training-test provenance; those metrics are not ladder assessment results. The new group receipt is separate from the original A1 selection and does not inherit its group labels or qualifiers. The completed comparison provides no bank coverage, functional specificity, causal interpretation or GPU admission.

## Open questions

The accepted plan permits informative per-seed assays despite failed stability if the measured remaining analysis budget supports them. Keep all required aliases and controls; do not substitute the diagnostic core, choose successful seeds or reinterpret instability as a completed functional test.

Next is a prospective original-H union-bank and scoring-timing proposal using this receipt and original A1 rates, followed by root-owned measured cost/authority decisions. No GPU submission is authorized by this handback. Existing A2/global caps and all retained original charges remain unchanged.
