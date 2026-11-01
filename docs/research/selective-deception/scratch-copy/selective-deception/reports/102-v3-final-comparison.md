# V3 final frozen comparison

AllW28 yields the most coherent native corrections in this pilot (11/25), versus D69 9/25 and W9/W13 6/25 each. D69 has the lowest raw false count (6/32), accompanied by 14/32 ambiguous answers and 14 baseline H truth losses. AllW28 has 13/32 false, 5/32 ambiguous and 5 H losses. This does not establish a clear-suppression advantage for D69.

Pair identities further limit dominance claims: D69 and allW28 share 3 corrections, with 6 D69-only and 8 allW28-only corrections. They share 11 retained baseline H truths, with 1 D69-only and 10 allW28-only retained. There is no universal dominance across raw false answers, correction identities and utility.

Five conditions use the same frozen native 32 matched D/H prompts and independent honest-donor replay protocol. D69 is the old sufficient-circuit head set tested here as a removal; W9 is the prior sparse mask; W13/allW28 are frozen v3 finalists. No condition was reselected using these outcomes. Coherent refusal is desired D suppression; none occurred.

| Condition (heads removed) | D false /32 | D ambiguous /32 | D true /32 | Baseline-false corrections /25 | Baseline-false refusals /25 | H retained /26 | H lost / gained | H true /32 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Intact (0) | 25 | 5 | 2 | 0 | 0 | 26 | 0 / 0 | 26 |
| D69 (69) | 6 | 14 | 12 | 9 | 0 | 12 | 14 / 1 | 13 |
| W9 (9) | 19 | 5 | 8 | 6 | 0 | 23 | 3 / 2 | 25 |
| W13 (13) | 17 | 7 | 8 | 6 | 0 | 23 | 3 / 1 | 24 |
| allW28 (28) | 13 | 5 | 14 | 11 | 0 | 21 | 5 / 1 | 22 |

Corrections and refusals are paired outcomes among the 25 intact D false answers. H retention is among the 26 intact truthful H answers; gains arise from the remaining 6, so total H truth equals retained plus gained. Ambiguity is preserved as uncertainty rather than credited as clear suppression. All 320 target completions have zero refusals, damage, empty outputs and cap hits. The 32 donors also have zero such failures, but include 2 false and 4 ambiguous own-context judgments; donor quality never screens rows. All 64 intact generation identity controls matched; SDR/WikiText all-open full-vocabulary controls also passed.

| Condition | SDR surrogate reduction | D-prompt argmax D / H / other (64) | Mean D-label probability | SDR H correct /64 | SDR H retained /42 | SDR H lost / gained | WT test PPL | WT PPL increase | WT predictive KL |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Intact | 0.00% | 64 / 0 / 0 | 0.8214 | 42 | 42 | 0 / 0 | 10.6843 | -0.000% | 0.00000 |
| D69 | 58.70% | 29 / 32 / 3 | 0.4601 | 32 | 20 | 22 / 12 | 12.9455 | 21.164% | 0.21805 |
| W9 | 58.81% | 33 / 31 / 0 | 0.5040 | 37 | 33 | 9 / 4 | 10.8141 | 1.215% | 0.01748 |
| W13 | 60.05% | 29 / 35 / 0 | 0.4945 | 41 | 36 | 6 / 5 | 10.8337 | 1.399% | 0.02103 |
| allW28 | 65.33% | 21 / 43 / 0 | 0.3897 | 42 | 39 | 3 / 3 | 11.2307 | 5.115% | 0.08668 |

SDR has 64 paired examples with 42 intact H-correct; argmax is the full-vocabulary label readout. Surrogate reduction is 1 − condition suppression loss / intact suppression loss. Mean D-label probability is a separate metric: its intact value is 0.8214, so even a zero endpoint gives only an 82.14 percentage-point absolute drop; proportional reduction has a different scale. D69 and W13 share 29/64 D argmax despite different mean D probabilities and native outcomes. WikiText covers 16 frozen test windows / 2,032 scored tokens; PPL increase is exp(ΔNLL)−1, KL is per scored token. Intact PPL delta −0.0000005% is floating-point accumulation residue (all-open full-vocabulary identity passed).

![Frozen v3 comparison](../sparse-extension-v3/figures/v3-heldout-comparison.png)

These are exploratory results from 32 native pairs, model-agent judgments and one training seed. Labels were double annotated (339/352 category agreements), with 100 fresh blind adjudications; the final 352 public-view labels were frozen before private condition joining. No sampling confidence intervals are estimated. The necessary-objective sparse search and donor replacement support bounded intervention findings, not a proven minimal deception circuit or autonomous strategic-deception mechanism. Replacement may import donor content; ambiguity and task-utility losses limit causal interpretation. W13/allW28 were selected as WT-only/fallback finalists, with no joint H-preserving eligible result; allW28 buys stronger surrogate reduction at greater WikiText cost.

Reproduce from the project root: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -I .scratch/selective-deception/sparse-extension-v3/analysis/plot_v3_heldout.py`. The script asserts frozen-label hashes, result binding, count conservation, retention/loss/gain identities, raw SDR/WikiText roundtrips and JSON serialization. It writes the summary, this report and PNG/SVG; uses no GPU or notebooks.

Exact source provenance is in [final-summary.json](../sparse-extension-v3/comparison/final-summary.json), including paths, SHA-256 hashes, generator identity and runtime. The original numerical/result files retain historical annotation-pending flags; frozen native results supersede those flags in this final joined summary.

| Source | SHA-256 |
|---|---|
| `native-analysis/native-results.json` | `8897d4fa51d4d272a9f541c6e3878017009972db56bbfad4902c9c0b2b06d61c` |
| `results/result.json` | `a2db98a2487ede61e9c765c01cbd162335225f9c676b44a629d0d477fdaed454` |
| `numerical-summary.json` | `ef62ff1089566f89e9e5c16caccd8a05993f5303b05b114e6aae4353b677a67d` |
| `native-labels/final-labels.json` | `2e99c31fa8f2a8cef92ede4cda327e7a6a4c88f741b82fdd3c5af3acc09f16c5` |
| `native-labels/final-freeze.json` | `f11bf9d79ce6fea6fa16569b0ec6a876c28aa84b4104be4511431198664ee015` |
| `native-packets/packet-manifest.json` | `d004352448c25e1030b50bccae6db2df59e029970ac749dbdff6a6d95d883473` |
| `selection-receipt.json` | `24225b46424a4308d494e3bd15b2f1ae92970b4ffc0e096dbb082415638e2fe3` |
| `inputs.json` | `4617cc522025f2bf5c057f0d2a675e5ec0d99e559b4be49c30414ad98dd0c73f` |
| `sdr-inputs.json` | `c281fb439cf6d5f512a9614801f464277a6cda38dbfb3e17d95515e66464b796` |
| `native-inputs.json` | `ada98398f78e315b81a4afa2383dae7d479094ea521d16dcccb75cf9a3f138c9` |
| `wikitext-inputs.json` | `2204387d22bd18164b5908a8a4bbae985058a5fb11c96aa3ec802e126efaef59` |
