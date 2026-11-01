# Frozen-mask pilot runtime — 2026-10-24

Implementation is opt-in in worktree `Deception-Circuit/.claude/worktrees/selective-transfer-v5`. No paid API calls, GPU/model experiment runs, notebooks, installations, jobs or git operations were performed by this worker. Tests use mocked transport and the repository's small synthetic test models. Root owns execution authorization and the reviewed ledger header.

## Runtime contract

New CLI inputs: `--benchmark-fixed-cohort`, `--benchmark-frozen-masks`, `--benchmark-configs`, `--benchmark-judge-cache`, `--judge-budget-ledger`. Stock state selection, model/dataset settings and suite-cache location remain defaults. Frozen pilot mode requires explicit fixed cohort, study-cache path and reviewed ledger; finest knockout and interchange are mandatory. The frozen manifest supplies exactly four removals and runtime adds intact, for five effective states without stock circuit-only/empty/random extras. Complete five-state blocks use the prospectively fixed `new-allW30` primary headline; stock knockout headlines retain their previous meaning.

Historical fixed-cohort input bypasses stock screening and screen-cache lookup entirely. It retains recipient IDs/beliefs and exact used native donor assignment, checks freshly rendered recipient prompts against historical strings before generation, and generates fresh intact and native donor responses through the same stock generation engine. No eligibility rejudging, refill, masking-dependent exclusion, old-device screen-hit claim or cache-key waiver occurs. Historical selection provenance is separate from current execution device/version provenance. Root must use one suite cell/task and the adapter's required five enabled gate families; technical calibration still must verify the actual model's effective support and all-open identity.

One explicit study judge-cache path uses the existing successful-verdict JSONL cache. Import policy and source immutability belong to report148's frozen importer/receipt; runtime adds no generalized cache service. Cache fingerprints remain the original full official judge requests, preserving exact historical request reuse. Guarded concurrent identical requests share one pending call. The imported cache is **not** assumed to cover all historic requests: report148 finds 81/323 exact hits and documents old rejudging text differences.

## Spending guard

`evaluation/benchmarks/judge_budget.py` reads an **existing** JSONL ledger, first row `{"schema":1,"reviewed":true,"max_usd":20,"max_paid_attempts":5000}` (smaller limits allowed). Root creates that reviewed receipt after independent review. Missing/malformed/torn/unreviewed ledgers fail closed. Each reserve and settlement is protected by an exclusive file lock, flushed and fsynced, across independent clients/processes. Pending calls reserve before transport; every transient retry reserves again. SDK automatic retries are disabled in guarded mode. The paid startup health-check uses the same ledger.

Only the four pinned plain-text OpenRouter judge models and official benchmark parameter/schema shapes are supported. Tools, images, multiple completions, arbitrary extra bodies/routing/plugins and unknown models/providers are rejected before transport. Full model context ceilings bound billable input, including formatting/schema overhead; full model output ceilings bound unbounded official requests. o3-mini always reserves its full 100,000-token output ceiling, including reasoning, even with a small visible-token setting. This deliberately avoids guessed local tokenization/hidden reasoning bounds or changing official prompt/output settings.

Pinned ceilings/rates are: Sonnet4.5 1M context/64k output at3/15 USD/M, Haiku4.5 200k/64k at1/5, GPT4o128k/16,384 at2.5/10, o3mini200k/100k at1.1/4.4. For nonreasoning models an explicit supported output maximum can reduce the output reservation. OpenRouter routing requires parameter support and maximum unit pricing for prompt/completion, plus zero per-request/image fees. An SDK that would drop/rename guarded parameters is rejected before transport.

Authoritative nonnegative finite `usage.cost` settles a reservation; absent/invalid cost retains the full reservation, even on transport errors or cancelled/empty/failed completions. Usage dictionaries, actual cost and response IDs are persisted when available. A charge greater than its reservation or ledger persistence failure stops judging for reconciliation. There is no automatic refund of unknown-charge failures. Conservative full-context reservation can temporarily exhaust the cap with concurrent requests, so calibration should start with low concurrency (Sonnet max500 reservation is about$3.0075; o3 reservation$0.66). Unknown-cost paths may stop early despite a low actual bill; that is intentional.

