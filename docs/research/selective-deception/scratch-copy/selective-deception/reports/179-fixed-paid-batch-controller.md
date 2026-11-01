# 179 — Fixed paid-batch mechanical controller

Prepared a thin external dispatcher for the remaining eight paid blocks. **Not activated.** No GPU/model/API calls, submissions, budget reservations, receipt finalizations, cancellations, cache/ledger writes, or existing core/helper edits were performed. Root remains the sole activation authority. Source d62 and original instructed result remain frozen. This implements the already authorized fixed order rather than choosing experiments from outcomes.

New files:

- `transfer-v5/run-fixed-paid-batch.py`
- `transfer-v5/test_fixed_paid_batch.py`
- `transfer-v5/fixed-paid-batch.manifest.template.json`

The template is deliberately unreviewed with empty root decision, no reservation IDs, no final receipt files and no bindings. It cannot dispatch. The separate worker's `fixed-paid-batch/preparation-index.json` provides the eight receipt templates/argv/actual CPU public-CLI dry-run records; report180 owns their preparation.

The finalized manifest must contain exactly harm-pressure, convincing, then MASK continuations, disinformation, doubling_down_known_facts, known_facts, provided_facts, statistics. Each entry has one unique finalized receipt and precharged reservation ID. It binds the union of every receipt's immutable `file_bindings`, every finalized receipt file itself, and the controller/test/versioned runner/policy/auditor sources. The manifest SHA is supplied explicitly to the CLI and rechecked from disk before dispatch and after completion. All source hashes are rechecked between blocks. Mutable common cache/ledger files are validated through their existing semantic guards, never whole-file hashes.

Each command is checked against one literal shape: absolute `/usr/bin/sbatch --parsable`, fixed manifest account, `gpuH200x8-interactive`, one node, one GPU, explicit `--time=01:00:00`, `--no-requeue`, exact V2 shell and exact receipt. Receipt validation reuses reviewed V2 CPU-only validation and enforces H200/oneGPU/3600s. Manifest records eight root-precharged GPU hours and cumulative36.6/40; controller does not create, recycle or reconcile master reservations. It records actual job IDs/state/elapsed/allocation in its own state for root reconciliation.

Before activation and each submission, the existing authoritative global budget parser checks exact $20/5000 limits and remaining capacity. Existing read-only `budget_audit` additionally rejects pending attempts, unknown settled costs, any over-reservation/invalid-history issue or torn ledger. Existing cache audit verifies the imported immutable prefix/path and every appended row. Every successful block repeats those gates before the next block. Existing integrated runtime guards still cover all health checks, judge requests and physical retries; this controller does not alter their parameters or price limits.

A permanent global `transfer-v5/fixed-paid-batch.used` file is created with exclusive-create and fsync before any submission. This prevents same-manifest and alternate-manifest duplicate activation, including after interruption before a submitted job ID is persisted. It is never deleted. Digest-named `fixed-paid-batch-<sha>.state.jsonl` is append-only with fsync for submission intent, returned job ID, state transitions, terminal accounting, validated output and completion/stoppage. There is no resume, retry, automatic guard deletion or alternate submission account. If the process is killed during submission, root must inspect Slurm manually using the persisted submission intent and reconcile; the guard prevents automatic replay. SIGKILL cannot append a final stopped event, so absence of `complete` means unresolved, never safe to restart.

Only one job is submitted at a time. A live queue check also refuses to submit while another extant GPU job, including queued/suspended/requeued jobs is present; no existing job is changed or cancelled. Scheduler submission policy failures stop immediately. Pending jobs wait. Polling is once/minute, state changes alone are logged. Missing/ambiguous accounting or scheduler command failure stops for root; no hidden retry. Terminal state must be exact COMPLETED with `0:0`, so partial75, nonzero, signal, timeout, cancellation and preemption cannot release the next block.

A terminal success also needs its freshly created paid once-guard to contain exactly the current submitted Slurm job ID and current receipt SHA. An already consumed receipt is refused before launch. Result mtime must differ from its prelaunch value and be at least the current job's guard mtime, using filesystem-relative comparisons rather than cross-node wall clocks. Existing V2 `complete_result` then checks the exact split/cohort/native512/all five states and zero judge errors/unscored for these eight datasets. The instructed-only official INVALID amendment is not generalized to other datasets. These are mechanical completion gates, not new scientific efficacy thresholds. A separate lean saved-content gate verifies exact fixed items/prompts/order/selection provenance/native512/native partner IDs; honest donor pool/pairing/size; fresh H200 intact/native donors with no screening; all five per-state generation strings/labels and zero raw unscored/judge-error rows. The successful identity gate is recorded in state. This does not independently reconstruct decoded checkpoint tokens into saved text or each cache reply into each label; scientific interpretation remains the existing audit/root reporting responsibility.

Verification: test-first missing-controller regression failed before implementation. Final **33 mocked tests passed in mgnp and base Python3.9**. They exercise a successful ordered two-entry dispatch and persisted job IDs; partial75/nonzero/signalled jobs; missing coverage; direct pending/unknown settlement gates; budget exhaustion; source/manifest changes; failed submission without retry; missing/wrong current-job guard; stale output; frozen-order rejection; permanent duplicate guard; scheduler wait transitions; refusal around another extant GPU (including pending); and changed frozen item/prompt/donor/native-cap/provenance or hidden per-state generation/judge failure. Ten additional regressions were observed failing before the independent181 queue/content fixes; the final source includes both fixes. No real Slurm/API transport is used by tests. Focused verification only: no evaluator source changed, so the unrelated evaluator suite was not rerun.

Root recipe after independent181 PASS, all eight actual public-CLI CPU preflights, live queue/budget review, pre-reservation and final receipts:

1. Fill a new final manifest from `fixed-paid-batch.manifest.template.json`; merge each final receipt's source bindings, add every receipt SHA, controller/test SHA and required policy/runner/auditor SHA. Mark reviewed/root decision only after review. Preserve fixed command/order/counts.
2. Compute its SHA256 externally and keep that exact digest. Execute with the frozen mgnp interpreter:

```bash
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/run-fixed-paid-batch.py --manifest /ABSOLUTE/FINAL-MANIFEST.json --manifest-sha256 EXACT_SHA --dry-run
```

This dry run validates finalized receipts/files/commands/live ledger/cache only; it **does not execute the public evaluator CPU preflight**. The separate eight public-CLI preflights remain required. It creates no guard/state and makes no Slurm call.

3. Root alone activates the exact reviewed command from a persistent CPU session, or uses absolute `/usr/bin/nohup` with output redirection and `&`; remove only `--dry-run`. No GPU allocation is requested for the controller itself. Example:

```bash
/usr/bin/nohup /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/run-fixed-paid-batch.py --manifest /ABSOLUTE/FINAL-MANIFEST.json --manifest-sha256 EXACT_SHA > /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/fixed-paid-batch-controller.log 2>&1 < /dev/null &
```

The OpenRouter credential must already be available in root's environment; never put its value in a command/log. Root later reconciles every terminal job's actual GPU accounting into the master ledger, audits outputs and reports all full denominators. A stopped controller leaves the rest unsubmitted and requires root reconciliation; it must not be restarted by deleting guards.
