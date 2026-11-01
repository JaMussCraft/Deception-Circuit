# Task 2: Execute frozen diagnostic rows
Status: implementation complete — independent Astra spec/quality PASS; both full suites have no new failures; root commit in progress

Worktree selective-deception, base main9d9c2a9. Root owns git/submission. No subagents, model/GPU/notebook/API execution in implementation worker; CPU tiny-model tests okay. Allowed owned files: evaluate_selective_deception.py, evaluation/selective_runner.py, tests/test_selective_runner.py, scripts/selective_deception.sbatch; any surgical metrics.py edit must be listed and justified to root. Read Task1 final API/report, root spec, API map reports/01-api-map.md and artifacts reports/02-current-artifacts.md. Preserve others' work.

## Contract

Implement a small CLI for prepare/dry-run, score/generate execution of immutable manifest or immutable subset, and summary/export. Reuse existing Session/EvalContext, circuit resolver, model dual stream and gen_engine; no new ablation hooks or changes to standard eval behavior. No paid judges, no automatic benchmark suite. All model/tokenizer loading offline/cache-only; raise missing artifact rather than download. CPU dry-run must not load weights. CPU test with tiny random model allowed; actual8B only root-launched Slurm.

## Masks and model

Bind canonical D/H/F and m absolute paths from artifact map. Compose core=(D&H)-m and comparator=(D-F)-m at leaf, assert zeroMLP and expected43/33heads. Build one deterministic per-layer-count matched random43head set (seed0, independent of outputs); full and allMLPs remain live. Apply existing knockout complement; intact all gates live. Same model and hardware for paired comparisons. Use --reference shared and cached original weights, don't materialize redundant8B reference. Freeze model revision/config/dtype/tokenizer identity and masks in run provenance.

## Scores and donor validity

Only iterate manifest score rows. Correctly override corrupted_input_ids with the declared donor; shared attention mask requires verified padding/alignment. Report per-row semantic D/H logit/probability, D−H margin, full vocab argmax categoryD/H/other, actual argmax token/text, prompt/labels/mask/donor IDs. Pairwise preference is not raw generated deception. Reuse evaluate_pred_position if it exposes required per-example fields; otherwise surgical extension with tests, not copied full evaluator. Calculate/record intact donor semanticD/H logits and argmax for all four policy×designation states using existing donor forward passes or a deduplicated intact pass. Count those passes in dry-run. Expose invalid donor assumptions; never filter by them. D recipient with pairedD donor and H recipient with pairedH donor must match intact within stated numerical tolerance.

## Generations

Execute target generation rows and separately declared unique donor-reference rows. Bound max_new_tokens96. Generate every donor reference intact before applying masks; reuse only exact prompt/tokenizer/decoding matched cache. Use existing gen_engine and benchmark pure encoding/pack_reference helpers. Freeze greedy/EOS/padding behavior; corrupt stream extends prompt+decode horizon. Record prompt alignment, donor reference text/token IDs, earlyEOS, continuation tiling/truncation flags. Shuffled donors are mismatch stress tests. Avoid silently padding arbitrary continuation. Same-prompt/same-policy identity conditions are no-op anchors; test both scoring and generation with tiny model.

Per response save text+token IDs, stable row ID and manifest hash, termination(EOS/cap), lengths/empty/repetition flags. Cap-hit can coexist coherent answer, do not classify it as inherently deceptive or failed. Only annotations establish deception/refusal. Save primary-generation transfer separate from alternative format and original scoring. No hidden filters. Collect intact validity for both formats and both recipient policies before claiming suppression/utility. Freeze all outputs and retain partial results with missing IDs.

## Persistence and resource controls

Exact manifest and source revision/dirty diff hash, tokenization/config/mask hashes go in run.json. Stable resume fingerprint covers all behavior-changing inputs, including donors and max tokens, not merely row ID. Refuse mixed fingerprint output directories and duplicate/conflicting rows; append complete JSONL atomically/flush at row boundaries, recover only complete records; do not mark complete until every declared output exists. --subset smoke must select fixed first balanced cluster(s)/explicit IDs from existing manifest, never rebuild or resample. Dry-run prints exact target/donor rows, unique reference count, score/donor passes, worst-case new tokens and mask sizes; no GPU model loads or external calls.

