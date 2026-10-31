# Ticket 05 hand-back (impl-05): FINAL, 2026-10-22

**Stage: DONE. The 6 coarse heads-only circuits are trained, post-processed and summarized. HARD STOP (spec §10 (ii)):
no evaluation of any kind was run.** Scope was user ruling G12: coarse only, fine runs deferred.

## Run directories (worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets`)

| cell | run dir | job (winner) | where | elapsed |
|---|---|---|---|---|
| far_v2 D | `outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717` | 23105421 | H200 interactive (beto) | 00:29:41 |
| far_v2 H | `outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323` | 23105388 | A40 (bjhz) | 02:25:17 |
| sdr_v2 D | `outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323` | 23105389 | A40 (bjhz) | 02:26:18 |
| sdr_v2 H | `outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323` | 23105390 | A40 (bjhz) | 02:26:43 |
| ser_v2 D | `outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101` | 23109196 | H200 interactive (beto) | 00:30:11 |
| ser_v2 H | `outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323` | 23105392 | A40 (bjhz) | 02:26:25 |

- Each directory was post-processed with `outputs/_launch_format_control/postprocess_coarse.sh`. It now holds
  `active_nodes.coarse.json` and `config.coarse.json`, and an expanded `active_nodes.json`.
- Failed run, kept and not used: `outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323`
  (job 23105391). After 2 min, phase 1's `from_pretrained` raised an OSError on a cache file that exists. Phase 0
  of the same job had loaded the weights. Three siblings passed the same call in the same minute, two on the same
  node. Diagnosis: a transient read on the shared filesystem. Its one resubmission, 23109191, was cancelled
  because the interactive run won.

## Size table and in-run gate

The gate is accuracy >= 0.90, exact match >= 0.90 and KL <= 0.20, on each run's own test split. It is a reading only.

| cell | heads | attn blocks | node acc | node EM | node KL | gate |
|---|---|---|---|---|---|---|
| far_v2 D | 58 | 10 | 0.964 | 0.966 | 0.102 | holds |
| far_v2 H | 60 | 11 | 0.982 | 0.976 | 0.089 | holds |
| sdr_v2 D | 60 | 11 | 0.926 | 0.928 | 0.137 | holds |
| sdr_v2 H | 58 | 12 | 0.942 | 0.944 | 0.163 | holds |
| ser_v2 D | 55 | 11 | 0.900 | 0.909 | 0.149 | holds (accuracy exactly at 0.900) |
| ser_v2 H | 69 | 11 | 0.905 | 0.915 | 0.197 | holds (KL near 0.20) |

D vs H head gap, computed as (H - D) / D:

| task | heads D | heads H | gap |
|---|---|---|---|
| far_v2 | 58 | 60 | +3.4% |
| sdr_v2 | 60 | 58 | -3.3% |
| ser_v2 | 55 | 69 | +25.5% |

v1 SDR references, recomputed with `count_masks` in the main checkout. They match the quote.

| run | heads | fine units |
|---|---|---|
| fine D | 68 | 11,251 |
| coarse D | 69 | n/a |
| coarse H (orientation) | 56 | n/a |

Every trained `config.coarse.json` equals the reference's `config.coarse.json` except task, deception_margin_loss
(0.7 vs null) and, for H, deception_condition. Full tables: `reports/05-training-summary.md` and `.json`.

## For the researcher

1. The ser_v2 D vs H head gap is +25.5%. It is above the 25% tolerance that format-control's size rule used.
   This ticket only reports it.
2. ser_v2 D sits exactly at the accuracy gate, and ser_v2 H's KL is 0.197.
3. Within the far and ser pairs, D trained on H200 and H on A40. Both sdr runs trained on A40. Memory records bf16
   drift on A100 evaluations, so GPU type can move results slightly.
4. The fine runs are deferred under G12. `submit_train.sh --dry` prints them, and submitting them requires
   `--include-fine`.

## Ledger

| item | GPU-h |
|---|---|
| Ticket 05 reconciled | 11.5 of the 20 allocated |
| Ticket 05 actual | 10.78 (38,797 GPU-s) |
| Holdback draw | none |
| Feature total | 22.75 of 60 |
| In flight | 0 |

- A40 runs were reconciled at 2.5 each and interactive runs at 0.5 and 0.75. The failed job counts 0.25.
- The four cancelled-while-pending jobs count 0.

## How the queue was handled

- Six beto/gpuH200x8 jobs were submitted on 2026-10-21. test-only projected starts weeks away on every account
  and on A40.
- The lead lifted the interactive ban for this ticket and runs went to `gpuH200x8-interactive` one at a time. The
  user moved the six backups to bjhz-delta-gpu, widened them to gpuH200x8,gpuA40x4 and set 03:00:00.
- The QOS stayed `beto-delta-gpu` after the move, which gave InvalidQOS. The agent fixed one job and the user
  fixed four.
- The first run to write results.json won its cell, and its twin was cancelled.
- The permission classifier refused three agent actions; the user then performed two of them:
  - a ledger "holdback draw" authorization entry, never needed;
  - the account move;
  - a QOS update on four jobs.
- The lead's request to "move to bjhz" came from an agent message, so it did not count as user consent until the
  user acted.

## Tests

Both envs, re-run on 2026-10-22 on the final code, after the last edit to the launcher files:

| env | failed | passed | skipped |
|---|---|---|---|
| base | 8 | 1665 | 58 |
| mgnp | 8 | 1818 | 19 |

The failures are exactly the 8 baseline names; none is new.

## Review

`reports/05-train-v2-circuits-and-hand-back-review.md`, both axes, done by the implementer. There are no
unresolved findings.

## Docs edited outside the repo

These are outside the git repo:

- `/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/issues/05-train-v2-circuits-and-hand-back.md`
- `reports/05-handback.md`
- `reports/05-training-summary.md`
- `reports/05-training-summary.json`
- `reports/05-train-v2-circuits-and-hand-back-review.md`
- `compute-ledger.json`

## Files to commit (worktree, 58 files, explicit paths)

- New: `outputs/_launch_mechanism_v2/check_launcher.py`. It is the login-node checker of the launcher and re-runs
  before any fine-run go.
- Each run dir has a 6.4 MB `history.json` and a 7.6 MB expanded `active_nodes.json`. Before committing them,
  match what main tracks for the existing `outputs/llama-8b-instruct_sdr_coarse/` run dirs. The implementer had
  no repository access to check.

```
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/_launch_mechanism_v2/check_launcher.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/_launch_mechanism_v2/submit_train.sh
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/_launch_mechanism_v2/train_jobs.txt
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/_launch_mechanism_v2/write_training_summary.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/active_nodes.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/active_nodes.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/config.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/config.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/history.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/plots/loss_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/plots/metrics_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/results.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/train.log
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717/active_nodes.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717/active_nodes.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717/config.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717/config.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717/history.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717/plots/loss_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717/plots/metrics_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717/results.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717/train.log
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/active_nodes.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/active_nodes.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/config.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/config.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/history.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/plots/loss_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/plots/metrics_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/results.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/train.log
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323/active_nodes.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323/active_nodes.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323/config.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323/config.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323/history.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323/plots/loss_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323/plots/metrics_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323/results.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323/train.log
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/active_nodes.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/active_nodes.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/config.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/config.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/history.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/plots/loss_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/plots/metrics_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/results.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323/train.log
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101/active_nodes.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101/active_nodes.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101/config.coarse.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101/config.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101/history.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101/plots/loss_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101/plots/metrics_node.pdf
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101/results.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101/train.log
```
