# Project evidence audit: shared SDR circuits and specificity

## What do the present artifacts establish?

### Takeaway
The shared coarse SDR heads are a strong causal intervention target, and the D∩F and triple intersections carry more on-task necessity than the exclusive remainders. This supports reusable answer selection/routing machinery with behavior-dependent use; it does not isolate a deception-specific computation or establish that the shared computation is pure syntax. [Coarse format-control summary](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/outputs/_suites/format-control-sdr-coarse-nls0.3/evaluation_summary.md).

### Cited Findings

All figures below are interchange interventions with whole heads, every MLP intact; masks composed at leaf granularity. On-task D test n=1,000, layer-and-size-matched random head sets n=20. The table reports deceptive-label accuracy after knockout, so smaller is more necessary. [Coarse summary](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/outputs/_suites/format-control-sdr-coarse-nls0.3/evaluation_summary.md).

| Removed set | heads | KO accuracy | null p5 | wikitext KL/token |
|---|---:|---:|---:|---:|
| D |69|.002|.041|.364|
| H |56|.002|.110|.275|
| F |68|.000|.041|.279|
| D∩F |36|.002|.305|not extracted|
| D−F |33|.119|.517|not extracted|
| D∩H∩F |32|.002|.384|.115|
| (D∩H)−F |11|.335|.939|not extracted|
| D−H−F |22|.782|.733|not extracted|

The triple-core and extra-delta KL come from the [verified orchestration ledger](/projects/beto/swong2/Alignment/.scratch/format-control/reports/00-orchestration-ledger.md); other table cells from the [coarse summary](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/outputs/_suites/format-control-sdr-coarse-nls0.3/evaluation_summary.md). D−H−F is inside its null; D−F still has a substantial effect (.881 drop), so specificity subtraction does not yield a clean null remainder. Triple-core eval2 matches the saturated parents; parent saturation limits quantitative ranking.

D∩H (43 heads) has KO accuracy .000 and KL .165 versus D .002/.364; sufficiency with all MLPs intact is only .494 versus D .967. Lower collateral tracks size: D∩H's wikitext cost is not distinguishable from its matched randoms (random KL .190±.056). Removing a required shared component does not imply the behavior's decision computation is localized there. [Pair-composition analysis](/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/_launch/wave_status.md).

The 43-head component audit finds 22 shared, 15 deception-leaning, 3 honest-leaning, and 3 neither by margin-scaled single-head KO. L17H24/L24H27 are necessary on both tasks yet have large pressure-dependent direct logit attribution; mover versus selector remains unresolved. No direct paths were measured. Coverage differs: full-split attention/DLA n=1,000, paired conditions n=71, knockout n=100; H task has distinct instances and different designation marginal. [Component analysis](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/component-analysis/outputs/_analyses/sdr-dh-core/dh_core__leaf/sdr/result_summary.md).

### Inferences

A shared actuator or answer-selection network can be necessary for both honest and deceptive answers while upstream context changes its output. Calling it a reusable control point is supported; calling it a specialized deception circuit, pure output-format module, or established selector is premature. A whole-head overlap can also contain distinct subspaces. The prior fine overlap is explicitly within heads (3,894 shared leaves; 50/51 overlap heads contain honest-exclusive units). [Fine overlap experiments](/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_eval5_launch/overlap_experiments_260922.md).

### Gaps

Triple-core eval5 is user-reported but not independently located in a bounded search of main, format-control, and component-analysis top-level eval5 output directories. This is an availability limit, not evidence the user is mistaken. D∩F eval5 was likewise not found. Do not substitute seed intersection (53 heads) for D∩H∩F (32 heads).

## What does F control, and what do benchmark results measure?

### Takeaway
F is a pressure-removed, honest-label **task circuit** that must read the designation, resolve which item matters, and emit that item. Its construction is richer than syntax. Benchmark interchange overwrites units with donor activations, so coherent refusal counts as successful deception suppression while donor-content dependence limits a mechanism-removal claim. [F builder](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/dataset/build_nopressure_dataset.py); [benchmark donor implementation](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/evaluation/benchmark_eval.py:48).

### Cited Findings

