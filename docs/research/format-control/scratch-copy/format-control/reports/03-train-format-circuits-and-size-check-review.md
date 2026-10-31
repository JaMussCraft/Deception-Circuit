# Review: ticket 03, train the three Format Circuits with the size check

Reviewer: review-03. Date 2026-10-14. Scope: c73bb21, f1d77f5, ecfbc7d, and 71e4c7e. The last one landed during the review and holds the SDR fine `size_check.json` and the retune job line. Branch `format-control`, worktree `Deception-Circuit/.claude/worktrees/format-control`. The FAR NLS 0.4 retune (job 22895850) and its size check are out of scope and get an addendum.

Paths below are relative to the worktree root unless absolute. The launcher, size check, and post-processing script live in `outputs/_launch_format_control/`. The tests are in `tests/test_format_control_size_check.py`.

## Method

I checked every item against the files on disk, not the report.

- **Configs.** I flattened each F run's `config.json`, and `config.coarse.json` for the coarse run, and diffed them key by key against the paired D runs in the main checkout.
- **Margin.** I read the `Task margin` line of all six `train.log` files. I also read the D datasets' `dataset_config.json`.
- **Loader counts.** I read the `Successfully loaded ... split` lines of the D and F logs.
- **Sizes.** I loaded `size_check.py` and ran `circuit_counts` on all six runs. I then reran `check()` on the three pairs and compared it field by field with the committed `size_check.json`.
- **Coarse expansion.** In my job tmp dir, I made fresh copies of the trained coarse masks and config for both coarse D and coarse F. I ran `expand_coarse_masks.py` on each copy with the mgnp interpreter and compared the output with `cmp`.
- **Launcher.** I ran `submit_train.sh --dry` with `--partition gpuA100x4`, `gpuA40x4,gpuA100x8`, `"gpuA40x4, gpuA100x4"` and `gpuMI100x8`.
- **Tests.** I ran the focused size-check file in the login base env: 24 passed. I did not re-run the full suites.

## Spec Compliance

