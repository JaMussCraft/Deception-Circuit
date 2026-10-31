# Format-control: final orchestration report

Orchestrator: Claude Fable 5.1 (background job fcfa1a47), 2026-10-13 to 2026-10-15.
Branch `format-control` in `Deception-Circuit/.claude/worktrees/format-control`, 35 commits on 5b61031, tip 6b8d2d6, **not pushed** (per the brief). Working tree clean. Both test suites on the tip fail exactly the 8 baseline names (base 857 passed, mgnp 858).

## 1. Findings for the researcher

**Polarity.** The stored FAR deceptive dataset is 100% `designation_polarity == identity` (train 200/200, test 1000/1000; `far_honest` is mixed). With the Pressure Clause deleted, only 9 of 1,400 FAR instances answer honestly at the 0.3 floor (median honest-label margin -1.12). FAR "deception" is designation-following, not pressure-driven. `far_nopressure` is therefore 791/800 honest-split fallback and its F column is unpaired; SDR's test split (520) is fully paired (106/96 paired train/val + 44/54 fallback).

**The drift fix reversed the FAR variant rows.** Before ticket 01's clause-surgery fix, the full model read 0.106 (honest instruction) and 0.058 (no pressure) deceptive on FAR's D-data variant rows; after it, 0.839 and 0.871. Every pre-fix FAR eval 2 / eval 4 variant row pointed the wrong way; the post-fix reading is the one consistent with the spec's +1.98 note and the polarity finding. Earlier FAR conclusions drawn from those rows should be reopened.

**FAR size and coherence.** No NLS in {0.3, 0.4} yields a size-matched, sufficient FAR Format Circuit: D 48 heads, H 65, F 82 (NLS 0.4 retune: 72 heads, in-run KL 0.214 fails the gate). F overlaps H (Jaccard 0.652) nearly twice as much as D (0.340): in effect a second honest circuit. Both honest-labelled circuits' knockouts are incoherent (wikitext KL H 2.784, F 4.265); the deceptive circuit's is coherent (0.327).

**FAR delta cells.** Three leaf-granularity deltas (D−F, D−H−F, F−D−H) are positional defaults (P(item_2) 0.71 to 0.79 vs base 0.48); their head-granularity versions, the primary reading, are content-driven.

## 2. Verdicts (eval 2 alone, pre-registered rule; quoted from the committed summaries)

| suite | verdict | wikitext KL D / H / F (gate 0.66) | caveats |
| --- | --- | --- | --- |
| FAR | (c) | 0.327 / 2.784 / 4.265 | F oversized; both honest circuits incoherent; F data unpaired; without the gate the rule gives (b) |
| SDR fine | (c) | 1.383 / 0.694 / 1.342 | D fails the gate too (same as September); remedy "retrain F at lower NLS" cannot apply |
| SDR coarse heads-only | (a) | 0.364 / 0.275 / 0.279 | all knockouts saturate (acc ≈ 0); honest rows non-discriminating (D/H/F within 1 SE; margin 0.011); information is in the deltas: D&F (36 heads) necessary 0.002, D−F 0.119, F−D 0.598, D−H−F 0.782 not outside null |

Overlap (Jaccard heads): FAR D/H 0.430, D/F 0.340, H/F 0.652; SDR fine 0.593 / 0.584 / 0.775; SDR coarse 0.524 / 0.356 / 0.531.

## 3. The decision in front of the researcher: EVAL 5

| family | F knockout KL | gate | state |
| --- | --- | --- | --- |
| far | 4.265 | refused | no submit line |
| sdr | 1.342 | refused | no submit line |
| sdr_coarse | 0.279 | passes | both groups dry-run ready |

Cost (dry-run upper bounds): sm 4,671 judge calls, 24-30 GPU h; lb 4,050 judge calls, 9-12.5 GPU h. Launch from the worktree root, on gpuA40x4 (screen comparability):

```
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control
FORMAT_CONTROL_EVAL5_GO=1 bash outputs/_launch_format_control/submit_eval5.sh sdr_coarse sm
FORMAT_CONTROL_EVAL5_GO=1 bash outputs/_launch_format_control/submit_eval5.sh sdr_coarse lb
```

Then `python write_format_control_summary.py outputs/_suites/format-control-sdr-coarse-nls0.3 --eval5-dir outputs/eval5_format_sdr_coarse --eval5-dir outputs/eval5_format_sdr_coarse_lb`. No override is recommended for the refused families (their generations are not fluent).

## 4. Non-pre-registered choices to confirm (all labelled in every summary and decision.json)

