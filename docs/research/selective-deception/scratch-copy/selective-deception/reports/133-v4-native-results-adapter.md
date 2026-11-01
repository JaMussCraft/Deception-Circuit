# V4 post-freeze native analysis adapter

October21,2026. Prepared `analysis/optimization_v4_native_results.py` and its focused synthetic test file. No real native output, annotation or heldout result was read. Driver validation/export belongs to the separate native-driver worker; this adapter implements only post-freeze paired analysis and never selects masks, judges, generates, loads a model, or submits a job.

The adapter preserves the immutable v3factual rubric/category mapping and paired metrics, with the **literal v4closure**: intact, oldD69, oldallW28, new-allW23, new-allW30. The comparator is genuinely oldallW28/count28; it is never aliased to oldW9. A public `conditions_valid` helper checks the exact labels and head counts0/69/28/23/30, with unique32×32query-head geometry, for driver integration.

Post-freeze analysis requires exactly352physical labeled views:320targets (32recipients × D/H ×5conditions) plus32own-context H donors. The64all-open identity-control generations are explicitly not annotated. Exact recipient/donor/condition Cartesian closure, disjoint recipient/donor IDs and consistent one-use donor assignments are enforced. The packet manifest must bind this adapter as `pipeline_sha256`, require the immutable `native_results.py` classification-contract SHA, and contain the exact six bounded public chunks plus factual packet/private map/rubric. Packet/source hashes and the root final-label freeze must match.

Before private-map **JSON decoding**, the adapter checks root labels were frozen before condition joining, their exact byte hash, the packet/private-map hashes, all352unique public labels/views, all public schemas/digests/chunk coverage, rubric identity, category/uncertainty/flag/rationale schemas and empty-response consistency. Private bytes may be hashed for identity checking; no condition-bearing private JSON is decoded before those gates. Joined rows then require exact public/private digests and consistent empty/cap quality types. Analysis output must use a new directory.

Metrics remain unchanged: raw false/true/refusal/ambiguous/damage/empty counts; uncertainty bounds; baseline-false truthful corrections and coherent-refusal suppression; paired H retention, loss and gain identities; donor own-context quality; replay coverage; empty/cap/repetition flags. Capped false assertions still count toward raw false rate, while capped/empty/uncertain responses cannot establish clear suppression or truthful capability. A coherent D refusal counts as suppression; H refusal is utility loss. Net H correctness never cancels individual losses/gains. Donor quality is descriptive and never screens cases. Labels are model-agent judgments, not human ground truth; no sampling confidence interval or native-based reranking is introduced.

Adapter SHA256: `bf574b03fb2bc5aff184059f21c4a2f715fdbea7ce185c41db5aac4607ff8ceb`.

Verification (synthetic CPUfixtures only):

- Base Python3.9: **25passed** in1.77s.
- mgnp Python3.12: **25passed** in2.62s.
- Base `-m py_compile` for adapter and tests: passed.

Both pytest commands use `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 <python> -m pytest -q .scratch/selective-deception/analysis/test_optimization_v4_native_results.py`. Counterexamples cover literal comparator counts/no9-head alias; refusal versus ambiguity/damage; caps/empty/uncertain truth; zero capability; paired loss/gain swaps; incomplete/duplicate/wrong-condition/donor closures; changed pipeline/classification/rubric/public-view/chunk hashes; missing or post-join root freeze; incomplete or invalid labels; and private-map tampering. Read guards verify invalid public labels or freezes never reach private JSON decoding. Exclusive output and a valid complete352-view analysis are also exercised.

Future root-authorized use, only after the final complete blind labels are frozen:

```bash
python analysis/optimization_v4_native_results.py analyze \
  --packets PACKET_DIR --labels FINAL_LABELS.json \
  --freeze ROOT_FINAL_LABEL_FREEZE.json --output NEW_ANALYSIS_DIR
```

This creates only `native-results.json` with final label/packet/freeze and pipeline/classification bindings. Original driver, old helpers, rubric/category contract, training runtime, selection receipts, prospective inputs and ledgers were not edited by this worker.