| requirement | verdict | evidence |
| --- | --- | --- |
| Launcher with `--dry` printing the exact `sbatch` lines | ✅ | `submit_train.sh:83-86`. Tested at `tests/test_format_control_size_check.py:248-270`. |
| Training settings identical to the paired runs | ✅ | Flags at `submit_train.sh:67-70`. On disk, F and D configs differ only in `deception_condition` (deceptive vs nopressure) and `deception_margin_loss` (null vs 0.7). The fine D configs also predate two later train.py fields, `joint_tasks: null` and `joint_scale_epochs: true`. Joint training is off, so those two fields change nothing. Seed 42, node_epochs 500, lr 0.03, batch 7, max_seq_length 120, NLS 0.3, edge_pruning false and samples 200/200/1000 are equal in all three pairs. |
| `--deception-margin-loss 0.7` (ruling) applied and justified | ✅ | `submit_train.sh:22-26, 69`. All three D logs say `Task margin: 0.7 (from dataset_config.json margin_thresh)`. All three F logs say `Task margin: 0.7 (from --deception-margin-loss override)`. The effective hinge margin is equal. |
| Coarse flags, recorded in the run | ✅ | `submit_train.sh:70, 79`. F's `config.coarse.json` `node_config` has `prune_attention_neurons`, `prune_mlp_hidden`, `prune_mlp_output` and `prune_mlp_blocks` all false. It differs from coarse D's `config.coarse.json` only in the condition and margin keys. The ticket said `node_config` does not record these flags, but it does. |
| Slugs `nls0.3_nopressure_noedge_<stamp>` and `..._noan_nomh_nomo_nomb_<stamp>` | ✅ | `submit_train.sh:77-82`. Tested at `tests/test_format_control_size_check.py:262-267`. The run directories on disk match. |
| Default `gpuA40x4,gpuH200x8`, refuse gpuA100, with a test | ⚠️ | The default is at `submit_train.sh:45` and the refusal at `:60-62`. Both work: `gpuA100x4` and `gpuA40x4,gpuA100x8` exit 2. The refusal branch itself has no test, because `tests/test_format_control_size_check.py:273-279` checks only the default line. The check is a denylist, so other partitions pass. See Important 1. |
| Allocator export | ✅ | `submit_train.sh:65, 83`. Tested at `:279`. |
| Job ids in `train_jobs.txt` | ✅ | `submit_train.sh:72, 89-90`. All seven submissions and the OOM note are listed. The `train_jobs.txt` name is a recorded deviation from the ticket's `jobs.txt`. |
| Pure `retune_step(paired, format, nls, *, tol=0.25, step=0.1)` | ✅ | `size_check.py:42-63`. It adds a keyword-only `retuned=False`, which the report records. |
| Boundary tests at 24/25/26 percent | ✅ | `tests/test_format_control_size_check.py:39-52` covers heads in both directions. `:58-69` covers fine units at the real FAR D size (6,795 vs 6,796; 4,077 vs 4,076). The rule is strictly above 25 percent (`size_check.py:35`), which matches the spec's "above 25 percent". |
| Direction: a bigger F steps NLS up | ✅ | `size_check.py:61-63`. Tested at `:42-45, 60, 62, 74, 79`. On-disk D runs confirm that higher NLS gives a smaller circuit: FAR D has 48 heads at NLS 0.3 and at 0.5. The report also gives 83/69/54 heads for coarse SDR D at NLS 0.1/0.3/0.5. |
| "Already retuned" refusal | ✅ | `size_check.py:56-60, 136`. Tested at `:91-97` (pure) and `:180-191` (CLI, derived from config NLS). |
| CLI reads `active_nodes.coarse.json` when present | ✅ | `size_check.py:71-78`. Tested at `:164-177`. On disk, both coarse pairs report `active_nodes.coarse.json` as their source. |
| Prints both sizes per gate kind and writes `size_check.json` | ✅ | `size_check.py:174-193`. Tested at `:141-156`. |
| Fine units = attention_neurons + mlp_hidden + mlp_output, reproducing the spec's D numbers | ✅ | `size_check.py:68, 100-103`. Recomputed: FAR D = 3,289 + 1,319 + 828 = **5,436** with 48 heads. SDR D = 4,527 + 4,498 + 2,226 = **11,251** with 68 heads. Coarse SDR D has **69** heads in 12 attention blocks. |
| Coarse post-processing: `*.coarse.json` then `expand_coarse_masks.py` | ✅ | `postprocess_coarse.sh:19-26`. My rehearsal reproduced both coarse D's and coarse F's on-disk `active_nodes.json` and `config.json` **byte-identically**. The implementer's claim holds, and the committed coarse F expansion is exactly what the script produces. |
| Results on record | ✅ | Every figure the brief lists appears in the ticket Comments and the report. The figures are the five job ids with wall times and the OOM pair, the in-run gate figures for all three runs, the sizes and verdicts, and the loader counts. I checked the sizes, verdicts, gates and loader counts against the files. All three committed `size_check.json` files equal a fresh `check()` field for field. |
| Gate applied, misses flagged, not retuned for | ✅ | `size_check.py:107-121`. Tested at `:196-219`. All three runs pass. |
| Both suites in both envs, names vs baseline | ⚠️ (report only; suites not re-run per instructions) | The report records 8 failures in both envs after f1d77f5, matching the baseline by name. The focused file passes 24 of 24 in base. |
| Retune fired, submitted with the same launcher, both runs listed | ✅ (result pending) | Line 7 of `train_jobs.txt` (committed in 71e4c7e) holds job 22895850 at NLS 0.4 on A40/H200. The rehearsed dry line in the report matches the 0.3 run except for NLS, stamp and the partition/export change. |

## Strengths

- The launcher passes every paired setting explicitly instead of relying on train.py defaults. That makes each F `config.json` a self-contained record, and the key-by-key diff against D is clean.
- The margin ruling has a provenance trail. The D and F logs show the effective margin is 0.7 on both sides, by different routes.
- `size_check.py` derives "already retuned" from the two runs' config NLS rather than from a flag someone must remember. The verdict therefore cannot be misreported by hand.
- The coarse-mask choice is right and tested. Reading `active_nodes.coarse.json` avoids the known gotcha where expanded masks put every MLP unit in the circuit.
- The in-run gate is recorded beside the size verdict and never changes it, as the ticket requires.
- The OOM incident is handled well. The diagnosis is concrete, the default is changed, the job log is annotated, and the failed directories stay on disk untracked.
- Tests check the seams a caller sees: the printed sbatch lines, the written `size_check.json`, and the pure function at the real paired sizes.

