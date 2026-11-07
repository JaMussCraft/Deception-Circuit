# A40 calibration execution audit

## What changed

Status: done

Execution gate: PASS for complete screening on A40 only, using the frozen code, prompts, source rows, scorer and model/tokenizer snapshot. Keep hardware-specific scores separate and assemble membership exclusively from the complete A40 run. The evidence supports internally consistent inference on A40; it does not establish hardware-invariant margins or membership. No deception-specificity claim follows.

Added this hand-back and an independent CPU audit script and calculation receipt, mirrored in primary and worktree. No run, dataset, production implementation, notebook or other worker artifact was changed.

The hardware-switch rationale and chronology are dispatch-supplied context: the parent reports an occupied A100 slot and long queue, with the choice stated in commentary and Slurm test-only calls before submission/results. There is no standalone pre-result decision artifact for independent chronology verification. A retrospective worklog entry must remain explicitly retrospective. The rationale is not inferred from the raw A40 output and does not determine the execution verdict.

## How verified

Directly read the A40 run manifests, scores and baseline replay files in `outputs/_analyses/specificity-ladder/a1-a40-pilot-dd9aed6/`, the corresponding raw A100 files under `outputs/_analyses/specificity-ladder/a1-pilot-dd9aed6/`, source derivation artifacts in `outputs/_analyses/specificity-ladder/a1-derive-dd9aed6/`, stdout/stderr, and the accounting receipt. No lead comparison summary or other narrative report was read. Used the already-read frozen START/spec/plan and shared instructions.

The CPU script [29-a40-calibration-audit.py](29-a40-calibration-audit.py) ran successfully under mgnp with single-threaded numerical libraries; its independently calculated results are [29-a40-calibration-audit-calculations.json](29-a40-calibration-audit-calculations.json). It recalculates score/replay hashes, derivation-file and manifest hashes, original D/H config/all-split source hashes, test source-row hashes, request-pool hash, prompt aggregates and every scored prompt hash; it validates record order, unique ids, score arithmetic, expected-token choices and exact self-replay. All assertions passed.

Across hardware, exact source hashes, prompt hash, request-pool hash, derivation-manifest hash, ordered ids, canonical model/tokenizer identities, revisions, scorer, dtype, batch size and maximum-length configuration agree. Both protected registries currently match the recorded hashes and remain empty. The recorded full code commit is `dd9aed69d115e87f8942c4a622f993f5996d7b77`; pinned model/tokenizer revision is `0e9e39f249a16976918f6564b8830bc894c89659`. The audit checks these manifest identities, locally pinned snapshot shard existence and tokenizer-config hash, without git or model-weight loading; historical worktree cleanliness is not independently reconstructed.

Derived cross-hardware comparison covers all native primary scores, not merely pool counts. Choices and argmax ids agree for 384/384. Only 150/384 native margins are exactly equal; only 127/384 native tuples (choice, argmax id, both logits and margin) are exactly equal. The table shows absolute A40-minus-A100 margin drift, calculated from the raw records. [29-a40-calibration-audit-calculations.json](29-a40-calibration-audit-calculations.json)

| Task/arm | Compared | Exact margins | Maximum absolute drift | Mean absolute drift |
|---|---:|---:|---:|---:|
| FAR inversion | 64 | 21 | 0.375 | 0.1103515625 |
| FAR neutral | 64 | 20 | 0.375 | 0.1142578125 |
| SDR inversion | 64 | 24 | 0.75 | 0.103515625 |
| SDR neutral | 64 | 29 | 0.25 | 0.083984375 |
| SER inversion | 64 | 27 | 0.375 | 0.099609375 |
| SER neutral | 64 | 29 | 0.375 | 0.0927734375 |

Derived threshold membership below requires opposite full-vocabulary argmax and opposite-minus-honest margin at least the threshold in both designation streams. The neutral competence floor is honest argmax and honest-minus-opposite margin at least 0.3 in both streams; competence does not alter primary inversion membership. Evidence: [29-a40-calibration-audit-calculations.json](29-a40-calibration-audit-calculations.json), with thresholds specified in `docs/research/specificity-ladder/plan-a1.md`.

| Derived task | A100/A40 retained at 0.7 | A100/A40 retained at 0.5 | A40 competent among 0.7 retained | A40 competent among 0.5 retained | Neutral competent overall |
|---|---:|---:|---:|---:|---:|
| FAR | 20/20 of 32 | 21/21 of 32 | 20/20 | 21/21 | 32/32 |
| SDR | 31/32 of 32 | 32/32 of 32 | 31/32 | 31/32 | 31/32 |
| SER | 26/27 of 32 | 28/28 of 32 | 27/27 | 28/28 | 32/32 |

Derived symmetric membership differences at 0.7 are zero for FAR and one each for SDR and SER, exclusively A40 additions; at 0.5 there are zero differences for all tasks. Baseline competence membership is unchanged across hardware. All neutral full-vocabulary choices are honest in both streams; the SDR competence exclusion is a margin-floor failure. Evidence: [29-a40-calibration-audit-calculations.json](29-a40-calibration-audit-calculations.json).

The boundary-sensitive SDR id `00cec805d9d4` has clean opposite margins 0.625 on A100 and 0.75 on A40; swapped margins are 4.625 and 4.875. SER id `0113fbe24429` has clean margins 0.625 and 0.875, with swapped margin 2.25 on both. Thus unchanged choices coexist with changed screening membership. Evidence: `outputs/_analyses/specificity-ladder/a1-pilot-dd9aed6/sdr_v2/test/scores.jsonl`, `outputs/_analyses/specificity-ladder/a1-a40-pilot-dd9aed6/sdr_v2/test/scores.jsonl`, and the corresponding ser_v2 files; ids are also in the independent calculation receipt. These are descriptive comparisons only, with no final pool extrapolation.

