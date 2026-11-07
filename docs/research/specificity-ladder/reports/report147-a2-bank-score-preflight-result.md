# A2 timing CPU preflight result

Agent: Codex Sol. Status: handed-back. Failed closed; GPU timing remains unadmitted.

## What changed

Root submitted CPU preflight `23471864` for corrected launch packet
`5320206803d71cba71a71850e5b204667d6d7cab80ccd9dcf73569c357367713` and frozen source
`40fe57289405fd53a3fce02e5d4e47a0ebf78b64`. The actual allocation was
`bjhz-delta-cpu/cpu-interactive`, four CPUs, 32 GiB, no GPUs, with a five-minute limit.
No source, packet, group, data or ledger was edited by this agent.
Exact submission: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/147-a2-bank-score-preflight-evidence/preflight-submission.json`.

## How verified

The actual job failed with exit `1:0` after 71 seconds. Batch MaxRSS was `1525888K`;
actual node/resources/accounting are retained in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/147-a2-bank-score-preflight-evidence/sacct-final.txt` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/147-a2-bank-score-preflight-evidence/run_manifest.json`. It produced only a failure record, with no CPU completion
marker: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/147-a2-bank-score-preflight-evidence/FAILED.json`, raw `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/147-a2-bank-score-preflight-evidence/slurm-preflight-23471864.log`.

The frozen owning `_validate_live` rejected `grader registry snapshot drift` at
`a2_pipeline.py:1121`. This is the equality check between the frozen group receipt's
grader registry and the real current `a1.grader_registry()`. It occurred before bank
contract/budget completion, tokenizer/model loading or any GPU work. The exact changed
registry entry/digest is not diagnosed here; no large receipt/source validation was
replayed locally, and this result does not assert that grader code itself changed.

The launch packet's original file hashes still match the accepted manifest. The new
preflight output is preserved under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/real-input-readiness/bank-scoring-timing/cpu-preflight-20261103`. No automatic retry or GPU submission followed.
The missing completion marker means the pre-submit gate cannot pass.

## Execution evidence

- Classification: real Slurm CPU source/protection preflight; no scientific numerical verdict.
- Expected control: unchanged frozen source/receipt plus owning live validators; the real final grader-snapshot guard rejected the current state, rather than being bypassed or refreshed in place.
- Exact command, stdout/traceback, failure record, timing/resources and packet hashes: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/147-a2-bank-score-preflight-evidence/preflight-submission.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/147-a2-bank-score-preflight-evidence/slurm-preflight-23471864.log`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/147-a2-bank-score-preflight-evidence/FAILED.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/147-a2-bank-score-preflight-evidence/sacct-final.txt` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/147-a2-bank-score-preflight-evidence/run_manifest.json`.
- No valid complete preflight was published. The prospective phase/global budget check was not reached, so this run makes no live budget-readiness claim.
- Root watcher owns RS reconciliation; this agent performed read-only monitoring and short evidence/report checks only.

## What is NOT done

No packet/source/data/ledger/RS/Git/scheduler mutation, retry, GPU submission, model or
large-weight load, API, notebook, subagent, effect inspection or local heavy verification.
No original receipt re-signing, grader-snapshot refresh or weakened guard. The proposed
bank/prefix scope remains unchanged and unexecuted.

## Open questions

Root and the authority owner must diagnose the snapshot drift and review any prospective
remedy before a new valid preflight can be attempted. Preserve original group/source
receipts and all charges. This failed CPU check grants no H200 model/timing admission,
no new reservation authority and no full-assay permission.
