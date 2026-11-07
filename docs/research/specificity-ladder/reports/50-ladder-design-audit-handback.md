# Frozen ladder design: independent CPU audit

## What changed

Status: handed-back

The original immutable prepared design passes the independent CPU audit. Its samples, source joins, token layouts, donor semantics, utility samples and grader/protected-set provenance satisfy the frozen ladder preparation rules. No assessment outcomes were inspected or produced.

This conclusion applies to `outputs/_analyses/specificity-ladder/ladder-6bd8bf5/design.json`, envelope digest `38783960519d8a12522d567642c52aca51cf611cb6ac0652626843caa56bbba1`, naming full supplied commit `6bd8bf5334f2e83613a129d2fcfeacf83e762191`. The parent is changing selection-execution metadata in the CLI concurrently. That changes the pipeline code hash, so this original design must not be passed unchanged to updated code. Before selection, prepare a distinct artifact under the new committed code and establish exact equality of all semantic design/data/utility fields with this audited artifact, while allowing only the declared commit/code-provenance differences. This audit does not review the new code change itself.

Added only this hand-back, the independent [audit script](50-ladder-design-audit.py), [calculation receipt](50-ladder-design-audit-calculations.json), and [audit-start source-code hash receipt](50-ladder-design-initial-code-hashes.json). The design artifact and source files were not modified. No git, model inference, GPU/API work, notebook execution or subagent was used. The report and owned evidence are mirrored in primary and worktree.

## How verified

Read START.md, the current specification and plan-ladder.md, then the raw prepared artifact and the actual source, original selection, deciding-set and cached utility files. No root narrative result or pipeline-author report was read. The audit independently implements balanced sampling and donor checks rather than invoking prepare, freeze_design or donor_plan. It independently reconstructs utility sampling from raw sources rather than calling the ladder utility adapter or correctness-filtering task loaders.

The successful CPU audit command was `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python /tmp/ladder-design-independent-audit.py`. The reusable owned copy is [50-ladder-design-audit.py](50-ladder-design-audit.py). It never writes the prepared design. The pinned tokenizer was loaded only from its local snapshot, with no model weights loaded.

Recomputed the envelope's canonical payload digest, every recorded source-file and selection-file byte hash, domain-separated assessment/selection/bank/donor hashes, actual utility source hashes and MMLU sample hash. Derived totals are 208 source files and three original selection files. All 16 recorded code-file byte hashes matched actual files at audit start; the concurrent pipeline edit is separately visible as the sole mismatch at the later audit run. The captured start receipt preserves that timing distinction. No claim about historical source-code cleanliness is inferred from a supplied commit; workers did not run git. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json) and [50-ladder-design-initial-code-hashes.json](50-ladder-design-initial-code-hashes.json).

The audit loads actual source Arrow datasets and checks every normalized row and both streams against them, including prompt bytes, canonical honest/opposite words, contextual answer tokens, condition-correct token, source split and source-content digest. Full prompts are re-tokenized without truncation, last-token readouts and role/content boundaries are checked against actual token sequences, and user-request spans/lengths/readouts match the builder rows. I/neutral twins have identical layouts and lengths, equal request spans and no token changes outside the request. Derived normalized-row totals are FAR 6,690, SDR 6,852 and SER 6,540, or 20,082 overall. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

The model/tokenizer identity is the canonical Llama identifier pinned to `0e9e39f249a16976918f6564b8830bc894c89659`. The actual cached tokenizer-config digest matches the record. The prepared dtype/readout and prospective operations remain BF16 execution with fp32 analysis readout and native diagnostics; this audit does not empirically test that execution path.

## Execution evidence

This is a CPU preparation audit, not a model run. No Slurm selection or assessment job is claimed here. The audit process completed with exit zero and wrote its independent calculation receipt; the immutable artifact remained byte-hash checked. Baseline replay, model scores, mover DLA arrays and actual mean-bank values do not exist in this audit and are not asserted. The supplied full provenance commit is recorded above and in the audited payload. The evidence below establishes prepared-input validity only; the planned selection run must create its own execution manifest and output evidence.

### Samples, exclusions and bank sources

The three actual primary selection files are `outputs/_analyses/mechanism-analysis-p1/s1/U__leaf/{far_v2,sdr_v2,ser_v2}/sample.json` under the primary repository, field `instance_ids`. Each task's exact ordered 100 ids is preserved in its mover-selection list. The cross-task union is 298 ids and is used only as the assessment exclusion union. Mover order is not inferred from that union. The selection files' actual byte hashes match the prepared record. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

Derived assessment draws below independently reproduce balanced allocation and the local seed-1 random draw from sorted five-condition common test ids after union exclusion. Every `eligible_pool_indices` entry points to its exact `eligible_pool_ids` id and equals the ordered assessment list. The indices are eligible-pool positions, not original source-loader indices. All nuisance-factor meanings agree across the five joined conditions. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

| Task | Eligible after union exclusion | Assessment ids | Ordered mover-selection ids | Original-H bank ids |
|---|---:|---:|---:|---:|
| FAR | 796 | 100 | 100 | 400 |
| SDR | 847 | 100 | 100 | 400 |
| SER | 745 | 100 | 100 | 400 |

Each assessment id has D, original H, F, user-I and its user-neutral twin on the same test id. Each original-H bank is exactly 200 train plus 200 validation rows, never assessment or test rows. The independent draw uses the full source-availability intersection and does not inspect neutral competence or donor support; optional diagnostic support cannot alter membership. These are samples conditional on the already behavior-filtered user-I pool, not random samples of the original full test population. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