## Execution evidence

- Job and cluster: `23412323`, Delta. A fresh read-only sacct query agrees with `outputs/_analyses/specificity-ladder/a1-a40-pilot-dd9aed6-accounting.txt`: COMPLETED, elapsed 101 seconds, exit `0:0`, one GPU. Batch and extern also completed successfully. Batch MaxRSS is `14499168K`, a host-memory metric. Logs are `logs/lad-a1-a40-cal-23412323.out` and `logs/lad-a1-a40-cal-23412323.err`; stderr has progress and a tokenizer cleanup warning, with no exception or OOM.
- Rows observed against expected: FAR 32/32, SDR 32/32, SER 32/32 primary records and 64/64 baseline-repeat records per task. Derived totals are 96 paired rows, 384 primary prompt evaluations and 192 repeats, hence 576 total. This is evaluation count, not separate model invocation count, because scoring batches prompts. Evidence: raw JSONL files, manifests, stdout and [29-a40-calibration-audit-calculations.json](29-a40-calibration-audit-calculations.json).
- Baseline reproduces: independent pair-major clean/swapped comparison finds exact choice, argmax token/id, native logits and native margin agreement for FAR 64/64, SDR 64/64 and SER 64/64. Derived aggregate is 192/192, maximum absolute native-margin difference 0.0, within the manifest's 0.02 tolerance. This is same-hardware A40 replay evidence, separate from cross-hardware drift. Evidence: each A40 scores.jsonl and baseline_repeat.jsonl plus [29-a40-calibration-audit-calculations.json](29-a40-calibration-audit-calculations.json).
- Provenance files: `outputs/_analyses/specificity-ladder/a1-a40-pilot-dd9aed6/far_v2/test/run_manifest.json`, `outputs/_analyses/specificity-ladder/a1-a40-pilot-dd9aed6/sdr_v2/test/run_manifest.json`, and `outputs/_analyses/specificity-ladder/a1-a40-pilot-dd9aed6/ser_v2/test/run_manifest.json`. Each names full commit `dd9aed69d115e87f8942c4a622f993f5996d7b77`, pinned model/tokenizer revision, native scorer, source/request/prompt and output hashes, job/cluster, limited scope, dtype/device, and protected-registry identities. All required execution-evidence fields are present.

A40 resource evidence is CUDA BF16, batch size 8, maximum length 256, single model load 23.199 seconds, peak allocated 17,407,058,944 bytes and reserved 17,758,683,136 bytes. Derived CUDA values are 16.212 and 16.539 GiB. These are inference measurements; they do not establish a training-memory budget. Evidence: all three A40 raw run manifests; [29-a40-calibration-audit-calculations.json](29-a40-calibration-audit-calculations.json).

Timing projection is derived, not measured full-run duration: pilot task-scoring windows sum to 26.454 seconds including replay. Fixed overhead is 101 minus 26.454 = 74.546 seconds, already including model load and setup. Full scoring has 4,200 rows times 4 prompts = 16,800 prompt evaluations; pilot has 96 rows times 6 prompts including replay = 576. Scale scoring by 16,800/576, equivalently 4,200/96 times 4/6, giving 771.579 seconds, then add fixed overhead for 846.125 seconds, about 14.10 minutes or 0.235 GPU-hours. A 20-minute single-GPU reservation is 0.333 GPU-hours and gives a reasonable initial buffer; recheck the live A1 ledger against its 25 GPU-hour cap. The pilot's derived spend is 101/3600 = 0.0281 GPU-hours. Evidence: raw run manifests, accounting receipt, frozen START and [29-a40-calibration-audit-calculations.json](29-a40-calibration-audit-calculations.json).

Derived actual prompt-length ranges, pilot/full across all splits, are FAR 115–121/114–121, SDR 132–139/131–139 and SER 123–130/122–130 tokens. Full-pool maxima equal the pilot maxima, remaining below the configured cap. Lengths come from the immutable derivation pairs' stream_metadata and are recalculated in [29-a40-calibration-audit-calculations.json](29-a40-calibration-audit-calculations.json). The pilot uses leading test ids and repeats baseline scores; full scoring changes row mix and batching and omits replay. Treat the timing and memory estimates as shape-dependent projections, not guarantees.

## What is NOT done

No full screening, pooled hardware score artifact, assembly, intervention, causal inference, specificity verdict, final pool-size extrapolation, notebook execution, git operation, GPU inference or API call was performed. Exact same-hardware baseline replay does not prove invariant inversion scores under every future batch shape. This coarse pilot explicitly does not show hardware-invariant margins; measured threshold crossings demonstrate boundary sensitivity.

## Open questions

No execution blocker remains for the scoped A40-only full score. Preserve the frozen prompt family and numerical path, score every source split afresh into a distinct immutable A40 root, recheck both protected registries immediately before model loading, and reserve within the live phase ledger. Do not fill full-run rows from either pilot or combine A100 and A40 scores. Report hardware, BF16 path, measured drift and the observed membership sensitivity with the final pools.

Use the complete A40 score cache for both threshold assemblies, each at a separate output root, and report primary retained and paired-competent counts separately. Downstream baseline/intervention comparisons should use the same hardware and matched computation path. If hardware must change again, a new calibration and internally consistent scoring plan are needed; these pilot agreements do not waive that requirement. No broader run is authorized by this audit.

Usage evidence: the live Codex check returned 9 percent used and 91 percent remaining, below the 80 percent cap; reset is `2026-11-06T16:07:41+00:00`. These readings are operational context, not scientific evidence. All other nonliteral conversions and projections above are explicitly derived; configuration thresholds and caps come from the frozen plan.
