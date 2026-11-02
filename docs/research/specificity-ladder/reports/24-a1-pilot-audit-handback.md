# A1 pilot execution audit hand-back

## What changed

Status: done

Execution-validity audit passes. Full-pool scoring can proceed with the frozen prompts, native scorer, pinned snapshot and batch size unchanged, after the required fresh protected-registry and budget checks. This is a recommendation to continue the existing scoring plan, not a deception-specificity result or an estimate of final pool retention.

Only this hand-back and its independent CPU audit script/calculation receipt were added. No production code, dataset, run artifact, notebook, GPU job or API call was changed. Lead summary JSON and other narrative reports were not read.

## How verified

Read START.md, spec.md and Task 3 of plan-a1.md, then inspected the raw pilot manifests, scores, replay files, source derivation files, job stdout/stderr and accounting receipt. The independent script is [24-a1-pilot-audit.py](24-a1-pilot-audit.py); its assertions ran successfully with the mgnp interpreter, CPU-only dataset loading and standard JSON/hash arithmetic. Results are in [24-a1-pilot-audit-calculations.json](24-a1-pilot-audit-calculations.json). The script fixes the audited worktree explicitly and never loads model weights.

The script recalculated SHA256 for every pilot score/replay file and test derivation file, the linked derivation manifest, canonical JSON hashes for original D/H configurations and every source split, the request pool, all test source-row identities, all test prompt aggregates, and every scored prompt. Ordered score ids match the first derived ids without duplication. Both primary and worktree protected registries currently match their recorded SHA256 and have empty set lists. A fresh registry check remains mandatory immediately before the next scoring job.

All manifests name the full supplied code commit `dd9aed69d115e87f8942c4a622f993f5996d7b77`. This audit checks its identity in provenance and the command; workers do not run git, so it does not independently establish the historical worktree cleanliness at execution. Native score arithmetic satisfies honest-minus-opposite equals logit-a minus logit-b, with the opposite margin carrying the reverse sign. Full-vocabulary choices agree with the recorded expected tokens.

The descriptive counts below are independently derived from scores.jsonl in each task's test directory under `outputs/_analyses/specificity-ladder/a1-pilot-dd9aed6/`, with exact calculations in [24-a1-pilot-audit-calculations.json](24-a1-pilot-audit-calculations.json). Retention requires opposite full-vocabulary argmax and the stated opposite-minus-honest margin in both designation streams. Competence requires honest full-vocabulary argmax and honest-minus-opposite margin at least 0.3 in both baseline streams.

| Task ([threshold protocol](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a1.md)) | Inversion retained at 0.7 | Retained and competent at 0.7 | Inversion retained at 0.5 | Retained and competent at 0.5 | Baseline competent overall |
|---|---:|---:|---:|---:|---:|
| FAR | 20/32 | 20/20 | 21/32 | 21/21 | 32/32 |
| SDR | 31/32 | 30/31 | 32/32 | 31/32 | 31/32 |
| SER | 26/32 | 26/26 | 28/32 | 28/28 | 32/32 |

All baseline choices are honest in both streams; the SDR competence failure is a margin-floor failure. No baseline failure was used to remove an inversion from its primary pool. These are descriptive pilot counts, with no extrapolation to the full test pools or inference about the final gate. [24-a1-pilot-audit-calculations.json](24-a1-pilot-audit-calculations.json)

The following mean margins are derived in the canonical honest-minus-opposite orientation from the same raw scores; clean and swapped streams are separate. No causal removal fraction is calculated. [24-a1-pilot-audit-calculations.json](24-a1-pilot-audit-calculations.json)

| Task | Inversion clean | Inversion swapped | Neutral clean | Neutral swapped |
|---|---:|---:|---:|---:|
| FAR | -6.9765625 | -3.8515625 | 8.78125 | 8.849609375 |
| SDR | -4.50390625 | -4.234375 | 2.60546875 | 2.546875 |
| SER | -3.46875 | -3.9765625 | 3.794921875 | 4.14453125 |

The recorded model and tokenizer revision is `0e9e39f249a16976918f6564b8830bc894c89659`. The stdout names that exact model snapshot. The loader resolves local shards under the pinned snapshot before loading; this audit checked shard existence and the tokenizer-config hash. Device/dtype are CUDA and torch.bfloat16, with batch size 8 and cap 256 in each manifest. This audits the recorded pinned identity, not an independent rehash of all model weights. Evidence: `dataset/user_inversion_pipeline.py` and each task's `run_manifest.json` below.

## Execution evidence

