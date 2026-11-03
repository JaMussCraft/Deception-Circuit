# Last message of d4-worker ad4-worker-d661ad07c14a7e55 (2026-11-02T12:37:43-05:00)

Both static-quartet rules fail. The three GPU riders are written, pass their dry runs and are ready for you to submit. The hand-back is at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/02-handback.md` and passes lint.

**P1 (query side) fails.** head.15.8 ranks 7 of 320, inside the cutoff of 16. head.14.4 ranks 24, outside it. By layer sum, layer 14 comes first but layer 15 only fourth, behind 13 and 12. Both named heads still compose more with the quartet's queries than with any of 20 random sets of four layer-17 heads.

| | score into quartet | best of 20 random draws |
|---|---|---|
| head.15.8 | 0.0384 | 0.0319 |
| head.14.4 | 0.0295 | 0.0224 |

**P2 (copy) fails, but the test is nearly powerless on this model.** The quartet copy scores are 0.000, 0.000, 0.012 and 0.000, against a bar of 0.5 for two heads. None of the 1,024 heads in the model reaches 0.5; the best is head.30.12 at 0.390. Mapping the embedding straight to the unembedding scores 0, because Llama's embeddings are untied. Read the fail as weak evidence against copying.

**How (d) ran.** It finished locally with exit 0, using commit b324c507 with uncommitted changes (the script's own sha256 is in the run manifest). The model shard hashes match an independent `sha256sum`. One earlier attempt was killed by the 40 GB memory cap that all our processes share on the login node; it wrote nothing.

**The other three riders.** Each command starts with `cd <worktree> && mkdir -p logs &&`. The account is your choice.
- **(a) Quartet attention, D against the twin, far and ser.** About 0.2 GPU-hours; reserve 0:30.
  ```
  sbatch --chdir=<worktree> --time=00:30:00 --partition=gpuA100x4 --account=bgrb-delta-gpu scripts/analyze_components.sbatch batch docs/research/deception-divergence/jobs/D4a.batch --timings outputs/_analyses/deception-divergence/d4a/timings/d4a.json
  ```
  The twin condition read the whole 1,000-row test split, so I added an opt-in flag to `attention_patterns.py` that restricts it to the 100 held-out ids. Default runs are unchanged.
- **(b) The after-cue arm on the sycophancy twins.** About 0.45 GPU-hours on an A100; reserve 0:45.
  ```
  sbatch --chdir=<worktree> --time=00:45:00 --partition=gpuA100x4 --account=bgrb-delta-gpu --nodes=1 --gpus-per-node=1 --cpus-per-task=1 --mem=64G --output=logs/d4b_after_cue_%j.out --wrap 'export HF_HOME=/work/nvme/beto/swong2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1; exec /u/swong2/.conda/envs/mgnp/bin/python scripts/b3_patch.py --task syc --sets S_all,heads_only --positions after_cue,post_tag --null 20 --out outputs/_analyses/deception-divergence/d4b'
  ```
  It calls the interpreter directly because the existing B3 job wrapper only runs from the instructed-route worktree. I went beyond the ticket's S_all by adding `heads_only` and `post_tag`. This separates whether mlp.5 to mlp.7 act over the cue window, and `post_tag` should reproduce J4's 0.724 as an in-run check.
- **(c) SDR key versus query.** About 0.6 GPU-hours on H100 or H200, about 0.9 on A100; reserve 1:15.
  ```
  sbatch --chdir=<worktree> --time=01:15:00 --partition=gpuA100x4 --account=bgrb-delta-gpu scripts/analyze_components.sbatch batch docs/research/deception-divergence/jobs/D4c-sdr.batch --timings outputs/_analyses/deception-divergence/d4c/timings/sdr.json
  ```
  After the job, this command applies the 0.15 query-minus-key rule with the offline estimator:
  ```
  python scripts/route_closure_readings.py outputs/_analyses/deception-divergence/d4c/sdr/Ct__leaf/sdr_v2/route_closure/route_closure.json --out-dir docs/research/deception-divergence/results/d4c
  ```
  Run on B1's far output relabelled as SDR, it reproduces B1's numbers exactly.

**Tests.** The new tests pass on both interpreters, and the existing patching and attention suites still pass on both.

**Bridges-2 is not ready.** Its fetch script copies back only the `mechanism-analysis-*` and `instructed-route-b1*` outputs, so these results would never return to Delta. The branch also needs a push and a sync first, and nobody has checked the allocation's balance. I left the fetch script alone because the D1 worker may be editing it too.

All new and changed files are in the worktree, and the hand-back lists them for your commit.
