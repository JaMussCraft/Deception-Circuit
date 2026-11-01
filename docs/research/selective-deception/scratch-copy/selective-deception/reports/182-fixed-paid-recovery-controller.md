# 182 — One bounded recovery for the remaining five paid blocks

Prepared **new versioned files only**, with no activation, Slurm submission/query, API/model/GPU operation, reservation, ledger/cache mutation or old artifact/source/guard edit:

- `transfer-v5/run-fixed-paid-recovery.py`
- `transfer-v5/test_fixed_paid_recovery.py`
- `transfer-v5/fixed-paid-recovery-001.manifest.template.json`

The original controller stopped on a scheduler observation race: its first `sacct` query after submitting MASK continuations23192484 returned no row. That is not evidence that the submitted job failed. Root's new reconciliation183 independently establishes the first three blocks completed. Recovery must never submit them again. It imports the exact reviewed179 controller by SHA `44b6f92ffed8a4e740d926556729cb0d58a667ecfe2e2ef1882dab88ee0aa4fc`, preserving all legacy files and old permanent guard.

The sole scheduling change is the new Slurm `wait` method. A persisted positive job ID remains the only job watched. An empty exact-job accounting response triggers an exact-job live `squeue` query: a unique matching active/PENDING/RUNNING witness means wait60seconds, never resubmit. If both views are empty, wait up to300seconds of continuous absence, then stop for root. Valid accounting resumes normal waiting and resets that absence timer. Duplicate, foreign or malformed records, command failures, or unexpected live states stop immediately. Only exact accounting COMPLETED/0:0 can release the next entry, via the unchanged179 dispatch gates. Live queue visibility alone never establishes success. Logging stays limited to observation/state changes; no extra GPU attempt/retry/requeue is introduced.

The final recovery manifest must preserve the original fixed account/Slurm paths and **exact original entries[3:]**, including all five unchanged receipt paths, reservation IDs and submission argv. Original eight-entry manifest SHA is pinned `b349d96c4e84f416da05fe8107d067f6f49dd8e2f92d125154b5756dd7c9cf1d`. Remaining order is MASK disinformation, doubling_down_known_facts, known_facts, provided_facts, statistics. Explicit budget claims are zero additional GPU hours, five already precharged hours remaining, and cumulative36.6/40 reserved. No reservation creation/recycling is implemented.

Required immutable bindings include the complete original manifest's source/receipt union; original manifest bytes, old once-guard and old append-only state; new recovery runner/test; report183's machine prefix reconciliation; and all three completed prefix receipt/result/guard files. Prefix audit must say passed=true and contain exactly the first three datasets with known jobs23191888/23191980/23192484, exact receipt/result/guard paths and hashes, with root-reconciled COMPLETED/0:0 terminal evidence. Recovery independently validates their guard job/receipt association, result freshness relative to guard, finalized receipt, original strict completion and fixed item/prompt/donor/state content. All those immutable hashes are rechecked before/after each suffix job through the unchanged179 preflight. Existing live cache prefix/appends and authoritative $20/5000 known-settled-only budget checks remain intact.

Each unused suffix receipt must still pass original authorization and have no paid once-guard. Recovery consumes a **new permanent `fixed-paid-recovery-001.used` guard**, never deletes/resets either guard, and writes its own digest-named append-only/fsynced state. It reuses179 dispatch for submission intent→job ID persistence→wait→strict current-job result/content/billing gates. It does not resume a partially started recovery or generalize into a workflow framework. Interruption requires root reconciliation; the permanent guard blocks replay even if no returned job ID could be persisted.

Test-first missing-module/accounting-race regressions failed before implementation. **16 new recovery tests plus unchanged33 original controller tests pass in both mgnp and base Python3.9 (49 total each).** Tests cover empty accounting with a live PENDING witness, both views transiently absent then exact accounting, five-minute absence stop, malformed/foreign/duplicate accounting/live records, command failure, genuine partial75 failure, prefix replay/suffix skipping/reordering, permanent guard reuse, consumed suffix receipt guard refusal, and unchanged old source hash. All scheduler transports/times are mocked. No public CLI args/runtime source changed; prior actual eight CPU preflights/model proof remain applicable.

Root finalization/activation after183 and independent184 PASS:

1. Confirm old controller is stopped and no selective GPU job is queued/running. Reconcile the completed three jobs and global actual API ledger. Finalize a new manifest from the unreviewed template, bind the files above, and record root decision/review. Do not modify original receipts/argv/source/old manifest/state/guards.
2. Compute the final manifest SHA and run:

```bash
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/run-fixed-paid-recovery.py --manifest /ABSOLUTE/FINAL-RECOVERY-MANIFEST.json --manifest-sha256 EXACT_SHA --dry-run
```

This validates existing CPU-safe receipt/content/source/cache/budget state only; it performs no Slurm/API/model/GPU work and creates no guards/state.

3. Root alone launches the exact command with `--dry-run` removed, optionally using absolute `/usr/bin/nohup` and a new log path. Preserve the existing credential environment without printing keys. Example:

```bash
/usr/bin/nohup /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/run-fixed-paid-recovery.py --manifest /ABSOLUTE/FINAL-RECOVERY-MANIFEST.json --manifest-sha256 EXACT_SHA > /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/fixed-paid-recovery-001.log 2>&1 < /dev/null &
```

Root later reconciles actual accounting into the already existing reservations and performs the scientific audit. Recovery completion is mechanical acquisition evidence, with the same raw-token/text and per-label cache-linkage verification boundary as179; it is not a scientific efficacy conclusion.