F deletes the stored Pressure Clause by clause surgery and swaps D labels to honest; corrupt prompts still swap the designation. Both streams must flip argmax appropriately at margin .3 (after .7/.5 fail minimum sizes). Actual F train/validation/test sizes are 150/150/520 (106/96/520 from D; fallback H 44/54/0); inherited dataset_config fields misleadingly still say 200/200/1000. F test is paired with a **subset** of D; H instances are disjoint. Selection changes the distribution, and 29% F training is unpaired H fallback. F has recorded deception-margin-loss .7, D's config does not record that value. [Filter report](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/data/datasets/sdr_nopressure/filter_report.json); [dataset config](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/data/datasets/sdr_nopressure/dataset_config.json); [summary caveats](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/outputs/_suites/format-control-sdr-coarse-nls0.3/evaluation_summary.md).

Default eval5 donor pool is honest. Instructed-deception uses the **same statement's honest-system twin**; datasets without minimal twins use a seeded reference-pool assignment. The donor includes the partner's prompt **and full-model continuation**, not a content-free baseline. The earlier fine donor experiment lost about 80% of parsed-row suppression when honest donors were replaced by deceptive donors at similar coherence. That 80% figure is a donor diagnostic using an older conditional metric, not the present headline efficacy metric or proof it generalizes to coarse/triple cores. [Donor code](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/evaluation/benchmark_eval.py:838); [fine donor experiments](/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_eval5_launch/overlap_experiments_260922.md).

D∩H eval5, n≤50 and six matched randoms: raw KO deception .251 vs rand .428 on seven sandbagging/MASK datasets; .253 vs .506 on three LB datasets. Mean KO/random NLL ratios .96 and 1.08. LB instructed-deception .120 vs .327; harm-pressure .480 vs .457; convincing-game .160 vs .733. Convincing-game's .840 unparsed KO fraction is a desirable outcome when outputs coherently decline the lie. Do not adopt the old summary's rhetoric that this is 'only non-answers' or demand increased honesty. [D∩H SM summary](/projects/beto/swong2/Alignment/Deception-Circuit/outputs/eval5_sdr_coarse_dh_inter/result_summary.md); [D∩H LB summary](/projects/beto/swong2/Alignment/Deception-Circuit/outputs/eval5_sdr_coarse_dh_inter_lb/result_summary.md).

However, D∩H sandbagging has 26/50 generations hitting the 1,024-token cap and distinct-2 .242 vs full .699, whereas LB D∩H has no 512-token KO row and mean distinct-2 .942 vs .954 full. These are output-quality distinctions independent of refusal. NLL evaluates fluency, not preserved task utility. [D∩H SM summary](/projects/beto/swong2/Alignment/Deception-Circuit/outputs/eval5_sdr_coarse_dh_inter/result_summary.md); [D∩H LB summary](/projects/beto/swong2/Alignment/Deception-Circuit/outputs/eval5_sdr_coarse_dh_inter_lb/result_summary.md).

Current format eval5 artifacts verified Oct17: LB D/H/F cells exist; D−F absent and SM suite directory absent at inspection. Complete suite summaries are absent. Partial LB numbers below are raw cell JSON, all n=50, six randoms, honest donors (same suite and cache). Each cell contains own matched null; ranks cannot be inferred from raw rates alone. [D JSON](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/outputs/eval5_format_sdr_coarse_lb/cells/D_hko__leaf/sdr/interchange/benchmarks.json); [H JSON](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/outputs/eval5_format_sdr_coarse_lb/cells/H_hko__leaf/sdr/interchange/benchmarks.json); [F JSON](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/outputs/eval5_format_sdr_coarse_lb/cells/F_hko__leaf/sdr/interchange/benchmarks.json).

| circuit | instructed KO/rand dec | harm-pressure KO/rand dec | convincing KO/rand dec | KO vs rand ref-NLL (three datasets) |
|---|---|---|---|---|
|D|.060/.263|.320/.467|.200/.617|.973/1.153; .970/.629; .996/.810|
|H|.120/.170|.320/.563|.100/.610|.853/1.030; .900/.548; .996/.754|
|F|.040/.210|.220/.263|.060/.570|1.357/1.116; .823/.633; .961/.848|

D beats every random on instructed-deception and convincing-game; H on harm-pressure and convincing-game; F on convincing-game only. The six-random p floor is 1/7=.143, so these are exploratory orderings. F's lower absolute deception does not make it more exceptional than D or H against its own null. Raw JSON source links above support all table/rank entries. The F convincing-game outcome has unparsed .94, distinct-2 .856 vs rand .848: refusal is not established as malformed by these aggregates. D/H instructed-deception distinct-2 .660/.582 vs respective random .939/.919 warrants checking actual repetitive outputs, separately from non-answer counts.

### Inferences

