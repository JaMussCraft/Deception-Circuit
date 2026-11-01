# Selective deception research execution

Approved basis: user approved the 2026-10-17 research plan and authorized execution on 2026-10-18 from merged main. Scientific handoff: `project_context/research_notes/Deception specificity and shared circuits/next_steps.md`. Root coordinator owns integration and compute. No need for a new session or greater agent depth now.

## Scope and sequence

1. Diagnose existing SDR coarse fixed masks using matched benign/deceptive prompts, answer-format/order contrasts, and controlled donor crossover.
2. Develop and run a bounded sparse suppression/preservation pilot after the diagnostic validates its measurements and controls. Failure of a coarse mask does not rule out a selective subset.
3. Scale only on evidence of a better held-out suppression/utility tradeoff, then dissect 1–3 components/paths. Confirmatory benchmark waves and large sweeps require an explicit costed decision with the user.

## Scientific contract

Coherent target refusal/evasion is successful suppression; honesty/disclosure is not required. Raw generated deception/n includes all target rows. Keep task-label accuracy/margin separate from free-generation deception, malformed output, and benign utility. F membership does not establish pure formatting; donor replacement is not neutral deletion. Never execute notebooks. Freeze data IDs, masks, donor identities, decoding, and evaluation rules per diagnostic. No new mask training in stage 1.

## Working arrangement and context control

One integration worktree: `Deception-Circuit/.claude/worktrees/selective-deception`, branch `selective-deception`, base main `9d9c2a93a93ebfcf30a06a06332e38007d0d64f9`. Preserve main and existing format-control outputs. Root performs git mutations and submissions. At most three active children; no nested workers. Fresh GPT-6.1 Sol worker contexts receive one task brief, precise input/output paths, constraints and acceptance tests, not root history. Use Astra for consequential uncertain decisions and final scientific/code review. Reuse an implementer only for focused fixes; bound review cycles. Record progress, source commits, tests, jobs, pending decisions and artifact locations here so compaction or a new session cannot restart completed tasks. Retain this record.

User prefers sparse high-level updates, no routine polling narration. Work from completion notifications and useful independent work. Runtime requirements may still require short liveness updates during long tool waits; keep these minimal.

## Stage 1 resource envelope

- At most **20.0 reserved GPU-hours cumulative** across this research, authorized by the user on 2026-10-18; target about 2 hours initially for stage 1, including all smoke runs, failures and retries; measure allocated GPUs × requested Slurm wall time. Do not replenish the cap from unused reservations.
- At most two active/pending GPU jobs at a time; independent jobs may run in parallel. Root alone submits. No arrays. No automatic retry or resubmission.
- Maximum paid API spend/calls: **$0 / 0**. Existing unscored outputs are not silently rejudged. No API credential changes.
- Every run must have a dry-run/manifest, exact sample/config count and output-token bounds, input hashes, source revision, GPU count/type, requested runtime, output path, and a reservation entered in `compute-ledger.json` before submission.
- Scheduler wall time enforces each job ceiling. Reconcile actual elapsed time and allocated TRES using sacct afterward; report allocation accounting separately from estimated currency (rates may be unknown).
- After a failure, diagnose before any retry. Never expand budgets, grids, tokens, seeds or concurrency silently. If the envelope is insufficient, preserve independent progress and present the next concrete run with its cost for a decision.
- Stage 2/3 may use the remainder of the shared 20-hour GPU envelope after measured estimates and scientific gates; no stage receives a fresh 20-hour allowance. Paid API allowance remains zero. Large batch expansions require a concrete high-level decision before launch even if within the cumulative cap.

## Known pending issue to verify

Oct18 handoff says format Liars' Bench completed, while MASK/sandbagging had HTTP 402 scoring failures. Read current artifacts before citing; credit recovery is outside the zero-API first stage. Component-analysis outputs moved from deleted worktree to primary `outputs/_analyses/`.

## Stage deliverables

Small tested diagnostic runner using existing ablation machinery; frozen manifest; bounded actual run if launch prerequisites pass; concise results with invalid/inconclusive outcomes visible; cost reconciliation; proposed next pilot. Do not claim stage 1 complete from teacher-forced metrics alone if planned generation/format contrasts remain missing.
