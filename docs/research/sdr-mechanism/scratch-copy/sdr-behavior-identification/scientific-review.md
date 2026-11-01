# Independent quantitative scientific review

2026-10-25. **Final quantitative scientific review PASS, no remaining blocking result findings.** Direct-source calculations and comparison with frozen implementation artifacts are complete. Final verification and hashes appear below; earlier checkpoint hashes are historical. Narrative review is separate.

`independent_check.py` reads the specified archived JSON/JSONL sources and frozen source-semantics artifact directly. It does not import or read `audit_native.py`. Run with `/sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-behavior-identification/independent_check.py`; the final fresh run completed in 4.01 seconds with every assertion passing and wrote `independent-results.json`. Checker SHA256 `13da0311f41da88326514fb68ec93c4e4a1b731ebd691a66c65012d41be0880f`; result SHA256 `4b6f31858cf9de928cfab93b355fcda0ce39cbe09b3a2db8c4e6d4e234e22ede`. Evidence hashes and selected row-level counterexamples are saved there. No model inference, jobs, notebooks, APIs, git, or immutable-data edits.

## Independently reproduced evidence

- Pilot: 480 first-token variants, 48 stories, 96 exact fixed-fact units; each unit's five prompts become byte-identical after deleting its actual P/H clause. The damaging/harmless roles are reparsed from literal named predicates, not inferred from numeric truth or IDs. Every baseline emitted ID equals its saved full-vocabulary top argmax.
- Native EOS: 256 responses, 32 stories, 128 P/N units. Each pair has exactly one P and one N, identical facts/order/contract bytes after literal clause deletion. All reach EOS. CandidateA/B is decoded through each row's candidates and independently agrees with archived correct/incorrect labels. These are semantic complete-response labels, not first-token logits.
- Panels share zero story IDs, zero source IDs, and zero exact fact/contract fingerprints. Therefore they cannot be called a paired endpoint replay. Both nevertheless remain historically selected, familiar populations; disjoint panels do not create unexposed confirmation.
- 576 directed pair proposals expand to exactly 6912 family/scope/dose proposals, matched one-for-one to unique terminal events: 6528 completed and 384 excluded. Raw event history also contains 7520 planned comparison records and 6528 attempted records; neither is an additional outcome population.
- All 1152 completed events carrying archived P↔P′ labels use the same pressure ID and identical clause text, with changed factual truth. They are not alternate-pressure-wording interventions. Alternative P clauses exist in the baseline panel and are baseline-only in this frozen patch schedule.

Pilot primary P is harmless on all 96 units by historical behavioral selection. P→H changes harmless→damaging in 74/96; P→N in 78/96; primary→alternative-P in 108/192. The remaining counts are 22, 18, and 84 harmless→harmless. Across three P wordings, 65/96 units emit both candidates. H/N each have one fixed prompt per unit and show zero within-condition both-answer units; no stronger full-crossing claim follows.

EOS N→P transitions are: damaging→harmless 80, harmless→damaging 13, both harmless 14, both damaging 21. Thus N damaging101/128 versus P34/128, with a substantial subset reversing the pooled direction. This is a paired clause-edit result for selected disclosure commitments, not a prevalence or deceptive-intent estimate.

Strict clause avoidance is defined for 53/288 pilot P rows (29 positional consensus and 24 problematic-role lexical inferences); 39 match that prediction. It is defined for 6/128 EOS P rows, all positional consensus; 5 match. Undefined rows remain in total denominators. These defined-only fractions cannot be compared directly with all-row cue-rule accuracy or promoted to evidence that all other clauses lack a pragmatic meaning.

Input-derived cue comparisons reproduce pilot first-example matches P134/288, H36/96, N32/96; EOS P90/128 versus N49/128. EOS damaging counts are P34/128, N101/128. Explicitly described, lexical-first, harmless and second-example rules remain separately available in the results. Native EOS does not simply inherit the later neutral-scaffold example-dominance interpretation.

## Real argmax copying and preservation

All 12 family/scope cells contain 544 measured outcomes and 32 exclusions. Every measured patched emitted ID agrees with its saved full-vocabulary top argmax, and its recorded effect equals patched minus baseline truth margin. Recipient-baseline IDs/margins independently match the baseline source.

Each cell has 232 recipient/donor pairs with the same emitted candidate. Counts where patching changes the actual emitted argmax away from that common answer are:

| Family | Common scope | Readout scope |
|---|---:|---:|
| candidate6 | 44 | 9 |
| selector2 | 0 | 0 |
| outsider2 | 12 | 9 |
| shared32 | 7 | 1 |
| outside_mask2 | 0 | 0 |
| empty | 0 | 0 |

