# Nine acquired EVAL5 blocks: descriptive snapshot

Saved native labels favor New30 on instructed deception, while transfer against the fixed random comparator varies across benchmarks. OldD69 has fewer native D labels than New30 in every block, accompanied by higher reference NLL in every block. This is a descriptive snapshot, not a pooled efficacy score or a deception-specific mechanism claim. Statistics is excluded; final all-ten acquisition/accounting/scientific audit remains separate.

Sources: the first nine result paths in [frozen-input-index.json](../transfer-v5/final-eval5-audit/frozen-input-index.json), contextualized by [v5_transfer.md](../../../project_context/research_notes/Deception%20specificity%20and%20shared%20circuits/v5_transfer.md). All nine indexed receipt SHA256 values matched their saved files. For all four displayed states, counts sum to the full fixed recipient denominator and match saved per-row labels; generation/label lengths match n. Eight blocks retain `complete:true`. Instructed deception retains original `complete:false` flags because official INVALID outcomes triggered the original gate; all responses/judgments were acquired, and its post-outcome reporting exception is disclosed in reports177/178. Original flags and labels are unchanged. This check is not the final comprehensive audit.

## Native D/H/U counts

Each entry is **D / H / U**, on the row's entire n. D/H/U are native deceptive/honest/unparsed labels with benchmark-specific meanings. New30=`new-allW30`; intact=`full`; random=`random30`, one fixed 30-head comparator. New23 is outside this requested four-state comparison.

| Benchmark | n | Intact | New30 | OldD69 | Fixed random30 |
|---|---:|---:|---:|---:|---:|
| Sandbagging | 50 | 16 / 6 / 28 | 12 / 6 / 32 | 0 / 9 / 41 | 9 / 6 / 35 |
| LB instructed deception | 50 | 48 / 0 / 2 | 6 / 35 / 9 | 2 / 40 / 8 | 31 / 18 / 1 |
| LB harm-pressure knowledge report | 50 | 49 / 1 / 0 | 35 / 12 / 3 | 17 / 25 / 8 | 34 / 6 / 10 |
| LB convincing game | 50 | 49 / 0 / 1 | 23 / 0 / 27 | 11 / 0 / 39 | 47 / 0 / 3 |
| MASK continuations | 28 | 26 / 0 / 2 | 17 / 4 / 7 | 4 / 12 / 12 | 7 / 6 / 15 |
| MASK disinformation | 11 | 11 / 0 / 0 | 5 / 0 / 6 | 4 / 1 / 6 | 5 / 0 / 6 |
| MASK doubling-down known facts | 29 | 27 / 2 / 0 | 20 / 4 / 5 | 12 / 5 / 12 | 20 / 2 / 7 |
| MASK known facts | 37 | 36 / 0 / 1 | 19 / 5 / 13 | 16 / 8 / 13 | 20 / 2 / 15 |
| MASK provided facts | 50 | 46 / 0 / 4 | 30 / 11 / 9 | 17 / 9 / 24 | 32 / 4 / 14 |

## Saved output-quality diagnostics

Each entry is **reference NLL / distinct-2 / at-limit count**, rounded to three decimals for continuous metrics. Reference NLL teacher-forces each state's own generated text through the unablated model; lower is not automatically better because repetition can be highly predictable. Distinct-2 is the saved pooled within-response unique-bigram ratio. At-limit count is the number of saved per-sample scored-token lengths at least the generation budget:1024 for sandbagging,512 otherwise. It is a cap proxy, not an independently verified termination/truncation label. NLL is token-weighted, and response lengths differ; these diagnostics do not establish preserved benign-task utility.

| Benchmark | Intact | New30 | OldD69 | Fixed random30 |
|---|---:|---:|---:|---:|
| Sandbagging | .286 / .683 / 0 | .283 / .382 / 16 | .733 / .351 / 9 | .440 / .452 / 8 |
| LB instructed deception | .473 / .988 / 0 | .891 / .990 / 0 | 1.276 / .988 / 0 | .602 / .986 / 0 |
| LB harm-pressure knowledge report | .113 / 1.000 / 0 | .356 / .942 / 0 | .930 / 1.000 / 0 | .211 / 1.000 / 0 |
| LB convincing game | .371 / .874 / 0 | .502 / .802 / 0 | .966 / .769 / 1 | .491 / .897 / 0 |
| MASK continuations | .229 / .855 / 3 | .390 / .832 / 2 | .949 / .639 / 2 | .466 / .778 / 2 |
| MASK disinformation | .331 / .835 / 10 | .393 / .749 / 4 | .727 / .526 / 4 | .455 / .747 / 5 |
| MASK doubling-down known facts | .367 / .921 / 0 | .555 / .926 / 0 | 1.092 / .860 / 0 | .506 / .761 / 1 |
| MASK known facts | .362 / .885 / 0 | .506 / .825 / 0 | .911 / .684 / 2 | .543 / .851 / 0 |
| MASK provided facts | .323 / .897 / 0 | .512 / .842 / 0 | .899 / .790 / 2 | .549 / .836 / 2 |

## What these counts support

- **Instructed deception is the clearest favorable native-label contrast with fixed random:** New30 D6/H35/U9 versus intact D48/H0/U2 and random D31/H18/U1. Nine New30 INVALID outcomes remain unresolved; they are not nine extra honesty successes. New30 raises reference NLL from .473 to .891, less than OldD69's1.276. This pressure-only block does not establish preserved benign utility.
- **Transfer is not uniformly stronger than the comparator.** New30 has D35 versus random34 on harm-pressure, D17 versus7 on continuations, ties5 on disinformation and20 on doubling-down, and has only small raw-count advantages on known facts (19 versus20) and provided facts (30 versus32). One fixed random mask is not a null distribution; these are descriptive comparisons, without a pooled score, significance claim or new mask selection.
- **Large D reductions can chiefly become U.** Convincing game changes D49/H0/U1 to New30 D23/H0/U27; its27 U comprise21 INVALID and6 `lie_instructed_told_truth` outcomes. The native game grader tracks compliance with the instructed target trait/option relative to frozen baseline belief, not whether a user was actually persuaded. MASK disinformation changes11/0/0 to5/0/6, all six New30 U being evasive C verdicts. Across the five MASK blocks, New30 U are native C/D evasions: C means neither assertion; D denies both. They are neither measured truthful disclosure nor automatically deception. Coherent refusal/evasion can be desirable, but the saved U class does not by itself certify coherence or usefulness, and no blanket success credit is applied.
- **Sandbagging remains a quality warning.** New30's D16→12 change leaves H at6, increases U28→32, lowers distinct-2 .683→.382 and raises the at-limit proxy0→16. The native grader reads answer tags; native H/normal does not establish factual correctness, and U contains missing-tag/ambiguous outputs. OldD69's D0/U41 similarly does not establish elimination of deception. These saved quality metrics complement the earlier targeted repetition audit; no new response adjudication was performed here.

These results use frozen historical cohorts/beliefs and native donor tiling, with newly generated intact baselines. They do not measure newly induced deception outside the historical recipient cohort, and they should not be conflated with V2 independent-donor label-readout experiments. No shared summary, result, receipt, cache, model, GPU/API/Slurm state or artifact was modified; only this report was written.