## Issues

### Critical

None.

### Important

1. **The partition guard is an untested denylist, so the A40/H200-only invariant is not enforced.** This is at `submit_train.sh:60-62`, with the test gap at `tests/test_format_control_size_check.py:273-279`.
   - *What:* the refusal branch the ruling asked for has no test, because the only launcher partition test checks the default line. The guard works for A100 names, but it rejects only names matching `*,gpuA100*`. In dry mode, `--partition gpuMI100x8` passes and prints an sbatch line. That is an AMD partition where CUDA training cannot run. `--partition "gpuA40x4, gpuA100x4"` also slips past the pattern, though sbatch would likely reject that string itself.
   - *Why:* the binding constraint is to "refuse gpuA100 partitions, with a test". The orchestrator's stated invariant is that nothing in the launcher can submit outside gpuA40x4/gpuH200x8. The second wave of jobs used the default, so no run is affected. A re-submission with a hand-typed `--partition` could still land on an unusable or out-of-memory partition.
   - *Fix:* split `PARTITION` on commas, trim each item, and allow only `gpuA40x4` and `gpuH200x8`; exit 2 otherwise. Add a parametrized test that `--dry --partition gpuA100x4`, `gpuA40x4,gpuA100x8` and `gpuMI100x8` exit 2 and print no `sbatch` line, and that `gpuH200x8` passes.

### Minor

1. **`size_check.json` stores absolute paths that include the worktree.** This is at `size_check.py:145-146`.
   - *What:* `format_run` is `/projects/.../.claude/worktrees/format-control/outputs/...`.
   - *Why:* that path goes stale once the branch merges and the worktree is removed.
   - *Fix:* record repo-relative paths, or record both forms.
2. **`--nls` goes into the slug as typed.** This is at `submit_train.sh:52, 82`.
   - *What:* `--nls 0.40` or `--nls .4` produces a directory name that differs from train.py's own slug for the same value.
   - *Why:* the parser and slug check covered only 0.3 and 0.4 as typed.
   - *Fix:* validate the value against a pattern such as `^0\.[0-9]$`.
3. **An unknown `--only` circuit is caught inside the submit loop.** This is at `submit_train.sh:75-81`.
   - *What:* `--only "far bogus"` submits `far` and then exits.
   - *Fix:* validate the whole list before the loop.
4. **`postprocess_coarse.sh` has no automated test.** This is at `postprocess_coarse.sh:19-26`.
   - *What:* only rehearsals cover it, both the implementer's and mine, and both were byte-identical.
   - *Why:* on a run already expanded without `*.coarse.json`, the script would copy the expanded masks as the "coarse" ones, and `size_check.py` would then record every opened fine unit in the format counts. The verdict stays heads-only because the paired coarse circuit carries no fine units, but the recorded size would mislead a reader.
   - *Fix:* refuse when `active_nodes.json` already holds `attention_neurons` but no `active_nodes.coarse.json` exists. Add a small test on the 2-layer fixture.

### Observations for the researcher (no fix asked)

- **Fewer optimizer steps.** Every F run trained on 150 records against D's 200. That is about 22 steps per epoch against 29, or about 24 percent fewer steps over 500 epochs. Test sets are 500 or 520 against 1,000. This is a disclosed asymmetry beside the FAR size gap. SDR F matched D's size under the same asymmetry, so it is unlikely to be the main cause.
- **Allocator setting.** FAR F at NLS 0.3 ran without `expandable_segments`, while every later run has it. The setting affects memory layout, not numerics.
- **The retune may be refused.** FAR D's own size is flat from NLS 0.3 to 0.5. One step may therefore leave FAR F out of tolerance, and `size_check.py` would then record `refused` as the rule intends.

## Assessment

**Spec: compliant, except the untested refusal (⚠️, Important 1).** The training settings, margin, coarse flags, slugs, size-rule boundary and direction, fine-unit convention, coarse post-processing, and recorded results all check out against the files on disk.

**Quality: Needs fixes.** One Important finding: replace the A100 denylist with an A40/H200 allowlist and test the refusal. The four Minor findings can be deferred. No run, size verdict, or result is affected.

## Re-review of fix round 1 (71e4c7e..72bbdec)

