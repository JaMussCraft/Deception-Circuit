# Hand-back 176: A2 full-score interface inventory

Agent: inventory worker. Status: handed-back. This is source inspection, not scientific acceptance or launch authority.

## What changed

This handback is the only file written. The accepted source root S is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime`; W is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`. Relevant paths below are virtual paths in the existing container mapping.

**Reuse.** The original CLI `component_analysis/a2_pipeline.py:817-842` does not require the same GPU UUID or node: `score()` requires exact model dtype, device *type* (the part before `:`), and exact `torch.cuda.get_device_name()` equality against bank execution provenance. It also requires the complete bank, original frozen context and `bank_contract`, including exact numeric software/backend environment (`numeric_environment`, lines 524-542 and contract lines 663-686). Thus another H100 UUID/node can satisfy the original CLI only if its exact GPU name and all other checks match; H100 label alone is insufficient. Separately, the existing timing controller's `controller.py:51-56` asserts identical UUID, name, device, visibility, memory and compute capability between its bank and prefix phases within the *same timing attempt*. That controller is a bank-plus-prefix-only packet, not authorization or an existing reusable full-score launcher. A future different-allocation score requires separately reviewed operational admission and bindings; source inspection alone does not establish them.

**CLI and paths.** The existing timing packet's template supplies the prefix command below. Run from S with the reviewed cluster/container environment; it is shown for interface comparison only, not a launch command authorization:

```bash
bash "$S/scripts/jobs/specificity_a2.sh" --design "$W/outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json" --selected "$W/outputs/_analyses/specificity-ladder/ladder-5f450dc/selected.json" --commit 50e947bb852613e3a270082651f2bd1b7bb0c525 --batch-size 8 --registry "$W/docs/research/held_out.json" --stage score --work-dir "$W/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1-timing-limit4" --limit 4
```

The prefix controller copies authentic G3 `groups.json` into that separate pilot root, links its `bank` to the main root's complete bank, and publishes prefix results under pilot `score/`; it requires the main `score/` absent. Full G3 scoring uses the same arguments, changes `--work-dir` to `$W/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1`, and omits `--limit` (default zero means all). The main root must have `groups.json` plus complete `bank/banks.json` and `bank/run_manifest.json`, with `score/` absent: `main()` lines 1338-1340, 1385-1390 and 1470-1482. A future launcher must review actual paths, output absence, remote identity and fresh support; existing prefix controller explicitly disallows full scoring. Timing config declares prefix 2484 rows and 144 controls, full 59652 expected rows, but these are planned counts, not a claim that a current run completed.

`a2_pipeline.py:302-334` `expected_keys()` constructs the complete crossed row domain across all nine task/seed groups, assessment IDs, conditions, streams, operations and optional donor seeds, plus IOI/MMLU utility operations; slicing with `limit or None` distinguishes prefix from full. `score()` lines 988-1005 validates row scope and reports observed/expected counts. `ladder_pipeline.py:220-235` `positive_keys()` constructs expected controls once per mechanism task, assessment condition/stream and utility row; `validate_positive_controls()` checks exact unique key set and valid controls. Score calls `calibrate()` for assessment and each utility in `a2_pipeline.py:875-988`.

**Before model entry.** `main()` calls `_load_context()` (lines 1087-1103): A1 prepared scope, pinned model/revision/commit, source/selection/code hashes, frozen design and donor rebuild, live registries, frozen grader source and selection artifact/completion sidecar checks (`ladder_pipeline.py:306-318, 449+`). `_validate_live()` (A2 lines 1224-1244) revalidates the receipt, execution commit/runtime code, referenced source files, all-18 comparison reconstruction, protected task and utility registries and complete grader-catalogue binding; `validate_receipt()` lines 220-299 checks receipt hash, comparison, nine seed groups, operations, aliases, bank-key union, frozen geometry and selection ancestry. `_validate_grader_catalogue()` lines 1145-1221 preserves the owned entry, foreign declarations and global fields under bound canonical digests. `read_stage()` lines 1278-1292 requires the bank completion manifest to match the reconstructed expected manifest and payload. `validate_banks()` lines 739-779 checks all tasks, exact contract/source/tokenizer/model/geometry/environment, sorted unique union keys, finite numeric vectors with exact typed dimensions, source IDs/splits/token counts and provenance. `model_geometry_receipt()` lines 545-599 checks pinned local config and valid Llama dimensions; `bank_contract()` lines 623-688 checks original H train/validation IDs, no assessment overlap, source/token identity and count, pooling, numeric environment and required shapes. Then tokenizer load and saved token/layout comparison precede another `_validate_live()` and `timed_model_stage()` model loader. Loaded model geometry, same dtype/device type and GPU name are checked inside `score()` **after model load**, not before. Independent release/cache/ledger/placement/protection gates are external to this source and still apply.

## How verified

Read the frozen A2 and A1 source, original job wrapper, and `h100-timing-launch-r5` config and controller. No model execution, effects, tests, scheduler/remote calls or source admission were performed.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No claim that the in-flight bank, prefix score, final receipt or scientific result has been accepted. The exact full control count was not calculated from the inputs. No new operational packet, resources, launch or source changes.

## Open questions

Root should obtain final bank/timing receipts and independent review, then review any future full-score packet, cross-node compatibility and separate budget/lease/protection gates. Default: do not launch full scoring until those gates pass.
