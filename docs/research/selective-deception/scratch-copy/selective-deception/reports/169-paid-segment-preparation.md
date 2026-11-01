# 169 — External paid segment preparation

Prepared only new external files; no paid launch, API call, GPU/model inference, reservation or ledger/cache mutation. Existing evaluator/SB helpers, receipts and all 107 active-SB source/artifact bindings remain byte-identical. Read finalized167 and168; this implements their integrated guarded inline route.

Files: `transfer-v5/run-paid-segment.py`, `launch-paid-segment.sbatch`, `test_paid_segment.py`, `paid-segment-001.argv.json`, `paid-segment-001.receipt.template.json`. Template remains reviewed=false, root decision empty and reservation null: it is not launch authorization. Root finalizes a new receipt only after SB completion/audit and concrete GPU/API cost review.

The lean wrapper pins and reuses the reviewed unchanged SB digest/GPU/once helpers and receipt001/proof002 bindings. Receipt requires all baseline107 source/artifact hashes plus new runner/shell/test/argv/baseline receipt hashes, same d62 source/workdir, exact passing proof, one H200 and positive wall/batch limits. Core manifest validation retains model, preprocessing, frozen cohort/masks, donor and imported historical bindings; generic checkpoint identity retains exact source/model/tokenizer/runtime/decoding/mask/donor/input identity. No new model proof is claimed.

Exact argv derives from frozen commands.full, replacing only the single split selector, its dedicated output/checkpoint directories and positive NEW-batch stop. Predeclared order is instructed-deception; harm-pressure-knowledge-report; convincing-game; MASK continuations, disinformation, doubling_down_known_facts, known_facts, provided_facts, statistics. First unapproved template is instructed-deception/N2/1800seconds. Native512, all recipients/donors and five states remain unchanged; no judge/pricing override, import, rebucketing or selection change.

Only OPENROUTER_API_KEY survives credential filtering in production; dry run strips all credential-like keys. Preflight logs credential names only, never values. Missing production key fails before GPU/model. Budget preflight reuses official parser/stats, requires exactly reviewed20USD/5000attempt header and remaining charged-or-reserved capacity; existing integrated guard controls every health call/retry/response request. Unknown charges retain reservations. Public resolve_cli validates frozen cohort and cache prefix before main startup health calls (evaluate_circuit.py353–361, main988); judging repeats cache checks. No mutable whole-cache/ledger hash and no importer rerun.

Content-SHA once guard prevents copied-receipt replay. Production has one child, no retry/requeue/continuation loop; timeout kills the whole child process group and waits, returning124. Status75 passes through as intentionally incomplete generation; any other nonzero remains failure. Zero requires freshly written exact single split/count/nativecap/five-state result, complete coverage with exact expected/label rows, zero judge-errors/unscored and exact label counts. Refusal/empty/damage classification semantics remain the frozen evaluator's; no efficacy follows partial status.

Verification:

- Test-first missing-wrapper regression failed as expected; additional forged-complete-without-coverage regression failed before stricter scoring validation.
- New external13mocktests pass mgnp (0.86s); same13 plus unchanged integrated15 judge-budget/cache tests pass base (28passed/1.64s). Existing15 pass mgnp separately (0.79s). These test cache-free replay at cap, pending concurrency, unknown/settled billing, retries/failures, provider price caps and prefix/appends, plus wrapper scope/source/argv/proof, key redaction, once guard, incomplete/failure/complete handling and actual mocked TimeoutExpired→killpg(SIGKILL)→wait behavior. No real transport is used.
- Actual shell→wrapper→public evaluator CPU dry run exited0: `/tmp/v5-paid-segment-dryrun.log`. Command: `bash .scratch/selective-deception/transfer-v5/launch-paid-segment.sbatch --receipt .scratch/selective-deception/transfer-v5/paid-segment-001.receipt.template.json --dry-run`. Reports50recipients/50donors/native512/five states, verified cache prefix, paid_attempts0/USD0 and credential_names_passed=[]; no paid guard created.
- Full unrelated evaluator suite was not rerun: no evaluator code changed; requested focused wrapper tests and relevant existing guarded-judge suite were run in both supported environments.

Launch limitations: first paid throughput/API waiting remains unmeasured; proof002 establishes generic raw replay, not paid throughput.20USD is a hard stop and can leave a block incomplete. Root must check live budget/queue/reservations, independently review these external files, finalize a new content-bound receipt and repeat actual CPU dry run after any edits. Future segments need fresh root receipts and reservations, preserving the same split/output/checkpoint identity. No paid work may be assumed active.

SHA256 of new executable/test/argv files:

- `run-paid-segment.py`: `b0e4c43a473ec5c50de8bbcd716d95929628302040d4eea964551bec128a1d10`
- `launch-paid-segment.sbatch`: `b04bd9551e968b57eb022cf9c5a76921d62576296dac30af088ff722ec4d027a`
- `test_paid_segment.py`: `ff7281f95c5007ebd73176e39e0b01c7352f130add40b1f3bdfe8c623e8c52ea`
- `paid-segment-001.argv.json`: `f183eda146948a4215c9bf21a4d70176c5827e869f532983afb90bd0f6bf03b7`
