# Review: ticket 05 (train the v2 circuits, coarse heads-only per G12)

Reviewer: impl-05, on both axes (Standards, Spec). The review skill's sub-agents need git for the diff, and git is
off limits to implementers. Files reviewed:

- `outputs/_launch_mechanism_v2/submit_train.sh` (new)
- `outputs/_launch_mechanism_v2/write_training_summary.py` (new)
- `outputs/_launch_mechanism_v2/train_jobs.txt` (written by the launcher)
- `outputs/_launch_mechanism_v2/check_launcher.py` (new: the login-node checker, kept for the fine-run go)

No existing file was edited. `scripts/train_deception.sbatch`, `train.py` and `postprocess_coarse.sh` are used unchanged.

## Spec axis

### Launcher against the reference configs

A login-node checker parses the launcher's own `--dry` output, so it checks the printed lines rather than a copy:

- `train.build_parser().parse_args` and `resolve_args` accept all 12 lines.
- `run_io.resolved_run_config` is diffed key by key, nested `node_config` and `edge_config` included, against:
  - coarse: `config.coarse.json` of `llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742`
    (spec 14.C2);
  - fine: `config.json` of `llama-8b-instruct_sdr/nls0.3_noedge_260819-083414`.
- Coarse lines differ from the reference only in `task`, `deception_condition`, `deception_margin_loss` (0.7 vs null)
  and `output_dir`. Every `prune_*` and `lambda_*`, `init_value`, the warmup steps and all hyperparameters are equal:
  seed 42, 500 node epochs, 300 edge epochs (unused), lr 0.03, batch 7, max_seq_length 120, 200/200/1000,
  node lambda sparsity 0.3, edge lambda sparsity 0.95, faithfulness weight 1.0.
- Fine lines differ in the same keys. They also carry `joint_tasks: null` and `joint_scale_epochs: true`, which the
  2026-08-19 reference predates. Both are inert for a non-joint task.
- `resolve_margin` returns 0.7 for D (dataset margin 0.7) and H (dataset margin 0.3). The pin overrides the
  dataset value, so D and H share one hinge (spec 9, 14.C2).
- `get_task(t).dataset_dir(args)` resolves to `data/datasets/<t>` for D and `data/datasets/<t>_honest` for H.
  All six directories exist. Each loads 200/200/1000 rows through the training loader. The longest prompts are
  101 (far), 106 (sdr) and 104 (ser) Llama tokens, under 120.
- Wrapper dry path: `scripts/train_deception.sbatch` was run on the login node with each coarse line's arguments
  plus a trailing `--help`. Env activation, the train.py import and argparse validation of every flag passed (rc 0).

### Slugs

- Coarse: `outputs/llama-8b-instruct_<task>_v2_coarse/nls0.3[_honest]_noedge_noan_nomh_nomo_nomb_<stamp>`,
  with one shared stamp per submission. This is the ticket's pattern and the v1 coarse wave's.
- Fine: no `--output-dir`, so the slug is train.py's default. `build_run_slug` gives `nls0.3[_honest]_noedge_<stamp>`
  under `outputs/llama-8b-instruct_<task>_v2/`. `deception_margin_loss` is not a slug key, so the pin adds no token.

### G12 scope

- `--dry` prints all 12 lines.
- `--plan`, `--test-only` and submit select only the 6 coarse runs.
- `--only <fine run>` is refused (exit 2) unless `--include-fine` is given. Checked.
- `--include-fine` was not used. No fine job was submitted.

### Partitions and time

- The allowlist is one partition per submission: `gpuH200x8` (default `--time 01:30:00`) or `gpuA40x4` (default
  `--time 03:00:00`).
- A100 partitions and comma lists are refused (exit 2). Checked.
- A single partition is a deliberate change from the format-control precedent, which mixed `gpuA40x4,gpuH200x8`
  under one 05:00:00. At the ticket's 01:30:00, an A40 landing would time out.

### No evaluation calls

- Neither new file calls `evaluate_circuit.py`, a suite, a knockout, a composition or EVAL 5.
- Neither calls `outputs/llama-8b-instruct_sdr_coarse/_launch/postprocess.sh`. The launcher's header names it
  only to warn against it.
- Post-processing used only `outputs/_launch_format_control/postprocess_coarse.sh`. It copies the masks to
  `*.coarse.json` and runs `expand_coarse_masks.py`, and nothing more. Checked by reading it.
- `write_training_summary.py` only reads files the training jobs wrote, plus `sacct`.

## Standards axis

- The launcher follows the format-control launcher's shape: cd to root, a `case` argument loop, a partition
  allowlist, an array `cmd`, `--test-only` via `"${cmd[0]}" --test-only "${cmd[@]:1}"`, and `tee -a` to `train_jobs.txt`.
- The header documents the settings, the margin-pin reason, the G12 rule, the partition reason and the
  post-processing step.
- `write_training_summary.py` reuses `evaluation.masks.count_masks`. It counts the trained masks from
  `active_nodes.coarse.json`, as `size_check.mask_source` does, and uses the same in-run gate thresholds as
  `size_check.SUFFICIENCY_GATE`.

### Mid-ticket changes, all lead- or user-directed

- **Interactive partition.** `gpuH200x8-interactive` is allowed at exactly 01:00:00, one `--only` run per
  submission, as the lead authorized on 2026-10-21.
- **Widened pair.** `gpuH200x8,gpuA40x4` is allowed with a 03:00:00 default. Any time under 03:00:00 is
  refused while gpuA40x4 is in the list. This is the shape the user set with scontrol for the backups.
- **Re-check.** The checker re-ran after each change and passed. It now also asserts:
  - the interactive refusals: no `--only`, two runs, or a time over the cap;
  - the widened pair's default time;
  - refusal of 01:30:00 with A40 in the list;
  - refusal of an A100 in a pair.

## Outcome check on the trained runs

- `write_training_summary.py` compares each trained run's `config.coarse.json` with the reference
  `config.coarse.json`. All 6 differ only in task and deception_margin_loss (0.7 vs null), plus
  deception_condition for H. No unexpected key.
- Each run dir holds `active_nodes.coarse.json` and `config.coarse.json`, written by `postprocess_coarse.sh`,
  and an expanded `active_nodes.json`.
- No run dir holds `evaluations*`. No evaluation job was submitted; sacct shows only the `mv2-*` training jobs
  for this ticket.

## Findings

- **No unresolved defects.**
- **Resolved during the ticket.**
  - The checker's first interactive assertion counted `sbatch ` inside `train_deception.sbatch `. The count now
    only uses lines that start with `sbatch`.
  - The launcher's refusal message still said "one partition per submission" after the pair was allowed. The
    wording is fixed.
- **Observations for the researcher. These are not defects.**
  - The ser_v2 D vs H head gap is +25.5%.
  - ser_v2 D sits at the accuracy gate (0.900).
  - Within the far and ser pairs, D trained on H200 and H on A40.
- **Limitation.** `train_jobs.txt` records each submission's partition at submit time. Backups the user moved
  with scontrol keep their original "gpuH200x8 01:30:00" fields; comment lines and the summary's sacct columns
  record what actually ran.