These are actual categorical counterexamples to universal donor-emitted-answer copying for the corresponding families/scopes, not merely positive margin changes. They are conditional replacement outcomes; zero counterexamples does not prove a family is a copier. **The 40 fixed-fact same-emission cases in each cell yield zero changed argmaxes in this schedule.** Consequently these particular universal-copy counterexamples depend on changed facts/content; they do not identify pure-pressure mediation. Fixed-fact clause effects and narrower copying tests remain valid on their own support; a full factorial is not a universal prerequisite for every causal statement.

For reference, candidate6/common preserves the recipient emitted ID349/544 and matches donor ID339/544; shared32/common preserves241/544 and matches donor521/544. These predicates overlap where recipient and donor agree and are not competing exclusive outcome categories. Empty preserves544/544 with exactly zero truth-margin effect; outside_mask2 preserves544/544 despite small logit changes. Outcome-derived donor-copying must stay separate from input-derived donor-rule matches.

## Historical comparison checkpoint (completed below)

After the implementer signals completion, compare these selected headline counts, strict-rule denominators, event aliases, exact pair checks, and representative counterexample rows against its output tables/report. No broad search, new inference, or additional population is needed. The unresolved source ambiguity is already explicit in the frozen semantics: positional competing anchors, uninstantiated flags, demonstratives, generic adverse outcomes, and third-party audience assumptions. None should be repaired by inspecting which response makes a rule look successful.

Fact-change detail independently checked: the 232 same-emission cases per family/scope comprise 40 exact fixed-fact cases and 192 changed fact/contract cases. Every actual same-emission argmax counterexample listed above is a same-story named-truth flip, with zero cross-story counterexamples. Counts for common/readout scopes are candidate6 44/9, outsider2 12/9, shared32 7/1, and selector2/outside_mask2/empty 0/0. The denominator for each changed-fact same-emission count is 192; the corresponding fixed-fact count is 0/40 in every cell.

## Approved exploratory donor factual-role addendum

This section is explicitly **POST HOC**, authorized after candidate6/common44 and shared32/common7 same-emission counterexamples were already known. The four predictors and strata were fixed before computing this additive table. The original input-rule checks above remain unchanged; this new rule uses the donor's baseline emitted answer and is outcome-derived.

The extended independent checker and all original assertions ran PASS in 4.69 seconds. Current checker SHA256 `22d38a63bda74a68057861135966e5923b0fa40e1339f1f1aa27b15b80d9302d`; current result SHA256 `afd279eb9ad034014120c4195e638c18549b0d0a0f2e3727d0371eab8c69288e`. Earlier hashes describe the preserved chronological fixed-check checkpoint, not these additive artifacts. Results include all family/scope cells and separate clause, fact/contract, and own/other-story groupings; all-row match fractions averaged within recipient stories are retained alongside raw counts.

On same-story named-truth flips, each family/scope has 288 measured outcomes. Matches below compare the actual patched argmax with literal donor identity, donor factual role applied to recipient facts, recipient baseline preservation, and always-recipient-damaging:

| Family/scope | Literal | Role | Preservation | Always damaging |
|---|---:|---:|---:|---:|
| candidate6/common | 204 | 84 | 148 | 202 |
| candidate6/readout | 152 | 136 | 270 | 92 |
| selector2/common | 209 | 79 | 231 | 133 |
| selector2/readout | 206 | 82 | 234 | 130 |
| outsider2/common | 182 | 106 | 234 | 124 |
| outsider2/readout | 181 | 107 | 241 | 119 |
| shared32/common | 276 | 12 | 150 | 212 |
| shared32/readout | 254 | 34 | 184 | 180 |
| outside_mask2/common | 152 | 136 | 288 | 76 |
| outside_mask2/readout | 152 | 136 | 288 | 76 |
| empty/common | 152 | 136 | 288 | 76 |
| empty/readout | 152 | 136 | 288 | 76 |

All-row544 matches for candidate6/common are literal339, role219, preservation349, always-damaging343; shared32/common gives521,235,241,325 respectively. These are predictive comparisons of conditional replacements, not inferred natural computation or psychological policy.

