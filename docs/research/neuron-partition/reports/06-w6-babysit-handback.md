# Hand-back 06: W6, the Bridges-2 ablation jobs A, B and C

Agent: worker W6 (Claude, Opus). Ticket: the lead's W6 brief of Tue 3 Nov 2026 (see jobs A, B and C through, fetch
them to Delta, run the verdict script, record everything). Status: resolved. All three jobs completed, and they were
fetched, checked, recorded and given verdicts by 6:10 pm EST.

`WT` is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`. `D` is the main
direction directory `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition`.

## What changed

- **Hand-back 02.** `WT/docs/research/neuron-partition/reports/02-w2-ablation-handback.md` gains the section
  "Addendum: full cells". It holds one execution-evidence block per sets file of each job, plus the three
  `verdict.md` files, copied verbatim below their titles.
- **Job list and ledger in `D`.** Jobs 50182995, 50183187 and 50183194 are marked COMPLETED with `job update`. They
  are reconciled with `ledger reconcile` at 4,035 s, 9,584 s and 9,724 s.
- **Fetched outputs, which are not committed.** These are under `WT/outputs/_analyses/neuron-partition/`:
  - `ablation/jobC-fe2db9e/`.
  - `ablation/jobA-fe2db9e/far_all_sets_k{500,1000}_with_nulls/`.
  - `ablation/jobB-fe2db9e/far_all_sets_k2000_with_nulls/` and `ablation/jobB-fe2db9e/far_sets_k1000_with_nulls/`.
  - Each holds `summary.json`, `rows.jsonl`, `cells_partial.jsonl` and `run_manifest.json`.
  - The Slurm logs are in `WT/logs/bridges2/np_ablate_<id>.out`.
- **Verdicts, which are not committed.** They are `verdict.json` and `verdict.md` in
  `WT/outputs/_analyses/neuron-partition/verdict/`:
  - `far_atp_all_c3d7763/` is the primary ranking, from jobs A and B at k 500, 1,000 and 2,000.
  - `far_atp_readout_c3d7763/` is the readout ranking, from job B at k 1,000.
  - `far_contrast_66741d7/` is the contrast ranking, from job C at k 1,000.
- **Helpers.** They are in `WT/outputs/_analyses/neuron-partition/w6_tmp/` and are not committed:
  - `rate.py` gives seconds per forward per cell.
  - `evidence.py` gives the numbers of one evidence block, with intact G and rate per stream from the twin cells.
  - `addendum.py` and `jobs.json` regenerate the addendum.
  - `waitjobs.sh` is the bounded sacct poll.
  - `bars.py` lists the failing N1 bars.
  - `STATUS.md` is the resume note.

## How verified

- **Evidence script.** On the pilot cell `ablation/pilot-e5962fe/`, `evidence.py` reproduces hand-back 02's intact
  G of 10.508 for D and 14.564 for I. It counts 30 of 30 cells and 17,808 of 17,808 rows. `rate.py` gives the pilot's
  0.201 s per forward.
- **Fetch.** Each job directory was fetched with `rsync -rl` through `b2dtn`. b2.sh's fetch was not used because its
  Delta root defaults to the mechanism-analysis worktree. For all 20 files of the five cells, the sha256 values of
  `summary.json`, `rows.jsonl`, `cells_partial.jsonl` and `run_manifest.json` were compared on Bridges-2 and Delta.
  Every value was equal. The four sets files were also hashed on both clusters and were equal.
- **Lint.** `research-session lint` reports nothing on hand-back 02 or on this file.
- **Verdict commands.** They are written in the addendum, and each ran from `WT` with the mgnp interpreter. The halves
  came from the `split_halves` rule, not the fallback.

## Execution evidence

The full blocks, one per sets file, are in the addendum of hand-back 02. Times are EST. Every job ran on Bridges-2,
partition GPU-shared, one H100-80 GB, allocation cis260372p.

| Job | Id | Node | State | Elapsed / reserved | Cells | Rows |
|---|---|---|---|---|---|---|
| C, contrast k 1,000 | 50182995 | w010 | COMPLETED 0:0 | 4,035 s / 2 h | 30 of 30 | 277,200 of 277,200 |
| A, all-position k 500 and 1,000 | 50183187 | w007 | COMPLETED 0:0 | 9,584 s / 4 h | 2 x 30 of 30 | 2 x 369,600 of 369,600 |
| B, all-position k 2,000 and readout k 1,000 | 50183194 | w008 | COMPLETED 0:0 | 9,724 s / 4 h | 2 x 30 of 30 | 2 x 369,600 of 369,600 |

- **Baseline reproduces.** IOI intact argmax accuracy is 0.51 against the brief's 0.51 in all five cells (ruling R4).
  The sentences sha256 is `61ebeea317ac4932c0b859cc62b88ed0c45a7d6602d4866a9cf2373ee2cc5e59`.
  - Intact G averaged over streams is 9.834 for D, against the ladder audit's 10.087, in every cell. For I it is
    14.708 against 14.979.
  - Per stream, G is 9.847 for D clean, 9.820 for D corrupt, 14.730 for I clean and 14.687 for I corrupt. The intact
    rate is 0.985 for D and 0.995 for I.
- **Checks.** The self-replay error is 0.0 on D and on I. The twin crosscheck's largest difference is 0.0 at n = 600.
  Nothing is unpaired.
- **Rate.** The measured rate is 0.039 to 0.046 s per forward. The model load from /ocean took 475 to 904 s.
- **Provenance.** Every `run_manifest.json` names `git_commit` fe2db9e0d4736469aa180c6d89a18b5736710c20,
  `git_dirty` false, and its own Slurm job id.

Readings from the verdicts. Every row is in the addendum.

- **N1 fails at every k under the all-position ranking.**
  - At k 500, D_only (338 neurons) fails only the IOI bar, on the whole sample and on both halves, under twin, mean
    and zero.
    - It removes 0.813 of the D margin under twin and 0.724 under mean.
    - It removes 0.145 and 0.161 of the I margin.
    - H and F move 0. The null p95 of D removed is 0.012 under twin and 0.020 under mean.
    - IOI moves -6.0 points. The 20 matched nulls moved IOI by -3 to +6 points, with a p95 of |shift| of 3.15, on
      100 IOI rows.
  - At k 1,000 and k 2,000, D_only also fails the I bar. It removes 0.340 and 0.495 of the I margin under twin, and
    0.414 and 0.573 under mean. IOI moves -11 and -13 points.
- **N1 fails under the readout and contrast rankings at k 1,000.**
  - The readout D_only removes 0.291 of the D margin under twin and 0.236 under mean.
  - The contrast D_only removes 0.039 under twin and 0.032 under mean.
- **N2 under the all-position ranking.** H_only is undetermined under the mean reference at every k.
  - At k 2,000 it is a near miss for bypass. H accuracy falls 23.5 points, the null p95 of |H shift| is 0.0, and D's
    deceptive rate moves -5.2 points against a bar of under 5. Half 1 reads bypass at -4.5, and half 2 reads
    undetermined at -5.9.
  - The zero reference reads bypass on the whole sample, with H at -44.3 and D's rate at -4.5.
  - The twin reverse patch reads "suppression or shared" at k 1,000 and 2,000, which is descriptive (ruling R7).
- **N2 under the readout and contrast rankings** is undetermined at k 1,000.

## What is NOT done

- **No interpretation.** No finding is logged. The N1 and N2 readings above restate the verdict script's output.
- **No new jobs.** Nothing was resubmitted, and no GPU time was spent beyond the three jobs.
- **Not committed.** The fetched outputs and verdicts are under `outputs/`, which is not tracked.

## Open questions

- **IOI near miss.** At k 500, D_only fails N1 only on the IOI bar, at 6 points against 5, on 100 rows. One null of 20
  moved IOI by 6 points. The frozen bar reads it as a fail, and the orchestrator decides whether a finding should
  record it as a lead. Default: record a fail with the margin stated.
- **N2 near miss at k 2,000.** D's deceptive rate moves -5.2 points against a bar of under 5. Default: record
  "undetermined at this size" under the mean reference, as the script reads it.

## Files to commit

- `docs/research/neuron-partition/reports/02-w2-ablation-handback.md`
- `docs/research/neuron-partition/reports/06-w6-babysit-handback.md`
- In the main directory `D`, the `research-session` tool updated `ledger.json`, `worklog.json` and `WORKLOG.md`.
  `state.json` there changed at 5:55 pm EST, and it is not known whether this worker's calls changed it.
