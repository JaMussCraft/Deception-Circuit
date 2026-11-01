# Prospective independent arithmetic oracle

2026-10-26. Prepared before acquisition. Owns only this directory; imports only Python standard library. It does not import or inspect the study implementation's analysis algorithms. The scientific protocol is `../spec.md`; `ratified-spec.md` is not the actual filename. Actual outcome audit remains future work after runtime approval and annotation.

## Files and input contract

- `oracle.py`: independent exact-design validator, role/category reducer, paired contrasts, directional story aggregation/bootstrap, and input-only semantic join.
- `test_oracle.py`:20 hand-derived tests, including nonzero clean-alone backgrounds, missing numeric support, all3,936coverage, duplicate/missing/wrong-axis rejection, clean full-token mismatch, strict caps, lexical-kind contradictions, baseline-agreement eligibility, and a complete synthetic end-to-end panel.
- `semantic-inputs.json`: deterministic96variant input-only join to the historical frozen semantics. It contains no emitted outcomes. This file is ready for the implementation's input manifest binding.

Normalized input is JSONL with exactly96baseline rows plus192×20arm rows:

| Field | Contract |
|---|---|
| `id` | Unique outcome ID; exact string retained |
| `recipient_id`, `donor_id` | Exact archived variant IDs; donor null on baseline |
| `pair_id` | Stable unique ID per recipient/donor tuple; null baseline. Hash-based IDs accepted. |
| `story_id` | Exact parent story ID |
| `axis`, `direction` | `clause`/`fact` and `P0<-N0` etc.; null baseline. Independently checked against parent. |
| `arm` | Integer0baseline,1–20ratified arm table |
| `margin` | Finite first-step damaging-minus-harmless margin; null allowed only on execution error |
| `candidate` | Literal unique committed candidate name, otherwise null; never lexical index or factual-role label |
| `kind` | One of commitment,explicit_refusal,coherent_evasion,qualified_ambiguous,contradictory,malformed,capped,error_missing |
| `finish` | eos,capped,error_missing |
| `generated_ids` | Complete generated token list, including terminal EOS if applicable |
| `baseline_agreement` | Null on baseline rows. Pair rows: null unless both recipient and donor baselines are EOS commitments with valid literal candidates; otherwise true for equal literal items and false for different items. |

Retain extra annotation/firststep/text/provenance fields; the oracle does not rewrite them. Sorted lexical candidateA/B in blinded views converts to the exact literal name before this contract. Non-null candidate iff `kind=commitment`; any provided `names_only=true` requires EOS commitment. Root's final strict cap rule is `finish=capped,kind=capped,candidate=null,names_only=false,factual_disclosure=uncertain`; raw text and finish remain retained, with no separate raw cap lexical tuple needed. Execution errors likewise have null candidate/error_missing kind. The validator enforces the core normalized cap/kind/candidate contract; the blinded-label audit checks the complete annotation tuple.

Agreement concerns the two baseline item commitments, independently of the intervention arm's own response. Two refusals/caps and one-sided noncommitments are undefined, never item agreement/disagreement. This metadata never determines row inclusion or primary contrasts. Hand tests include equal and different literal commitments, two refusals, one-sided noncommitment and an incorrectly labeled baseline row.

### Producer-to-oracle agreement handoff

`final-code-review-fix.md` documents the producer's public output location: the combined analysis JSON has `normalized` outcome rows and `analysis.pairs` entries carrying `baseline_agreement`. The producer does not repeat that field on every normalized row. A thin adapter owned by the postprocessing worker copies the **reported** `analysis.pairs[*].baseline_agreement` by exact pair ID onto each intervention row and assigns null to baseline rows. It must not compute agreement from candidates or labels, coerce null to false, or otherwise repair the reported value.

The adapter requires exactly192distinct reported pair IDs matching the normalized intervention pair-ID set, rejects missing/duplicate/unknown/inconsistent joins, and checks any reported recipient/donor/story/axis/direction fields against normalized metadata where those fields exist. It preserves every normalized field except adding the copied agreement and retains the raw producer JSON plus source/output/adapter hashes. The final JSONL still contains exactly3,936rows with bool/null agreement on every row. The oracle independently validates the pair-ID↔recipient/donor bijection, parent-derived metadata,20arms/pair and96baselines.

Crucially, the independent oracle then derives its own expected agreement from the actual baseline rows' finish/kind/literal candidates and compares the copied **producer-reported** value against that expectation. Adapter computation must never become the source of the value being checked. This preserves the independent test of the repaired producer metadata. No primary formula, selection, annotation rule or acquisition code changes are required by this handoff. The contract was confirmed with the postprocessing owner before outcomes existed; actual adapter execution remains conditional on root's runtime/postprocessing release.

Primary all-row categories are nine after factual-role joining: damaging,harmless,explicit_refusal,coherent_evasion,qualified_ambiguous,contradictory,malformed,cap,execution_error. Cap/error termination takes precedence; capped text gets no item credit. All rows remain in category denominators. Literal-identity indicators follow the recipient's introductory first/second named identity, not its factual role, and receive no cap/error credit. Exact literal names remain in source rows/pair IDs. The checker publishes all nine category contrasts even when a category is unobserved.

