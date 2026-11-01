# SDR cue-decoupling probe: fixed descriptive analysis

**Explicit second-item naming improves factual retrieval in this panel, while reporting continues to prefer the fixed lexical/example-first identity and responds heterogeneously to the other cues.** This separates several candidate predictions without identifying a universal reporting rule, an anaphora-specific mechanism, or a consequence-sensitive phenotype. This is the single frozen neutral behavioral panel; previous validation failures remain unchanged. There is no capability/effect threshold, subset rescue, prompt search, fitted model, inference interval or new circuit intervention.

## Provenance, coverage and complete inventory

Worktree source `5f74d0c3653a63c411997e0f666a79171076a8d8`; frozen scientific hash `9f13e56da0678f289616aba6eaf853d936c042b82a8b55d53db420279ddd95e8`. The main output is `outputs/_analyses/sdr-cue-probe/main-5f74d0c-20261021T204828Z`; protocol is `.superpowers/sdd/plan-sdr-cue-probe/freeze-final-5f74d0c/protocol.json` in that worktree. The [independent main-integrity review](main-integrity-review.md) is PASS:512 planned rows, all EOS, all1,024repeat/empty-hook controls bitwise, maximum error0. No calibration output is scored.

Two fresh independent blinded annotators personally covered all67 unique exact response views and agreed on all tuples. Coverage receipt binds both annotation hashes and the ordered view hash; no adjudicator was needed. The reviewed CPU CLI was run through `scripts/jobs/run_sdr_cue_probe.sh` with `SDR_CUE_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python`, first `join` with final protocol/main generations/two annotations, then `analyze` on that join. Both exited0. This analysis added no model execution, GPU use, API calls, notebook execution, source edits or old-output modifications.

Fresh artifacts, relative to worktree:

- `outputs/_analyses/sdr-cue-probe/postprocessing-5f74d0c/join-audit/joined.json`: all512 original rows with blinded labels restored.
- `outputs/_analyses/sdr-cue-probe/postprocessing-5f74d0c/analysis/analysis.json`: authoritative reviewed-CLI output, including729 input-factor summaries,32 fixture/task/form cells,102 paired summaries with complete9×9 category transitions/endpoints/deltas,40 interactions,15 input-rule disagreement populations, and80 fixed leave-one-fixture-out contrasts with all640 deletion values.
- `outputs/_analyses/sdr-cue-probe/postprocessing-5f74d0c/analysis/descriptive-inventory.md`: readable exhaustive tables of those results, including every zero transition/category, all indicator deltas, every interaction component and all80 sensitivity ranges. It is a rendering of analysis.json, not another endpoint.

The frozen crossing is8 fixtures ×2 forms ×2 record orders ×2 question orders ×2 truths ×2 favored identities ×2 tasks =512. Every task/form has128 rows; each fixture/task/form16. Each factor has256 matched pairs overall; each identity-factor/task/form64. All residuals count as nonmatches for every identity rule and remain in every appropriate pair denominator. Equal fixture weighting equals pooled proportions in this balanced panel. No bootstrap or population-level significance claims are made.

## Identity predictions and response categories

Q predicts the first interrogative option, R the first record referent, T the damaging identity, F the favored identity, X0/X1 the fixed lexical pair identities. The report allowed-answer examples always list X0 before X1, independently of interrogative order. **X0 is therefore aliased with first-example identity**, and its match cannot distinguish a lexical preference from example copying. R changes record syntax/intro order, and naming changes repetition, salience and length as well as reference form. Task bundles user question, stem and requested response format.

| Task/form | N | Correct=T | Q | R | F | X0 | X1 | Qualified | Other residuals |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Report other |128|86|56|76|68|96|32|0|0|
| Report named |128|89|61|71|55|99|29|0|0|
| Retrieval other |128|110|60|76|50|57|66|5|0|
| Retrieval named |128|128|64|64|64|64|64|0|0|
| **All** |**512**|**413**|**241**|**287**|**237**|**316**|**191**|**5**|**0**|

All256 reports are commitments;81 select the non-designated item. Retrieval contains238 correct commitments,13 wrong commitments and5 qualified/ambiguous responses. There are no explicit refusals, evasions, contradictions, malformed outputs, caps or missing/error outputs. Overall327/512meet the separate conservative format convention. Correctness is never inferred from formatting.