All recorded full groups match actual `rab[task].deciding_numbers.members` in the primary `docs/research/mechanism-analysis/phase1/p1c_readings.json`, preserving order and parsed head/MLP identities. Each has exactly 20 members. FAR/SER are recorded deciding sets; SDR is explicitly descriptive. No mover subtraction or new answer-contribution result was invented by preparation. Evidence: the cited source JSON and [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

### Maps and diagnostic coverage

Independently checked every frozen map, including the exact recipient/condition/stream/operation/seed key set, donor-source digest, actual same-instance and same-stream constraints, candidate eligibility/order, independent seeded choice, layout/length compatibility, absolute position lists and full unpadded coverage. Derived total is 9,000 maps per task, 27,000 overall; no padding, interpolation, repeated position or clamping is used. Supported whole-sequence maps cover every requested unpadded token; unsupported maps have empty position lists and an explicit reason. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

Same-condition item swap is supported for all 200 stream cells per condition per task and uses that same id/condition's opposite stream. D twin replacement uses same-id original H in the recipient stream; I uses its own same-id user-neutral twin in the same stream. Both have 200 supported nonidentity cells per task. H and user-neutral twin replacement each have 200 explicitly marked no-op/degenerate cells per task and `gate_valid=false`. These no-ops cannot establish honest preservation. F-to-H twin maps are unsupported for all 200 cells per task because full length/layout differs, with no fabricated correspondence. Zero, empty and H-mean maps keep their defined positions and no individual donor. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

Optional different-instance donor support is partial. The derived denominators below count both streams across three independent donor seeds, hence 600 cells per condition/task. Each supported donor is from the appropriate H-derived train/validation pool, excludes the same/assessment id, matches exact answer words/item identity and template/layout, and additionally matches request id/span for user-I/user-neutral. Sorted eligible ids and hash-derived seeded selection reproduce exactly. F has no compatible independent H donor, and the assessment remains unchanged. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

| Task | D supported | H supported | F supported | I supported | User-neutral supported |
|---|---:|---:|---:|---:|---:|
| FAR | 318/600 | 318/600 | 0/600 | 318/600 | 318/600 |
| SDR | 264/600 | 264/600 | 0/600 | 264/600 | 264/600 |
| SER | 378/600 | 378/600 | 0/600 | 372/600 | 372/600 |

### Utility sources and grader protection

IOI was independently regenerated using actual generator constants and names, canonical sorted single-token names and local random seed 1, without calling the ladder adapter. All 1,000 generated unique rows are eligible; the first 100 eligible source ids exactly match the frozen sample. Both final answer names are removed before tokenization, contextual A/B answer tokens are single distinct tokens, BOS/readouts/masks and full prefix bytes match, and all 100 same-row repeated-B item-swap maps are supported. The source hash includes the actual generator and names-file bytes. No model-correctness filter was used. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

MMLU was independently read from actual cached test parquet bytes at revision `c30699e8356da336a370243923dbaf21066bb9fe`. Parquet digests match. All 14,042 source rows are eligible, with zero malformed, overlength or contextual-token rejections; stable original parquet row ids are sorted before the independent `random.Random(1).sample(...,32)`. The exact 32 source ids and sample hash match. Neutral system/user formatting, chat-template bytes, prompt byte representations, complete token arrays, contextual A/B/C/D answer tokens, gold expected tokens, masks and readouts match actual raw questions. No correctness filter is used. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

All 32 MMLU maps are different-question cyclic readout-only positive calibrations, not native item swaps or H donors. The prepared utility sample does not fabricate a second truth-labelled IOI assessment or a native MMLU corruption. Utility outcome accuracy has not been measured. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

Independently recomputed the canonical benchmark grader fingerprint from actual grader source files in both primary and worktree: `866fd15dd30b695e46ffe955b09894fb831af92e2b9015eafbd7f0eee151d2f9`. Both actual direction registries hold that frozen grader field and their complete byte hashes match this design's recorded registry hashes. Both held-out registries also match their recorded hashes and currently contain no protected sets, so no overlap exists. The utility adapter/formatter source and chat-template hashes match too. Evidence: [50-ladder-design-audit-calculations.json](50-ladder-design-audit-calculations.json).

The nested MMLU preparation manifest retains `grader_registry: null` and preparation-only status; it is not a benchmark execution receipt. The prepared envelope's top-level actual grader and both registry records supply the current freeze evidence. Future selection/assessment manifests must record their actual grader and local adapter/runner hashes rather than citing that nested leaf alone. No EVAL 5 authorization is implied.

## What is NOT done

No model inference, native/fp32 baseline reproduction, mover screening, mean-bank tensor collection, positive-control recovery, intervention assay, bootstrap uncertainty, full ladder gate or specificity claim is made. Actual selection outputs still need their own row counts, raw DLA evidence, bank provenance and execution manifest. This audit does not approve unreviewed concurrent code changes or replace the required model pilot and replay checks.

## Open questions

The original semantic design has no CPU-validity blocker. After the parent's metadata-only code change, require a distinct prepared root, a committed full code identity, current code hashes and exact original-versus-new semantic design/data/utility equality before selection. Refresh both protected registries and actual grader fields immediately before model loading. Keep selection outcomes separate from assessment, and freeze the selection-only group subtraction and H bank before any assessment scoring.

Report F twin unsupported cells, H/user-neutral twin no-ops and partial optional-donor coverage alongside later results. They are recorded limitations, not reasons to shrink or redraw the sample. The utility sample is prospective; it makes no capability-preservation claim.

Final operational usage check returned 15 percent used, 85 percent remaining, below the 80 percent cap, with reset `2026-11-06T16:07:41+00:00`. Counts, hashes and coverage above come from independent calculations and actual raw files; nonliteral totals are derived. Prospective sample sizes, seeds and operation meanings come from the frozen plan.