Sources checked directly on2026-10-24: [provider max-price and support requirements](https://openrouter.ai/docs/guides/routing/provider-selection), [parameter/reasoning-token caveat](https://openrouter.ai/docs/api_reference/parameters), model context/output ceilings and rates on [Sonnet4.5](https://openrouter.ai/anthropic/claude-sonnet-4.5), [Haiku4.5](https://openrouter.ai/anthropic/claude-haiku-4.5), [GPT4o](https://openrouter.ai/openai/gpt-4o), [o3mini](https://openrouter.ai/openai/o3-mini). These are prospective guard assumptions, not a paid execution receipt.

## Incomplete coverage

BudgetExceeded propagates through the judge rather than becoming a nondeceptive error verdict. Already-paid pending calls are drained and cached/settled before the stop propagates. Generated text and item IDs are checkpointed before inline judging; each completed config/block is checkpointed under `benchmark_partial/`. Budget stops preserve the partial block, mark missing states, stop later datasets, and suppress its efficacy headline. Per-config coverage separates missing/invalid judge results from model empty/refusal/evasion outputs. Refusals and model emptiness retain the frozen denominator and their raw categories; they are never counted as confirmed truthful correction. Fresh intact failures also remain in the cohort.

Known untouched-main worktree MASK sibling-path failure remains expected and is not repaired; final verification follows below.

## Verification and review follow-up

Relevant regressions after coverage/headline/prompt checks: mgnp **199 passed,19 skipped,1 known failure**; base **198 passed,20 skipped,1 same known failure**. Failure is exactly `tests/test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py`, the untouched worktree sibling MASK-path issue documented in report143 and the plan. Commands pinned OMP/MKL/OpenBLAS threads to1 and ran `tests/test_benchmarks.py tests/test_benchmark_eval.py tests/test_judge_budget.py`. Logs: `/tmp/v5-runtime-final-mgnp.log`, `/tmp/v5-runtime-final-base.log`.

Independent runtime review requested two additional strict seams: bind frozen runtime cache to `judge_cache_import.output.path`, reject same-file historical source aliases, and verify the initial imported byte-prefix SHA256 before appends; and reject guarded structured judging when the SDK lacks parse support rather than silently taking the old prompt-appending fallback. These are implemented; append-aware resumes allow only complete valid `{key,text}` rows after the frozen imported prefix, preserving the existing cache's documented last-write semantics. Adapter report148 adds `imported_bytes` to the frozen cache receipt. This avoids mutating originals or silently substituting unrelated cached verdicts. Final focused verification of those review additions is recorded next when complete.

Final reviewed source focused checks: **86 passed in mgnp;86 passed in base** (base3existing dependency warnings), running `tests/test_judge_budget.py tests/test_benchmark_eval.py`. Structured judge refusals also preserve available billing cost/response IDs while remaining failed verdicts. Stable runtime source hashes are saved in `transfer-v5/runtime-source-hashes.json`; all four final/reviewed logs were copied to `transfer-v5/runtime-{final,reviewed}-{mgnp,base}.log`. Actual frozen-cache consumer validation awaits report148's regenerated `imported_bytes` receipt before any live run. Root still owns calibrated model/support checks, exact launch review, ledger initialization, paid-call authorization and all GPU/job/git operations.

## Concrete root commands (after reviewed ledger initialization)

The original D69 anchor already has the exact five required gate families enabled (`attention_blocks`, `attention_heads`, `attention_neurons`, `mlp_hidden`, `mlp_output`) and the other gate families disabled. Its model is `llama-8b-instruct` → `meta-llama/Llama-3.1-8B-Instruct`. Use that single unchanged anchor plus one explicit home task, with study output outside the historical run. Explicit dataset names avoid accidentally including `lb:harm-pressure-choice`, which is not in the frozen cohort. Offline HF flags require existing cached model/tokenizer inputs for live execution; the CPU dry-run itself loads no model/tokenizer and calls no API.

```bash
v5_study=/projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5
v5_tree=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/selective-transfer-v5
v5_anchor=/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742
cd "$v5_tree"
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
/u/swong2/.conda/envs/mgnp/bin/python evaluate_circuit.py "$v5_anchor" \
  --task-from "$v5_anchor" --evals benchmarks --ablation interchange \
  --knockout-granularity finest --benchmark-ref-pool honest \
  --benchmark-repo-root /projects/beto/swong2/Alignment \
  --data-dir /projects/beto/swong2/Alignment/Deception-Circuit/data/datasets \
  --benchmark-fixed-cohort "$v5_study/fixed-cohort.json" \
  --benchmark-frozen-masks "$v5_study/frozen-masks.json" \
  --benchmark-judge-cache "$v5_study/judge-cache-import.jsonl" \
  --judge-budget-ledger "$v5_study/judge-budget.jsonl" \
  --mask-judge-model openai/gpt-4o --mask-numeric-judge-model openai/o3-mini \
  --benchmark-new-tokens 512 --benchmark-gen-batch-size 8 \
  --benchmark-coherence-batch-size 2 --judge-concurrency 2 \
  --reference separate --n-random 0 --benchmark-n-random 0 \
  --no-benchmark-screen-cache \
  --benchmarks sandbagging lb:instructed-deception lb:harm-pressure-knowledge-report lb:convincing-game \
    mask:continuations mask:disinformation mask:doubling_down_known_facts mask:known_facts mask:provided_facts mask:statistics \
  --output-dir "$v5_study/eval5-full" --dry-run --device cpu
```

Root chooses the actual reviewed ledger filename if different; substitute it consistently. The dry-run prints all five named states, each fixed recipient/donor count and native token budget/judge, historical source paths, exact imported cache path, ledger totals/limits, pinned prices and model token ceilings. It performs no screen lookup, model loading, paid health-check, API call or GPU execution. It cannot run successfully before root creates the reviewed ledger; this worker has deliberately not created one.

For the first bounded **complete sandbagging block**, use the same arguments, replace the benchmark list with only `--benchmarks sandbagging`, replace the output directory with `"$v5_study/eval5-sandbagging-calibration"`, add `--skip-judge-check`, remove `--dry-run`, and use `--device cuda` inside root's reviewed H200 Slurm wrapper. Sandbagging is entirely locally graded, so the 50×5 recipient block and its historical native donor regeneration cost **zero API dollars**. Preserve native1024 tokens: `bench.new_tokens=1024` takes precedence over the CLI's general512, exactly as stock EVAL5. This final consumer precedence bug was reproduced with the parameterized `test_fixed_cohort_regenerates_intact_and_used_native_donors_without_screen[1]`, then fixed. No reduced-row or shortened-token calibration flag was introduced.

Before submission, repeat the CPU dry-run with the sandbagging-only list to read its actual donor count and rough runtime estimate; the estimate is the preexisting A40 token-time calibration, not a measured H200 promise. Root's proposed30-minute cap is an external hard bound; root should assess the printed estimate plus technical all-open/support checks before launch. Five complete states are the reporting unit; a wall-time interruption does not establish a completed block.

Read-only actual artifact contract check on regenerated receipts PASS: imported cache prefix matches; exact states are `full,new-allW23,new-allW30,oldD69,random30`; sandbagging50×1024 native tokens and each selected LB dataset50×512 agree with frozen historical budgets. This check loaded only JSON/source metadata, no model, ledger, API or CUDA.

Final narrow native-budget regression: **2 passed in each environment**, including benchmark-native precedence despite a smaller general CLI maximum, with no source changes after these checks. Logs: `transfer-v5/runtime-native-budget-{mgnp,base}.log`. Source hashes were refreshed for this last change and the detailed dry-run output; reviewer was explicitly reactivated for scoped last-change review.

Actual sandbagging JSON inputs contain50 recipients and50 used native donors at1024 tokens. The existing A40 estimate is4,725 seconds (78.75 minutes) of generation:787.5 intact+787.5 donor+3,150 removal seconds. It excludes model startup and coherence overhead. A30-minute H200 cap needs more than approximately2.6× generation speedup before overhead; the historically observed roughly5× H200/A40 ratio suggests feasibility but does not measure this launch. Root should rely on hard wall time and technical calibration, preserve incomplete blocks, and avoid interpreting this estimate as guaranteed completion.

## Combined-integration cache-flag guard follow-up

Root combined tests exposed one new failure: the existing introspected EVAL5 flag-omission guard had not classified five new flags. The narrow fix changes only `tests/test_screen_cache.py`: configs/frozen masks affect ablation states only; fixed cohort dispatches to its explicit loader and bypasses stock screen-cache load/save; judge-cache path and budget-ledger authorization retain official request fingerprints and do not change stock key semantics. The existing nonempty argument-group assertions and exact unclassified-set guard remain intact. No production key or runtime code was changed.

Semantic regressions prove all five flag mutations leave the stock key unchanged, the fixed-cohort consumer dispatch cannot consult stock screening/cache, and an actual stock screening loop reaches a selected partial cohort before BudgetExceeded on its second eight-row judging chunk, propagates that exception, and never calls save or writes a screen artifact. Full screen-cache suite: **66 passed in mgnp;66 passed in base** (base3existing warnings). Logs: `transfer-v5/screen-cache-final-{mgnp,base}.log`; test hash: `transfer-v5/screen-cache-classification-hash.json`. Scoped reviewer reactivated; no broader refactor.

Scoped independent classification review **PASS** in report151 addendum; reviewer independently ran the7 new focused cases in both environments and the omission guard in mgnp. No remaining cache-classification finding.