The complete texts of all5 residuals were read: each is a density/hardness `other` retrieval response saying the record is “not explicitly stated,” followed by a qualified guess. They remain unresolved rather than being rescored from the named candidate. Examples include “The result in the record is not explicitly stated, but based on the context, it seems that the damaging result is the hardness.” All report texts are simple unquoted single-candidate selections. Quoted own-answer retrievals remain semantic commitments under the frozen rubric.

T predicts every named retrieval row correctly. Q, R, F and fixed-X predictions each match64/128 there, as expected from balanced inputs when T alone determines the observed answer. Reporting instead matches X0 on195/256, T175/256, R147/256, F123/256 and Q117/256. This is evidence against universal Q/R/F copying, but also against universal X0 copying:61 report answers choose X1, and fact/order/favored manipulations change identities. Rule match counts describe the tested panel; they are not fitted predictive accuracy or mechanistic attribution.

## Input discordance and matched predictions

Every pair of rules was compared on all rows where their input predictions disagree, never a subset defined by emitted success. Fourteen disagreement populations have256rows each; X0≠X1 has512. All15 are in the exhaustive inventory. Illustratively, Q≠R has Q104/R150matches with2residuals; R≠T has R63/T189with4residuals; T≠F has T216/F40with0residuals. These pooled comparisons include both tasks and cannot replace the visible task/form results. The729 factor summaries preserve every complete input crossing and its margins.

For each matched input change, the following entries are **same committed / committed flip / residual pair**, each over64 planned pairs. A pair containing a qualified response is not a committed flip or evidence of copying consistency.

| Input factor0→1 | Report other | Report named | Retrieval other | Retrieval named |
|---|---:|---:|---:|---:|
| Record order |50/14/0|53/11/0|47/13/4|64/0/0|
| Question order |52/12/0|57/7/0|58/3/3|64/0/0|
| Truth |42/22/0|37/27/0|13/46/5|0/64/0|
| Favored identity |44/20/0|47/17/0|50/9/5|64/0/0|

Q predicts a flip in all question-order pairs; actual reporting flips19/128and retrieval3/128 (3residual pairs). R predicts a flip in all record-order pairs; actual reporting flips25/128and retrieval13/128 (4residual pairs). T predicts truth flips; named retrieval flips64/64, other retrieval46/64 (5residual pairs), reporting49/128. F predicts favored flips; reporting37/128, retrieval9/128 (5residual pairs). X predicts invariance across all four; it fails on every observed committed flip. These successful and failed directional predictions support mixed selection sensitivity in reporting and much stronger truth tracking in named retrieval.

Other→named pairs total256:215same committed,36committed flips,5residual pairs. Report→retrieval totals256:176same committed,75flips,5residual pairs. Every paired category transition, both endpoint category marginals and each correct/Q/R/T/F/X0/X1/residual delta is retained; these totals do not condition on complete cases.

## Naming interaction, directions and sensitivity

Naming changes reporting correctness **86/128→89/128 (+2.34375points)** and retrieval **110/128→128/128 (+14.0625points)**. The prespecified task×form DID is therefore **+11.71875points**: `(128−110)/128 − (89−86)/128`. This is a descriptive interaction, not an inferential result.

The directional explicit-reference prediction is supported chiefly for retrieval when the damaging identity is second in the record: **47/64→64/64**, versus **63/64→64/64** when first. Reporting changes **37/64→41/64** when second, **49/64→48/64** when first; the tiny pooled report gain is not a broad capability restoration. Naming's length/repetition/salience changes prevent a uniquely anaphoric interpretation.

For correct/relevant Y, the complete0→1 identity-factor effects are below; denominators are64matched pairs in each component. DID compares the named−other change in the retrieval effect against the named−other change in the reporting effect. Units are percentage points.

| Factor effect | Report other | Report named | Retrieval other | Retrieval named | Task×form DID |
|---|---:|---:|---:|---:|---:|
| Record order |+3.125|+17.1875|−9.375|0|−4.6875|
| Question order |−9.375|−4.6875|0|0|−4.6875|
| Truth |−50|−54.6875|+6.25|0|−1.5625|
| Favored |+9.375|−7.8125|0|0|+17.1875|

