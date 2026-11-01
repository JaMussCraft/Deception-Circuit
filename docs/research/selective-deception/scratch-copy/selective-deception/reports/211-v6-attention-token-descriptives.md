# 211 — V6 exact-token attention descriptives

L17H27 assigns substantial raw attention mass to recipient answer-word occurrences on both D and benign inversion I; those two patterns are similar here. L13H23 assigns much less mass to those exact answer IDs, and the fixed example has high-weight punctuation/turn-header tokens. These are lexical/position descriptions, not semantic segment labels or causal head functions. Both heads were nominated by the earlier causal study before this summary; no new head ranking or selection was performed.

Source: the existing complete720 eager-attention rows (30 heads ×D/H/I ×8 previously exposed development scenarios), joined to the frozen panel. Each query is the recipient’s own last actual prompt position. The exact token IDs, key positions, tokenizer strings, weights, row mass and source/code SHA256 bindings were checked. [All90 head×variant summaries, all per-case occurrence counts/positions/top3 tokens, broad distributions and hashes](../component-analysis-v6/token-descriptives-001.json).

## The two previously nominated heads

Cells are means across the same8 scenarios, expressed as percentages of original raw attention weight. Truth/false mass sums **every occurrence** of the corresponding recipient answer-token ID. D/I request the false alternative; H requests truth. No mass is renormalized to answer words or selected tokens. BOS is the exact first-key token128000; final-key mass refers to the exact final query position.

| Head | Variant | Truth-token mass | False-token mass | First/BOS mass | Final-query-key mass |
|---|---|---:|---:|---:|---:|
| L17H27 | D | 24.565% | 11.470% | 11.774% | 0.726% |
| L17H27 | H | 10.006% | 11.105% | 12.195% | 1.404% |
| L17H27 | I | 24.824% | 13.016% | 13.400% | 0.677% |
| L13H23 | D | 0.448% | 0.226% | 2.559% | 1.132% |
| L13H23 | H | 0.473% | 0.301% | 6.384% | 1.607% |
| L13H23 | I | 0.313% | 0.247% | 3.922% | 1.268% |

For L17H27, D/I truth-token mass is24.565%/24.824%, with false-token mass11.470%/13.016%. Under H, truth/false masses are10.006%/11.105%. This does not establish that the head “represents truth,” endorses an answer, or mediates refusal: attention weights are not output contributions, and the same word appears at multiple prompt positions. L13H23 answer-token mass is below0.5% for truth and below0.31% for false in each variant; its causal role cannot be inferred from that low direct lexical mass.

Each answer ID occurs3–4 times per case, mean3.5 for both truthful and false IDs in every variant; there are no zero-occurrence cases in this panel. The JSON explicitly retains zero-occurrence case lists (empty here), so missing words are not conflated with unobserved/omitted rows. Summed token mass is affected by occurrence frequency, location, tokenization and prompt context. Equal average occurrence counts do not remove those confounds.

## Broad30-head context, without new ranking

Each cell is the median [minimum, maximum] across30 head-specific eight-scenario means, in percent. These are descriptive ranges, not uncertainty or significance intervals.

| Variant | Truth-token mass | False-token mass | First/BOS mass | Final-query-key mass |
|---|---:|---:|---:|---:|
| D | 1.356 [0.004,24.565] | 1.160 [0.002,22.255] | 46.631 [2.559,95.361] | 1.797 [0.227,35.376] |
| H | 1.113 [0.004,18.226] | 0.882 [0.002,16.229] | 46.655 [5.099,95.361] | 1.720 [0.260,36.157] |
| I | 1.279 [0.004,24.824] | 1.130 [0.002,27.828] | 47.375 [3.922,95.361] | 1.930 [0.192,36.011] |

The broad median first-key mass is roughly47%, showing why raw special-token attention cannot be silently discarded or renormalized away. The full frozen head list is retained in the JSON. No additional sender/receiver, candidate or path is selected from these patterns.

## Fixed illustrative token rows

The example is the first previously declared attended scenario, `["Alcove Property",["client","server"]]`, selected before attention outcomes. Entries are exact key-position / tokenizer-string / token-ID / raw weight. Only the top3 positions are displayed; they are not semantic spans, and ties use ascending key position.

- **L17H27 D**, case `sdr:447b95fb9bd4:D`: `0 / <|begin_of_text|> / 128000 / 0.122559`; `68 / Ġserver / 3622 / 0.066406`; `86 / Ġclient / 3016 / 0.051025`.
- **L17H27 H**, case `sdr:447b95fb9bd4:H`: `0 / <|begin_of_text|> / 128000 / 0.107422`; `68 / Ġserver / 3622 / 0.085938`; `88 / Ġserver / 3622 / 0.066406`.
- **L17H27 I**, case `sdr:447b95fb9bd4:I`: `0 / <|begin_of_text|> / 128000 / 0.128906`; `68 / Ġserver / 3622 / 0.095703`; `86 / Ġclient / 3016 / 0.068848`.
- **L13H23 D**, case `sdr:447b95fb9bd4:D`: `54 / <|eot_id|> / 128009 / 0.211914`; `92 / assistant / 78191 / 0.090820`; `93 / <|end_header_id|> / 128007 / 0.090820`.
- **L13H23 H**, case `sdr:447b95fb9bd4:H`: `93 / <|end_header_id|> / 128007 / 0.186523`; `92 / assistant / 78191 / 0.120117`; `94 / ĊĊ / 271 / 0.096680`.
- **L13H23 I**, case `sdr:447b95fb9bd4:I`: `53 / . / 13 / 0.349609`; `54 / <|eot_id|> / 128009 / 0.070801`; `93 / <|end_header_id|> / 128007 / 0.070801`.

The literal `<|eot_id|>`, `assistant`, `<|end_header_id|>`, newline token and period in L13H23’s displayed rows contrast with answer-word/BOS positions in L17H27’s rows. This single fixed example does not characterize every scenario or identify verified instruction/fact boundaries.

## Backend and claim boundary

Both SDPA and eager independently pass the actual clean/no-op/self controls, but their logits differ. Across24 cases, maximum absolute full-vocabulary drift is0.437500 native and0.463084 fp32; maximum requested-margin drift is0.250000/0.236446, with0/24 argmax changes in each readout. These descriptive attention rows are eager, while the causal pilot/follow-up effects use SDPA. Small causal effects cannot be explained quantitatively by treating these backends as identical.

No verified semantic clause/fact segment mapping is available. No “lie attention,” statistical significance, causal attention mediation, deception specificity, preserved benign utility or free-generation/refusal conclusion is claimed. All attention summaries use only the fixed8 scenarios and are separate from the16-scenario validation follow-up. No new model/GPU/API/job/git, source/receipt/label edit or selection occurred.

Verification independently recomputed all720 per-case answer-token mass/count/top3 records and all90 head×variant means from the source JSONL. Original raw row masses range0.997913–1.002090; this small deviation from one is retained, with no selected-token renormalization. Source and dependency hash checks passed. Existing202/209 reports and every raw artifact remain unchanged.
