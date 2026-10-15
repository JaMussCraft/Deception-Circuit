# Format-control summary: format-control-far-nls0.3

| field | value |
| --- | --- |
| suite | `format-control-far-nls0.3` |
| family | fine (atomic knockouts at finest; deltas at head and leaf, head primary) |
| task | far |
| evaluated on | eval 2 alone |
| circuit D | condition `deceptive`, NLS 0.30, `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_far/nls0.3_noedge_260819-083914` |
| circuit H | condition `honest`, NLS 0.30, `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_far/nls0.3_honest_noedge_260819-084020` |
| circuit F | condition `nopressure`, NLS 0.30, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/outputs/llama-8b-instruct_far/nls0.3_nopressure_noedge_261013-203424` |
| D data | `far` (condition `deceptive`, from the manifest), full-model accuracy 1.000; not paired with F data |
| H data | `far_honest` (condition `honest`, from the manifest), full-model accuracy 1.000; unpaired (disjoint instances) |
| F data | `far_nopressure` (condition `nopressure`, from the manifest), full-model accuracy 1.000; NOT paired: 98% honest-split instances |

## Decision

**Verdict: (c).** (c) Uninformative: F is already oversized (+71% heads); the spec's remedy (lower NLS) enlarges it further (higher NLS = smaller circuit); the one allowed retune toward smaller (NLS 0.4) also failed the in-run gate (KL 0.214) and its side-job knockout KL is 2.317; researcher decides. Nothing is launched.

The rule is evaluated on eval 2 alone until an eval 5 directory is given (`--eval5-dir`).

The rule's honest-answer rows: `variants` (the eval 2 variant rows only; the H and F test sets are informational); orchestrator ruling 2026-10-13: spec rows only; researcher may flip. Set with `--honest-rows {variants,all}`.

| condition | rule | D | F | result |
| --- | --- | ---: | ---: | --- |
| deception drop | F >= 0.8 x D; threshold 0.800 | 1.000 | 1.000 | PASS |
| honest-answer drop | F <= D on every rule row (`variants`) |  |  | FAIL |
| &nbsp;&nbsp;honest_instruction (D data) | F <= D | -0.682 | -0.680 | FAIL |
| &nbsp;&nbsp;no_pressure (D data) | F <= D | -0.777 | -0.788 | PASS |
| &nbsp;&nbsp;H test set (informational: not in the rule) | F <= D | 1.000 | 1.000 | F <= D |
| &nbsp;&nbsp;F test set (informational: in-distribution for F; not in the rule) | F <= D | 0.996 | 1.000 | F > D |
| collateral | F <= D (wikitext KL/token (eval 2)) | 0.327 | 4.265 | FAIL |
| outside nulls | knockout accuracy < null 5th percentile, for D and for F | 0.000 vs p5 0.440 | 0.000 vs p5 0.164 | PASS |

(c) gate on F's knockout: wikitext KL/token 4.265 vs gate 0.66 (FAILS); distinct-2 knockout/full 1.142 vs collapse below 0.5 [threshold not pre-registered; orchestrator choice 2026-10-13, researcher to confirm] from eval 2 wikitext continuations (word bigrams) (not degenerate). Wikitext KL/token of every knockout: D 0.327 (passes), H 2.784 (FAILS), F 4.265 (FAILS) (gate 0.66).

Rule order: (c) first: F's knockout fails the wikitext KL gate (KL/token > 0.66) or its generations are degenerate (distinct-2 collapse) [order not pre-registered; orchestrator choice 2026-10-13, researcher to confirm]; (a) when all four conditions pass: deception drop, honest-answer drop, collateral, both knockouts outside their nulls; (b) otherwise.

## Paired table

Drop = full-model accuracy minus knockout accuracy on the cell's own labels: the deception drop on D data (deceptive labels, `LABEL_CONVENTION`), the honest-answer drop on H and F data (honest labels). A knockout is outside its null when its accuracy is below the null's 5th percentile.

Null: size-matched random circuits drawn layer by layer in fine units: the same number of heads per layer, the same attention neurons placed inside the drawn heads (`uniform` allocation), and the same MLP units per layer; n = 20, knockout granularity `finest`, blocks held fixed (evaluation/masks.py `sample_random_masks`).

### D data `far` (deception drop; not paired with F data)

| circuit | circuit-alone acc | intact acc | knockout acc | drop | null p5 / p50 / p95 | outside null | wikitext KL | flip audit | paired |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |
| D | 0.969 | 1.000 | 0.000 | 1.000 | 0.440 / 0.872 / 0.999 | yes | 0.327 | content-driven flip; separable | not paired with F data |
| H | 0.474 | 1.000 | 0.000 | 1.000 | 0.297 / 0.766 / 0.949 | yes | 2.784 | content-driven flip; separable | not paired with F data |
| F | 0.733 | 1.000 | 0.000 | 1.000 | 0.164 / 0.638 / 0.977 | yes | 4.265 | content-driven flip; separable | not paired with F data |

### H data `far_honest` (honest-answer drop; unpaired (disjoint instances))

| circuit | circuit-alone acc | intact acc | knockout acc | drop | null p5 / p50 / p95 | outside null | wikitext KL | flip audit | paired |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |
| D | 0.265 | 1.000 | 0.000 | 1.000 | 0.544 / 0.904 / 0.985 | yes | 0.327 | content-driven flip; separable | unpaired (disjoint instances) |
| H | 0.967 | 1.000 | 0.000 | 1.000 | 0.194 / 0.774 / 0.968 | yes | 2.784 | content-driven flip; separable | unpaired (disjoint instances) |
| F | 0.943 | 1.000 | 0.000 | 1.000 | 0.146 / 0.644 / 0.842 | yes | 4.265 | content-driven flip; separable | unpaired (disjoint instances) |

### F data `far_nopressure` (honest-answer drop; NOT paired: 98% honest-split instances)

| circuit | circuit-alone acc | intact acc | knockout acc | drop | null p5 / p50 / p95 | outside null | wikitext KL | flip audit | paired |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |
| D | 0.290 | 1.000 | 0.004 | 0.996 | 0.626 / 0.904 / 0.990 | yes | 0.327 | content-driven flip; separable | NOT paired: 98% honest-split instances |
| H | 0.950 | 1.000 | 0.000 | 1.000 | 0.226 / 0.812 / 0.975 | yes | 2.784 | content-driven flip; separable | NOT paired: 98% honest-split instances |
| F | 0.956 | 1.000 | 0.000 | 1.000 | 0.234 / 0.732 / 0.872 | yes | 4.265 | content-driven flip; separable | NOT paired: 98% honest-split instances |

### Honest-answer drop on the eval 2 variant rows

Full / knockout accuracy on the cell's labels, then the honest-answer drop. On D data the labels are deceptive, so the honest-answer drop is knockout minus full; on H data it is full minus knockout. F data has no variant rows: the dataset already is the no-pressure variant.

| circuit | honest_instruction on D data | no_pressure on D data | honest_instruction on H data | no_pressure on H data | honest_instruction on F data | no_pressure on F data |
| --- | --- | --- | --- | --- | --- | --- |
| D | 0.839 / 0.157 -> -0.682 | 0.871 / 0.094 -> -0.777 | 0.957 / 0.048 -> 0.909 | 0.994 / 0.016 -> 0.978 | n/a (condition is nopressure) | n/a (condition is nopressure) |
| H | 0.839 / 0.172 -> -0.667 | 0.871 / 0.090 -> -0.781 | 0.957 / 0.030 -> 0.927 | 0.994 / 0.005 -> 0.989 | n/a (condition is nopressure) | n/a (condition is nopressure) |
| F | 0.839 / 0.159 -> -0.680 | 0.871 / 0.083 -> -0.788 | 0.957 / 0.031 -> 0.926 | 0.994 / 0.005 -> 0.989 | n/a (condition is nopressure) | n/a (condition is nopressure) |

## Overlap

| pair | Jaccard heads | shared heads | heads A / B | Jaccard fine units |
| --- | ---: | ---: | --- | ---: |
| D/H | 0.430 | 34 | 48 / 65 | 0.185 |
| D/F | 0.340 | 33 | 48 / 82 | 0.166 |
| H/F | 0.652 | 58 | 65 / 82 | 0.407 |

## Delta cells (on D data)

| delta | expr | granularity | heads | ablated fine units | knockout acc | drop | null p5 / p50 / p95 | outside null | flip audit |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| D_minus_F | `D - F` | head (primary) | 15 | 920 | 0.504 | 0.496 | 0.939 / 1.000 / 1.000 | yes | content-driven flip; separable |
| D_minus_F | `D - F` | leaf | 47 | 2815 | 0.375 | 0.625 | 0.968 / 0.996 / 1.000 | yes | positional default; separable |
| D_and_F | `D & F` | head (primary) | 33 | 7569 | 0.000 | 1.000 | 0.394 / 0.819 / 0.989 | yes | content-driven flip; separable |
| D_and_F | `D & F` | leaf | 33 | 2621 | 0.000 | 1.000 | 0.752 / 0.981 / 1.000 | yes | content-driven flip; separable |
| F_minus_D | `F - D` | head (primary) | 49 | 7312 | 0.155 | 0.845 | 0.677 / 0.983 / 1.000 | yes | content-driven flip; separable |
| F_minus_D | `F - D` | leaf | 82 | 10365 | 0.006 | 0.994 | 0.474 / 0.883 / 0.988 | yes | content-driven flip; separable |
| D_minus_H_minus_F | `D - H - F` | head (primary) | 11 | 610 | 0.775 | 0.225 | 0.982 / 1.000 / 1.000 | yes | content-driven flip; separable |
| D_minus_H_minus_F | `D - H - F` | leaf | 45 | 2274 | 0.593 | 0.407 | 0.875 / 0.994 / 1.000 | yes | positional default; separable |
| H_minus_D_minus_F | `H - D - F` | head (primary) | 3 | 225 | 0.988 | 0.012 | 0.998 / 1.000 / 1.000 | yes | content-driven flip; separable |
| H_minus_D_minus_F | `H - D - F` | leaf | 63 | 3477 | 0.862 | 0.138 | 0.976 / 0.999 / 1.000 | yes | content-driven flip; separable |
| F_minus_D_minus_H | `F - D - H` | head (primary) | 21 | 1344 | 0.588 | 0.412 | 0.667 / 0.998 / 1.000 | yes | content-driven flip; not separable |
| F_minus_D_minus_H | `F - D - H` | leaf | 80 | 5463 | 0.622 | 0.378 | 0.845 / 0.990 / 1.000 | yes | positional default; separable |

## Caveats

- atomic knockouts saturate, so the eval 2 deception-drop condition is trivially satisfied and cannot tell D from F; the rule still evaluates it on eval 2 (eval 5's deception drop, when given, is informational and not in the rule). Knockout accuracy on D data: D 0.000, F 0.000, both below 0.02.
- variant rows read the ablation source; condition non-discriminating at n=1000 (honest_instruction (D data): D -0.682, H -0.667, F -0.680, |F - D| 0.002 < SE 0.016; no_pressure (D data): D -0.777, H -0.781, F -0.788, |F - D| 0.011 < SE 0.013). SE is the binomial standard error of the difference of D's and F's knockout accuracies on the row.
- Variant rows (honest_instruction, no_pressure) of FAR and SDR runs at NLS levels other than 0.3 are suspect: they were computed on mixed-wording prompts before the ticket 01 drift fix. Compare this suite's rows only with rows computed after it.
- H column unpaired: the Honest Twin's instances are disjoint from the deceptive ones (a given instance either lied or it did not), so cells on H data are not instance-paired with D or F data.
- Honest-answer drops on the H and F test sets are informational: the F test set is in-distribution for F; not in the rule (honest-answer rows: `variants`, orchestrator ruling 2026-10-13: spec rows only; researcher may flip).
- EVAL 5 absent: the rule is evaluated on eval 2 alone (wikitext KL as the collateral cost; distinct-2 from eval 2's three greedy wikitext continuations). Pass --eval5-dir to add the benchmark columns.
- F trained on 99% honest-split instances (train 149/150); validation 100% (150/150), test 98% (492/500): the tagged fallback subset of the nopressure build.
- F data NOT instance-paired with D data: 98% of the F test set comes from the honest split.
- F oversized at NLS 0.3 (+71% heads, +139% fine units); retune to 0.4 failed the in-run gate (KL 0.214, misses kl_div; still +50% heads, +97% fine units); carried nls0.3.
- F trained with --deception-margin-loss 0.7 (D: not recorded in its config.json).

## Decisions taken in applying the rule

- The (c) gate is checked before (a): an incoherent F knockout trivially lowers deception, so 'uninformative' pre-empts 'format explains it' (not pre-registered; orchestrator choice 2026-10-13, researcher to confirm).
- F's honest-answer drop must be <= D's on EVERY rule row. Mode `variants` (default): the rule rows are honest_instruction and no_pressure on D data (the eval 2 variant rows the spec names); the H and F test sets are informational. Mode `all` adds the H and F test sets to the rule (orchestrator ruling 2026-10-13: spec rows only; researcher may flip).
- Collateral is the reference-NLL rise (eval 5, knockout minus full, mean over the benchmark datasets both D and F have, with the sm and lb groups merged; a dataset only one of them has is excluded and named) when an eval 5 directory is given, else the wikitext KL/token of eval 2.
- Distinct-2 collapse = F's knockout distinct-2 below 0.5 x the full model's: eval 5 `distinct_n` (mean over all of F's datasets) when given, else word bigrams of eval 2's three greedy wikitext continuations (not pre-registered; orchestrator choice 2026-10-13, researcher to confirm).
- Outside the null = knockout accuracy strictly below the null's 5th percentile.
- The deception-drop and outside-null conditions are evaluated on eval 2 (task accuracy and its task-side null) even when --eval5-dir is given; eval 5 enters the rule only through the collateral condition (reference-NLL rise) and the distinct-2 gate. Eval 5's deception drop is printed as an informational row, not in the rule (not pre-registered; orchestrator choice 2026-10-15, researcher to confirm).
- A condition whose inputs are missing is reported as missing; the verdict is then undecided unless the (c) gate fires or another condition already fails, which rules (a) out and gives (b). A missing (c) gate input (F's wikitext KL or distinct-2) always leaves the verdict undecided unless the other gate input already fires: (c) pre-empts both (a) and (b).

## Missing

Nothing missing.
