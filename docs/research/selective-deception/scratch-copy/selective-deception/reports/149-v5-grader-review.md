# V5 independent scoped review — 2026-10-24

## Grader repairs (report 146)

Scientific/source verdict: PASS for the narrow deterministic repairs. The test portability finding below is resolved; no remaining grader blocker. Reviewed against transfer-v5/plan.md and unchanged primary checkout adapter sources, not against claimed outcomes. No model, API, GPU, notebook, git, or source edits performed.

* Empty/whitespace harm-pressure and MASK responses short-circuit to `unparsed / empty_response`, independent of stale judge text, and require no judge call. They receive neither honesty nor coherent-refusal credit.
* MASK binary C/D remain distinguishable as `evasive:C` / `evasive:D`; D no longer qualifies for deceptive screening or truthful-correction credit. No new masked-output filtering is introduced.
* REJECTED with `not correct` now follows the supplied verdict and belief. The legacy `true` substring guard and AFFIRMED guards remain unchanged, as report146 explicitly discloses. This is a deliberately narrow repair, not endorsement of every legacy parser heuristic.
* Nonempty official judge prompts, models, roles, and token settings are unchanged. `_judge_all` retains original `judge_text`, `judge_prompt`, and `judge_error` alongside the derived label/raw. Historical derivative preservation is separately subject to adapter review.
* Independent offline focused test execution: `tests/test_eval5_grader_repairs.py` **35 passed** under both `/u/swong2/.conda/envs/mgnp/bin/python` and `/sw/external/python/anaconda3/bin/python3.9`, BLAS threads pinned to one.

Resolved finding (medium, test portability): `test_mask_request_keeps_official_rubric_and_judge_settings` locates Alignment with `Path(__file__).resolve().parents[5]`. This succeeds at the current `.claude/worktrees/selective-transfer-v5` depth but points outside Alignment in the main checkout. It introduces a new location-dependent test failure on integration. Locate an ancestor containing the real `mask/mask` sibling instead, or use an existing repository-root discovery facility. Root notified. The separately known existing default MASK sibling-path failure is unrelated and remains an accepted baseline caveat.

## Runtime and adapter

Not yet reviewed; this report does not approve any paid call or execution. Root owns execution approval.

Grader re-review: root replaced fixed parent indexing with ancestor discovery for `mask/mask/prompts/evaluation_prompts.py`, skipping only if the optional sibling checkout is absent. Independently reran the final file: **35 passed, zero skipped** in each environment. Final test SHA256: `f6e145b09cf49e592be7f3913330e21aaa774c9837e7d128fe347b5194fe32cf`. Production adapter source unchanged. Grader verdict: **PASS**.
