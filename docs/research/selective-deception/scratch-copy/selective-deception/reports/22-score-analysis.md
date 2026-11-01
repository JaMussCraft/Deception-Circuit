# Predeclared descriptive score analysis (2026-10-18)

Implemented `analysis/summarize_scores.py` and `analysis/test_summarize_scores.py`, standard library only. No real outcomes or manifests were opened for implementation or verification. Existing generation analysis is unchanged. Root must review this utility before invoking it on the complete corrected Stage1r2 run with its trusted blind-preparation receipt.

API: `summarize(manifest_path, run_dir, packet_receipt) -> dict`. `run_dir` must contain complete `run.json` and `results.jsonl`; `packet_receipt` is the trusted `prepare_blind.py` output `hash_manifest.json` for those exact inputs. It reuses that CPU-only utility's canonical hash and expected-row derivation, without importing any model code. It performs no inference, jobs, APIs, plots, bootstrap, filtering, eligibility selection, or generated-response annotation.

## Integrity and complete coverage

The receipt must record320 recipient generations,84 donor references,404 blinded records and1848 full results. Before interpreting score payloads, the utility checks SHA256 of the exact manifest/run/results bytes against that receipt. Paths may move, but bytes may not change. It recomputes the manifest content hash, checks the run's embedded manifest, recomputes the run fingerprint and matches both to receipt identities. Every record's kind, embedded frozen inputs, row hash, result hash and run fingerprint must match the expected manifest row; IDs must be unique, declared and complete. A missing donor score is fatal even if all recipient scores exist. Duplicate JSON keys and unterminated result logs fail closed.

Declared full counts are exact:1088 recipient scores (1024 original +64 reversed),320 recipient generations,84 donor references,356 deduplicated intact donor scores =1848. The utility checks64 unique semantic clusters and source IDs, D/H token IDs, endpoint identity and intended-policy mappings, unique cluster membership in every recipient cell, all64 original clusters in every condition/policy, and the same16 clusters in all reversed/free_response/alternative cells. Nonself selectivity conditions must have an H-clean donor, a different cluster, and the same fixed donor-cluster assignment across conditions/policies/views. Every numeric score must be finite; D/H full-vocabulary probabilities and their label mass must lie in[0,1], and label mass must equal their sum within `rel_tol=1e-5, abs_tol=1e-6`. Stored argmax categories are checked against actual local D/H token IDs; donor intended-answer flags must agree with their intended original-label argmax.

Receipt authenticity/custody is a root responsibility. This utility records receipt SHA256 and input hashes in its output; hashes alone do not prove that the receipt came from an independently trusted preparation step. Generation text is parsed only as part of complete result-record integrity checks and is not semantically analyzed. There is no partial-run or count-override mode.

Root-only command after completion, trusted blind preparation, and independent source review:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/sw/external/python/anaconda3/bin/python3.9 \
  .scratch/selective-deception/analysis/summarize_scores.py \
  --manifest /ABSOLUTE/FROZEN/STAGE1r2/manifest.json \
  --run-dir /ABSOLUTE/COMPLETE/STAGE1r2_RUN \
  --packet-receipt /ABSOLUTE/TRUSTED/BLIND_PACKET/hash_manifest.json \
  --output /ABSOLUTE/PRIVATE/NEW_SCORE_ANALYSIS.json
