# V7 analysis preparation

Prepared CPU-only analysis, without reading actual V7 outcome artifacts. No model, GPU, paid API, git, notebook execution, mask selection or new experimental contrasts were used.

`summarize.py` copies V6's strict JSON parsing, scalar consistency checks, raw tables and linear-interpolated percentile-bootstrap style into a standalone script. The V7 bootstrap is exactly 10,000 draws with seed 1729. It samples the sixteen scenario indices once per draw; each index carries all four variants and seven conditions. D−I is formed within scenario before bootstrapping. Neither 64 case variants nor technical repeats are independent observations.

Frozen estimands are New30 final-margin minus prompt-margin; release-minus-New30 restoration at both supports and prompt-minus-final restoration; intact-minus-single drop at both supports and prompt-minus-final single drop. All seven estimands retain raw D/I/H/F and paired D−I summaries, individual scenario values and four descriptive strata. No inference thresholds, adaptive contrasts, mask ranks, exclusions or normalizing by token count are added.

The main-only reader first checks `completion.json` for exactly 448/448 rows and bound artifact hashes before parsing any row data. It then checks frozen manifest/design/selection identities, sixteen complete balanced scenario clusters, one row per case/condition, label and donor joins, selected heads, right-aligned mapping inventory, finite metrics, signs/probability bounds, native/fp32 argmax agreement, controls coverage and 64 repeated donor capability records. Independent runtime/raw-artifact audit remains required before scientific interpretation; this reader does not replace that audit.

The output JSON retains all raw causal and capability rows, condition-level probabilities/KL/margins/choice counts and strata, native numerical margins and native-minus-fp32 differences, mapping coverage and individual maps, unique versus repeated donor counts, capability failures, and every native/fp32 first-choice transition with case ID. Failures remain in the population. Choices are first-token argmaxes; an `other` answer is never automatically called a coherent refusal.

The standalone `paired-position-effects.png` and `.svg` show each of sixteen scenario effects, means and descriptive bootstrap intervals for the position increments and release difference, including paired D−I. Figure generation and label readability have been tested and visually inspected on synthetic data; no actual-results figure has been produced.

Validation command (both interpreters passed 6 tests):

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python .scratch/selective-deception/component-analysis-v7/analysis-tests/test_analysis.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 .scratch/selective-deception/component-analysis-v7/analysis-tests/test_analysis.py
```

Tests independently verify arithmetic/signs for primary and secondary contrasts, a known random-stream percentile interval, perfect paired D/I heterogeneity cancellation, duplicate-key/nonfinite JSON rejection, complete synthetic schema ingestion, missing/duplicate/nonfinite/sign/mapping rejection, the completion gate before outcome reads, artifact tampering, missing/false/nonzero exact controls, transition labels, and PNG/SVG rendering. Runtime schema is coordinated with the production source: nested baseline and two per-support New30 control sets are mandatory for main. Production uses right padding, so its tensor position indices equal actual ordinals; explicit recipient/donor ordinals are also checked and retained. Root/independent post-smoke audit owns historical V6 anchor reproduction before interpretation.

After root confirms audited main completion, use a fresh output directory:

```bash
/u/swong2/.conda/envs/mgnp/bin/python .scratch/selective-deception/component-analysis-v7/summarize.py --run-dir MAIN_DIR --output-dir NEW_ANALYSIS_DIR
```

Reports215 and the shared `v7_positions.md` draft are intentionally deferred until that instruction and complete data. Interpretation must preserve exposed-panel status, positional rather than semantic alignment, matched D/I coverage versus different F alignment, contextual natural release, the total incremental earlier-position effect including nonlinear interactions, and first-token/readout scope.

Independent prospective review caught a grouping bug before outcome use: construction strata now use only `designation_polarity` and `item_polarity`, while preserving equality of full within-scenario metadata. A regression reads actual frozen case metadata/token IDs with entirely synthetic margins and verifies four cells × four scenarios for every contrast; pressure/template metadata never expands the construction-cell denominator.
