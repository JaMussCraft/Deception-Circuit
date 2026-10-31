# 05 — Train the v2 D and H circuits (fine and coarse heads-only nls0.3), then hand back

> **SCOPE RULING G12 (user, 2026-10-21): COARSE HEADS-ONLY ONLY.** Train the 6 coarse heads-only runs
> (far_v2, sdr_v2, ser_v2 x {deceptive, honest}). The 6 fine runs are DEFERRED: do not submit them. Wherever
> this ticket says "12 runs" read "6 coarse runs"; the launcher still has to be able to print the fine lines
> under `--dry` (for the later go) but `--test-only`/submission default to the coarse set only, and a fine
> submission requires an explicit `--include-fine` flag that is NOT to be used now. Report fine-unit counts
> only for the v1 reference run. Everything else (settings, hard stop, ledger) is unchanged.

**What to do:** train 12 circuits (3 v2 tasks x {D, H} x {fine, coarse heads-only}) at NLS 0.3 with the
settings of the existing SDR runs, post-process the coarse runs, tabulate sizes and the in-run node
evaluation, and hand back BEFORE any circuit evaluation.

**Status:** resolved (impl-05, 2026-10-22; coarse-only per G12; fine runs deferred)
**Type:** task
**Blocked by:** 04
**GPU allocation:** 20 reserved GPU-h (spec §11). Training on `gpuH200x8` (preferred) or `gpuA40x4`; never an
A100 partition (8B training OOMs at 40 GB).

## Facts to build on

- Reference configs to match: `outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414/config.json`
  (fine) and `outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742/config.coarse.json`
  (coarse heads-only; its `node_config` has prune_attention_neurons, prune_mlp_hidden, prune_mlp_output and
  prune_mlp_blocks all False; do NOT read that run's `config.json`, which mask expansion rewrote; spec
  §14.C2), both in the main checkout: seed 42, 500 node epochs, lr 0.03, batch 7,
  max_seq_length 120, 200/200/1000, no edge pruning, node lambda sparsity 0.3.
- Launcher precedent: `outputs/_launch_format_control/submit_train.sh` (`--dry`, `--test-only`, explicit
  settings, `--deception-margin-loss 0.7` ruling) and `outputs/_launch_format_control/postprocess_coarse.sh`
  (backup to `*.coarse.json` + `expand_coarse_masks.py`, no evaluation).
- Coarse flags: `--no-prune-attention-neurons --no-prune-mlp-hidden --no-prune-mlp-output --no-prune-mlp-blocks`.
- `scripts/train_deception.sbatch` passes everything after the task to `train.py`; its `#SBATCH` account,
  partition and time defaults are overridden on the command line.
- A fine run took about 32 min on an H200 (memory `slurm-job-policy`); about 2 h on an A40.
- Sizes: `evaluation/masks.count_masks`; in-run node evaluation in each run's `results.json`
  (`node_eval`, `node_granularity`).

## Acceptance criteria

- [x] `outputs/_launch_mechanism_v2/submit_train.sh` in the worktree, modelled on the format-control launcher:
      `--dry` prints the 12 `sbatch` lines, `--test-only` runs `sbatch --test-only` on each, `--only <run>`
      submits one; `--account`, `--partition`, `--time` options. Every line passes `--task <task>_v2`,
      `--deception-condition {deceptive|honest}`, `--node-lambda-sparsity 0.3 --no-edge-pruning --seed 42
      --node-epochs 500 --lr 0.03 --batch-size 7 --max-seq-length 120 --train-samples 200 --val-samples 200
      --test-samples 1000 --deception-margin-loss 0.7` (deliberate: both reference configs record
      `deception_margin_loss: null`; v2 pins 0.7 so D and H share one hinge, spec §14.C2); coarse lines add the four coarse flags and
      `--output-dir outputs/llama-8b-instruct_<task>_v2_coarse/nls0.3[_honest]_noedge_noan_nomh_nomo_nomb_<stamp>`;
      fine lines use the default slug under `outputs/llama-8b-instruct_<task>_v2/`. Every submission is
      appended to `outputs/_launch_mechanism_v2/train_jobs.txt`.
- [x] Before the first submission, on the login node without weights: `train.build_parser().parse_args(...)`
      accepts every flag of every launcher line, `resolve_args` succeeds, and
      `get_task("far_v2").dataset_dir(args)` resolves to `data/datasets/far_v2_honest` for the honest
      condition and the directory exists; the `--dry` output reviewed; `sbatch --test-only` accepted, ledger reservations entered. Waves sized so
      in-flight reservations never push the ledger past the 20 h allocation (with `--time 01:30:00` on H200,
      that is at most about 6 jobs in flight before reconciliation).
- [x] An A40 fallback (`--time 03:00:00`) is used only if the ledger still fits after reconciliation, and is
      recorded with its reason.
- [x] (6 coarse per G12; fine DEFERRED) All 12 runs finish with `results.json`. A crashed run is diagnosed before any resubmission; one
      resubmission per run at most, then hand back.
- [x] Each coarse run post-processed with
      `bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/_launch_format_control/postprocess_coarse.sh <run_dir>`.
- [x] `reports/05-training-summary.md` and `.json`: per run, path, job id, partition, elapsed, heads, fine
      units (fine runs) from `count_masks`, `node_eval` accuracy / exact match / KL, and whether the coarse SDR
      wave's in-run gate (acc >= 0.90, em >= 0.90, KL <= 0.20) holds, reported only, not acted on. Per task
      the D vs H head gap in percent. Side by side, for orientation, the v1 SDR reference sizes quoted in
      `Alignment/.scratch/format-control/spec.md` ("Pairing targets"): fine D 68 heads / 11,251 fine units
      (`outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414`), coarse D 69 heads
      (`outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742`); recompute
      them with `count_masks` rather than trusting the quote.
