# Hand-back 16: A1 immutable staged pipeline

Agent: Codex worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a1.md`, Task 3. Status: handed-back

Implementation is ready for lead review; no real scoring was authorized or performed by this worker.

## What changed

The orchestrator commits these worktree files by explicit list:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/user_inversion_pipeline.py`: CPU derive, allocation-only native score, CPU assemble, and meaningful no-write score preflight. Immutable task/split artifacts bind original source rows/configurations, frozen requests, exact prompts, ordered ids and tokenizer revisions. All source splits are checked before scope selection. Protected ids are unioned from primary, branch and optional registries immediately before loading; registered files are hashed and their actual ids read.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_user_inversion_v2.py`: only a deferred main delegate appended; reviewed pure functions unchanged.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/jobs/specificity_user_inversion.sh`: common cluster profile/activation for dry and real runs, BLAS one thread, offline caches, explicit interpreter override, allocation enforcement and no self-submission.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_user_inversion_pipeline.py`: injected CPU scoring, immutable/hash/split/protected-id guards, cached threshold fallback, pilot replay, stratified reports and actual A2 consumer admission.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_user_inversion_job.py`: actual wrapper positive preflight over tiny real-tokenizer derived records, malformed commit rejection and login allocation refusal.

Score uses one loaded model across selected tasks, native scorer batch size eight and maximum length 256, with explicit prechecks preventing silent truncation. The limited test pilot repeats baseline scoring on the same path, recording agreement, margin differences and prospective absolute tolerance 0.02, plus measured model load/scoring timing and CUDA peak memory when actually run. Limited records cannot assemble a full pool. Separate output roots allow 0.7 and 0.5 assembly from identical saved scores. Both assembled arms contain byte-identical self-contained receipts and score files matching the shared contract; baseline competence remains diagnostic at 0.3.

Required-file local cache resolution replaces snapshot_download: the latter refused a valid tokenizer/model cache because README/LICENSE metadata was absent. Base transformers 4.57.3 also invokes Hub model_info inside its irrelevant Mistral heuristic despite local_files_only and fix_mistral_regex=False. Lead approved a version-scoped exact-local-snapshot tokenizer load, with logical canonical identity normalized and explicit tokenizer_loading provenance recording actual path, resolved snapshot, normalization and reason. Normal mgnp loading keeps the canonical model id. The consumer worker was informed; no required contract field changed.

## How verified

Initial RED command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_user_inversion_pipeline.py tests/test_user_inversion_job.py
```

Observed: two failures and eight setup errors because the pipeline module and shell wrapper did not exist. Further targeted RED runs observed missing primary-registry support, missing pilot replay, missing stratified counts, literal interpreter provenance, missing real preflight and missing local-tokenizer compatibility. The first base wrapper preflight exposed the offline Mistral heuristic error; it was fixed without an online retry. The initial help-only wrapper dry run was inadequate and was replaced after lead review.

Final owned checks:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_user_inversion_pipeline.py tests/test_user_inversion_job.py
```

Observed: 18 passed, two existing environment warnings, 32.19 seconds. Full log `/tmp/a1-pipeline-base-final.log`. Warnings concern bottleneck version and TRANSFORMERS_CACHE deprecation.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_user_inversion_pipeline.py tests/test_user_inversion_job.py
```

Observed: 18 passed, 31.36 seconds. Full log `/tmp/a1-pipeline-mgnp-final.log`.

Earlier focused native regression commands added `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_inversion_v2.py` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_matched_honest.py` to that same invocation. Both interpreters passed 117 tests; base took 31.19 seconds with the bottleneck warning, mgnp took 27.69 seconds. Subsequent edits were restricted to new pipeline preflight/provenance and its tests. The previously passing pure suite was not unnecessarily repeated; the actual consumer admission integration and native regression checks cover the seam.

```bash
bash -n scripts/jobs/specificity_user_inversion.sh
```

Observed: exit zero. Python AST parsing with feature_version=(3,9) also accepted all owned Python files before the final preflight additions; the final base pytest run imports and exercises those additions under actual Python 3.9.

## Execution evidence

CPU-only tokenizer derivation command, run from the worktree:

