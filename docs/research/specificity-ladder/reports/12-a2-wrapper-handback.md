# Hand-back 12: A2 frozen wrapper, paused implementation

Agent: Codex worker. Ticket: `plan-a2.md` Task 2 only. Status: held after a HOLD. User requested restart; Task 2 implementation remains incomplete.

## What changed

Files saved for orchestrator review and explicit-file commit; no worker git operations:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/twin_training.py`: focused stdlib launcher with dry-run default, fixed coarse configuration, selected-ID prefixes, production readiness gate, allocation/hardware checks, full-process clock, stdout/stderr log, artifact/config checks, failed receipts, allowlisted environment, and supplied source commit injected into native manifest.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/jobs/specificity_ladder_a2.json`: fixed model, seeds 42/1/123, epochs 500, sparsity 0.3, lr 0.03, batch 7, faithfulness 1, gate defaults and sample caps.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_twin_training_wrapper.py`: 15 CPU contract tests including real tiny fake training children and success/failure/missing/config-mismatch/stale outputs.
- This handback is mirrored into primary and worktree report paths. No staged apply operations.

## How verified

```
OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_wrapper.py -p no:cacheprovider -q
```

Observed: 15 passed in 0.62 s. Initial red collection failed because the wrapper module did not exist. That is a missing-module error, not a completed assertion-level red phase.

The following combined check was already running when HOLD arrived and completed before handback. Observed: mgnp 47 passed in 43.78 s; base Python 3.9 47 passed in 49.69 s, with existing pandas bottleneck-version and TRANSFORMERS_CACHE deprecation warnings. No failures.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_wrapper.py tests/test_twin_training.py -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_wrapper.py tests/test_twin_training.py -p no:cacheprovider -q
```

Observed source: actual loader uses deterministic prefixes; manifest schema is `tasks[task].split_ids/counts`, top-level `max_seq_length`, `source_commit`, `build_hash`, `fleet_ready`, `cohort`. Build manifest has no output root; CLI derives data root from its parent unless config supplies it. Actual printed timing is `Node pruning time: ...s`; actual artifacts are config/active_nodes/results/history/run_manifest JSON.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- Task2 is incomplete; do not launch a pilot from this handback.
- Known direct-launch bug: `python scripts/twin_training.py ...` cannot reliably import root-level `config` because the script directory is the initial import path. `python -m scripts.twin_training ...` from repository root should work. Add a subprocess CLI regression test and fix import resolution before using the direct launcher. No new edit started after HOLD.
- Combined materializer/wrapper focused suite passed on both required interpreters; no broader suite was run because this task adds an isolated wrapper.
- No external review, direct CLI dry-run subprocess check, actual-training argparse integration check, or final quality review. Current argv test checks known actual CLI flags but does not invoke train.py parser.
- Consider strengthening prelaunch consistency checks against private dataset_config files and manifest build hash, plus artifact semantic validation beyond parseable nonempty JSON. Currently split ID integrity/counts are checked in manifest, resolved output config subset is checked, and stale directories are refused.
- Actual allocation/hardware path is untested; requires Slurm job ID and exactly one A40/H100/H200 reported by nvidia-smi. Fake runner injection alone bypasses those checks.
- Task3 projection deliberately absent; CLI accepts dry-run/run only. No bash wrapper, training, model loads, API calls, GPU usage, sbatch, notebooks, or subagents.

## Open questions

- Lead should choose whether module invocation is the documented launcher or direct-script invocation also supported; default: support both with a CPU subprocess regression test.
- Lead should review whether manifest prefixes capped 200/200/1000 remain the agreed matched selection. Current implementation follows plan; materializer itself retains all matched rows.
- Lead should require a fresh review before production. Default: resume Task2, finish targeted verification on both interpreters, then independent review; Task3 remains separate.

Live Codex handback reading: 5% weekly used, 95% remaining; reset November 6 at 16:07:41 UTC. Pause is the user-requested restart hold, independent of usage.