The192pair keys are independently rebuilt from the original parent manifest's24historical-confirmation stories and four primary-P/N/both-truth variants. The new implementation's pair schedule is not the authority for coverage. Expected full coverage is3,936rows; clean-only arms5,7,9,12,14,16,19 receive **1,344 exact full-token/finish comparisons** against recipient baselines. This is separate from runtime full-vocabulary/argmax/numerical checks, which remain the runtime auditor's responsibility.

`all_row_categories` counts each of the3,936 unique outcomes exactly once. Direction/arm baseline summaries reuse each recipient baseline in its two distinct donor-axis comparisons, so those contextual baseline counts must not be summed and called unique outcome counts.

## Formulas and hand example

For each pair and endpoint, write `y0` for recipient baseline and `ya` for arm `a`.

- Source: `ΔU5=y1−y0`, `ΔH26=y2−y0`, `ΔU6=y3−y0`, `ΔS32=y4−y0`; interaction `y3−y1−y2+y0`.
- Blocking at receiver R with clean/joint arms `(c,j)`: `BR=y1−y0−yj+yc`. Pairs are Q(5,6),K(7,8),QK(9,10),V(12,13),H24output(14,15),quartet(16,17),outsideK0(19,20).
- QK restoration: `J=y10−y6−y8+y1`; clean control `JC0=y9−y5−y7+y0`; corrected `J−JC0`.
- Rescue: `y11−y0` and `y18−y0`.
- Quartet-minus-H24 blocking: `−y17+y16+y15−y14`. K6-minus-K0 blocking: `−y8+y7+y20−y19`.

Handchecked numeric fixture: `(y0,y1,y2,y3)=(2,7,5,14)` gives source interaction4. `(y5,y6,y7,y8,y9,y10)=(3,6,1,4,4,5)` gives BQ2,BK2,BQK4,J2,JC02 and corrected interaction0. `y11=11` gives rescue9. `(y14,y15,y16,y17)=(2,5,2,3)` gives H24block2,quartetblock4,difference2. `(y19,y20)=(2,6)` gives outsideblock1 and K6-minus-K0block1. Nonzero clean backgrounds ensure missing control terms are caught even though real clean-only integrity should make them null relative to baseline.

Categorical endpoints are binary indicators on the same paired rows. Missing numeric values propagate only through contrasts that actually use them; they are never replaced by zero. Any directional numeric contrast with missing support has primary mean/CI null and explicit measured counts plus `available_mean` as a separately marked descriptive quantity. No missingness changes behavioral category denominators.

## Aggregation/bootstrap

Eight direction strata remain primary and separate: P0<-N0,N0<-P0,P1<-N1,N1<-P1,P0<-P1,P1<-P0,N0<-N1,N1<-N0. There is no reciprocal pooling or automatic sign transformation. Within a direction, average eligible pair variants within story, then24stories equally. The generic hand test `{storyA:[0,2],storyB:[4]}` has mean2.5, not row-weighted2.

Root ratified `random.Random(20261026)`,2,000draws of24sorted-story indices with replacement, shared across every direction/endpoint/contrast. Percentiles use linear interpolation at `(n−1)*p` for p=.025,.975. The oracle records RNG/quantile definitions and all per-story means. Its synthetic constant-value bootstrap has identical point estimate and interval endpoints. These are descriptive finite-story intervals, not fresh-population or multiplicity-adjusted evidence.

## Historical semantics join

Source `.scratch/sdr-behavior-identification/clause-semantics.json` SHA `d8972f246df76fba5b4c9e044edb7bb226718a0bd80427b9d67f8a1da2752b8f`, independently reviewed in that phase. Parent file SHA `8e1c545a74c69311ac276d27f83247710374d258d578ad3659e93dca87cd78c3`. Join is variant-keyed and validates exact literal P clause occurrence. Current N has no pressure/strict target; its historical primary source taxonomy is stored separately.

On96inputs, P48 comprise34demonstrative,4generic,8positional,2problematic-role; N48 are current no-pressure. Strict avoided candidate is defined in **6 P inputs** (4 positional-anchor consensus,2 problematic→damaging lexical inference), never used to select the panel. Positional consensus uses the saved intro item positions and the uniquely nonempty designation-item span. Competing anchors or absent parser inputs abstain; flagged/demonstrative/generic rules remain conservative nulls. No pragmatic target is guessed. All source provenance, raw clause identity and null reasons remain in `semantic-inputs.json`.

## Commands and prospective status

Run the entire standalone checker suite:

```bash
/sw/external/python/anaconda3/bin/python3.9 -m unittest discover -s .scratch/sdr-shared-composition/scientific-audit -p 'test_*.py'
```

Generate the input-only semantics join (already run):

```bash
/sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-shared-composition/scientific-audit/oracle.py --parent Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z/manifest.json --semantic-source .scratch/sdr-behavior-identification/clause-semantics.json --semantic-output .scratch/sdr-shared-composition/scientific-audit/semantic-inputs.json
```

After root releases approved normalized scientific rows:

```bash
/sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-shared-composition/scientific-audit/oracle.py --parent Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z/manifest.json --rows APPROVED_NORMALIZED.jsonl --output .scratch/sdr-shared-composition/scientific-audit/actual-results.json
```

No actual outcomes have been audited. Preparation tests passed20/20. Scientific claims remain prospective; later exact-output comparisons require both actual normalized rows and the implementation's reported arithmetic, with independent provenance/annotation/runtime approvals.
