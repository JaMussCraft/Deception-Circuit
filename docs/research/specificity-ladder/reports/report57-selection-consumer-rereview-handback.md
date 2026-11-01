# Hand-back `57`: Selection completion consumer closure

Agent: Codex independent reviewer. Ticket: close report `54` selection-sidecar finding. Status: handed-back.

## What changed

Production files were read only. The orchestrator may commit `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report57-selection-consumer-rereview-handback.md`. The report is mirrored in primary. No staged operations exist.

**Verdict: the report `54` P1 is closed by the current consumer guard; no remaining blocking finding in this narrow re-review.** Author report `56` was not read.

`read_selection` in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_pipeline.py:449` now requires the final completion sidecar to exist and parse as the expected manifest schema. It reads the sealed selected artifact, checks its kind and design/group/bank content joins, checks exact task coverage, and checks injected provenance against preparation. It validates selection execution identity against both CLI arguments and prepared identity, checks code identity, and requires recorded full groups, ordered selection IDs, ordered head keys, raw DLA dimensions and bank IDs to match the frozen preparation.

The writer and reader share `selection_manifest_core`, so the consumer rebuilds the expected sidecar fields from the actual selected artifact and prepared inputs. It requires the exact top-level field set and compares every expected value by canonical content hash. This binds schema/kind, exact selected artifact location and bytes, selected payload, design, group, bank, raw DLA, input hashes, code, supplied commit/model/tokenizer identity, execution evidence, counts and injected status. A whitespace-only selected file change now invalidates its exact-file link; a changed payload with a recomputed envelope still invalidates the sidecar links.

The actual `main` path invokes `read_selection` for both score and summarize immediately after prepared validation, before dry-run tokenizer loading and before any scoring model or score-summary consumer. This closes the original model-loader reproduction and also prevents a missing sidecar from being ignored by summary or dry-run paths. A valid intact completion marker passes and reaches the intended downstream consumer. Selection still writes the sidecar last and refuses existing outputs; no artifact-layout replacement is required.

The scoped implementation changes factor the existing sidecar schema into a shared helper and add consumer validation. They do not change selection DLA, screening, group subtraction, H-bank collection, sample membership/order/seed, intervention calculations, metric definitions or gate thresholds. Existing prepared artifacts are not rewritten. Their code identity remains subject to the lead's separate distinct-root preparation and semantic comparison after commit.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_specificity_ladder_cli.py -k 'refuses_incomplete_selection or accepts_completed_selection or dry_run_rejects_incomplete_selection' -q
```

Observed: `52 passed, 28 deselected in 2.48s`; exit code `0`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_specificity_ladder_cli.py -k 'refuses_incomplete_selection or accepts_completed_selection or dry_run_rejects_incomplete_selection' -q
```

Observed: `52 passed, 28 deselected, 1 warning in 2.48s`; exit code `0`. The warning is the existing base pandas/bottleneck version combination.

The targeted tests call the actual `main` dispatch for both score and summarize, using guarded downstream consumers. Missing, malformed, empty, partial and wrong-schema markers are rejected. The mutation matrix also covers exact file bytes, recomputed selected-payload envelope, artifact path/payload/file links, design, raw DLA, group, bank, counts, commit/model/tokenizer identity, source/selection/code hashes, execution and injected provenance. The intact marker reaches the score loader sentinel or summary-read sentinel as appropriate. Dry-run tests require rejection before tokenizer or model access. Unrelated prepared/source/registry validation is mocked in these fixtures to isolate the completion consumer; the sidecar reader itself is not mocked.

## Execution evidence

Local scoped CPU tests only. Each interpreter produced `52` passing against `52` selected tests, with `28` intentionally deselected; both commands exited `0`. No pretrained model, GPU, API, job, notebook, production behavioral baseline or assessment output was run. There is no scientific run manifest for this review, so production model behavior is not yet verified here.

## What is NOT done

No production edits or git commands. No broad rerun, prior tiny native-model repeat, real selection/scoring job, existing preparation mutation, new preparation semantic comparison or unrelated runtime modification. The earlier tiny native integration and metadata checks remain documented in report `54`; this re-review exercises only the new completion-consumer requirement and valid path.

## Open questions

No current blocker. Default: retain the sidecar as the final selection completion marker and carry the reviewed code through the lead's separate immutable preparation and bounded pilot workflow.