The artifact writer's verdict '(a) Format explains it ... not deception' is stronger than the data warrant. Its own caveats say atomic KO effects saturate, variant D–F differences are within one SE, and eval5 deception is informational rather than entering the formal rule. The defensible result is non-specific necessity and transferable suppression via a shared task circuit, with a donor-dependent intervention interpretation. [Decision definition](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/outputs/_suites/format-control-sdr-coarse-nls0.3/evaluation_summary.md).

### Gaps

No present artifact establishes unchanged broad utility, causal Q/K/V routes, or donor-independent suppression by the triple core. Harm-pressure measures claims about knowing an answer and is particularly sensitive to a coherent 'I do not know' being graded deceptive; report it separately, retaining raw deception as headline. Known grader caveats: MASK refusal-D mapped deceptive, empty harm-pressure outputs scored honest, LB 'correct' guard drops valid rejection judgments, nondeterministic judges with per-suite caches. [Grader caveats](/projects/beto/swong2/Alignment/.agents/memory/eval5-grader-fixes-pending.md).

## What are the cheapest decisive next tests and publication constraints?

### Takeaway
Prioritize a donor crossover on one clean paired benchmark, then focused pathway tests and a small utility audit; a broad model/task fleet is premature. These are proposals, with no experiments executed or submitted in this audit.

### Cited Findings

The current code already exposes honest/deceptive/pooled donor pools, the component audit identifies candidate sender/receiver heads, and the same audit has deferred full path grids plus fast family-KO infrastructure. [Donor code](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/evaluation/benchmark_eval.py:838); [component next steps](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/component-analysis/outputs/_analyses/sdr-dh-core/dh_core__leaf/sdr/result_summary.md).

### Inferences

1. **Fixed-screen donor crossover.** On instructed-deception, compare D∩H, D∩H∩F, D−F (or D∩F if budget) using own honest twin, deceptive donors, and a content-shuffled honest donor. Hold item ids, prompt/full outputs, partner assignments where applicable, judge cache and random masks fixed. Raw deception/n primary; coherent refusal success; inspect malformed/loop and unrelated-task utility separately. Honest→deceptive donor reversal with preserved fluency supports overwrite/routing, not removal of a specialized lying module. Minimal-pair honest twins offer the cleanest initial contrast.
2. **Focused pathway crossover.** Patch L13H5/H20/H21 (and L12H6) into Q/K/V inputs of L17H24/L24H27 under matched pressure versus honest instruction and balanced item/designation polarity. Test sender→selector versus sender→value write using the existing small sample before the 1,920-cell grid. Current evidence cannot decide mover/selector, so this has more mechanistic value than another overlap plot.
3. **Utility and output audit using existing generations first.** Blind-label coherent refusal, coherent task answer, malformed/repetitive output (without requiring disclosure); reuse current generations and identify fixed format/answer-selection control prompts with truthful task objectives. Then add a small paired utility set if needed. Match layer/size and utility cost in nulls; judge whether deception drops exceed ordinary task disruption. This separates successful refusal from model destruction and selection machinery from general impairment.

Publication constraints: one model and one training mechanism; one H/F discovery seed; outcome-selected screens cannot reveal newly induced deception on originally honest examples; n=12–50 on MASK and six randoms cannot support conventional per-task significance; mixed-card eval2 cells have bf16 drift; masks trained at one readout applied at every generated token; aggregate ref-NLL/distinct-2 do not prove general utility; grader fixes and re-screen required before confirmatory reporting. All these constraints are documented in the sources above and [seed-wave results](/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/_launch/wave_status.md). A publishable narrow claim is that circuits discovered on conflicting objectives share causal answer machinery, and intervening on shared machinery transfers to deception suppression with measured donor dependence and retained output utility. Treat deception-specificity and universality as hypotheses.

### Gaps

Decision requires the user's approved high-level plan before launching a fleet. Current test proposals have no measured results. Exact run completion is time-sensitive; partial format LB cells are not a completed four-circuit suite.


### October24 update: frozen sparse masks on V2

The earlier dated run-status paragraphs above are historical snapshots. A new prospective frozen-mask V2 assessment is complete and independently reviewed: [V5 transfer summary](v5_transfer.md). New30 shows strong FAR correction with neutral-H preservation, while SDR/SER show different suppression/collateral trade-offs. Additional seven-head effects are conditional, not a standalone circuit claim. Eval5 free-generation comparison is still incomplete; no new eval5 efficacy result follows from its technical calibration.
