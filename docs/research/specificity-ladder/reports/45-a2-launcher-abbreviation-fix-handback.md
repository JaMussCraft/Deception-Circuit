# Hand-back for ticket #45: Reject abbreviated launcher stage overrides

Agent: Codex worker. Ticket: independent registry review launcher blocker. Status: handed-back.

## What changed

Orchestrator commit list from the worktree:

- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/twin_training.py: disabled argparse option abbreviation in the stage pre-parser and main parser, so a launcher dry-run cannot become run or project through --sta, --stag or other option prefixes.
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/twin_training_projection.py: disabled argparse option abbreviation consistently in the projection parser.
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_twin_training_wrapper.py: actual shell-launcher regression uses an executable CPU shim that injects run/project stubs and writes a marker if either dispatch is reached. Covers split and equals forms of --sta/--stag for run/project; separate exact dry-run/run/project dispatch tests preserve supported behavior.

The root-owned launcher /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/jobs/specificity_twin_training.sh was exercised without modification. The fake interpreter avoids model or training execution even when reproducing the original bug.

## How verified

Commands ran from /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder. Observations are retained in /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/45-a2-launcher-abbreviation-checks.json.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_wrapper.py -k actual_launcher_rejects_abbreviated_stage -p no:cacheprovider -q
```

Before implementation: eight failures, each because the actual launcher reached the injected execution/project marker.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_wrapper.py -k 'actual_launcher_rejects_abbreviated_stage or exact_stage_names_keep' -p no:cacheprovider -q
```

After implementation: eleven passes; abbreviated stage requests exit with an argument error and never reach run/project, while exact stage names retain dispatch.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_projection.py tests/test_twin_training_wrapper.py -p no:cacheprovider -q
```

Observed: 168 passed; see /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/45-a2-launcher-abbreviation-checks.json.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_projection.py tests/test_twin_training_wrapper.py -p no:cacheprovider -q
```

Observed: 168 passed, with the existing pandas/bottleneck warning; see /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/45-a2-launcher-abbreviation-checks.json.

Both report copies pass research-session lint; strict report-number checking resolves every numeric claim. Weekly quota remains below the user threshold, with the reading retained in /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/45-a2-launcher-abbreviation-checks.json.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No GPU, model, API, notebook, git, Slurm submission, training pilot or fleet reservation. No shell-launcher source change. The positive run-stage test invokes only an injected CPU stub; it is not measured training evidence. No unrelated test suites were run. Root owns independent review, explicit-file commit and any later launch.

## Open questions

None blocking for this fix. Registry review may identify separate issues; this patch addresses only option abbreviation and preserves the accepted exact stage names.
