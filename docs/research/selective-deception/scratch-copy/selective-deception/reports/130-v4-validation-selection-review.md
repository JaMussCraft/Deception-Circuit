# Independent v4 validation and prospective selection review

October21,2026. **PASS. No blocking findings.** The two proposed finalists follow the frozen selection rule. The native assessment's numerical criterion is satisfied by the joint-preservation finalist; execution becomes eligible only after root freezes the reviewed finalists, as the prospective execution rule requires. No GPU/model execution, job action, source edit or heldout outcome read was performed by this review.

Reviewed completed `audit/summary.json` and supplementary `readouts/`, frozen protocol and `native-assessment-execution-rule.json`. Independently recomputed eligibility/selection from all96validation rows and H losses/gains directly from manifest labels and baseline/checkpoint argmax arrays. Both runs have3072loss records and48validations at the exact64-update cadence; baseline metrics agree. The prior full technical audit remains the evidence for checkpoint/runtime integrity; this review independently checked the selected checkpoint/export/manifest/run-identity file SHAs against the proposal.

## Selection

| Tier | Run/update | Removed heads | D surrogate reduction | H lost/gained | WT PPL rise | WT KL |
|---|---|---:|---:|---:|---:|---:|
|Joint preservation|init10/768|23|67.1681%|0/3|2.7715%|.04133672|
|WT only|init10/832|30|70.1231%|3/3|3.4380%|.04911681|

There are two joint-eligible rows, both init10, and12WT-eligible rows:five init1/seven init10. Neither eligible set reaches90% or95%, so the correct rule is strongest constrained suppression, then fewer heads, earlier update and fixed run order. Each winner has a unique best loss within its tier; ties do not affect this result. The masks are distinct, with the23-head support strictly contained in the30-head support. Both slots are filled by constrained-tier winners; no unconstrained fallback is appropriate.

The30-head finalist is **not jointly preserving**: its unchanged net H-correct count86conceals three lost baseline-correct examples and three gains. The23-head finalist preserves all86baseline-correct H examples and gains three, giving89correct. Joint preservation here means the preregistered argmax/WT criteria, not unchanged H distributions, flawless honesty or general utility preservation.

Verified proposal export file SHA256s:

- init10/768: `e203d83e5936272af46afb71950f2d4123c7f17d65136c84ff3ebb1b7384ccbe`.
- init10/832: `746ceb37633eafb69d3137c6e559616f75d987f5c2cde3451abccf7f6ef86f75`.

Reviewed audit SHA256: `1c87dfa489269af2e10901649fad2083324a01a88f050753d43f860860380395`. Reviewed native-rule SHA256: `2eecfbf1a60759b107336b94fa3550ad7603a82f645293514d57c28486d5e5fe`.

## What changed scientifically

The initialization contrast produced a useful validation finding: init10 has an early23-head checkpoint with slightly stronger suppression than oldallW28(67.17%versus65.27%), fewer heads, zero versus five baseline-H losses, and lower WT PPL/KL that now pass both thresholds. Its first nonempty deterministic mask appears at384updates versus704for init1. This supports the proposed optimization diagnosis in this fixed-seed contrast; it does not establish stability across seeds, global optimality or deception-specific localization.

Longer training does improve the surrogate, but it does not improve the selected preservation-constrained finalists:

|Run|Update|Heads|D reduction|H lost/gained|WT PPL rise|WT KL|
|---|---:|---:|---:|---:|---:|---:|
|init1|1536|28|65.27%|5/4|5.56%|.06963|
|init1|3072|61|74.33%|6/9|5.47%|.08892|
|init10|1536|58|76.74%|3/9|4.50%|.07524|
|init10|3072|92|85.70%|3/20|6.64%|.10083|

All four matched-horizon rows fail WT limits, including init10/1536which passes PPL but failsKL. Across the entire grid the maximum surrogate reduction is86.67%at init10/3008, with92heads,4H losses and WT PPL+7.44%/KL.10663. **No90%or95%target is reached anywhere.** Larger net H accuracy at late checkpoints must not conceal retained individual H losses. The useful finalists are early stopping points under the unchanged prospective rule, not evidence that3072steps itself yields the best balanced mask.

Supplementary readouts support a real output-distribution change beyond the nonlinear scalar: for the23-head finalist, D-stream D/H argmax counts are30/89, its mean D-minus-H margin is−.87815 and approximate mean D probability is.34462, compared with oldallW28's37/82,−.63550 and approximately.37400. For the30-head finalist the D argmax counts remain30/89 despite a better surrogate; mean margin/probability continue to change. Probability estimates are inverse transforms of saved per-pair surrogates, not newly measured exact probabilities; the selected rows have no inferred capped examples. None of these are native free-generation deception rates.

## Prospective native gate and limits

The frozen rule requires an already-frozen finalist with reduction>=.6526523470225304, zero baseline-H losses, WT meanNLL increase<=log(1.05) and KL<=.05. Init10/768meets every numerical requirement: reduction.6716811928203097, zero losses, PPL+2.7715%, KL.04133672. Init10/832fails the H-loss part. Once root freezes exactly the reviewed finalists, the one-shot native-only assessment may proceed under its separate technical/reservation gates, max0.5GPUh and fixed intact/oldD69/oldallW28/two-finalist conditions. This is not permission to resample cases, tune masks or revise the gate from future outcomes.

All selection used increasingly exposed development SDR/WT validation, with96checkpoints and one seed per initialization. The result is exploratory optimization evidence; fresh native assessment remains a small instructed-lying transfer comparison rather than strategic-deception validation. The separate cleaner-data effort is untouched. Preserve failed frontiers and matched horizons, distinguish expected stochastic from deterministic removed counts, and do not claim minimality, generalization or broad collateral safety from this result.
