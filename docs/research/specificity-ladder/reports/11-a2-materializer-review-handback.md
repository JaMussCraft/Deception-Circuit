# Hand-back 11: A2 materializer independent review

Agent: Codex Sol independent reviewer. Ticket: A2 plan Task 1. Status: resolved; changes required before matched-cohort acceptance.

## What changed

Review only; implementation and tests were preserved. The orchestrator can commit this report from:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/11-a2-materializer-review-handback.md`.

A matching report is copied to the primary direction reports directory. No staged apply operation exists.

One correctness blocker remains in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_twin_training.py`:

**P1: Matched inputs can bypass the scored A1 control gate and receive fleet-ready status.** At lines 204–210 the materializer accepts any finite nonnegative threshold, any nonempty model string, and the baseline-kind string. It does not require score/assembly provenance, compare the model/tokenizer identities, or validate the recorded A1 source-row hashes against the current D/H sources. At line 183 it sets `fleet_ready` solely from the requested cohort. The positive matched test fixture contains no scoring evidence, has arbitrary D/H source hashes, and is accepted as ready. A focused reproduction also changed I's threshold to zero and model to a different identity; the result remained ready.

This permits training an unfiltered control, a control scored under the wrong model, or a control detached from its declared source provenance. The existing training loader assumes preprocessing already applied the behavioral filter and does not repair this gap. The required A1 threshold is 0.7, with the recorded 0.5 fallback; zero is neither.

Minimal required fix: agree the A1 assembly-provenance schema with the producer, then make matched mode require and validate its score/assembly manifest, prompt/source hashes, full commit provenance, model/tokenizer identities and selected threshold. Require the I threshold to be 0.7 or the recorded 0.5 fallback. Validate each donor arm using its recorded threshold rather than imposing the inversion threshold on honest rows. A boolean `scored` alone would not establish that provenance. Add rejection tests for absent/stale scoring evidence, invalid I threshold, mismatched model/tokenizer, and mismatched A1 D/H source hashes. Timing-only D behavior can remain unchanged.

No additional blocker was found in the same-item H.clean reference selection, recipient labels, source-prefixed original prompts, duplicate/cross-split validation before matching, deterministic matching, explicit path overrides, refusal of existing outputs, Arrow nested roundtrip, actual loader masks/readout checks, pre-tokenization length bounds, or explicit validation under optimized Python.

## How verified

Read the implementation, its focused tests, A1 construction source, A2 Task 1 and START A2 requirements directly. Read the actual `DeceptionDatasetLlama`, dataset loading/saving helpers, and `DeceptionTask` dataloader. No worker narrative report was read.

Focused reproduction executed in the worktree with the mgnp interpreter:

```python
import contextlib, io, json, tempfile
from pathlib import Path
from tests.test_twin_training import matched_inputs
from dataset.build_twin_training import materialize
with tempfile.TemporaryDirectory(prefix='a2-review-') as tmp:
    with contextlib.redirect_stdout(io.StringIO()):
        args = matched_inputs(Path(tmp))
    path = Path(args['input_paths']['far_v2']['I']) / 'dataset_config.json'
    cfg = json.loads(path.read_text())
    cfg['margin_thresh'] = 0
    cfg['model'] = 'different-model'
    path.write_text(json.dumps(cfg))
    args['validate_only'] = True
    with contextlib.redirect_stdout(io.StringIO()):
        manifest = materialize(**args)
    print(manifest['fleet_ready'], manifest['tasks']['far_v2']['counts'],
          Path(args['output_root']).exists())
```

Observed: `True {'train': 1, 'validation': 1, 'test': 1} False`; exit code zero. D, H and I-neutral configs retained model `fake`; I used `different-model`. The accepted fixture had no scoring manifest or assembly provenance.

Read direct existing logs without rerunning suites:

- `/tmp/a2-materializer-focused-mgnp.log`: 32 passed.
- `/tmp/a2-materializer-focused-base.log`: 31 passed and one locally unavailable tokenizer skip.
- `/tmp/a2-materializer-mgnp-tests.log` and `/tmp/a2-materializer-base-tests.log`: each 236 passed and one failure in `test_hyperparameters_are_identical_across_the_three_mechanisms`, showing the existing 120 versus 128 mismatch.
- `/tmp/a2-materializer-real-validation.log`: inspected the materializer validation-only manifest, including the final build hash. This review did not repeat the full real-source validation.

## Execution evidence

- Job id and cluster: local CPU reproduction only, no scheduler job.
- Exit code: zero.
- Row counts: one accepted row in each of train, validation and test, against one expected fixture row in each; no materialized output was written.
- Baseline comparison: the existing positive matched fixture expects ready status; the changed-model, zero-threshold fixture still returned ready status. No scientific accuracy baseline was run.
- Provenance file: no `run_manifest.json` was produced by this CPU reproduction. The caller supplied the fixture commit of forty `a` characters; this is deliberately synthetic. This is code-review evidence, not yet verified as a scientific result.
- Usage reading: live Codex weekly usage was 5 percent spent against the delegated 80 percent threshold at handback.

## What is NOT done

No implementation changes, broad test reruns, GPU work, model inference, API calls, notebook execution, git operations or subagents. Tasks 2 and 3 of A2 were outside this review. The A1 assembly producer is still being implemented, so this review does not invent its final provenance schema.

## Open questions

The lead should freeze the A1 assembly provenance schema and have the materializer validate it before granting matched fleet-ready status. Default: accept timing-only D preparation while withholding matched acceptance until the blocker and negative tests are resolved. No other correctness change is requested.