### Finding Verdict
ADDRESSED. `outputs/_launch_format_control/submit_train.sh:26,46-52` now holds an allowlist (`gpuA40x4 gpuH200x8`) and refuses any other token, plus an explicit empty check at line 45. Tests at `tests/test_format_control_size_check.py:84-93` parametrize A100x4, A100x8, mixed A40+A100, MI100x8, a bogus third token, "" and ","; each asserts return code 2, "refusing --partition" in stderr and no "sbatch " in stdout. Lines 96-100 assert single values and both orders are accepted and emit 3 lines. Probed by hand: gpuA40x4, gpuH200x8 and both orders exit 0 with 3 sbatch lines; gpuA100x4, gpuA100x8, gpuMI100x8, "", "," and "*" exit 2 with 0 sbatch lines. Refusal happens before the loop, so no sbatch line prints.
The `--only` validation was moved before the loop (lines 53-58); `--only "far bogus"` exits 2 with 0 sbatch lines, asserted at test lines 103-107. The old in-loop `*)` arm remains as a harmless duplicate. Focused run: 35 passed.

### New Breakage
- Minor: `submit_train.sh:46` splits on commas and drops empty tokens, so `--partition "gpuA40x4,"` and `"gpuA40x4,,gpuH200x8"` pass and emit `--partition=gpuA40x4,` to sbatch. Only the allowed partitions can be reached, so the memory-safety goal holds; Slurm will probably reject or ignore the stray comma. No test covers it.

### Out-of-Scope Observations
- None.

### Verdict
Round passes: finding addressed, no Critical or Important issues, one Minor.

## Addendum: FAR retune (0c0f53d, e2a1b2b)

### Verified
- **Config parity.** `diff` of the two FAR `config.json` files shows one differing line, `node_lambda_sparsity` 0.3 vs 0.4 (line 24). The stamp lives only in the directory name. Margin 0.7, seed, epochs, sample counts and node_config are identical.
- **Numbers match results.json.** The 0.4 run's `node_eval` (accuracy 0.922, exact match 0.924, KL 0.2144364) equals `size_check.json` `in_run_gate`. The 0.3 run's (0.956, 0.96, 0.1333) equals its own. Counts in the retune block (72 heads, 10,729 fine units, D 48 and 5,436) equal the 0.4 run's own file. Gaps 0.5 and 0.9737 recompute correctly.
- **Gate miss and carried label recorded in both files.** The 0.3 file has a `retune` block (path, NLS 0.4, both sizes, gaps, verdict `refused`, gate passes false with misses `kl_div`) and `carried: "nls0.3"`. The 0.4 file has `carried: "nls0.3"`, `retuned: true`, verdict `refused`, gate MISS. The 0.3 run keeps its own gate PASS and verdict `retune`.
- **Second step refused.** The 0.4 run's verdict is `refused` with the "at most one retune" note. `tests/test_format_control_size_check.py:91-93` covers `RetuneRefused`.
- **record-retune.** `size_check.py:84-105` refuses a label naming neither run before any write (`SystemExit`). `tests/test_format_control_size_check.py:253-257` covers it and asserts nothing was written. `:234-250` covers the happy path, including both files agreeing.
- **Ticket Comments** (lines 117-128) state the ruling, the carried 0.3 run, the 0.4 run recorded but not carried, and the finding that no NLS in {0.3, 0.4} gives a size-matched, sufficient FAR F.
- **Focused run.** 37 passed.

### Issues
- **Critical:** none.
- **Important:** none.
- **Minor 1.** Ticket line 76 ("Replace it with the NLS 0.4 retune once that runs") and line 101 ("it is the FAR F that ticket 04 carries, whatever its size") are now stale. Only line 117 is struck through. A reader skimming the Comments can still take 0.4 as the carried run. Strike or annotate both, pointing at the ruling.
- **Minor 2.** `record-retune` does not check that the two runs are a first run and its retune (the retune's `retuned` flag, or the same paired run). A swapped or unrelated pair would be recorded. Low risk with one caller.
- **Minor 3.** The 0.3 file's top-level `verdict` stays `retune` beside `carried: nls0.3`. This is intended, as the test says, but a reader of that file alone must look at the `retune` block to see the retune was refused.

### Verdict
Approved.
