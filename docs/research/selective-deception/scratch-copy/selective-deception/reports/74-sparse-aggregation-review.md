# Sparse aggregation independent CPU review

2026-10-19. **PASS within the bounded review scope; no blocking findings.** Reviewed `analysis/summarize_sparse.py` and `analysis/tests/test_summarize_sparse.py` against report52, the frozen protocol, report73, and the immutable selective-wikitext trainer/export serialization. This is an implementation review, not a completed-grid audit, scientific selection, expansion decision, or finality receipt.

Reviewed analyzer SHA256: `94dc1ef95619e82e1162551b4442f0c081d4ecc668601320d8a68c6e29c80a4f`.

Reviewed tests SHA256: `7109f7ceae6f1dec96bf37a26366311c446019855550b57a7fcfad6872628b8f`.

## Findings

No correctness defect found in the requested selection or completion rules:

- Each requested space requires exactly six distinct H/W/HW × rho0/.01 runs. Every run requires the full 512-step loss log and the eight exact 64-step checkpoints. An incomplete or technically invalid disk grid cannot produce selection or expansion proposals. Failed updates are not negative findings.
- Independent own-arm admissibility matches the frozen runner. W success survives H failure; H selection does not impose W preservation; HW requires both. Binary removal must be nonzero for admissibility. Compact usefulness requires 1–16 heads and at least 10% D-surrogate reduction.
- Selection spans both rhos per arm and space. It prefers admissibility, then lower suppression, fewer removed heads, earlier update, and rho0 before .01. If neither rho has an admissible checkpoint, the best D-surrogate checkpoint across both remains a failed-frontier example.
- Every validation row contributes to compact usefulness, including earlier checkpoints and nonfinalists. Any compact useful union finding in any arm prevents the absence-based expansion proposal. Only a complete technically audited grid can reach that proposal.
- Disk checks use the actual trainer field names and digest-aware CPU loader. Checkpoint optimizer steps, cursor/history/log prefixes, frozen schedule hashes, source/manifest/protocol/receipt/reference identities and calibration evidence are bound. Deterministic exports are reconstructed from gate tensors with exact threshold behavior, candidate eligibility, outside-support openness and all nonhead removal entries open; their complete hashes must agree.
- Proposals preserve all three union finalists, or all six union/all finalists, and retain the full training/validation records and paired H summaries. Publication sets `authoritative:false` and `finalists_frozen:false`; the existing native caller explicitly rejects the latter. Root must independently review expansion closure and freeze the actual shared receipt before any heldout assessment.

## Verification

Only the focused synthetic aggregation suite was executed:

- Base Python3.9: **19 passed in 9.81s**; one existing pandas/bottleneck dependency warning.
- mgnp Python3.12: **19 passed in 9.49s**.

Two additional independent tiny synthetic checks passed: the globally best failed-frontier checkpoint can come from rho.01 at update512, and a compact W-only finding prevents expansion even when every H/HW checkpoint loses H retention.

Read only the field names/container structure of the first H run's `latest.pt` and `validation-000064.pt`, loaded on CPU. Their payload/cursor/history/log/gate/optimizer/RNG schemas match the auditor. No production metric values were reported or interpreted, and no actual finalist or expansion proposal was computed. This compatibility check does not establish completed-run readiness.

No production files, trainer source, ledgers, receipts, model weights or scientific records were edited. No GPU/model execution, APIs, submissions, git commands, notebooks, full suites or subagents were used. The normal read tool initially failed at bwrap setup; narrowly escalated reads and focused CPU tests were used afterward. This report is the only deliverable written by the reviewer.

## Practical limits

The focused suite directly exercises a fully populated H disk fixture; W/HW block coverage and source identity logic were also inspected against the trainer, but no completed real six-run grid was available or audited here. Actual model-weight bytes are intentionally not rehashed by this analyzer; final callers retain their own snapshot checks. Schedule coverage is established from the frozen trainer and recorded schedule hash/counts, rather than an independent replay of model forwards. Those limits do not change root's obligation to inspect the completed audit before freezing finalists.
