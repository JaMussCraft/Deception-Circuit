# Implementation preparation

Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot`; root reported verified clean base `4f0278487b0285dd27cbc34d20d88c911dc5562a`. Worker performs no git mutations or model/cache loads on login.

Read root and canonical repository AGENTS, root `.claude/CLAUDE.md`, shared memory index and relevant job-env, worktree, SDR mechanism and worktree-pin notes; study plan, seams, root decisions, scientific review and final ratified spec. Source selection preserves original saved IDs/text/token arrays. Reuse `hooks.capture_forward` and `rp.capture_logits`; no direct-edge freezing helper or new hook path. Banks retain separate per-key common/prefix masks. Setup reused within each physical eight-pair group; arm-level atomic receipts permit recomputing the bank for only remaining arms after verified resume.

Workflow: Karpathy guidelines, TDD, verification-before-completion. Initial tests written before additive runner and observed missing-runner failure with `pytest ... --maxfail=1` (exit1; missing-file assertion, no production file yet). Existing focused base/mgnp baseline tests are running; final counts will be recorded in implementation-report.md.