Equivalences are essential. On all288 truth-flip outcomes, literal and role disagree. Literal coincides with always-damaging212/288, leaving76 distinguishing cases; on those76, candidate6/common follows literal39 and damaging37, whereas shared32/common follows literal70 and damaging6. Donor role coincides with preservation136/288 and always-damaging76/288. Role-versus-preservation disagreement152/288 yields candidate6/common44 role matches versus108 preservation matches, and shared32/common7 versus145. Thus the original44/7 counterexamples supply only part of the picture: **candidate6 does not generally transport donor factual role**, and its near equality with always-damaging on the pooled flip panel is partly an alias with literal copying. Shared32 remains much closer to literal identity transport in this diagnostic.

The truth-flip same-emission denominator is152 per cell; the broader changed-fact/contract same-emission denominator192 additionally includes40 cross-story same-emission cases. Counterexamples occur only in the152 same-story truth-flip cases, with none in the cross-story cases or the40 fixed-fact same-emission cases. This refines the earlier232-total/192-changed-context decomposition without altering any count.

No latent truth/role representation, goal, pressure-specific policy, mediation proportion, selective suppression, or restored knowledge follows. No further predictor search or inference is justified automatically. At this exploratory checkpoint, implementation agreement was pending; the completed comparison is recorded below.

## Final independent implementation comparison — PASS

The final fresh independent checker completed in 5.01 seconds with all original source assertions and **5,193 finite output-comparison assertions passing**. It did not import the implementation. Compared structural counts/support; baseline/EOS rule totals and undefined coverage; exact transition counts; all12 family/scope argmax-change, copying, preservation and truth-margin summaries; all1152 P↔P′ alias classifications; and all four exploratory predictors' matches/mismatches/undefined/outcome-other counts, pairwise equivalences and disagreement outcomes across family/scope and the specified clause/fact/story strata. All-row within-story averages were also compared for whole-family/scope and the input-defined same-story truth-flip subset. No family-pooled count was substituted for a per-family headline. No discrepancy remains.

Final checked implementation source SHA256: `86efc95da85042d15382ff4b44c8ebb49436a15c274f290007503626638e982f`.

Final independent checker SHA256: `2b7bfdb797e85cf0286c436f325aacd02c9c93d2063cfeb7238030e56658698e`.

Final independent result SHA256: `6d7864ab5b97db7c91efd107f8ee8d81dd52544725e2d5eb574b5772c4bf0e2b`.

Bound final implementation outputs:

| Artifact | SHA256 |
|---|---|
| audit.json | c1469a81d12e9e9c9e3526a10efe0eae710333dae70186bd4cb51dc76e9922b1 |
| role-transport.json | f9fb914a7fabce4788aa5a45e27692cc663b4f5e756643e44ebbe899477c68fd |
| results-summary.md | 1cd3c2a64d0c17ef4d90e192a602b399b25bde96c26ddf01c0001828be12a541 |
| patch-outcomes.jsonl | 05ded8caabb1e3a216799c0217a1799113da2698f46be71515eae3b930846723 |
| source-manifest.json | 4246f5b2795da241a41189d5ba493482a607406eb4b95cd391303793f55f7910 |

Hashes of every final output file are retained in `independent-results.json` alongside two source-linked headline cases:

1. Candidate6/common, recipient `1240d0bf…:0` P and donor `1240d0bf…:7` N: both baseline argmaxes are **density**; the actual patched argmax becomes **hardness**, truth-margin change `+3.9111175537109375`. The recipient and donor have opposite named factual truth. Source output and implementation agree exactly. This is an actual counterexample to universal emitted-identity copying, not just a margin movement, and it remains content-confounded.
2. Shared32/common, recipient `329ebc6c…:7` N and donor `329ebc6c…:0` P: both baseline argmaxes are **clock**; the actual patched argmax becomes **timer**, truth-margin change `−2.3037853240966797`. Facts again differ. This shows that literal copying is not universal even for the shared mask, whose aggregate pattern is nevertheless strongly closer to literal identity than factual-role transfer. Full IDs and exact output keys are saved in the independent result.

The useful increment is a sharper finite identification boundary: precise support and clause-label aliases, actual category changes distinguished from margin-only shifts, and the retrospective four-predictor comparison with its large equivalence cells. The strict avoidance53/288 and6/128 coverage counts are conditional on the declared conservative operationalization; they are not estimates of how many prompts humans understand. Matched clause effects and specific copying counterexamples survive on their exact support. None of these results establishes false factual assertion, realized concealment, intent, pressure-specific natural mediation, selective suppression or unexposed confirmation.

This PASS covers quantitative/source scientific validity of the frozen audit artifacts and bounded exploratory addendum. It does not assert an implementation test result independently, supply a code-quality review, or approve a later narrative that has not yet been read.
