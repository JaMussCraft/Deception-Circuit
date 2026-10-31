# 03 — Train the three Format Circuits with the size check and retune rule

**What to build:** A launcher that submits the three Format Circuit training runs (fine FAR nls0.3, fine SDR nls0.3, coarse heads-only SDR nls0.3) with the paired mechanism run's settings, post-processes the coarse run, compares sizes to the paired circuits, and applies the retune rule at most once.

**Status:** resolved
**Type:** task
**Blocked by:** 01, 02

**Facts to build on**
- Paired runs and their sizes: FAR D 48 heads / 1 MLP block / 5,436 fine units; SDR D 68 heads / 3 MLP blocks / 11,251 fine units; coarse heads-only SDR D 69 heads (12 attention blocks). Handles in `agent-brief.md`.
- Paired training settings (from the D runs' `config.json`): seed 42, `node_epochs` 500, lr 0.03, batch size 7, `max_seq_length` 120, `--no-edge-pruning`, `--node-lambda-sparsity 0.3`, `train/val/test_samples` 200/200/1000 (the loader takes what exists if fewer survive; confirm and report).
- Coarse flags and slug: `--no-prune-attention-neurons --no-prune-mlp-hidden --no-prune-mlp-output --no-prune-mlp-blocks`, slug `nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_<stamp>` under `outputs/llama-8b-instruct_sdr_coarse/`; post-processing copies `active_nodes.json` / `config.json` to `*.coarse.json` then runs `expand_coarse_masks.py <run_dir>` (see `_launch/postprocess.sh` and memory `coarse-sdr-wave`). `config.json`'s `node_config` does not record the no-prune flags; the slug does.
- `scripts/train_deception.sbatch <task> [train.py args]`; `_launch/submit_train.sh` shows the sbatch invocation with `--account`, `--partition`, `--time` on the command line. A fine run took about 3 h on an A40 peaking near 40 GB.
- Size rule (spec): a gap above 25 percent in head count, or in fine-unit count for fine circuits, triggers one retrain at NLS 0.3 ± 0.1 toward the paired circuit's size; at most one retune; both sizes recorded regardless.

- [x] `outputs/_launch_format_control/submit_train.sh` (worktree) with `--dry` printing the exact `sbatch` lines; accounts and partitions chosen by queue length (`sbatch --test-only`, `squeue`), any of A40 / A100 / H200; job ids appended to `jobs.txt`.
- [x] `outputs/_launch_format_control/size_check.py`: pure function `retune_step(paired_counts, format_counts, nls, *, tol=0.25, step=0.1) -> Optional[float]` plus a CLI that reads two run directories (`active_nodes.coarse.json` when present, else `active_nodes.json`), prints both sizes per gate kind and the verdict, and writes `size_check.json` beside the format run. Tests at the boundary (24, 25, 26 percent), direction of the step, and "already retuned" refusal.
- [x] Three runs submitted, dry-run rehearsed; coarse run post-processed; in-run sufficiency numbers (accuracy, exact match, KL on the no-pressure test set) quoted in Comments, with the gate from the coarse wave (acc >= 0.90, EM >= 0.90, KL <= 0.20) applied and any miss flagged to the researcher rather than retuned for.
- [x] Size check run for all three; if a retune fires, the second run is submitted with the same launcher and both runs are kept and listed; the one to carry into ticket 04 is the retuned one.
- [x] Both suites in both envs (launcher and size-check tests only; no model code changes expected).
- [x] Independent review; report in `reports/03-train-format-circuits-and-size-check-review.md` (orchestrator-dispatched; approved with addendum).

## Comments

- 2026-10-13 20:34 CDT (impl-03): submitted the three Format Circuit training jobs with `outputs/_launch_format_control/submit_train.sh --account beto-delta-gpu` from the worktree root, after a `--dry` rehearsal and a parse check of each printed line through `train.py`'s own parser and slug composer (all three slugs equal the auto slug; every setting resolves to the paired value). Account beto-delta-gpu (fairshare 0.132, best of the three; `sbatch --test-only` put beto earliest, bgrb three days later); partitions `gpuA40x4,gpuA100x4,gpuA100x8,gpuH200x8`; `--time 05:00:00`.
  - FAR F fine: job **22879579**, `outputs/llama-8b-instruct_far/nls0.3_nopressure_noedge_261013-203424`
  - SDR F fine: job **22879581**, `outputs/llama-8b-instruct_sdr/nls0.3_nopressure_noedge_261013-203424`
  - SDR F coarse heads-only: job **22879582**, `outputs/llama-8b-instruct_sdr_coarse/nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-203424`
- `--deception-margin-loss 0.7` is passed explicitly on all three runs (orchestrator ruling 2026-10-13): the paired D runs had `deception_margin_loss: null`, so their hinge margin was their dataset's `margin_thresh` 0.7, while the `<task>_nopressure` datasets were built at 0.3. The launcher carries the reason as a comment.
- Job ids go to `outputs/_launch_format_control/train_jobs.txt` (orchestrator's name; the ticket's `jobs.txt` would sit beside ticket 04's `suite_jobs.txt`).
- 2026-10-13 20:48 CDT: SDR F fine **22879581** and SDR F coarse **22879582** FAILED after 2 min 17 s on gpuA100x8 (gpuc02) with `torch.OutOfMemoryError` (39.49 GiB cards; 38.3 GiB allocated by PyTorch at the failure). FAR F 22879579 landed on an A40 (48 GB) and runs normally. Resubmitted with the same arguments and fresh stamps, restricted to `--partition=gpuA40x4,gpuH200x8` and with `--export=ALL,PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (orchestrator instruction):
  - SDR F fine: job **22879743**, `outputs/llama-8b-instruct_sdr/nls0.3_nopressure_noedge_261013-204850`
  - SDR F coarse heads-only: job **22879744**, `outputs/llama-8b-instruct_sdr_coarse/nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-204850`
  - The failed `..._261013-203424` SDR directories stay on disk and are not committed. `submit_train.sh` now defaults to the A40/H200 list, refuses any `gpuA100*` partition, and passes the allocator setting; a launcher test covers it.

- 2026-10-13 orchestrator: session stopped at its usage limit with this ticket in progress; see reports/00-orchestration-ledger.md for the exact remaining steps.

### Outcomes (2026-10-13, impl-03, after the orchestrator's no-go)

**Jobs.** All ran on beto-delta-gpu.

| circuit | job | state | wall | partition / node |
| --- | --- | --- | --- | --- |
| FAR F fine | 22879579 | COMPLETED | 02:02:24 | gpuA40x4 / gpub097 |
| SDR F fine (1st) | 22879581 | FAILED, CUDA OOM | 00:02:17 | gpuA100x8 / gpuc02 |
| SDR F coarse (1st) | 22879582 | FAILED, CUDA OOM | 00:02:17 | gpuA100x8 / gpuc02 |
| SDR F fine | 22879743 | COMPLETED | 02:02:06 | gpuA40x4 / gpub009 |
| SDR F coarse | 22879744 | COMPLETED | 01:50:36 | gpuA40x4 / gpub068 |

**Loader counts (train logs).** Every run printed `Task margin: 0.7 (from --deception-margin-loss override)`. Loaded train / validation / test: FAR 150 / 150 / 500; SDR fine 150 / 150 / 520; SDR coarse 150 / 150 / 520. FAR F's data is 791 of 800 honest-split fallback records (ticket 01), so FAR F is trained almost entirely on instances disjoint from FAR D's.

**Sizes and size check.** Fine units are attention neurons plus MLP hidden plus MLP output. The rule compares heads, plus fine units for fine pairings; heads set the direction if both fire. Coarse sizes come from `active_nodes.coarse.json` (heads only).

| circuit (NLS 0.3) | heads D / F | fine units D / F | attn, MLP blocks D / F | verdict |
| --- | --- | --- | --- | --- |
| FAR fine | 48 / 82 (+70.8%) | 5,436 / 12,986 (+138.9%) | 10, 1 / 14, 3 | **retune to NLS 0.4** |
| SDR fine | 68 / 73 (+7.4%) | 11,251 / 11,882 (+5.6%) | 13, 3 / 14, 3 | within tolerance |
| SDR coarse heads-only | 69 / 68 (-1.4%) | n/a | 12 / 12 | within tolerance |

`size_check.json` is written beside FAR F and SDR coarse F. It is **not** written for SDR fine F, which finished after the orchestrator's stop. The SDR fine numbers above were read directly from its `active_nodes.json` and `results.json`. To write the file, run this from the worktree root:
`python outputs/_launch_format_control/size_check.py /projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414 outputs/llama-8b-instruct_sdr/nls0.3_nopressure_noedge_261013-204850`

**In-run sufficiency.** Each run was scored on its own no-pressure test set against the coarse-wave gate (acc >= 0.90, EM >= 0.90, KL <= 0.20). All three pass, so no miss needs flagging.

| circuit | accuracy | exact match | KL | gate |
| --- | --- | --- | --- | --- |
| FAR F | 0.956 | 0.960 | 0.133 | pass |
| SDR F fine | 0.962 | 0.962 | 0.127 | pass |
| SDR F coarse | 0.965 | 0.967 | 0.102 | pass |

**Pending retune: FAR F at NLS 0.4, NOT submitted.** The rule fired mechanically. The orchestrator ruled no-go for this session because it hit its usage limit. To submit, run from the worktree root:
`bash outputs/_launch_format_control/submit_train.sh --only far --nls 0.4 --account beto-delta-gpu`
FAR D's own size barely moves between NLS 0.3 and 0.5: 48 heads at both, and 5,436 vs 5,629 fine units. So one step may not close an 82-to-48 gap. The rule allows only one step, and `size_check.py` gives a retuned run that still misses the verdict `refused`. Until the retune runs, the FAR F that ticket 04 can use is the NLS 0.3 run below, and ticket 05 should caveat its size.

**Run directories for ticket 04.** All are under the worktree's `outputs/`, committed by the orchestrator as ecfbc7d.
- FAR F: `outputs/llama-8b-instruct_far/nls0.3_nopressure_noedge_261013-203424`. (carried; the NLS 0.4 retune is recorded, not carried: superseded by the orchestrator ruling below)
- SDR F fine: `outputs/llama-8b-instruct_sdr/nls0.3_nopressure_noedge_261013-204850`
- SDR F coarse: `outputs/llama-8b-instruct_sdr_coarse/nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-204850` (post-processed: `*.coarse.json` kept, masks expanded). Rehearsed on a copy of coarse D, the expansion was byte-identical to the researcher's own.

**Tests.** The full suites ran after c73bb21, with ticket 04/05 files present.
- Login base: 8 failed, 695 passed, 20 skipped.
- mgnp: 8 failed, 696 passed, 19 skipped.
- The 8 failing names match `reports/00-baseline-failures.md` in both envs.
- After the OOM fix, `tests/test_format_control_size_check.py` passes 24 of 24 in base.
- The full suites were not re-run after f1d77f5.

**Commits.** The orchestrator made these on impl-03's instruction:
- c73bb21: launcher, size check, coarse post-processing, tests.
- f1d77f5: the A100 out-of-memory fix.
- ecfbc7d: the three run directories, with `size_check.json` where written.

**Checkboxes.** Left unticked on the orchestrator's instruction to only append Comments. Verified: boxes 1 to 3, with the job log named `train_jobs.txt` and A100 excluded after the OOM. Open:
- Box 4: the FAR retune is not submitted and the SDR fine `size_check.json` is not written.
- Box 5: the suites have not been re-run after f1d77f5.
- Box 6: the orchestrator dispatches the review, and it has not run.

**Status stays `claimed`.**

### Session resumed (2026-10-14, impl-03)

- 08:13 CDT: on the orchestrator's GO, submitted the FAR retune after a `--dry` rehearsal: job **22895850**, NLS 0.4, `outputs/llama-8b-instruct_far/nls0.4_nopressure_noedge_261014-081312`. Settings are otherwise identical to the NLS 0.3 run (margin 0.7), on beto-delta-gpu, `gpuA40x4,gpuH200x8`, 5 h. The launcher appended it to `train_jobs.txt`. ~~Once it finishes it is the FAR F that ticket 04 carries, whatever its size.~~ (superseded: the 0.4 run failed the in-run gate and is not carried; see the ruling below) Both FAR runs stay listed.
- `size_check.json` is now written for SDR fine F: 68 / 73 heads, 11,251 / 11,882 fine units, within tolerance, in-run gate pass.
- Boxes 1 to 3 ticked. Box 1 holds with two deviations: the job log is named `train_jobs.txt`, and A100 partitions are excluded after the OOM.
- The full suites re-ran after f1d77f5 and commit C: login base 8 failed / 818 passed / 20 skipped, mgnp 8 failed / 819 passed / 19 skipped. The 8 names match the baseline in both envs, so box 5 is ticked. Report: `reports/03-implementer-report.md`.
- Fix round 1 from the review (committed as 72bbdec): `--partition` is now an allowlist (`gpuA40x4`, `gpuH200x8`), with tests for A100, unknown and empty partitions. `--only` is validated before any line prints. `tests/test_format_control_size_check.py` passes 35 of 35 in both envs.
- **FAR retune result.** Job **22895850** COMPLETED in 00:32:44 on gpuH200x8 (gpue07). It loaded 150 / 150 / 500 with margin 0.7.

  | FAR | heads | fine units | acc | EM | KL |
  | --- | --- | --- | --- | --- | --- |
  | D, NLS 0.3 | 48 | 5,436 | | | |
  | F, NLS 0.3 (`..._261013-203424`) | 82 (+70.8%) | 12,986 (+138.9%) | 0.956 | 0.960 | 0.133 |
  | F, NLS 0.4 retune (`..._261014-081312`) | 72 (+50.0%) | 10,729 (+97.4%) | 0.922 | 0.924 | **0.214** |

  - Its `size_check.json` records `retuned: true`, verdict `refused` and `next_nls: null`. No further retune is allowed.
  - **Finding for the researcher (size):** FAR F stays well above FAR D's size after its one retune.
  - **Finding for the researcher (gate):** the NLS 0.4 run misses the in-run KL bar (0.214 against 0.20). Accuracy and exact match pass. Flagged, not retuned for.
- ~~FAR F carried into ticket 04: the NLS 0.4 run.~~ Superseded by the orchestrator's ruling below.
- **Ruling (orchestrator, 2026-10-14): the FAR Format Circuit carried into ticket 04 is the NLS 0.3 run.**
  - Carried: `outputs/llama-8b-instruct_far/nls0.3_nopressure_noedge_261013-203424`.
  - Recorded, not carried: `outputs/llama-8b-instruct_far/nls0.4_nopressure_noedge_261014-081312`. Ticket 04 gives it one side evaluation (orchestrator). Its tracked files are committed in commit E.
  - **Why:** the NLS 0.4 run fails the in-run sufficiency gate (KL 0.214 against 0.20). The researcher's coarse-wave `postprocess.sh` refuses to evaluate any run that fails that gate. The retune also did not close the size gap.
  - **Where it is recorded:** `size_check.py record-retune` (new, tested) wrote the retune outcome into the NLS 0.3 run's `size_check.json`. That covers the 0.4 run's path and NLS, both sizes, gaps, verdict `refused` and the gate MISS on `kl_div`. It also wrote `carried: "nls0.3"` into both runs' `size_check.json`. Ticket 05's writer reads that file beside F.
  - SDR fine and SDR coarse F are unchanged from above.
- **Finding for the researcher: no NLS in {0.3, 0.4} yields a size-matched, sufficient FAR Format Circuit.**
  - At NLS 0.3, F passes the gate but has 82 heads and 12,986 fine units against D's 48 and 5,436.
  - At NLS 0.4, F still has 72 heads and 10,729 fine units, and it fails the gate.
  - FAR D, at 48 heads, is the smallest of the three FAR circuits: H has 65 heads and F has 82.
  - Size therefore remains a confound for FAR. The size-matched random nulls in ticket 04's knockouts control it only partly.
  - FAR F's data is also 791 of 800 honest-split fallback records (ticket 01), so the FAR F-data column is unpaired.
- Box 4 ticked. Every box except the independent review (box 6, owned by the orchestrator) is ticked, so Status is set to `resolved` per the orchestrator's instruction.
