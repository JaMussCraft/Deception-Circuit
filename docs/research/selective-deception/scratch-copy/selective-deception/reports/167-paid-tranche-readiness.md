# Paid LB/MASK readiness — 2026-10-24

Recommendation: finish/audit SB first; keep its runtime source bytes frozen. Then reuse the existing public evaluator and generic raw-token checkpoints for fixed LB and MASK blocks, with one narrow paid-launch wrapper/receipt adaptation. No new judge/cache infrastructure is needed. Existing SB wrappers cannot launch these paid blocks unchanged. All dollars/GPU hours below are prospective; this audit made no requests or submissions and changed only this report.

## Existing launch path and minimal remaining work

`transfer-v5/launch-commands.json` contains exact public CLI argv arrays `commands.full` and `commands.sandbagging`; its status explicitly says CPU preflight only, not execution authorization. The full array already has the correct D69 model/task anchor, five frozen masks, fixed cohort, finest interchange, honest native donors, explicit benchmark repository root, mgnp interpreter, shared judge cache/ledger and judge overrides. Its benchmark order is SB, LB instructed-deception, harm-pressure-knowledge-report, convincing-game, then the six MASK splits. General512 preserves SB's native1024. Paid datasets all have native512.

The precise new argv derivation, using existing options only, is:

```python
# Preparation specification, not an existing receipt or submitted command.
argv = json.load(open(STUDY / 'launch-commands.json'))['commands']['full']
a = argv.index('--benchmarks') + 1
b = argv.index('--output-dir')
argv[a:b] = names  # one fixed split, or the fixed LB/MASK list below
argv[argv.index('--output-dir') + 1] = str(new_output)
argv += ['--benchmark-generation-checkpoint-dir', str(new_checkpoint),
         '--benchmark-stop-after-generation-batches', str(positive_new_batch_limit)]
# CPU preflight only: append ['--dry-run', '--device', 'cpu'].
```

Fixed names, in existing order: `lb:instructed-deception`, `lb:harm-pressure-knowledge-report`, `lb:convincing-game`; then `mask:continuations`, `mask:disinformation`, `mask:doubling_down_known_facts`, `mask:known_facts`, `mask:provided_facts`, `mask:statistics`. Prefer a fixed single-split argv/output/checkpoint for each complete five-state reporting block. Freeze that choice before outcomes. Checkpoint execution identity includes the entire benchmark list: do not change it while resuming the same checkpoint. Never use SB's output/checkpoint directory for paid work.

Reusable unchanged: `evaluation/generation_checkpoint.py`, `generate_under` integration, fixed-cohort fresh intact/used-donor generation, per-mask generation and budgeted JudgeClient. The raw checkpoint supports dataset/phase names generally, not SB only. It preserves original stable buckets, order, tokens, EOS/pad, masks and donor/corrupt identity. It caches generation only; coherence and judging rerun, with exact successful judge-request hits reused.

SB-specific pieces requiring a small *new* paid counterpart, preserving originals:

- `run-sandbagging-segment.py`: receipt purpose, expected argv, output/checkpoint names, one-use guard, fixed proof path and completion test are hardcoded SB50/native1024. Completion must instead require the declared split's exact fixed count/native512 and all five states, complete valid scoring, fresh output and intact donor/input bindings.
- Its imported `run-sandbagging.py.clean_environment()` strips every API credential; paid wrapper must intentionally make only the required OpenRouter credential available, without printing it. Preserve one H200, absolute Python/bash launcher, CUBLAS4096:8, timeout/process-group kill, no requeue/retry and per-receipt once guards.
- SB auditors are also hardcoded. A bounded paid audit must additionally reconcile shared ledger attempts/usage/cost, cache prefix/appends, complete state coverage and unscored/error categories.

