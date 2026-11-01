# Scratch CPU audit implementation

Status: **DONE; independent code/scientific review pending.** The metadata-first handoff was completed before root released the independently reviewed semantic mapping and saved outcome joins. Original metadata-stage files in `results/` remain intact; final files live in `results/final/`.

Run from Alignment:

```bash
/sw/external/python/anaconda3/bin/python3.9 -m unittest discover -s .scratch/sdr-behavior-identification -p test_audit_native.py -v
/u/swong2/.local/bin/ruff check .scratch/sdr-behavior-identification/audit_native.py .scratch/sdr-behavior-identification/test_audit_native.py
/sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-behavior-identification/audit_native.py --outcomes
```

For a new metadata-only output, pass `--metadata-only --output PATH` instead. The final CLI defaults to `results/final/`, preserving the original handoff. No model imports, GPU, jobs, APIs, notebooks, production edits, old-result mutation or git operations were used.

## Scope and verification

The standard-library script uses one finite source manifest with resolved paths/bytes/SHA256, including its own code/tests, fixed spec/plan, reviewed clause JSON/review and explicit exploratory addendum. It verifies saved prompt hashes using the archived JSON-string hashing convention. Exact terminal-system-clause removal leaves byte-identical facts/order/contracts for all 96 pilot units and 128 EOS P/N pairs. Named damaging/harmless roles are checked against saved token IDs. No whitespace/punctuation/duplicate-token normalization occurs. Native EOS membership comes from the frozen input manifest; candidateA/B labels decode through each actual row's candidate names. Duplicate variants/events, stale prompt hashes, link/hash mismatches, impossible completed missing-donor proposals and unexplained expected counts fail explicitly.

Actual coverage is 25 clauses; 480 pilot variants/48 stories/96 units; 256 native EOS responses/32 stories/128 pairs; 1,024 synthetic rows excluded; 576 pair proposals×6 families×2 scopes=6,912 patch proposals, with 6,528 completed and 384 excluded. All completed outcomes and all excluded proposals are retained. Planned and attempted events are not measurements. Cross-panel overlap is zero by story ID, source-instance ID and exact fact/contract fingerprint.

Focused test-first evidence: the initial API skeleton produced 7 assertion failures and 2 missing-result errors. Six added semantic/outcome tests then failed for missing APIs before implementation. Two additional structural checks failed before fixing stale prompt-hash and impossible missing-donor handling. Four role-transport tests failed for the absent additive API before implementation. Final fresh verification passes all **21** focused tests; Ruff passes. No unrelated model suite was run, per assigned scope. A real metadata run exposed archived H-prefixed pressure IDs (`H:sdr_08`); lookup removes only that literal prefix while output preserves the archived ID.

## Fixed analysis outputs

`results/final/audit.json` contains every fixed-rule match/mismatch/undefined count, noncandidate coverage, all-row and within-story means, pairwise rule-disagreement cells, category/factor margins, P/H/N and primary/alternative-P transitions, EOS truth/order cells, and patch family/scope/structural cells. Adjacent JSONL files preserve baseline/EOS/patch row metadata, input predictions, decoded outcomes and terminal diagnostics. `support.json` explicitly lists missing condition×answer cells. `results-summary.md` is the writer handoff.

Primary P is harmless96/96; H is damaging74/96; N78/96; alternative P108/192. Within fixed facts, primary→H flips74/96 and primary→N78/96; alternative-P flips108/192. Both identities occur across the three P wordings in65/96 units, but H/N each have one saved response and no within-condition answer crossing. This limits diagnostics requiring full crossing; it does not erase existing clause-edit comparisons.

EOS P is damaging34/128 versus N101/128. Exact N→P pairs are damaging→harmless80, harmless→damaging13, both damaging21, both harmless14. Strict conditional avoidance has pilot matches39/mismatches14/undefined427 of480; EOS matches5/mismatches1/undefined250 of256. Primary P's13 defined cases all match, while alternative P has26matches/14mismatches/152undefined. Other fixed rules remain separately tabulated; undefined strict co-reference does not reject pragmatic consequence-sensitive alternatives. Question/example and intro/example order coincide in all saved rows; lexical/example order agrees in300/480 pilot and128/256 EOS rows, so equal aggregate scores are not identity equivalence.

All **1,152** scheduled patch rows labeled archived P↔P′ retain identical pressure IDs and literal clauses while changing facts. This archive alias is never interpreted as distinct pressure wording. Same-emission output-copy counterexamples are actual argmax changes, not margin-only shifts: shared32 has7 common/1 readout out of232 same-emission cases per scope; candidate6 has44/9; outsider2 has12/9; selector2/empty/outside_mask2 have0. These actual counterexamples occur in changed-truth P/H or P/N cells; they reject a specified universal literal-copy account without identifying pressure mediation. For example selector2/common has232 same-emission margin-only changes and zero same-emission output changes.

## Explicitly post-hoc extension

After preliminary exposure to candidate6/common44/232 and shared32/common7/232 same-emission counterexamples and literal-copy counts, root proposed the bounded donor-role diagnostic; the independent critic accepted it before aggregate computation. This is outcome-derived and post hoc, separate from the original fixed rule library. No fitted rule, threshold search or inference was added.

`role-transport.json` compares literal donor identity, donor factual role transported into recipient facts, recipient output preservation and always recipient damaging across all6,528 completed patches, with6,912proposal/384excluded coverage explicit. It separately covers the pre-existing input-defined same-story named-truth-flip subset of3,456completed patches. All family/scope and exact clause/fact/story/alias cells include matches/mismatches/undefined, pairwise equivalences/disagreements and within-story means. In the3456-row input-defined truth-flip subset, candidate6/common matches are204literal/84role/148preservation/202recipient-damaging of288; shared32/common is276literal/12role of288. All6families/scopes are reported separately rather than interpreting a pooled rank that includes empty controls. No predictor is undefined and no outcome is noncandidate in this artifact. Grouped comparisons and predictor coincidences are essential; agreement does not uniquely identify abstract role encoding. The fixed `audit.json` remained byte-identical when this extension was added.

No interpretation establishes false factual assertion, realized omission, intent, audience belief, latent reporting-time knowledge, pressure-specific natural mediation, circuit removal, selective suppression or generalization. Retrospective behavior selection and known prior aggregates prevent prevalence or independent-confirmation claims. Final code/results are ready for the independent reviewers.

## Final review freeze

No code or result edits after this freeze unless review identifies a required correction. SHA256:

- `audit_native.py`: `86efc95da85042d15382ff4b44c8ebb49436a15c274f290007503626638e982f`
- `test_audit_native.py`: `658ae7a51e50f61e383b3047fc18b51f649437df4f7e29c93333b89ae5e7cdce`
- `results/final/audit.json`: `c1469a81d12e9e9c9e3526a10efe0eae710333dae70186bd4cb51dc76e9922b1`
- `results/final/role-transport.json`: `f9fb914a7fabce4788aa5a45e27692cc663b4f5e756643e44ebbe899477c68fd`
- `results/final/source-manifest.json`: `4246f5b2795da241a41189d5ba493482a607406eb4b95cd391303793f55f7910`
