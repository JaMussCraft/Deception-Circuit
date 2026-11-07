# Hand-back: A3 diagnostic transport 254

Agent: Terra worker. Status: handed-back. Candidate is unbound and not deployed; independent review is required.

## What changed

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport254/` contains the candidate host, inner mount guard, absolute launcher, unchanged copy of transport229 helpers, sealed manifest, unbound config and source inventory, focused tests and raw logs, and deployment notes.
- The 1,120 deployment245 source records are augmented with six exact diagnosis253 files; all eight literal aliases are retained. The recipe selection positions are 85, 86, 87, 88, 117, 120 and 122 out of 223. No source, test, or recipe was changed.
- Manifest SHA-256: `8df6759644ae549869a8d4d0675d20b86a0e856e2ababfb6a0f131142f1d2e0d`. The status is unbound and the coordinator must create a separately sealed config only after review.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport254/test_transport.py
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport254/test_transport.py
```

Observed: eight pure mock tests passed in each interpreter; the exact raw outputs are `test-mgnp.log` and `test-base.log` in the package. Both interpreters also checked all 1,126 local file hashes, eight local alias targets, the 223-item collection and the six-plus-one selections; see `inventory-mgnp.log` and `inventory-base.log`.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No Slurm submission, native pytest suite, container execution, remote staging, source review, or configuration binding occurred. Actual Bridges Python 3.6, scheduler allocation fields, mount behavior, `prctl`, path transfer and resource margins remain to be checked on site. The focused tests are mocks and do not establish end-to-end deadline or descendant-reaping behavior. Neither partial diagnostic is an accepted GREEN result. Original Delta jobs were not touched.

## Open questions

Independent reviewer should inspect the 25-minute deadline and process-group logic, container effective-mount check, recipe environment/path substitutions, and source sealing before deployment. Default: keep unbound and do not schedule until review and actual-binding checks pass. Root should establish whether diagnostic module origin evidence needs strengthening before binding; the candidate currently pins the plugin source and sets its PYTHONPATH but does not record the imported module's actual `__file__`.