No executable paid SBATCH command or paid execution receipt currently exists. Before launch: reviewed counterpart + exact argv/source/input/proof bindings, shared-cache/ledger validation, CPU public CLI dry run, new reservation and receipt. Source changes under the current worktree would invalidate active SB checkpoint identity; leave them until SB finishes, or avoid runtime edits entirely. Proof002 demonstrates generic cold restart but does not measure LB/MASK throughput or API behavior.

## Paid counts and cost

Frozen counts: LB50 each ×3 ×5 states =750 response requests at most; MASK171 ×5 =855. Empty responses can skip requests and identical official request keys can deduplicate. Used donors require generation but no new belief/eligibility judging. Maximum distinct response requests before those savings: **1605**, plus up to four distinct-model startup health requests in a combined paid launch. Separate launches add their own health probes. Each transient retry is another attempt/reservation; the default permits up to six attempts/request but the shared5000/$20 guard stops earlier.

|Judge / use|Response requests|Official visible output limit|Hard reservation per attempt|
|---|---:|---:|---:|
|Sonnet4.5 / LB instructed|250|100|$3.0015|
|Haiku4.5 / LB harm report|250|100|$0.2005|
|Sonnet4.5 / LB convincing|250|500|$3.0075|
|GPT4o / MASK binary|775|500|$0.325|
|o3-mini / MASK statistics|80|no explicit cap; reasoning low|$0.66|

Rates are frozen in `judge-pricing-reference.json`, with model ceilings in `judge_budget.py`: Sonnet3/15, Haiku1/5, GPT4o2.5/10, o3-mini1.1/4.4 USD per million input/output tokens. Hard reservations intentionally charge full supported input context, and o3 full100000 output/reasoning ceiling. Summing these full-context bounds over all1605 requests gives **$1857.05**, before startup/retries. This is a rigorous deliberately loose bound, not an expected bill. The shared guard enforces at most$20 committed/pending exposure and5000 physical attempts; it does not guarantee complete coverage under$20. Missing authoritative `usage.cost` retains the full reserve and can stop a cheap run early. Concurrency2 can have two large reservations pending.

Expected-cost planning used the exact selected historical full-row `judge_prompt` lengths from the two source-bound format-control suites, not historical dollars. Totals: instructed67208 chars, harm38050, convincing88959; MASK binary771642, statistics109163. These old texts include old generated responses. New responses are at most512 Llama tokens, but Llama tokens are not judge tokens. The following transparent proxies add **another512 input tokens plus64 framing/schema tokens per request**, assume no cache savings/retries, use maximum visible judge outputs100/500, and vary numerical reasoning/output from1000 to10000 tokens/call:

|Input proxy|LB total|MASK binary|MASK numerical|All paid responses|
|---|---:|---:|---:|---:|
|historical chars/4 +576/request|$4.02|$7.40|$0.55–3.72|**$11.97–15.14**|
|historical chars/2 +576/request|$4.65|$9.81|$0.70–3.87|**$15.17–18.33**|

These are planning sensitivities, not tokenizer-derived upper bounds or a guarantee that numerical reasoning stays under10000. Startup at its full4096 output settings adds at most about$0.18 by the same small-input proxy; repeat launches, retries, longer reasoning and tokenizer differences consume remaining margin. Historical visible numerical verdicts are short (685 total chars for16), but reveal no reasoning-token usage. Historical costs/usage were never saved. Broad tokenization/pricing research is unnecessary: freeze rates already reviewed; record actual provider usage/cost on the first real requests and stop on guard failure.

Imported cache audit reports81 hits/242 misses for323 historical requests (the pre-exclusion historical audit, not all1605 future requests). Do **not** deduct81 prospectively: fresh H200 outputs may differ. Conservative planning above takes zero savings. The cache already contains original last-write choices, including52 differing LB duplicate occurrences and80 selected historical full texts differing from cached last-write text; it cannot restore a unique original grading history.

## Cache, budget and provenance constraints

