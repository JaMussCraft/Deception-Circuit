# Hand-back 19: A2 wrapper independent review

Agent: Codex reviewer. Ticket: A2 plan Task 2. Status: blocked on two fixes below.

## What changed

Review only. No implementation edits, git, model execution, GPU use, API calls, notebooks, or subagents.

- Orchestrator review artifact: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/19-wrapper-review-handback.md`.
- Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/19-wrapper-review-handback.md`.

Two blocking findings:

1. **Freeze the actual D/I training loss margin.** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/twin_training.py:113` omits the existing `--deception-margin-loss` parser option. The materializer copies each recipient configuration, retaining `margin_thresh`; `tasks/deception.py` calls `resolve_margin`, and its hinge loss uses that resolved value. Thus a D source screened at 0.7 and an allowed I fallback screened at 0.5 produce different training objectives despite the frozen wrapper plan. A read-only call to the actual resolver yielded 0.7 and 0.5 respectively. Lead ruling: freeze explicit training margin **0.7** in the JSON and argv for both conditions, retain historical screening thresholds unchanged, add float conversion and an expected-config assertion, and reject a frozen-config or output-artifact margin mismatch. Required regression: D/I private configs with screening margins 0.7/0.5 must resolve via the actual train parser and loss resolver to training margins 0.7/0.7; an artifact config with 0.5 must fail.

2. **Check the stored cohort before launch.** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/twin_training.py:45` checks only dataset configuration, while `_selection` reports manifest IDs. The actual loader consumes Arrow row prefixes without checking those IDs. Concrete reproduction: `/tmp/a2-wrapper-review-stale-8hxss75s` retains the original private configuration and manifest but stores `stale-train-1`, `stale-validation-1`, and `stale-test-1`. `plan_run` accepts it and reports the original IDs. This ordinary stale-input case can spend on the wrong cohort; native dataset hashes written after launch do not prevent it. Minimum fix: inspect stored split row counts, full ID order and selected prefixes, and check prompt hashes/labels against materializer provenance before invoking training. Reject a changed ID, order, count, clean/reference prompt, or recipient label with a CPU regression. No tokenizer or behavioral scoring rerun is needed.

Available proof fields: private `token_proofs[split][instance_id]` includes `recipient_prompt_hash` and `reference_prompt_hash`, computed using the builder's canonical JSON SHA-256 helper, plus replacement/readout information. Stored rows include `source_recipient`, `source_reference`, `target`, `distractor`, `donor_identity`, `orientation`, `recipient_condition`, and `corruption_kind`. Source paths and content hashes are in manifest task `sources`. The build manifest currently has no produced-file hashes or authoritative per-output label map. Labels can be tied to the retained source rows, or compact output proofs can be added; merely trusting the current row's labels is insufficient.

Other reviewed behavior has no blocker: coarse gates are explicit; sparsity is 0.3; full epochs are 500; seeds are 42/1/123; counts use equal deterministic prefixes capped at 200/200/1000; low training count is flagged; provisional D permits timing only and rejects scientific production/I. Default CLI dry-run avoids model/hardware/submission/git calls. Real run requires Slurm plus one supported GPU. Allowlisted environment excludes credentials. The timer surrounds subprocess startup through artifact checks, so model load, cache, validation, training, final evaluation, and writes are included; pruning duration is separate. Failed child processes, absent artifacts, stale outputs, config mismatches, incomplete histories, bad native hashes, and out-of-bounds MLPs fail receipts. Actual parser and native artifact schemas are covered by direct tests.

## How verified

Both commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`:

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_wrapper.py -p no:cacheprovider -q > /tmp/a2-wrapper-review-base.log 2>&1
```

Observed: 36 passed; one existing pandas/bottleneck version warning. Exit code 0.

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_wrapper.py -p no:cacheprovider -q > /tmp/a2-wrapper-review-mgnp.log 2>&1
```

Observed: 36 passed. Exit code 0. No broader materializer suite was rerun.

Inspected actual `/tmp/a2-wrapper-finish-check/direct-dry-run.json` and `/tmp/a2-wrapper-finish-check/module-dry-run.json`; they differ only in the argv executable. Loaded the fixture Arrow data without a model: train, validation, and test each contain the expected single ID. Neither the planned receipt nor training output exists. The preserved dry-run builder hash predates a concurrent materializer edit; all other recorded source hashes match current source. Direct focused tests include the current materializer launch contract.

Stale-cohort reproduction used `datasets.load_from_disk` on the preserved fixture, constructed a temporary DatasetDict changing only row instance IDs, saved it under `/tmp/a2-wrapper-review-stale-8hxss75s`, copied the unchanged private config, and called `plan_run` with the unchanged manifest and timing epochs 20. Full output is `/tmp/a2-wrapper-review-stale-repro.log`; it reports `plan_accepted: True` and the planned/actual ID mismatch. This reproduces the second blocker without touching project inputs.

Read the implementation and direct tests rather than implementation-report narratives. Reviewed actual `train.py`, `run_io.py`, `run_manifest.py`, `pruning.py`, task loader/objective, builder, frozen JSON, START and A2 plan.

## Execution evidence

- Job id and cluster: no Slurm job; focused local CPU pytest commands above and local synthetic-data checks only.
- Exit code: both focused suites and fixture/reproduction checks exited 0.
- Counts: 36 passing wrapper tests against 36 collected in each interpreter. Original fixture contains 1 train, 1 validation, and 1 test row against expected 1/1/1. Stale fixture preserves counts but disagrees on all three IDs.
- Baseline reproduces: wrapper suite 36 passes against prior reported 36 passes. This is software-test agreement, not a scientific baseline result.
- Provenance file: no scientific `run_manifest.json` exists because no model/training run was performed. Fixture commit `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` is deliberately synthetic, not source revision evidence. No scientific result is claimed.
- Usage: live Codex weekly reading was 7 percent used, 93 percent remaining, below the 80 percent cap; reset reported 2026-11-06T16:07:41+00:00.

## What is NOT done

The two blockers are reported for the owning worker; review made no implementation changes. Task 3 projection is intentionally absent and is not a defect in this Task 2 review. No pilot, GPU model load, scientific seed, fleet reservation, or scientific gate assessment occurred. The tiny fixture cannot justify pilot or fleet cost estimates. Required project startup reconciliation remains orchestrator-owned; this reviewer did not run a synchronization mutation.

## Open questions

Default: withhold Task 2 approval until both blockers have focused CPU regression coverage and the worker supplies updated dry-run artifacts. No user decision is needed for the fixes: the lead has explicitly chosen training loss margin 0.7 independently of screening thresholds. The orchestrator should decide the smallest authoritative label-proof representation while preserving the materializer's existing source provenance.
