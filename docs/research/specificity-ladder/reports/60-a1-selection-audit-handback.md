# A1 selection: independent artifact and execution audit

## What changed

Status: handed-back

Selection-validity gate: PASS. The new prepared design is semantically identical to the previously audited design, current code/provenance links are consistent, and the saved raw DLA arrays reproduce the recorded candidate screens exactly. Bank source membership, token counts, dimensions and finite values pass. The next valid step is the bounded assessment pilot, subject to fresh live resource, protected-registry and grader checks. No full assessment or specificity verdict follows from this audit.

Added this hand-back, [60-a1-selection-audit.py](60-a1-selection-audit.py), and [independent calculations](60-a1-selection-audit-calculations.json), mirrored in worktree and primary. No run artifact or source implementation was modified. The audit used CPU-only file/Arrow loading, a local cached tokenizer and numeric calculations; no git, model inference, GPU/API work, notebook or subagent was used. No root narrative result summary was read.

## How verified

Read raw `design.json`, `design-semantic-equivalence.json`, `selected.json`, `selection_run_manifest.json` and `selection_accounting.txt` under `outputs/_analyses/specificity-ladder/ladder-0253f49/`, plus original source H datasets, original selection files, deciding-set readings, current code and both actual registries. The independent script completed successfully using `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python /tmp/a1-selection-independent-audit.py`. It does not call the selection runner or model and does not trust the equivalence receipt's conclusion without comparing the payloads itself.

Recomputed both prepared envelopes, selection envelope, exact selected-file byte digest, linked selected payload digest, complete group and bank digests, raw-DLA digest and design link. All sidecar fields agree with the actual selected artifact and its execution payload. Recomputed all recorded source, original selection and current code byte hashes; all match. Both canonical grader fingerprints and actual frozen grader fields match, and both protected registries byte-match the prepared records and remain empty. Derived source scope is 208 files, three original selection files and 16 current code files. Evidence: [60-a1-selection-audit-calculations.json](60-a1-selection-audit-calculations.json), with actual artifact paths fixed in the audit script.

The original and new design payloads have exactly 24 equal semantic fields. Only `commit` and `code_hashes` change; only `component_analysis/ladder_pipeline.py` differs within the code-hash map. Exact rows, normalized tokens/layouts, assessment draws, donor maps, source/selection hashes, utility samples, groups, registries, model revisions and numerical settings are unchanged. The separately supplied equivalence file's old/new byte hashes, field digests and changed-file list match the independent comparison. This carries forward the earlier CPU design audit without silently reusing a stale code identity. Evidence: [60-a1-selection-audit-calculations.json](60-a1-selection-audit-calculations.json).

The full supplied selection commit is `0253f494af007f93b2a00cb1e63cb3cdf1a8b519`. Model/tokenizer revision is `0e9e39f249a16976918f6564b8830bc894c89659`. The frozen loader resolves the pinned local model snapshot before CUDA loading. This worker checks recorded provenance, current source hashes and the actual loader path; it does not reconstruct historical source-code cleanliness with git or independently rehash all model weights.

For each task, raw DLA axes exactly match the original task-specific ordered H selection ids and ordered head subset of the actual recorded full group. The original selection-file id list, design mover list, evidence list and screen list are identical. All array values are finite. From those arrays, the audit independently recomputes clean means, separate clean/swapped positive counts, both-positive counts, rankings, candidate booleans, removed intersection, remaining membership and duplicate status, without calling choose_mover_candidates.

The native screen criterion is positive mean clean H correct-minus-other DLA and strictly positive correct-minus-other DLA in both streams on at least 75 of 100 selection rows; zero ties do not qualify. The actual original H source row's clean target is the honest word and its distractor is the other word, reversing in the swapped stream. The audit checks those words, source prompts, contextual token ids and readouts against every selected H row in both streams. The frozen selection path explicitly calls component_logit_difference with honest token as target and opposite token as distractor. This checks label orientation and recorded computation provenance; saved arrays alone do not independently reconstruct the original forward-pass contributions. The prospective criterion is recorded in `docs/research/specificity-ladder/plan-ladder.md`.

Derived screen results below come directly from the raw clean/corrupt arrays in selected.json. No head meets the frozen criterion, so full and minus memberships are identical and all duplicate flags are correct. MLPs are retained throughout. SDR remains descriptive. Evidence: [60-a1-selection-audit-calculations.json](60-a1-selection-audit-calculations.json).

| Task | Selection rows | Head columns per stream | Saved raw DLA values | Largest both-positive count | Removed heads | Full/minus members | Duplicate |
|---|---:|---:|---:|---:|---:|---:|---|
| FAR | 100 | 18 | 3600 | 10/100 | 0 | 20/20 | yes |
| SDR | 100 | 14 | 2800 | 62/100 | 0 | 20/20 | yes |
| SER | 100 | 19 | 3800 | 10/100 | 0 | 20/20 | yes |