```

The output is exclusively created with mode0600; existing paths/symlinks are refused. It contains private condition identities and should not go to blinded annotators. `audit_rows` contains all1444 recipient/donor score records with IDs, endpoint metadata, numeric scores and argmax identities, bound to the full input receipt.

## Recipient score tables

`recipient_tables` keeps `view=original` and `view=reversed` separate. Original:8 conditions ×2 recipient policies ×64 clusters =1024 observations,16 table cells each n64. Reversed: intact/core_deranged_honest_clean ×2 policies ×16 clusters =64 observations,4 cells each n16. No views are pooled. All four primary conditions have `role=primary`; the other four original conditions have `role=paired_core_routing_diagnostic` and are not retention comparators.

Each cell contains n, mean_D_probability, mean_H_probability, mean_label_probability_mass, mean_D_minus_H, and full-vocabulary argmax counts D/H/other summing to n. Probabilities are full-vocabulary probabilities, not renormalized two-label probabilities; D_minus_H is the stored logit margin, not a probability difference. `policy_label_argmax_count/rate` matches local D for recipient policy D or local H for policy H. These are intended answer-label metrics, **not actual generated semantic deception rates**, and must not be reported as such.

For each nonself interchange condition, `donor_intended_token_match` separately reports n, the number of recipient argmax tokens exactly equal to the donor's intended answer token, and the intended token's relation to local recipient D/H/other. The donor token is resolved from the donor cluster's **original** D/H label mapping indexed by `donor.intended_label`. It is not resolved from recipient labels or directly from donor policy. Exact matches can overlap local D/H when answer tokens coincide; the donor-match count is never folded into or used to redefine D/H/other. This is a copying diagnostic, not evidence of semantic deception, useful suppression, or benign utility.

## Donor diagnostics

`donor_tables` describes356 unique intact forwards, grouped separately by original/reversed/free_response/alternative donor view, donor policy, and clean/corrupt factual stream. Deduplication exactly follows the runner: token inputs plus the donor's local semantic labels; the first declared endpoint supplies descriptive provenance. Counts are unique forward identities, not target-use frequencies. They never modify recipient denominators or selection.

Each donor cell retains original D/H probability means and argmax counts, and adds own-fact truthful/false/other argmax counts, mean own-fact truthful/false probability, intended original label, and intended-policy argmax count/rate. Mapping:

| Donor policy | Stream | Own-fact truth in original labels | Intended original label | Intended own-fact behavior |
|---|---|---|---|---|
| D | clean | H | D | false |
| D | corrupt | D | H | false |
| H | clean | H | H | truthful |
| H | corrupt | D | D | truthful |

Factual truth changes with stream; intended own-fact behavior follows policy in both streams. These score diagnostics are separate from generated donor validity labels against donor facts.

## Paired descriptive effects

`paired` contains30 original-view effects: five condition/reference comparisons ×two recipient policies ×three endpoints. Comparisons are each core/D−F/random minus intact, plus core minus D−F and core minus random. Endpoints are D_probability, D_minus_H logit margin, and truthful_label_argmax (full-vocabulary argmax equals original H on the clean recipient). Each comparison matches exactly the same64 semantic cluster IDs within policy and reports `difference = mean(condition - reference)` with n_pairs64. Binary H-label contrasts also report gain/loss/both_1/both_0 counts. Negative D probability/margin changes and positive H-label changes have their literal answer-label meanings; none automatically establishes semantic suppression.

There are no new confidence intervals, bootstrap procedures, significance tests, multiple-testing selection, or reversed-view paired effects. These descriptive score shifts complement the separately predeclared generation intervals. Core43 versus D−F33 is unmatched in component count. Random43 matches the core's layer counts, but one fixed random comparator is not a null distribution. Paired core donor conditions are routing/sanity diagnostics. Findings remain conditional on nonself mismatched-content interchange, rather than universal deletion.

## Verification

Synthetic fixture creates all64 semantic clusters, all1088 recipient score rows,320 synthetic recipient-generation placeholders,84 donor references, and356 unique intact donor scores. No real outcome file was opened. Fixture probabilities, label masses, margins, local argmax IDs and cross-cluster donor matches are known independently of the summarizer.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/sw/external/python/anaconda3/bin/python3.9 -m unittest discover \
  -s .scratch/selective-deception/analysis -p test_summarize_scores.py -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/u/swong2/.conda/envs/mgnp/bin/python -m unittest discover \
  -s .scratch/selective-deception/analysis -p test_summarize_scores.py -v
```

Final verification: **7 tests passed in each environment**, Python3.9:8.452s; Python3.12:8.763s, BLAS/OMP/MKL threads fixed to1. Both environments exercise CLI `--help`, complete synthetic CLI invocation, output mode0600 and overwrite refusal. Checks cover separate views, exact counts, known means/margins, all30 contrasts, binary discordance, all four donor policy/stream mappings, cross-cluster donor token matches, repeatability, exact receipt/input byte binding, partial/duplicate/extra results, fingerprint/hash/input/kind tampering, truncated JSONL, malformed/invalid/nonfinite payloads, duplicate JSON keys, and duplicate paired semantic clusters.

Only the owned synthetic score test file was discovered for these runs. No actual analysis invocation, GPU/model/API/job/git/notebook/subagent operations occurred.

Root independent source reviewPASS before realuse. Fullfrozen1848integritychecked, separate64/16denominators anddonorownfactmappingcorrect, exactdonorcopytokendiagnostic keepslocalD/H/otherseparate, descriptivepairedcontrastsnotlabeledsemanticdeception. No codechanges ortest reruns.
