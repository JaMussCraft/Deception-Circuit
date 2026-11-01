# Selective deception diagnostic implementation plan

> Agentic execution: bounded fresh workers, independent review, root integration. User already authorized execution; do not add another plan-approval gate.

Goal: execute the first-stage fixed-mask diagnostic reproducibly and cheaply, with valid donor and prompt controls, then use its results to scope a selective-mask pilot.
Architecture: pure frozen JSON manifest → existing EvalContext/dual-stream inference → row-level metrics and blinded generation review. No new hooks or training framework. Python3.9/3.12, existing torch/transformers compatibility.
Spec: `spec.md`; scientific plan in project_context/research_notes/Deception specificity and shared circuits/next_steps.md.

## Global constraints

Root-only git/submissions; preserve main and existing outputs; no notebooks; no paid APIs; at most20 cumulative reserved GPU-hours and max2 independent concurrent jobs. Count failures/retries, no auto-retry/requeue. Stage1 small target~2h, not a renewed budget. Coherent refusal desired success; label metrics separate from generated deception; preserve all selected denominators; paired assignment frozen before outcomes; all MLPs live.

## Task 1: Freeze paired inputs and donors

Requirements and tests: issues/01-manifest.md. Own evaluation/selective_diagnostics.py and tests/test_selective_diagnostics.py. Output pure manifest API and fixture tests, report exact API. Independent task review before use.

## Task 2: Bounded inference and durable results

Requirement brief to be finalized from Task1 API and review. Own evaluate_selective_deception.py, evaluation/selective_runner.py, tests/test_selective_runner.py, scripts/selective_deception.sbatch; optional surgical metrics extension only if needed. Reuse session/circuit resolver/gen engine. --dry-run resolves actual artifact identities, masks and cached tokenizer without loading weights; validate row counts and outputs. Execute frozen rows only, no automatic benchmark suite or paid grading. Cache results by full manifest/row/model/mask/donor/generation fingerprints, resume only exact matches; write incomplete status on missing rows. Score actual D/H probabilities/margins/full argmax. Generate donors under intact state, cache donor continuations and alignment flags. Record output quality and blinded review files, never infer deception from regex. Unit/tiny-model tests in both envs; main still untouched. Independent task/code review before GPU submission.

## Task 3: Smoke and pilot run

Root-only CPU dry-run then sbatch --test-only, reserve runtime×allocatedGPU count in ledger. Smoke initially15min1GPU, then use measured throughput/model-load time to set main reservation within cap. Validate no-op matches intact and nontrivial donor changes outputs; detect truncation/mask/denominator errors before main. Source commit and input hashes frozen per run. Up to2parallel independent chunks only after smoke passes; no duplicate donor extraction unless measured cheaper. Full table completion and generation counts required for stage1 completion.

## Task 4: Blinded analysis and next decision

Fresh Sol annotation worker gets anonymous prompts/outputs+ground truth and rubric, not mask/donor labels. All rows retained; ambiguity explicit, deceptive assertion overrides refusal wording. Independent review of ambiguous and a balanced sample; label-freeze before unblind. Pair/cluster effects and uncertainty with benign cost separately; one random mask not a null distribution. Astra reviews the scientific interpretation and proposed next pilot. Reconcile reserved vs actual GPU-hours and all job states. Update report/checkpoint with exact next task. Do not infer a dedicated deception mechanism or confirmatory specificity from this small diagnostic.

## Review focus

- Counterfactual policy and designation/content are distinct, self donor is no-op.
- Stored-template edits preserve semantic truth/answer identities and cluster denominators.
- Generation prompt change is an explicit transfer test; intact validity can fail.
- Dual stream alignment/padding/EOS/continuation reuse is recorded and tested.
- Cost/resume provenance: strict manifest identity, finite row/token/runtime limits, no hidden API or retries.

## Preflight interface check

| Pair/task | Interface / consistency | Resolution |
|---|---|---|
|1→2|Manifest dict/version/hash/rows; task2 consumes exact API|Task1 report freezes API before task2 begins; no simultaneous editing|
|2→3|CLI dry-run and frozen command/manifest to Slurm|Root reviews dry-run and test-only before reserve/submit|
|2→4|Anonymous generation rows and private mapping|Reviewer receives only anonymous export; mappings unblinded after labels freeze|
|1|1088scores/320generations nominal64clusters; all8conditions named|Smoke uses immutable subset, does not resample|
|2|No new hooks, use dual stream; reference shared|Tests must distinguish zero-removal reference and no-op donor|
|3|20h total and max2jobs vs initial2h target|Global user-amended cap authoritative; stage1 target is not a hard2h cap|
|4|Raw generated deception/n vs label accuracy|Separate output tables; incomplete/ambiguous explicit|

## Scientific correction carried across tasks

The final Task1 brief changes D−F/random comparison donors and small-order/alternative comparisons to the same nonself derangedH donor policy. Root/Astra found self-H retention is vacuous; paired core conditions remain routing/sanity only. The direct utility comparison is conditional on nonself mismatched-content interchange, not universal deletion. Task2 and Stage2 must retain this distinction. Target row counts unchanged; final donor-reference count comes from amended preflight. The data/control fix takes precedence over earlier abbreviated plan phrases.

## Analysis frozen before GPU outputs

Primary generative comparison: intact/core/D-minus-F/random under the same nonself H donor assignments,16 paired semantic clusters per policy. Report every rubric category on the full denominator; target coherent suppression=(truthful+coherent refusal/evasion)/n, alongside raw deceptive/n and its ambiguity bounds. On benign H, truthful/n is primary utility; refusal, malformed and empty remain separate. No copying-induced irrelevant output counts as useful suppression. Report paired changes and discordant counts. Original/reversed label scores and alternative-format generations are separate endpoints, never pooled as independent scenarios. Any uncertainty estimate resamples paired semantic clusters, not prompt variants; small-n intervals are exploratory, no confirmatory multiple-testing claims. Paired core donor conditions are routing/sanity diagnostics, not retention comparators. One random mask is a comparator, not a null distribution. All donor-reference generations are annotated against their own facts without changing target eligibility.

Pre-unblinding numerical analysis detail: primary generation view is named free_response in the schema; original/reversed are scoring views. Primary paired-cluster percentile bootstrap uses10,000 samples,seed0,95%intervals, exploratory only. Freeze label byte hashes against packetreceipt before private mappingread.