- [x] No `evaluate_circuit.py` call of any kind (not even `--dry-run`), no suite, knockout, composition or
      EVAL 5 launch, no `outputs/llama-8b-instruct_sdr_coarse/_launch/postprocess.sh`.
- [x] Ledger reconciled for all jobs; `totals` updated.
- [x] Review written to `reports/05-train-v2-circuits-and-hand-back-review.md` (launcher correctness against
      the reference configs, slugs, no evaluation calls).

## Hand-back (HARD STOP, spec §10 (ii))

Stop here. Report the 12 run directories, the size table, the in-run gate readings and the ledger total to
the orchestrator. Circuit evaluations of any kind need the user's explicit go-ahead.

## Comments

**impl-05, 2026-10-22: resolved under G12. The 6 coarse runs are trained and post-processed. No evaluation was run.**

- **Built.**
  - `outputs/_launch_mechanism_v2/submit_train.sh`. `--dry` prints 12 lines. `--plan`, `--test-only` and submit
    default to the 6 coarse runs. A fine run needs `--include-fine`, which was never used.
  - Partitions: gpuH200x8 (01:30:00), gpuA40x4 (03:00:00), and two lead-authorized options. One is
    gpuH200x8-interactive: 01:00:00, one `--only` run per submission. The other is the widened pair
    gpuH200x8,gpuA40x4: 03:00:00 minimum whenever A40 is in it. A100 is refused.
  - `outputs/_launch_mechanism_v2/write_training_summary.py`. It writes the sizes via `count_masks` on
    `active_nodes.coarse.json`, the node_eval, the gate reading, the D vs H gap, all submissions per cell, a
    config-vs-reference check, and the recomputed v1 references.
- **Login-node checks before the first submission.**
  - Every `--dry` line passes `build_parser().parse_args`, `resolve_args` and `dataset_dir`, and the
    directory exists.
  - `resolve_margin` returns 0.7 for D and H.
  - The resolved config equals the coarse reference's `config.coarse.json`, except task, condition, margin
    and output_dir. Fine lines match the fine reference the same way, apart from two inert joint keys.
  - Wrapper `--help` dry path: rc 0 for all 6 lines.
  - Data: 200/200/1000 rows per dataset; max prompt 106 tokens.
  - `sbatch --test-only` accepted.
- **Runs.** The table is in `reports/05-training-summary.md`. All 6 hold the in-run gate.
  - far_v2: D 58 heads, H 60 (+3.4%).
  - sdr_v2: D 60, H 58 (-3.3%).
  - ser_v2: D 55, H 69 (+25.5%).
  - The recomputed v1 references match the quote: fine D 68 heads and 11,251 fine units, coarse D 69 heads.
- **Slurm.**
  - Six beto/gpuH200x8 jobs were submitted (23105387-92). test-only projected starts weeks away.
  - The lead authorized serial gpuH200x8-interactive runs. The user moved the backups to bjhz, widened them to
    gpuH200x8,gpuA40x4 and set 03:00:00. The QOS was fixed by the agent for one job and by the user for four.
  - Winners:
    - far D: 23105421, H200 interactive, 29:41.
    - far H: 23105388, A40, 2:25:17.
    - sdr D: 23105389, A40, 2:26:18.
    - sdr H: 23105390, A40, 2:26:43.
    - ser D: 23109196, H200 interactive, 30:11.
    - ser H: 23105392, A40, 2:26:25.
  - ser D backup 23105391 FAILED after 2 min. Its second `from_pretrained` hit a transient cache read; the
    cache is intact, and three siblings passed the same point in the same minute. The one resubmission,
    23109191, was cancelled after the interactive run won. The failed dir `..._261021-140323` is kept, unused.
  - Cancelled while pending: 23105387, 23108699, 23108737 and 23109191.
- **Ledger.** Ticket 05 reconciled 11.5 GPU-h of the 20 allocated (10.78 actual) with no holdback draw. The
  feature total is 22.75 of 60, with nothing in flight.
- **Tests.** Both envs, re-run on 2026-10-22 on the final code:
  - base: 8 failed, 1665 passed, 58 skipped.
  - mgnp: 8 failed, 1818 passed, 19 skipped.
  - The failures are exactly the 8 baseline names; none is new.
- **Review.** Both axes, done by the implementer: `reports/05-train-v2-circuits-and-hand-back-review.md`. No
  unresolved findings. Two observations go to the researcher.
- **For the researcher.**
  1. The ser_v2 D vs H head gap is +25.5%. It is above the 25% tolerance that format-control used for its size
     rule, which this ticket only reports.
  2. ser_v2 D sits exactly at the accuracy gate (0.900), and ser_v2 H's KL is 0.197 against the 0.20 limit.
  3. Within a pair the hardware differs: far and ser D trained on H200, far and ser H on A40. sdr D and H both
     trained on A40. Memory records bf16 drift on A100 evaluations, so GPU type can move results slightly; this may matter for D vs H comparisons.
  4. The fine runs remain deferred under G12. The launcher prints them under `--dry` and needs `--include-fine`
     to submit them.
- **Files to commit.** These are the 58 absolute paths listed in `reports/05-handback.md`: 4 files under
  `outputs/_launch_mechanism_v2/`, including `check_launcher.py`, and the 6 used run directories.
