# Independent implementation task review

2026-10-26. **Spec compliance: CHANGES REQUIRED (one operational requirement). Code quality: CHANGES REQUIRED (same finding); otherwise acceptable within this additive baseline scope.** No independent scientific-design defect found. This is not a GPU release.

Reviewed the complete three-file task-review package against final spec.md, plan.md, implementation-brief.md, implementation-seams.md, rubric.md, priority-review.md and input-review.md. Checked live sources against package: differences are unused-import removal only. Inspected the reused intact decoding/control/deadline helpers rather than assuming their outer protocols apply. No source edits, git commands, jobs, GPU/model execution, notebooks, APIs or test-suite repeats performed. Only this review file written.

## Material finding

**P2 — A crash between terminal and timing publication strands a valid accepted batch.** `scripts/sdr_clause_choice.py:314–319` publishes an immutable `<batch>.accepted.json` and then a separate mandatory `<batch>.timing.json`. `run_baseline` at line612 immediately requires `batch_timing` for every accepted batch on resume. SIGKILL between those writes therefore leaves a valid complete terminal that cannot resume: `accepted_batches` accepts it, but opening its missing timing raises before execution proceeds. An I/O exception while publishing timing also produces a nonresumable failure even though generation, numerical validation and accepted publication succeeded. This defeats the promised safe interrupted resume and can strand already completed work.

Smallest suitable correction: make every timing fact needed for resuming part of the atomically accepted terminal, or conservatively recover absent auxiliary timing from a validated immutable terminal without changing/replaying accepted outputs. Do not discard valid accepted rows or relax numerical/provenance failure stops. Add a focused fault-injection test that interrupts after accepted publication and before auxiliary timing publication, then explicitly resumes and proves the accepted batch is skipped while all remaining rows complete. Root received this finding for implementer action; reviewer did not self-edit source.

## Checks that passed review

- Metadata-only single ranked fixture scan, globally distinct unordered pairs, first8/ninth per template, exact640main/32excluded preflight rows and crossed named truth/order/target/condition/task match the spec. Main safe N has no duplicated threatened identity.
- Literal prompts preserve explicit named facts and task-private audience rules, with empty assistant stem and archived manual shell. C/U differ only in final preserved/wiped predicate. Freeze records272 C/U checks, exact role/scope masks, all768 prospective donor maps and the correct five head sets before outcomes. Final provisional prefixes110–125 fit unchanged B8/L224/cap64 without truncation.
- S32/candidate6 and archived C_S/outside6 selection follow the corrected frozen rules. C6 is `(12,15),(13,3),(13,27),(13,30),(14,22),(17,21)`; permitted overlap with C_S is retained. No later patch execution was implemented here.
- The external first vector uses the same fixed physical shape/readout FP32 path as the intact decoder. Acceptance ties its input hash, slot, true last-prefix readout, full-vector hash and argmax to decoder control expected hashes and first generated ID. Decoder checks finite full128256-vocabulary FP32 values every forward, uses full-vocabulary argmax, retains EOS/caps and logical append histories, and checks deadlines before forwards. No old outer runner protocol is invoked.
- Runtime uses actual numeric900s Slurm start/end, EndTime−90s forwarding deadline, measured four-batch preflight before main,1.5×remaining-batch forecast with measured publication, and67-forward full-cap per-batch admission. Accepted batches bind manifest, run/hardware receipt, planned IDs and terminal/control coverage. Explicit resume rejects recorded numerical/provenance failures. These controls are otherwise sound; the finding above concerns the publication crash boundary.
- Export includes exactly opaque ID, actual question, lexical candidates, complete response and finish; question is part of deduplication. Hidden facts/condition/target/head metadata stay outside views. Distinct complete-coverage raters and fresh full-tuple adjudication enforce the declared annotation contract. Independence/personal reading remain attestations, as stated by rubric.
- Cap/error overrides, refusal/evasion/ambiguity/contradiction categories, factual-disclosure flags, all640 denominators, equal fixture weighting, N56/64, U112/128, retrieval304/320, report delta≥.15 with positive templates, retrieval |delta|≤.05, numerical coverage, complete category transitions and refusal/disclosure inventory match the baseline specification. Missing/noncommitment outputs cannot certify capability or avoidance.

## Evidence and remaining verification

Existing focused test logs inspected: base28passed (one unrelated existing bottleneck/pandas warning); mgnp28passed; lint `All checks passed!`. These are existing implementer receipts, not reviewer reruns. The complete `cpu-freeze-provisional-final.json` is available and binds the reviewed current sources,640/32rows,768pairs,272C/U checks and maximum prefix125. Its scientific hash is `d22cb1edbb8ed2b3109c3142d74460da9aa360b4cfb4615e6b05d21e6ed94d7c`; manifest hash `be868b568a3d8bd36ca7564c43c9622a2a4597c698605fedab5c23063e5f4b32`.

**Pending evidence, not additional code findings:** implementation-report.md and a fresh actual-wrapper CPU `run --dry-run` receipt were unavailable at this review checkpoint. Static control flow returns before output creation, allocation/hardware checks and model loading in dry-run, and the focused mocked dry-run test passes; this does not replace actual-wrapper verification. Committed revision binding, refreshed freeze/source hashes after the crash-gap fix, final independent full-freeze oracle comparison and fresh actual-wrapper dry-run remain release conditions. The current freeze is explicitly provisional/UNCOMMITTED and correctly cannot execute real inference.

## Reviewed live source SHA256

- `scripts/sdr_clause_choice.py`: `3451dbd60611981f5ca12831e2f2b9580608bc9d163458e0d7073765b7455565`
- `scripts/jobs/run_sdr_clause_choice.sh`: `2c3a771d9edd869042efcc81e117aa664961f655930adb123a44dbc1cc827fe3`
- `tests/test_sdr_clause_choice.py`: `c906c83146538317cd404c194045ccd6d29682a7d4679e7fa25a27d7f82df0e8`

These hashes are the import-cleanup revision reviewed here; any subsequent fix needs a scoped re-review and new evidence binding. Prior studies/results/gates remain unchanged.