1. (c) is checked before (a).
2. Distinct-2 collapse = knockout distinct-2 < 0.5 × full model's.
3. Honest-answer condition uses the eval 2 variant rows only (`--honest-rows variants|all`).
4. Non-discriminating-row flag at 1 binomial SE.
5. Spec amendment: for (c) with an oversized F, the remedy sentence replaces "retrain at a lower NLS" (which enlarges F); spec sentence kept as `spec_sentence`.
6. Spec amendment: with `--eval5-dir`, the deception-drop and outside-null conditions still read eval 2; eval 5 enters as collateral and an informational deception-drop row.

## 5. Rulings I made (every `Ruling:` line in the ledger, in order, with cost if wrong)

1. Ticket 05's real-suite run deferred if GPU time ran out (did not apply in the end). Cost: none.
2. No agent calls EnterWorktree while others run; absolute paths and `git -C` (superseded by 4). Cost: an edit in the wrong sibling.
3. Empty-variant guard in `evaluation/context.py`, reason detected from the records, not from args. Cost: a small additive change later.
4. Orchestrator is the single git actor; agents send commit requests by file list. Cost: coarser commits.
5. Sibling worktrees abandoned; all tickets in the one pinned worktree on disjoint files. Cost: agents' suite runs can see each other's in-progress files (mitigated by re-running suites at each merge point).
6. `far_nopressure` committed as built (791/800 fallback); FAR F trained per spec; F column marked unpaired by data. Cost: one training job the researcher may discard.
7. Validation follows the train minimum (150); fallback tops up only to the minimum (800/820 records, not ~1,400). Cost: F trains on 150 instead of 200 instances; a rebuild is a 6-minute GPU job.
8. `--deception-margin-loss 0.7` on all Format Circuit runs (paired runs' hinge margin). Cost: hinge beyond the full model's margin on 0.3-0.7 instances.
9. Coarse knockout/delta cells composed at leaf as `(expr) − m`, reported at head level (head composition keeps all 589,824 MLP units). Cost: ~24 coarse cells re-run.
10. Delta cells run eval 2 only; merged cells refiled by dataset condition with the mapping in the manifest. Cost: none.
11. (c) before (a); distinct-2 threshold 0.5. Cost: one suite's verdict label.
12. Honest-answer condition on the spec's variant rows only; H/F test sets informational; `--honest-rows` flag. Cost: one flag flip and a writer re-run.
13. Ticket 05 round 2 (eval 5 shared datasets) not separately re-reviewed; covered by the whole-branch review. Cost: none observed.
14. EVAL 5 launcher: worktree-local screen-cache copy; gpuA40x4 default; explicit recorded gate override only. Cost: a cache copy per suite; a slower partition.
15. FAR F carried = NLS 0.3 run (gate pass); NLS 0.4 retune recorded, evaluated once as a side job (reverses the earlier "carry the retune" plan). Cost: one line in suites.json and 21 FAR cells.
16. Non-discriminating-row criterion stays at 1 SE as implemented. Cost: one row re-read with the saturation caveat in view.
17. Collateral = eval 2 wikitext KL until an EVAL 5 directory is given. Cost: writer re-run with `--eval5-dir`.
18. (c) remedy sentence replaced for an oversized F. Cost: one sentence.
19. `--allow-rescreen "reason"` beside `--gate-override "reason"`, both recorded, never default. Cost: remove two flags.
20. Training on gpuA40x4/gpuH200x8 only (A100 40 GB OOM at ~41.6 GB peak); EVAL 5 on gpuA40x4 (screen comparability). Cost: edit two partition lists.
21. Deception-drop and outside-null conditions stay on eval 2 with `--eval5-dir`. Cost: a one-flag change.
22. Pre-flight ruling on the test-location MASK failure and the 8 baseline names judged by name (recorded as the baseline rule). Cost: none.

## 6. Housekeeping

- **Keep the `format-control` worktree until EVAL 5 has run.** The EVAL 5 gate reads the F run directories and the cells by their recorded worktree paths (it matches F by mask content, so a repointed `suites.json` also works while those directories exist); `_shards/`, Slurm logs and the local screen cache (`outputs/_eval5_format_cache/`) are untracked there. If prompted keep-or-remove at session end, choose keep.
- Branch unpushed, unmerged, per the brief; merge locally or push and open a PR as you prefer.
- Branches `format-control-01`, `format-control-02`, `format-control-04` are merged/ancestor pointers (worktrees removed); safe to `git branch -d`.
- Hardware: training needs A40/H200; the fine SDR decision-rule inputs all came from H200 (sanity cells drift by one tolerance step there); coarse SDR and FAR cells all ran on A40 and reproduce the September rerun exactly.
- Slurm jobs: 22878917 (dataset build), 22879579/22879743/22879744 (F training), 22879581/22879582 (OOM), 22895850 (FAR retune), 22895954-22895996 (39 SDR cells), 22906787-22906802 (16 FAR cells incl. side job); all recorded in `train_jobs.txt` and `suite_manifest.json`.
- Deferred minors: listed per ticket in the ledger and in `07-whole-branch-review.md` (triaged: none block merge).
- Process slips: impl-03 and impl-06 each ran one read-only `git log`; impl-04 ticked a review box once (reverted).

## 7. Where things are

- Ledger: `reports/00-orchestration-ledger.md`; baseline: `reports/00-baseline-failures.md`; reviews: `reports/01..06-*-review.md`, `07-whole-branch-review.md`, `08-code-review-two-axis.md`; implementer reports `reports/0N-implementer-report.md`.
- Suites: `outputs/_suites/format-control-{far,sdr,sdr-coarse}-nls0.3/evaluation_summary.md` and `decision.json`.
- Launchers: `outputs/_launch_format_control/` (README_suites.md, README_eval5.md).

## Addendum 2026-10-16: six extra coarse delta cells (job f037b43a)

Researcher request: H&F, H−F, D∩H−F, D∩F−H, H∩F−D, D∩H∩F on the coarse SDR suite, as knockout cells on the D test set (n = 1000), same recipe as the existing deltas (`(<expr>) − m` at leaf, interchange, 20-sample size-matched null). Commits b776e8b, bf8ad9a, cec85bb (branch tip cec85bb, 38 commits on 5b61031, unpushed). Verdict unchanged: (a); the 24 earlier cells are byte-identical.

| circuit | heads | knockout acc | null p5 / p50 / p95 | outside null | wikitext KL | flipped / stayed | hardware |
| --- | ---: | ---: | --- | --- | ---: | --- | --- |
| D | 69 | 0.002 | 0.041 / 0.414 / 0.774 | yes | 0.364 | 998 / 2 | A40 |
| H | 56 | 0.002 | 0.110 / 0.525 / 0.918 | yes | 0.275 | 998 / 2 | A40 |
| F | 68 | 0.000 | 0.041 / 0.496 / 0.747 | yes | 0.279 | 1000 / 0 | A40 |
| D&F | 36 | 0.002 | 0.305 / 0.720 / 0.947 | yes | 0.150 | 998 / 2 | A40 |
| D−F | 33 | 0.119 | 0.517 / 0.786 / 0.988 | yes | 0.137 | 866 / 134 | A40 |
| F−D | 32 | 0.598 | 0.627 / 0.889 / 0.972 | yes | 0.091 | 362 / 638 | A40 |
| D−H−F | 22 | 0.782 | 0.733 / 0.920 / 0.999 | no | 0.096 | 187 / 813 | A40 |
| H−D−F | 2 | 1.000 | 0.986 / 1.000 / 1.000 | no | 0.007 | 0 / 1000 | A40 |
| F−D−H | 21 | 0.965 | 0.530 / 0.863 / 0.983 | no | 0.047 | 27 / 973 | A40 |
| **H&F** | 43 | 0.003 | 0.315 / 0.671 / 0.910 | yes | 0.214 | 997 / 3 | H200 |
| **H−F** | 13 | 0.307 | 0.944 / 0.990 / 1.000 | yes | 0.037 | 674 / 326 | H200 |
| **D∩H−F** | 11 | 0.335 | 0.939 / 0.996 / 1.000 | yes | 0.029 | 635 / 365 | A40 |
| **D∩F−H** | 4 | 0.591 | 0.790 / 0.998 / 1.000 | yes | 0.021 | 388 / 612 | A100 |
| **H∩F−D** | 11 | 0.679 | 0.724 / 0.997 / 1.000 | yes | 0.044 | 279 / 721 | A40 |
| **D∩H∩F** | 32 | 0.002 | 0.384 / 0.679 / 0.942 | yes | 0.115 | 998 / 2 | H200 |

Decomposition: H−F (13) = D∩H−F (11, 0.335) + H−D−F (2, 1.000): the effect is in the heads shared with D. F−D (32) = H∩F−D (11, 0.679) + F−D−H (21, 0.965). D−H (26) = D∩F−H (4, 0.591) + D−H−F (22, 0.782, inside null). The 32-head triple core D∩H∩F knocks out as fully as the 69-head D. Flip audit: positional default 0/21; all six new cells content-driven and separable from a random knockout of their size; stayed sets D∩H∩F ~ D&F ~ D ~ H identical (the same 2 items); D∩H−F ~ H−F Jaccard 0.85 vs 0.21 random. Hardware: the only row near its null is H∩F−D (margin 0.045) and it ran on A40; the H200 and A100 rows are all 0.2 or more from their nulls. Slurm: 22945674 (H200-int, packed trio), 22946213/22946215 (A40-int), 22946214 (A100x4-int); 22945587 and 22946115 cancelled before starting. EVAL 5 is still unsubmitted; `submit_eval5.sh` evaluates D, H, F per family, so an EVAL 5 on a composed circuit such as D∩H∩F would need an expression operand added to the launcher.

## Hand-off 2026-10-18: EVAL 5 ran; sm needs a judge re-score; branch ready to merge

**CLOSED 2026-10-19.** sm re-scored (4,661 calls, 0 rows still failing) under mgnp; the coarse SDR verdict is now **(b) on eval 2 + eval 5**, failing only collateral (mean ref-NLL rise F 0.668 vs D 0.611; F lower on 6 of 10 datasets, gap from lb:instructed-deception and sandbagging; eval 5 deception drop F 0.777 >= D 0.723). sm mean deception under knockout: full 1.000 / D 0.312 / H 0.172 / F 0.273 / D−F 0.650. Branch merged (4314c5b), records repointed (aef064a), untracked state moved to the primary checkout, worktree removed, branch deleted. Details in the ledger's 2026-10-19 entry. The text below is the pre-re-score hand-off, kept for the record.

**EVAL 5 (sdr_coarse, D / H / F / D−F in one invocation per group).** lb (22947270) is complete and sound; sm (22947260, 14.5 GPU h) generated everything but lost 6,032 of ~6,228 scoring judge calls to OpenRouter HTTP 402 (credits ran out between the two jobs). Recovery is a judge-only re-score on the login node, no GPU: `rejudge_benchmarks.py` (commit f4e50f7), 4,661 calls, about $20-40; exact commands in `outputs/_launch_format_control/README_eval5.md` ("PENDING") and the ledger. Until then the sm suite's rows read 0.0 and must not be quoted.

**lb result (Liars' Bench, n = 50 per dataset, deception under interchange knockout):**

| dataset | full | D KO | H KO | F KO | D−F KO | D−F random |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| instructed-deception | 1.000 | 0.060 | 0.120 | 0.040 | 0.720 | 0.493 |
| harm-pressure-knowledge-report | 1.000 | 0.320 | 0.320 | 0.220 | 0.680 | 0.687 |
| convincing-game | 1.000 | 0.200 | 0.100 | 0.060 | 0.860 | 0.800 |
| mean | 1.000 | 0.193 | 0.180 | 0.107 | 0.753 | 0.660 |

F's knockout removes benchmark deception at least as much as D's on all three datasets (the eval 2 (a) pattern carried to the benchmarks); D−F's knockout does not move it and sits at or below its own random null on two of three. Collateral (reference NLL) is mixed: F higher than D on instructed-deception, lower on the other two. The suite's `evaluation_summary.md` / `decision.json` still read eval 2 alone; re-run the writer with both `--eval5-dir` flags after the re-score.

**Merge checklist.** Branch `format-control`, 41 commits on 5b61031 (tip d6b0cea), unpushed. Full suites on the tip fail exactly the 8 baseline names (see the ledger's closing entry for the counts). Untracked state that lives only in the worktree and must be moved or kept if the worktree is removed: `outputs/eval5_format_sdr_coarse{,_lb}/` (the EVAL 5 cells, judge caches, lb summary), `outputs/_suites/*/_shards/`, `outputs/_launch_format_control/logs/`, `logs/evaluate_circuit_2294*.out`, `outputs/_eval5_format_cache/`, and the F training runs `outputs/llama-8b-instruct_{far,sdr,sdr_coarse}/nls0.3_nopressure_*` plus `nls0.4_nopressure_*` (FAR retune), which `suites.json` names by worktree path (the EVAL 5 gate matches F by mask content, so repoint `suites.json` after moving them). Branches `format-control-01/-02/-04` are merged or ancestor pointers and can be deleted. Suggested: `git -C Deception-Circuit merge --no-ff format-control` from main, then move the untracked directories listed above into the main checkout at the same relative paths and repoint `suites.json`, then remove the worktree.