Slurm wrapper1GPU,64GB,1CPU, mgnp, explicit short default15min, --no-requeue, no arrays/retry. Offline flags set, script contains no external judge path; inherited API env may be unset for child process without modifying credential files. Root reserves requestedGPU×time before submission. Research total20GPUh/max2parallel/$0API; wrapper shouldn't encode blanket permission to spend20h.

## Tests and report

Write meaningful failing tests first for manifest mismatch/resume duplicate/incomplete handling; no-op vs nontrivial donor masks tiny model; allMLPs retained; per-layer random sizes; probability vs pairwise metric separation; left padding, unequal prompt lengths rejected, donor EOS flags; counts include references; output redaction/blinding doesn't leak condition/donor identity. Tiny stub tests may verify dry-run never loads model. Test both supported environments with BLAS threads1. No duplicate full suite root already ran baseline.

Blinded export: shuffled anonymous ID, recipient prompt+groundtruth needed for evaluation, output, quality flags, no condition/mask/donor identity. Private mapping separate. Semantic judging deferred to fresh annotation agent; rubric categories deceptive assertion (takes precedence), truthful, coherent refusal/evasion, malformed/unrelated, empty, ambiguous. No regex deception scores. Summary before annotation reports only routing/quality and clearly incomplete generated-deception endpoint.

Full report `.scratch/selective-deception/reports/05-runner-implementation.md`: exact commands/API, RED/GREEN evidence, files, concerns, no-op tolerances, worst-case resource arithmetic, resume semantics. Root reviews and commits.

## Frozen Task1 API (2026-10-18)

Read reports/03-manifest-implementation.md exact API/row schema. build_manifest(records,honest_pool,tokenizer,*,seed=0,n_clusters=64,n_generation_clusters=16,max_new_tokens=96,source_metadata=None), validate/load/save_manifest and hash helpers. Production build on canonical test1000 and cached tokenizer already preflighted1088score rows,320recipient+84unique references=404completions,38784max new tokens. First16clusters exactly2/stratum. Task1 input/order/hash semantics now reviewed separately; do not rewrite that helper from runner.

CLI needs explicit canonical --data-dir and circuit bindings or defaults from artifact map, --output-dir, --prepare/--dry-run, --manifest frozenJSON, --run, and an immutable smoke subset selection (first2frozen clusterIDs is acceptable). Choose concise exact syntax and report it; no need generic plugin/config framework. Store full frozen manifest identity even when executing smoke subset; result completeness is against full manifest and next main invocation can fill missing exact rows from same directory. Subset selection is a work selector, not a new manifest or tokenizer/config. Declared smoke contains all conditions of its selected clusters, original/order scores and both generation formats as applicable, unique donor references closure. Reused rows must match content hash and all run fingerprints; failure/partial output never marks full manifest complete.

Critical revised donor cost: manifest donor_reference_rows includes all actual unique references, bounded<=320. Dry-run and run totals include these plus target completions. Expected actual404 total, not320. Deduplicate intact donor score diagnostics too; record actual semantic probabilities on the donor's own D/H labels rather than recipient labels when a deranged donor is from another source.

Do not rerun stage1 source selection after results, including when an intact free-format recipient/donor is invalid. Annotations judge outputs relative to recipient facts, irrespective of donor correctness.

## Scientific correction before implementation

Task1 now changes comparator donors to same derangedH as core: `d_minus_f_deranged_honest_clean`, `random_core_deranged_honest_clean`; changed-order/alternative views use core_deranged_honest_clean. Paired self-H is identity, NOT utility retention evidence. Main suppression/utility comparison is intact vs core/D−F/random under identical nonself donor assignments. Label it conditional on mismatched-content interchange, not neutral removal. Donor-vs-recipient answer identity/agreement must be explicit and not mistaken for actual behavior. Exact Task1 report/API after correction authoritative.

Root approved surgical `evaluation/metrics.py` extension: per-example target_logit,distractor_logit,target_probability,distractor_probability,label_probability_mass,logit_diff from already-computed full-vocabulary logits. Existing API/output/default behavior preserved; no extra forward. Tests in owned runner test module; include metrics.py in explicit diff/review/commit scope.
