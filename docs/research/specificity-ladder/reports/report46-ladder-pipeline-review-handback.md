# Hand-back `46`: Independent staged ladder pipeline review

Agent: Codex reviewer. Ticket: ladder plan Task `4`. Status: handed-back.

## What changed

Production files were read only. The orchestrator may commit `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report46-ladder-pipeline-review-handback.md`. A matching hand-back is saved in the primary direction directory. No staged operations exist.

**Verdict: no remaining blocking finding in the reviewed pipeline after the narrow SDR summary qualification fix.** This is a code and CPU integration review, not authorization or evidence for a full model assessment. The bounded real-model pilot remains necessary.

One concrete reporting issue was found and closed during review. Selection recorded SDR as descriptive, but the initial summary path discarded that qualification. A model-free synthetic numerical pass returned `task='sdr_v2'`, `status='strong'`, `strong=True`, `point_pass=True`, `complete_assay_ready=True`, with `descriptive` absent. The implementer added `qualify_summary` in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_pipeline.py:417` and wired it into the actual summary write path. Inspection and a direct call now show `descriptive=True`, `status='descriptive_only'`, `strong=False`, while retaining `point_pass=True`, readiness, and the original numerical status/strength as diagnostics. Source-group memberships and duplicate-group provenance survive in the summary. The new pure regression passes. A first exploratory call omitted the required `duplicate_group` fixture field and raised `KeyError`; rerunning with the actual complete selected-group schema produced the output above.

Reviewed behavior:

- Prepare freezes the paired mechanism intersection at the specified fixed count and seed, excludes the union of actual prior selection artifacts, and passes each task's ordered selection IDs separately. It uses source/builder hashes, original D/H source checks, actual request spans and explicit role/content token boundaries. Assessment membership is not filtered by baseline correctness or donor availability.
- Select captures original-H selection rows only for the native DLA screen, with honest-minus-opposite orientation in both streams, and builds each bank from original-H train/validation IDs in both streams. Assessment outcomes do not enter the selection calculation. Recorded groups are loaded from the source artifact; SDR's qualification is retained. The real deciding groups all include MLPs, which the screen preserves.
- Artifacts refuse overwrite, seal payload hashes, and join design, groups, banks, scores and final summary. Validation checks live source/selection files and rebuilds the frozen design to catch changed assessment, bank or donor definitions. Score and positive-control coverage are checked by exact identity tuples rather than trusting row counts supplied by a result.
- Primary and worktree held-out registries, plus optional extra registries, are read again before model loading; utility IDs are included. The current code recomputes the canonical grader source hash and checks both direction registry entries before model loading. Native loading requires a Slurm CUDA allocation and resolves the pinned local snapshot/shards. Dry runs load no model. Injected provenance propagates through stages; pilot and injected artifacts cannot produce a production final verdict.
- IOI and MMLU samples use the fixed utility adapter defaults. IOI assessments use clean streams with corrupt donors; MMLU has only its stated floor/replay cells and readout calibration, without an invented item swap. Optional IOI task-resample diagnostics are explicitly not requested, so their omission is not a required-scope gap. Mechanism independent donor seeds remain explicit, with unsupported rows retained.
- The runner supplies the same-path no-op controls, full-sender readout calibration, full-vocabulary expected-token accuracy, raw and canonical margins, optional choice diagnostics, and source/donor provenance. The tiny native-hook test exercises real selection and scoring with these interfaces, rather than only monkeypatching the runner.
- Finalization checks complete expected rows, exact positive-control coverage, fixed mechanism and utility sample sizes, and `complete_assay_ready` for primary item-swap cells. Readiness is distinct from numerical success: nonpositive denominators or a completed scientific null can finalize. The separate MMLU guard remains visible as `passed=False` when it fails; completeness does not silently turn it into a pass. Unsupported optional independent donors and the documented F-twin gap do not block otherwise complete required cells. H's identity twin cannot supply preservation evidence.

## How verified

All commands below ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_specificity_ladder_cli.py -q
```

Final observed output: `20 passed, 1 warning in 15.26s`, exit code `0`. The actual tiny native-hook select-to-score test passed. Earlier suites ran before the concurrent narrow additions and were superseded by this final run.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_specificity_ladder_cli.py -q
```

Final observed output: `19 passed, 1 skipped, 3 warnings in 21.37s`, exit code `0`. The tiny native-hook integration test skips because this interpreter does not have the pinned NNsight version; the mgnp pass above supplies the applicable integration check.

```bash
bash -n scripts/jobs/specificity_ladder.sh
```

Observed: exit code `0`.

```python
from component_analysis.ladder_pipeline import qualify_summary
summary = {'cells': [dict(task='sdr_v2', group='sdr_v2_full', status='strong',
    strong=True, point_pass=True, complete_assay_ready=True)]}
selected = {'groups': {'sdr_v2': dict(full=[['mlp',0,0]],
    minus=[['mlp',0,0]], duplicate_group=True, descriptive=True)}}
cell = qualify_summary(summary, selected)['cells'][0]
print({k: cell.get(k) for k in ('task','status','strong','point_pass',
    'complete_assay_ready','descriptive','numerical_status','numerical_strong')})
```

Ran with the mgnp interpreter and BLAS threads pinned. Observed the closed-issue output described above, exit code `0`.

I also read the implementer's raw canonical wrapper log at `/tmp/ladder-cli-canonical-wrapper.log`, which ends `prepare: validated dry-run; no model or writes`, and checked that `/tmp/ladder-cli-preflight` does not exist. I did not independently rerun that full local-cache preflight and do not count it as my own command execution. Author report `42` was not read.

## Execution evidence

Local CPU unit, integration and model-free reproduction commands only. No pretrained model, GPU, API, notebook or Slurm job was executed by this reviewer. Final focused-suite counts are `20` passing against `20` collected in mgnp, and `19` passing plus `1` expected skip against `20` collected in base. Commands exited `0`; no real behavioral baseline or production assessment row output exists from this review. There is no scientific run manifest for the review, so real-model assay behavior is not yet verified.

## What is NOT done

No production edits or git commands. No full staged real-model run, actual assessment, timing/memory pilot, scoring job submission, empirical denominator/competence assessment, or claim of preserved general capability. The wrapper syntax check and tiny native-model tests do not establish the real-model acceptance criteria. The eventual pilot must record walltime, peak memory, baseline competence, exact output counts and calibration/no-op tolerances before the full reservation.

## Open questions

No current code blocker requires a user answer. Default: freeze the reviewed source and prospective design, then follow the bounded pilot gate with fresh registries and its complete provenance. Preserve the explicit SDR descriptive-only qualification and keep any failed numerical gates visible when reporting a completed assay.
