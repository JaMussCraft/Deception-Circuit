# Hand-back 42: staged specificity ladder CLI

Agent: Codex implementation worker. Ticket: approved plan-ladder Task 4. Status: handed-back.

## What changed

Committed by the orchestrator from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_pipeline.py`: immutable prepare/select/score/summarize CLI; CPU normalization of original D/H/F and assembled I/neutral; source and builder proof checks; balanced fixed assessment design; separate selection exclusion union and ordered mover IDs; original-H selection DLA and two-stream train/validation bank; canonical expected score/control coverage; protected registries and frozen/current grader hash checks; complete execution manifest; pilot/injected finalization refusal.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/jobs/specificity_ladder.sh`: canonical module wrapper, offline cluster environment, real CPU dry run, no submission.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_specificity_ladder_cli.py`: staging guards, stale source/bank/donor/assessment/grader refusals, ordered selection provenance, canonical delegation, exact positive controls, and actual tiny native select-to-score integration.

Independent review found that SDR descriptive qualification was dropped by the metrics consumer. The pipeline now retains source-group provenance and numerical status, marks SDR summaries descriptive-only, and prevents a local numerical pass from becoming a strong specificity claim. A pure regression covers the qualification.

Root approved deduplication of repeated bank provenance: the selected artifact retains complete canonical bank provenance once; score rows carry checked artifact/bank hashes, task, reference, source IDs and token/instance counts. JSON round-trip dereferencing recovers the identical provenance hash and refuses a mutated artifact even after its envelope hash is recomputed. The in-memory runner is unchanged.

No files staged for the apply tool. Root owns the thin runner delegate and commits. No git, GPU, API, production model, or notebook execution occurred.

## How verified

Working directory for commands: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_specificity_ladder_cli.py tests/test_ladder_design.py tests/test_ladder_tasks.py tests/test_ladder_metrics.py -q -p no:cacheprovider
```

Observed: 78 passed, one deprecation warning. The actual tiny random Llama/NNsight pipeline passed, including selection, H mean bank, every required operation, utility scoring and 12 positive controls. Row coverage matched independently reconstructed expected keys.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_specificity_ladder_cli.py tests/test_ladder_design.py tests/test_ladder_tasks.py tests/test_ladder_metrics.py -q -p no:cacheprovider
```

Observed: 77 passed, one skipped, three warnings. Base environment lacks pinned NNsight 0.7.0; its native integration skipped. The pinned mgnp test above supplies actual execution evidence.

```bash
bash -n scripts/jobs/specificity_ladder.sh
```

Observed: exit 0.

```bash
DC_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python bash scripts/jobs/specificity_ladder.sh --dry-run --stage prepare --artifact-root /projects/beto/swong2/Alignment/Deception-Circuit --data-root /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/data/datasets --user-control-root /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a1-control-77b6487-m07 --work-dir /tmp/ladder-cli-preflight --design /tmp/ladder-cli-preflight/design.json --groups /tmp/ladder-cli-preflight/groups.json --tasks far_v2 sdr_v2 ser_v2 --commit 77b6487b08b4410a4e5a9995c6ff5e46834a5ce3
```

Observed: exit 0; `prepare: validated dry-run; no model or writes`. Log: `/tmp/ladder-cli-canonical-wrapper.log`. The command checked original and assembled sources, tokenization/proofs, selection provenance, fixed mechanism samples, IOI100, MMLU32 and protected/frozen registries. This was CPU preflight of uncommitted implementation using the prior commit as supplied identity; production freeze must use the later reviewed implementation commit.

```bash
test ! -e /tmp/ladder-cli-preflight
```

Observed: exit 0; no output artifacts were written by the dry run.

```bash
/sw/external/python/anaconda3/bin/python3.9 -c "from component_analysis.ladder_pipeline import grader_registry; print(grader_registry())"
```

Observed: exit 0. Current canonical grader source fingerprint matched the frozen value in both registries; both direction-registry files had SHA256 `f8c7dbb92f2edc509c7bb8e94624a5c8adabddd103a8c48db1cc59bd69a3c6b0`.

Live Codex reading at hand-back: 13 percent spent, 87 percent remaining; reset November 6, 2026 at 16:07:41 UTC. Threshold 80 percent was not reached.

## Execution evidence

- Job id and cluster: local CPU commands above; no Slurm job or production scoring.
- Exit code: wrapper and focused suites exited 0.
- Row counts: fixed prepare requests mechanism100 per task, IOI100 and MMLU32; dry run writes zero rows. The tiny pipeline asserted exactly 12 positive-control rows and equality of scored and independently expected row counts.
- Baseline reproduces: not applicable; no production baseline or empirical specificity claim is made. Tiny controls require native donor-logit recovery and empty/self-replay agreement.
- Provenance file: no production run manifest exists because preflight writes nothing. Production scoring writes immutable `score/run_manifest.json` with the full supplied commit and content hashes.

## What is NOT done

- No production assessment design or mover/bank artifact was frozen; root must review and commit code, then freeze with that full commit before GPU scoring.
- No production select/score/pilot/final gate has run. No budget reservation or submission was attempted.
- Optional IOI task-resample robustness is not requested by this pipeline and is explicitly labeled omitted. Mechanism independent donor seeds remain 101/102/103.
- Base tiny-native skip is not evidence of patch correctness; the mgnp integration passed instead.
- Independent review and any requested fixes remain the orchestrator's gate before production freeze.

## Open questions

None blocking implementation. Production job walltime/account and immutable artifact destinations remain orchestrator decisions. Default: retain the current no-production-freeze state until review and commit.