Use exactly `transfer-v5/judge-cache-import.jsonl` and `judge-budget.jsonl` for every paid block. Original cache sources stay immutable. Frozen initial prefix:5982474 bytes, SHA256 `c1a4c31f3113c029c77700c7f728d3398b32b32f9c2516eb5939b53e19acea42`; only complete valid appended key/text rows are allowed. Runtime validates exact declared path, rejects historical source aliases, verifies prefix hash and append syntax. Never rerun the importer over paid appends. Keep its declared within-source last-write policy/cross-source conflict exclusion.

The initialized reviewed ledger is20USD/5000 attempts; at audit it still had only its header, no paid attempt. Provider-credit preflight says enough credit for20, without exposing account details; this is not a live billing test. Every retry and health check must retain the shared guard. Official prompts, models, structured parse, temperature and output parameters remain unchanged. Provider routing price ceilings and required-parameter enforcement are part of the guard. Partial blocks, budget stops and invalid/API labels have no efficacy headline; no denominator shrink/refill.

Preserve all historical A40 eligibility/provenance, 171 corrected MASK cases/no replacements, same frozen heads, fresh H200 intact/used-donor outputs and native donor tiling. Fresh intact failures remain in cohort. Independent V2 donor replay is a separate protocol.

## Runtime and CPU judging option

There are126 generation batches for LB and142 for MASK with existing batch8/stable buckets (ceil counts per intact/donor/four masks); donor pools total150 LB and151 MASK. That is **1906 physical generations**:1605 recipient states +301 used donors; LB900, MASK1006. The batch total268 is the useful conservative workload count. Coherence, model startup, technical checks and API waiting are additional.

Relevant measurements are wide: earlier noncheckpoint SB first8/native1024 took289.98s; the deterministic resumable SB first8 produced636 steps in48.03s, and its second batch reached651 steps. These are real H200 observations, but only intact batches. Linear native512 scaling gives about38–145s/batch, hence **roughly2.8–10.8GPUh generation alone** for268 batches. Treat11h plus overhead as the conservative planning case, not a formal upper bound; long MASK prompts and masked/donor paths may differ. The earlier A40/5 heuristic and V2 prefill timing are unsuitable completion promises. With25.6/40h reserved before additional SB segments,14.4h headroom does not safely justify reserving one full paid suite plus remaining SB without measurement. Start the first fixed complete LB block with a bounded segment; update time/reservation from measured batch classes while preserving all rows/caps/masks.

Current evaluator always judges inline after fresh full/donor generation and after each masked state, before coherence/next state. `--skip-judge-check` skips only startup health, not response judging. A raw checkpoint segment stop can precede judging, but resumption eventually reaches inline judging; no current generation-only/defer-all-paid flag exists.

Existing CPU `evaluation/rejudge.py`/`rejudge_benchmarks.py` rebuild official requests and verify stored prompt/model identity, so deferred judging can preserve scientific semantics in principle. **Do not use this tool unchanged here**: it creates an unguarded JudgeClient, chooses suite-local cache rather than the frozen common cache, scans complete `benchmarks.json` failed labels rather than raw checkpoints, and does not implement V5 complete-coverage bookkeeping. Faking API failure to reach this path is inappropriate. A narrow future defer/judge adapter could save GPU idle time while preserving requests, raw outputs, coherence and completeness, but requires source changes/review and is not necessary to finish the authorized tranche. Recommendation now: existing guarded inline route with narrow paid wrapper; consider deferred mode only after measured API waiting warrants it and active SB source is no longer needed.

## Blocking items before paid submission

1. Complete/audit SB and reconcile its remaining reservations; preserve its source/checkpoint identity until then.
2. Prepare/review new paid wrapper, per-split exact argv/receipt and completeness/billing audit; no paid receipt exists yet.
3. Freeze tranche order/segment limit/new output/checkpoint before outcomes, execute CPU dry run, reserve only within remaining40h, then root submits one H200 job.
4. Accept that $20 is a hard stop, not guaranteed full-suite coverage; retain incomplete status if missing cost, retries or reasoning exhaust it. Do not silently substitute judges, trim cohort/states/native caps or omit unscored rows.