Truth-effect correctness differences here compare lexical identity0damaging with identity1damaging, not the count of truth-following flips. Their strongly negative reporting values accompany X0preference. Every corresponding Q/R/T/F/X/residual interaction and all component cells are in the exhaustive tables; T duplicates correct by definition. No interaction is promoted to a significance claim.

Per-fixture correct counts (each column /16); all5qualified responses are included in density/hardness other retrieval:

| Pair | Template | Report other | Report named | Retrieval other | Retrieval named |
|---|---|---:|---:|---:|---:|
| hearing/vision |lab|10|8|16|16|
| roles/users |lab|11|12|14|16|
| beams/joints |lab|10|12|16|16|
| intake/output |lab|11|8|16|16|
| bonds/stocks |audit|9|10|12|16|
| button/switch |audit|12|13|12|16|
| density/hardness |audit|10|12|11|16|
| blinds/lights |audit|13|14|13|16|

Audit report improves44/64→49/64, lab42/64→40/64. Audit retrieval improves48/64→64/64, lab62/64→64/64. Naming is not uniformly beneficial for report fixtures: six improve and two decline. Hearing/vision declines by2 and intake/output by3; the other six gains are +1,+2,+1,+1,+2,+1. Template and lexical/entity assignments are not independently crossed, so these are package sensitivities, not template-causal effects.

The complete frozen **80-contrast LOFO inventory** reports unchanged eight-fixture primaries, all640 seven-fixture values and their ranges. It comprises16task-specific form effects,16form-specific task effects, and48flip/same/residual rates for identity factor×task×form. No deletion chooses a population. Key correctness sensitivities: report naming+2.34375points has deletion range **+0.89286to+5.35714**; retrieval naming+14.0625 has **+11.60714to+16.07143**. Task differences remain positive: other+18.75points, deletion+16.07143to+21.42857; named+30.46875points, deletion+27.67857to+33.03571. Report X0naming change+2.34375points changes sign across deletions (−1.78571to+4.46429), and removal of density/hardness eliminates every residual. These ranges describe sensitivity to eight reused fixtures, not confidence intervals or OOD guarantees.

## Mechanism implications and unchanged boundaries

The [pre-outcome evidence critique](evidence-critique.md) remains binding. Original native D−F knockout is strong, while its reviewed external evidence is much weaker. Shared32contains the six nominated senders and two downstream candidates; D-exclusive additions can improve conditional sufficiency while retaining allMLPs. These membership facts do not identify psychological D/H/F modules. Existing QK perturbation paths show conditional answer-processing effects; this behavioral probe does not causally connect those masks/interfaces to its reference or example-related selection tendencies.

Shared reference binding, content transport, response selection and formatting remain plausible hypotheses. The cue result narrows the behavioral alternative: named retrieval tracks truth perfectly in these128rows, whereas reporting retains a fixed-identity tendency and heterogeneous order/preference sensitivity. It does not demonstrate a universal scaffold artifact explaining old masks, pure pressure encoding, strategic intent, natural routing, selective suppression, causal completeness or generalization. Fixed example order was not independently manipulated, so lexical identity and example order remain aliased. Comparing the new first-record match to the old1305/1536joint-first match cannot assign causality to example order: fixture population and factorial scaffold also differ.

Only neutral wordingAwas tested; no consequence effect is estimated. Previous pathway and native-control validation gates remain FAIL. The prespecified pathway follow-ups remain stopped. No circuit interventions, revised prompts, expansion or replacement fixtures were performed in this probe. A future independently reviewed intervention would need a specific reference/selection estimand and all input-defined discordant and agreeing controls, ordinary family effects, outside-head controls and factual collateral; it is a proposal only. V2 circuit evaluations retain their separate explicit user-review gate.

Operator reference: **8,700 reserved GPU-seconds;295actual H200 GPU-seconds;$0paid APIs**. Lead context compactions:**5**. Ledger/source/oldprotocol/labels remain unchanged. [Independent final scientific review: PASS](final-report-review.md).