```bash
HF_HOME=/work/nvme/beto/swong2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m dataset.build_user_inversion_v2 --stage derive --tasks far_v2 sdr_v2 ser_v2 --data-dir data/datasets --work-dir outputs/_analyses/specificity-ladder/user-control-cpu --model-revision 0e9e39f249a16976918f6564b8830bc894c89659 --tokenizer-revision 0e9e39f249a16976918f6564b8830bc894c89659
```

Exit zero. Each task produced 200 train, 200 validation and 1000 test pairs, exactly the corresponding source counts: 4200 pairs total, zero rejections. Every saved row was inspected for role terminators, request-span/readout separation and the 256-token bound; per-request and per-pressure counts are in each derivation report. New prompt token lengths span FAR 114–121, SDR 131–139, SER 122–130. The canonical cached tokenizer revision is the full snapshot hash in the command. Baseline behavioral reproduction is not applicable: no inference occurred.

Immutable diagnostic artifacts are under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/user-control-cpu/{far_v2,sdr_v2,ser_v2}/{train,validation,test}/`, each containing pairs.jsonl, derivation_report.json and derivation_manifest.json. They were created during implementation and intentionally contain no supplied scoring code commit or measured receipt. The lead will derive fresh immutable roots after code review and commit; these CPU artifacts must not imply that this pipeline existed at an older code commit.

Actual strong wrapper preflight command, run with default profile and activation:

```bash
bash scripts/jobs/specificity_user_inversion.sh --dry-run --tasks far_v2 sdr_v2 ser_v2 --splits test --limit 32 --data-dir data/datasets --work-dir outputs/_analyses/specificity-ladder/user-control-cpu --score-dir /tmp/specificity-default-preflight-no-write --commit aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --model-revision 0e9e39f249a16976918f6564b8830bc894c89659 --tokenizer-revision 0e9e39f249a16976918f6564b8830bc894c89659
```

The all-a commit is explicitly synthetic preflight input, never actual scoring provenance. `/tmp/a1-pipeline-default-preflight.log` retains output. A second actual wrapper run set DC_PYTHON=/sw/external/python/anaconda3/bin/python3.9 and used score root `/tmp/specificity-base-preflight-no-write`; its output is `/tmp/a1-pipeline-base-preflight.log`. Both commands exited zero, and a separate parsed-plan check found both requested output roots absent. Both plans require 32 test pairs and 128 primary prompt forwards per task, plus baseline replay when a real pilot later runs; no forward happened here. Both plans report model_loaded=false and writes=false, current primary/branch registry digests and exact local model snapshot. No Slurm job, GPU inference, paid API, notebook or git operation occurred.

Synthetic scoring tests use injected functions and fixture commit aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. Their 0.6 opposite margin retains zero rows at 0.7 and one per split at 0.5, with paired baseline competence one per split. The actual A2 materializer accepts these assembled self-contained receipts with validate_only=True. These are test values, not scientific pool-size or baseline measurements.

## What is NOT done

- No real score, GPU allocation/submission, full assembly of measured rows or native precision comparison. Real inference remains gated on lead review, full supplied commit and registered ledger reservation.
- No behavioral 300-id gate claim. CPU alignment coverage is not behavioral retention and does not complete A1.
- No crossed ladder, mover subtraction, response-turn fallback, MMLU floor, training, A2 fleet or A3 work.
- No full-repository test run: the task explicitly requested focused checks and preservation of the existing pure-suite result. Relevant native regression files and real consumer integration were exercised.
- Native GPU loading and resource metrics are implemented but have not been exercised on actual hardware; CPU preflight checks all required cached configuration/index/shard files only.
- No worker commit. The lead owns independent review, provenance commit, integration and any subsequent run.

## Open questions

No blocking schema question remains. Default next action: lead review and commit, regenerate final immutable derivation root, then registered single-GPU limited pilot under a distinct score root. Require its repeat-baseline validity and actual runtime/memory evidence before full scoring reservation.

The completion usage checkpoint read 7 percent spent, 93 percent remaining, should_pause=false; reset 2026-11-06T16:07:41+00:00. The cap remains 80 percent.