Full membership exactly matches the actual primary p1c_readings.json deciding_numbers lists and the prepared groups, preserving their order. The current assessment code emits each duplicate membership once and omits an invented distinct minus group. Empty candidate sets are an allowed screen outcome; they provide no evidence for copying or deception specificity.

## Execution evidence

- Job/cluster: `23415379`, Delta. A fresh read-only sacct query agrees with `outputs/_analyses/specificity-ladder/ladder-0253f49/selection_accounting.txt`: COMPLETED, elapsed 195 seconds, exit `0:0`, one GPU. Batch and extern steps also completed with exit `0:0`. Logs are `logs/lad-a1-select-23415379.out` and `logs/lad-a1-select-23415379.err`; stdout ends with `select: complete`, stderr contains actual weight-load progress and no exception or OOM. Batch MaxRSS is `11922832K`, a host-memory figure separate from CUDA peaks.
- Counts observed against expected: each task has 100/100 ordered selection rows, two complete raw DLA arrays with the expected task head width, and 400/400 original-H bank ids with 800/800 stream records. Derived raw DLA total is 10,200 finite values. No assessment id appears in any selection or bank source. The assessment union has 300 ids; the selection union has 298, with zero overlap. Evidence: [60-a1-selection-audit-calculations.json](60-a1-selection-audit-calculations.json).
- Baseline reproduction: this selection job does not save an intact behavioral baseline or an assessment replay, so no numerical baseline-reproduction claim is made. DLA screens are recomputed from saved arrays, not replayed model inference. The assessment pilot must separately establish its intact/empty/self-replay and positive-control validity before any necessity claim.
- Provenance files: `outputs/_analyses/specificity-ladder/ladder-0253f49/selected.json` and `selection_run_manifest.json` bind the exact selected bytes, selected payload, prepared design, raw DLA evidence, groups, banks, original source/selection hashes, current code hashes and shared execution payload. All name full commit `0253f494af007f93b2a00cb1e63cb3cdf1a8b519`. Prepared, selected and sidecar injected flags are all false. Execution records actual `cuda:0`, `torch.bfloat16`, NVIDIA A100-SXM4-40GB, job/cluster and pinned model/tokenizer identity.

Recorded CUDA peaks are 18,310,754,816 allocated bytes and 18,717,081,600 reserved bytes, scoped to selection compute after model loading and including the resident model. Model load took 40.747 seconds; compute took 116.914 seconds; measured stage time was 158.728 seconds, including load/compute and excluding publication. Whole-job elapsed is 195 seconds; derived actual GPU spend is 195/3600 = 0.05417 GPU-hours. These timings describe selection, not a projection for assessment. Evidence: raw selection_run_manifest.json and [60-a1-selection-audit-calculations.json](60-a1-selection-audit-calculations.json).

Each bank has the exact frozen original-H train/validation id set in sorted order, with both clean and swapped source records and no assessment/test membership. The audit checks complete embedded source records against the prepared original H rows, which remain hash-bound to actual original Arrow files. The adapter's utility_assessment field marks clean versus corrupt stream; actual split/id checks establish that these bank rows are train/validation rather than assessment. Equal-token pooling over both streams/all unpadded positions is the frozen collector's explicit fp32 computation path. Independently recalculated token counts and vector checks are below. Evidence: [60-a1-selection-audit-calculations.json](60-a1-selection-audit-calculations.json).

| Task | Original H ids | Stream records | Unpadded tokens pooled | Bank keys | Head dimension | MLP dimension |
|---|---:|---:|---:|---:|---:|---:|
| FAR | 400 | 800 | 78026 | 20 | 128 | 4096 |
| SDR | 400 | 800 | 81626 | 20 | 128 | 4096 |
| SER | 400 | 800 | 81254 | 20 | 128 | 4096 |

Every saved bank value is finite, every key is unique and exactly matches its full group's ordered keys, and vector dimensions match the actual cached model configuration. No saved source activation tensors are available for an independent numerical reconstruction of the means; this audit validates bank membership, token counts, shape, finite values, content hashes and pooling provenance, and explicitly does not claim to recompute the numerical bank means.

## What is NOT done

No model replay, independent numerical DLA forward-pass reconstruction, independent bank-mean reconstruction, assessment scoring, positive-control recovery, necessity fraction, bootstrap uncertainty or specificity verdict was performed. Empty mover screens do not turn duplicate memberships into a subtraction contrast. SDR's descriptive source set remains descriptive.

## Open questions

No selection-artifact validity blocker remains. Proceed to the bounded assessment pilot under the current committed numerical path, after live budget/registry checks. Keep all frozen assessment ids, unsupported F twins, H/user-neutral no-ops and optional-donor coverage visible. Use full groups once because all minus groups are duplicates, and require the pilot's full expected count, same-path replay, positive calibration, baseline competence and resource evidence before reserving the complete assessment.

Operational usage check returned 17 percent used and 83 percent remaining, below the 80 percent cap, resetting `2026-11-06T16:07:41+00:00`. Counts, hashes and classifications above trace to the actual raw files and independent receipt; totals and conversions are explicitly derived. The frozen threshold is prospective, not inferred from these arrays.