- Job and cluster: `23411942`, Delta. Fresh read-only `sacct -j 23411942 --noheader --parsable2 --format=JobID,Cluster,State,ElapsedRaw,ExitCode,AllocTRES,MaxRSS` agrees with `outputs/_analyses/specificity-ladder/a1-pilot-dd9aed6-accounting.txt`: state COMPLETED, elapsed 95 seconds, exit `0:0`, one GPU; batch and extern steps also COMPLETED with exit `0:0`. Stdout and stderr: `logs/lad-a1-pilot-23411942.out` and `logs/lad-a1-pilot-23411942.err`. No exception or OOM appears; stderr contains progress and a tokenizer cleanup warning.
- Observed against expected: FAR 32/32, SDR 32/32 and SER 32/32 score rows; each has 64/64 replay records. Derived total is 4,200 rows, with 200 train, 200 validation and 1,000 test rows per task. Derived forward counts are 384 primary plus 192 replay, or 576 total prompt evaluations; the primary counts also match manifests and stdout. Counts do not mean that many separate model invocations: prompts were batched. Evidence: raw scores/replay files, derivation manifests and [24-a1-pilot-audit-calculations.json](24-a1-pilot-audit-calculations.json).
- Baseline reproduction assertion: independently compared the original baseline records with replay in pair-major clean/swapped order. Choices agree for FAR 64/64, SDR 64/64 and SER 64/64, hence derived 192/192 overall. Native margins also agree for 192/192, with maximum absolute difference 0.0 against declared tolerance 0.02; argmax token/id and both native logits are exactly equal too. Evidence: each task's scores.jsonl and baseline_repeat.jsonl, plus [24-a1-pilot-audit-calculations.json](24-a1-pilot-audit-calculations.json).
- Provenance: `outputs/_analyses/specificity-ladder/a1-pilot-dd9aed6/far_v2/test/run_manifest.json`, `outputs/_analyses/specificity-ladder/a1-pilot-dd9aed6/sdr_v2/test/run_manifest.json`, and `outputs/_analyses/specificity-ladder/a1-pilot-dd9aed6/ser_v2/test/run_manifest.json` each name full commit `dd9aed69d115e87f8942c4a622f993f5996d7b77`, canonical model/tokenizer, pinned revision, native scorer, source/request/prompt hashes, both registry hashes, job identity, limited scope and output hashes. No missing execution-evidence field remains.

Resource evidence supports unchanged inference on this GPU. Manifests report NVIDIA A100-SXM4-40GB, peak allocated 17,407,058,944 bytes and peak reserved 17,758,683,136 bytes; derived values are 16.212 and 16.539 GiB. The single model load took 28.150 seconds. These are measured inference values, not permission to train on this device. The live accounting batch MaxRSS is `14511608K`, a host-memory metric separate from CUDA peaks. Evidence: the raw run manifests and accounting query above; conversions in [24-a1-pilot-audit-calculations.json](24-a1-pilot-audit-calculations.json).

Timing projection is derived, not measured full-pool runtime. Task scoring windows, including replay, total 13.635 seconds; fixed overhead is 95 minus 13.635 = 81.365 seconds, including model loading and other setup. Full scoring uses 4,200 rows times 4 prompts = 16,800 evaluations, versus the pilot's 96 rows times 6 including replay = 576 evaluations. Scaling only scoring work gives 397.693 seconds; adding the fixed overhead gives 479.058 seconds, about 7.98 minutes or 0.133 GPU-hours. The pilot itself consumed 95/3600 = 0.0264 GPU-hours. A 15-minute single-GPU reservation would be 0.25 GPU-hours, leaving substantial room inside A1's 25-hour cap; the orchestrator must still check the live phase ledger. Evidence and arithmetic: [24-a1-pilot-audit-calculations.json](24-a1-pilot-audit-calculations.json), raw run manifests and `plan-a1.md`/`START.md` for scope/cap.

Measured-shape caveat: the pilot consists of deterministic leading test ids and includes replay; full scoring spans all source splits, omits replay and changes prompt grouping/batch padding. Derived metadata lengths for pilot/full are FAR 115–121/114–121, SDR 132–139/131–139, SER 123–130/122–130 tokens. Thus full observed source length maxima do not exceed pilot maxima, but throughput and memory remain shape-dependent. The estimate supports a bounded full-scoring reservation, not a runtime guarantee. Evidence: `outputs/_analyses/specificity-ladder/a1-derive-dd9aed6/` pairs.jsonl stream_metadata, with the range calculation performed CPU-only.

## What is NOT done

No full-pool score, assembly, fallback prompt construction, intervention, ladder assessment, model inference rerun, paid API use, notebook execution or git operation was performed. No final pool-size inference, causal specificity judgment, benchmark result or downstream phase gate follows from these pilot counts. The audit did not re-evaluate semantic transparency of the frozen prompt family or independently reconstruct model weights.

## Open questions

No execution-validity blocker remains. Proceed with the frozen full-scoring plan, distinct immutable output root, current protected-registry check and observed-runtime reservation buffer. Report full test-pool membership and paired competence separately before applying the preregistered fallback. Full scoring alone does not finish A1's later ladder work.

Numerical provenance: thresholds, row scope, batch size, cap and phase budget are prospective specifications; counts, margins and hashes above come from the cited raw files and independent audit receipt. Timing, GiB and GPU-hour conversions are explicitly derived. Usage check returned 8 percent used, 92 percent remaining, below the 80 percent cap, with reset `2026-11-06T16:07:41+00:00`; no budgeted work was started by this audit.
