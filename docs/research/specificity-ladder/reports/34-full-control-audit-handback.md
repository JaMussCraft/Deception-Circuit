# Full A100 screen and assembled-control audit

## What changed

Status: done

Execution and control-availability gate: PASS. The complete A100 screen and the assembled inversion/neutral arms meet the frozen scored-data contract. FAR and SER exceed the primary test-pool requirement at the original threshold. Valid admission to A2 matched CPU materialization can proceed, with its own source joins, receipt checks and split safeguards. This is neither completion of A1's intervention ladder nor evidence of causal deception specificity.

Added this hand-back, [34-full-control-audit.py](34-full-control-audit.py), and its [independent calculation receipt](34-full-control-audit-calculations.json) in the worktree and primary. No inference, GPU/API work, git, notebooks, dataset modification or other worker's files were involved. Both copies contain the same audit evidence.

## How verified

Ran the independent audit with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/reports/34-full-control-audit.py`. All assertions passed. The script uses CPU Arrow loading, hashes, JSON comparisons and scalar arithmetic. It reads raw full scores/manifests under `outputs/_analyses/specificity-ladder/a1-full-77b6487-a100/`, original derivations under `outputs/_analyses/specificity-ladder/a1-derive-dd9aed6/`, original D/H Arrow datasets, and actual assembled arms under `outputs/_analyses/specificity-ladder/a1-control-77b6487-m07/`. No root lead summary or narrative result report was read.

Recomputed every original D/H configuration and split-content canonical hash, source-row hashes, request-pool hash, derivation file and manifest byte hashes, complete prompt aggregates, each scored prompt hash, full score-file byte hashes, copied receipt/score hashes, linked full run-manifest hashes, and every file in each arm's assembly-provenance file map, including its Arrow shard. The file map covers all arm files except the assembly-provenance file itself. Both protected registries still byte-match the recorded hashes and have empty protected-set lists; protected overlap is zero. A later job must check the live registries again.

For every task/split, complete ordered score ids equal derived ids and original D-source ids, with expected counts and no duplicates. Original D/H and both assembled arms each preserve within-task split separation. Cross-task sharing of matched source ids is intentional and not treated as leakage. Every derived and assembled row's D/H source-row hashes match the actual source rows. Every assembled Arrow row exactly equals its independently selected derivation-arm row, preserving prompts, metadata, conditions, labels and order.

Checked both copied scoring receipts are identical, self-contained and configuration-digest bound, with every split score file byte-identical to the full raw score file. Dataset configurations correctly declare their conditions, task/model, new maximum length, baseline kind, actual split sizes and receipt digest. Inversion uses the declared primary threshold; neutral uses its diagnostic honest threshold. Receipt source commit, scorer, canonical model/tokenizer, both pinned revisions, request hash and dtype match all full run manifests. Assembly provenance links the exact full manifests and source hashes. No receipt was manufactured for raw unscored rows.

Recorded full code commit is `77b6487b08b4410a4e5a9995c6ff5e46834a5ce3`; model/tokenizer are `meta-llama/Llama-3.1-8B-Instruct`, pinned to `0e9e39f249a16976918f6564b8830bc894c89659`, using native CUDA BF16 scoring. The parent supplied a git-diff determination that the A1 runtime files are unchanged from pilot commit `dd9aed69d115e87f8942c4a622f993f5996d7b77`; this worker did not independently run git or reconstruct historical cleanliness. These are recorded provenance identities, not a rehash of model weights.

Every score uses the canonical honest/opposite words from its original inversion orientation, reversed in the item-swapped stream. Choices agree with expected full-vocabulary argmax tokens, all required score numerics are finite, signed stored margins are consistent, and native margins equal BF16-rounded subtraction of native logits. Promoted subtraction happens to agree for this complete artifact too; that agreement is descriptive, not a requirement imposed on future native-dtype scoring. No promoted arithmetic or tolerance widening was used to change membership.

Derived pool counts below come directly from both-stream opposite full-vocabulary argmax and opposite-minus-honest margin at least 0.7. Neutral competence requires honest argmax and honest-minus-opposite margin at least 0.3 in both streams and is diagnostic only. The columns distinguish actual argmax failures from additional margin-only failures. Evidence: [34-full-control-audit-calculations.json](34-full-control-audit-calculations.json), with source/raw paths fixed in the script.

| Task/split | Scored | Retained | Paired competent | Neutral argmax failure among retained | Neutral margin-only failure among retained |
|---|---:|---:|---:|---:|---:|
| FAR train | 200 | 177 | 177 | 0 | 0 |
| FAR validation | 200 | 177 | 177 | 0 | 0 |
| FAR test | 1000 | 891 | 891 | 0 | 0 |
| SDR train | 200 | 187 | 157 | 21 | 9 |
| SDR validation | 200 | 187 | 158 | 17 | 12 |
| SDR test | 1000 | 952 | 834 | 58 | 60 |
| SER train | 200 | 168 | 161 | 5 | 2 |
| SER validation | 200 | 167 | 151 | 9 | 7 |
| SER test | 1000 | 835 | 791 | 29 | 15 |

Actual test neutral full-vocabulary accuracy is reported separately from the competence floor, with derived counts below. The calculation receipt contains corresponding counts for every train/validation split too. Evidence: [34-full-control-audit-calculations.json](34-full-control-audit-calculations.json).

| Derived task/cohort | Denominator | Honest clean | Honest swapped | Honest both | Competent both |
|---|---:|---:|---:|---:|---:|
| FAR all scored test | 1000 | 1000 | 1000 | 1000 | 1000 |
| FAR retained test | 891 | 891 | 891 | 891 | 891 |
| SDR all scored test | 1000 | 970 | 971 | 941 | 879 |
| SDR retained test | 952 | 922 | 924 | 894 | 834 |
| SER all scored test | 1000 | 982 | 988 | 970 | 954 |
| SER retained test | 835 | 817 | 824 | 806 | 791 |

No baseline-filter leak exists: the independently recomputed inversion-only id lists exactly equal both actual Arrow arm lists, including all retained baseline failures. Filter reports' rejected ids, competent ids and baseline-failure ids match these independent calculations. Primary test pools are FAR 891 and SER 835 unique ids, each above the required 300 at 0.7; SDR has 952. The 0.5 fallback is unnecessary and was not used in this assembly. Evidence: [34-full-control-audit-calculations.json](34-full-control-audit-calculations.json), `docs/research/specificity-ladder/a1-data-contract.md` and `docs/research/specificity-ladder/START.md` for prospective requirements. This delivers usable measured controls; it does not satisfy the later causal ladder gate.

## Execution evidence

- Job/cluster: `23412591`, Delta. Fresh `sacct -j 23412591 --noheader --parsable2 --format=JobID,Cluster,State,ElapsedRaw,ExitCode,AllocTRES,MaxRSS` agrees with `outputs/_analyses/specificity-ladder/a1-full-77b6487-a100-accounting.txt`: COMPLETED, 429 seconds, exit `0:0`, one GPU; batch/extern also completed with exit `0:0`. Logs `logs/lad-a1-full-23412591.out` and `logs/lad-a1-full-23412591.err` show every task/split completed with no exception or OOM. Batch MaxRSS is `13742456K`, a host-memory figure separate from CUDA peaks.
- Rows observed against expected: FAR, SDR and SER each have train 200/200, validation 200/200 and test 1000/1000, hence derived total 4200/4200 paired rows and 16800/16800 prompt evaluations. All ordered ids and all raw/assembly hashes pass. Full-run manifests declare unlimited full scope, all source splits and zero replay forwards; no pilot score file was used as part of assembly. Evidence: all full raw run manifests/scores and [34-full-control-audit-calculations.json](34-full-control-audit-calculations.json).
- Baseline reproduction assertion: the original A100 pilot's first 32 test ids per task overlap exactly, and 32/32 complete score records per task are identical as parsed dictionaries. Derived baseline choices reproduce for 192/192 and native baseline margins for 192/192, maximum absolute difference 0.0; including inversion, choices and margins reproduce for 384/384. This is pilot-to-full same-hardware overlap evidence, not a separately executed full-run replay. Evidence: original pilot raw `outputs/_analyses/specificity-ladder/a1-pilot-dd9aed6/` scores and [34-full-control-audit-calculations.json](34-full-control-audit-calculations.json).
- Provenance files: all nine `run_manifest.json` files under `outputs/_analyses/specificity-ladder/a1-full-77b6487-a100/{far_v2,sdr_v2,ser_v2}/{train,validation,test}/` name full commit `77b6487b08b4410a4e5a9995c6ff5e46834a5ce3`, exact pinned model/tokenizer revisions, native scorer, dtype/device, batch size, source/request/prompt/output hashes, both registry hashes, job identity and complete row scope. Each assembled arm links exact full manifests and copies the scored receipt/files. No required execution-evidence field is missing.

Measured execution was on NVIDIA A100-SXM4-40GB, BF16, batch size 8, maximum length 256. Peak allocated CUDA memory is 17,407,058,944 bytes and reserved 17,758,683,136 bytes; model load took 25.108 seconds. Summed task/split scoring windows are derived 370.912 seconds, inside the measured 429-second job; actual derived spend is 429/3600 = 0.1192 GPU-hours. Evidence: the full raw run manifests and accounting receipt; [34-full-control-audit-calculations.json](34-full-control-audit-calculations.json) contains timing sums. These are inference measurements, not training-memory or training-timing evidence.

## What is NOT done

No causal intervention, crossed ladder, deciding-set subtraction, unrelated-task/MMLU floor, A2 training-ready materialization, mask training or A3 analysis was performed. No claim that baseline competence is perfect on SDR or SER is warranted. No source-split mixing, competence-based primary membership change, threshold fallback or pooling of A40 scores occurred. The isolated CPU audit does not independently establish historical source-code cleanliness or hardware invariance.

## Open questions

Proceed to the authorized matched CPU materialization using these measured controls. The materializer must enforce the binding receipt contract against actual original D/H source rows, retain source split membership, and verify copied score provenance and prompt/source hashes before readiness. Keep primary inversion membership separate from any explicitly named paired-competent assay; do not silently discard baseline failures. Training data selection must follow the separately frozen A2 matching plan, not infer new criteria from these test diagnostics.

A1's larger causal question remains open. The next admissible result is a valid matched materialized cohort with CPU validation, not a specificity verdict. Repeat live protected-registry and budget checks before any future scoring or training job.

Operational usage evidence: live Codex reading was 11 percent used and 89 percent remaining, below the 80 percent cap, resetting `2026-11-06T16:07:41+00:00`. All nonliteral totals, classifications and conversions above are explicitly derived from cited raw artifacts or the independent calculation receipt; thresholds and pool requirements are prospective spec values.
