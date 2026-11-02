# Hand-back 03: B3 plan, spontaneous deception through the instructed route

Agent: planner-B3 (Opus). Ticket: the team-lead brief of 2026-11-01 for sub-direction B3 (no ticket file). Status:
resolved.

## What changed

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B3-plan.md`.
  It is new, 250 lines, and holds the costed B3 plan:
  - the premise test, the Gupta positive control and the transfer with its controls;
  - the optional scratchpad intent test and the sycophancy fallback;
  - code, cost, tickets T1 to T7, and risks.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/03-handback.md`
  (this file).
- Nothing was staged for the apply tool. No code, data, spec, ledger or state file was changed.

## How verified

```
timeout 120 /u/swong2/.conda/envs/mgnp/bin/python -c "
from transformers import AutoTokenizer
t=AutoTokenizer.from_pretrained('meta-llama/Llama-3.1-8B-Instruct')
for s in ['<USER_TIER>free</USER_TIER>','<USER_TIER>paid</USER_TIER>','<is_free_tier_user>True</is_free_tier_user>','<is_free_tier_user>False</is_free_tier_user>','User tier: free\n','User tier: paid\n', ' monitored', ' unmonitored']:
  ids=t.encode(s,add_special_tokens=False); print(repr(s),len(ids),[t.decode([i]) for i in ids])
for s in ['I can\'t help with that.','I cannot','I\'d be happy to help','Sorry, I','Here is','**Title','Unfortunately','As a']:
  ids=t.encode(s,add_special_tokens=False); print(repr(s),[t.decode([i]) for i in ids])
"
```

Observed: `<USER_TIER>free</USER_TIER>` and `<USER_TIER>paid</USER_TIER>` are both 11 tokens and differ only at token
6. `<is_free_tier_user>True|False</is_free_tier_user>` are both 15 tokens. "I can't" tokenizes as `I`, ` can`, `'t`,
and "I'd be happy to help" also starts with `I`, which is why the plan freezes a two-level proxy.

```
/u/swong2/.conda/envs/mgnp/bin/python -c "
import json;d=json.load(open('docs/research/mechanism-analysis/phase1/p1c_readings.json'))
for t in ['far','ser']:
  m=d['rab'][t]['deciding_numbers']['members']; print(t, d['rab'][t]['deciding'], len(m), m)
far=set(d['rab']['far']['deciding_numbers']['members']); ser=set(d['rab']['ser']['deciding_numbers']['members'])
u=far|ser; print('union',len(u), 'inter', sorted(far&ser))
"
```

Run from the worktree root. A second one-liner counted the union plus L17H24 to L17H27 by (kind, layer).

Observed:
- The FAR and SER greedy k=20 deciding sets share 9 members.
- Their union with L17H24 to L17H27 has 35 members: 32 heads in layers 7 to 17, plus mlp.5, mlp.6 and mlp.7.
- head.15.8 is in the FAR set.

```
timeout 60 /u/swong2/.conda/envs/mgnp/bin/python -c "
from huggingface_hub import HfApi
a=HfApi()
for r in ['bench-llm/or-bench','walledai/XSTest','natolambert/xstest-v2-copy']:
  i=a.dataset_info(r); print(r,'gated=',i.gated)
"
```

Observed: `bench-llm/or-bench` is public (gated=False), `natolambert/xstest-v2-copy` is public, and `walledai/XSTest`
has gated=auto.

```
research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B3-plan.md
wc -l /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B3-plan.md
```

Observed: lint exit 0, and 250 lines.

Code was read to confirm the reuse claims:
- `evaluation/benchmarks/judge_budget.py` `settle` replaces a reservation with the reported `usage.cost`.
- `component_analysis/hooks.py` `capture_forward` and `Replacement` support position-masked interchange.
- `run_manifest.py` `build_run_manifest` records the git commit.
- `outputs/_launch_mechanism_analysis/p1c_groups.py::layer_matched_nulls` is the null used by the mechanism analysis.

The timing basis is `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_analyses/mechanism-analysis-02a-smoke-timings/timings.json`:
1,051 s for the completeness sweep, plus a 476 s model load.

The paper facts were read from the arXiv HTML of 2607.13346 and 2610.22937 and the abstract of 2609.04166, on
2026-11-01.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **No code is written.** Tickets T1 to T7 are specified only.
- **No judge prompt text is written.** It is a T3 deliverable, frozen as G1 before any judge call.
- **No grader hash is recorded** in `spec.md` or `directions.json`. That happens at freeze G1 and again at G2.
- **No Mehta or Greenblatt prompt is obtained.** Mehta releases only a paraphrase. The V-B source file name in the
  public alignment_faking_public repository was not verified, and T1 fetches and hashes it.
- **No datasets are downloaded**: OR-Bench-Hard-1K, XSTest and MMLU are not fetched.
- **Walltime is not measured.** The estimates are scaled from one H100 timing file by prompt length. The decode
  speed of 25 ms per step at batch 32 on an A100 is an assumption.
- **Gupta's full top-8 head list is unknown.** The positive control uses the six named heads, with a 0.18 floor
  taken from Gupta's writers-only number.
- **Shkolnikov's full text is unread.** Only the abstract was read.

## Open questions

1. **Ruling R-B3-a.** START section 10 says "first-token proxy", while section 2 allows "first-token or
   refusal-token proxy". May the primary proxy be P2, the refusal-token proxy that resolves "I", when P1's
   calibration agreement is under 0.85? Default: yes. Record R-B3-a in `spec.md` before the calibration run.
2. **Ruling R-B3-b.** Should "shared" also require f(S_all) to exceed all 20 layer-matched null draws, with a null
   maximum of at least 0.5 labelled "non-specific"? Default: yes, which mirrors mechanism-analysis test (i).
   Record it before J4.
3. **Judge model.** Mehta used Claude Opus 4. Default: `anthropic/claude-haiku-4.5` as the primary judge, with a
   200-row `anthropic/claude-sonnet-4.5` cross-check. Both are among the four models the budget guard pins.
4. **Query count.** Default: 100 test queries plus 20 calibration queries, against the rule's minimum of 50.
5. **Response length.** Default: 512 new tokens, against Mehta's 1,024. The judge is told responses may be
   truncated.
6. **J3 timing.** Default: J3, the sycophancy positive control, runs before the premise verdict and counts toward
   the 10 pre-premise GPU-hours.
7. **Optional scratchpad test (3.6).** Default: run it only after a shared or partial verdict, within the remaining
   budget.
8. **Package location.** Default: a new top-level package `spontaneous/`, so no file is added under
   `evaluation/benchmarks/` and the EVAL 5 grader hash is unchanged.
9. **Judge ledgers.** `judge_budget.py` refuses a header above 5,000 attempts, and the main stage, cross-check and
   optional scratchpad together come to about 5,500 calls. Default: the orchestrator creates one reviewed ledger per
   stage, with $20 split across them as $10, $3 and $7, and logs actual spend in the direction ledger.
