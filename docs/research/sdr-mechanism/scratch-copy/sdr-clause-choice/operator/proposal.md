# Clause-choice baseline operator proposal

Prepared 2026-10-26. Root accepts the prospective resource choice; **no reservation or submission is released**. Operator owns this directory and the sibling ledger only. Source remains implementer/root owned. No model load, inference, GPU job, API call, git action, cancellation, or Bridges-2 access occurred during preparation.

Use one allocation for the frozen 32 excluded natural preflight responses and 640 main responses: **1 A100, 4 CPUs, 64G, 00:15:00**, `gpuA100x4-interactive`, account/QOS `beto-delta-gpu`. This would reserve 900 GPU-seconds (0.25 GPU-hours) only after root release; booked now: **zero**. The 20-minute planning ceiling mentioned in delegation is neither a reservation nor a user cap.

## Evidence and placement

The receipt files contain exact argv, UTC query times, exit codes and stdout/stderr. Names include `T1500Z` as a preparation label; actual timestamps inside are authoritative (~14:57 UTC). Slurm prints prospective job identifiers during `--test-only`; none is a submitted job or reserved allocation.

At that snapshot no `swong2` jobs were queued/running. All four accounts are associated with matching account/QOS. User fairshare: beto .142306; bimc .130980; bgrb .130077; bjhz .071292. A100x4-interactive 15-minute test-only requests under beto/bimc/bgrb forecast immediate starts at 09:57:53–54 Chicago. A100x8-interactive also forecast immediate. H200-interactive 10-minute requests forecast 09:58:24, about 30 seconds later. Normal A100/H200 forecasts were days away. Forecasts are observations, not promises.

A100x4-interactive currently bills at GPU=2000, CPU=125, Mem=32G (Slurm TRESBillingWeights). The historical identical 1GPU/4CPU/64G request allocated billing=2048. A 15-minute request corresponds to 512 billing-unit-hours if that allocation remains the same; this is scheduler accounting, not a dollar price. Root should record actual AllocTRES after submission and terminal elapsed seconds. H200-interactive has GPU=6000, CPU=500, Mem=24G; no H200 reservation is proposed here.

Prefer A100 to preserve H200 interactive availability for the independent selective-components-v6 owner. That thread's current RESUME has CPU workers active and no GPU release at read time. The separate mechanism-analysis fleet is holding until the Oct28 weekly reset; its Bridges-2 state is outside this task. No other-thread job may be cancelled or changed. Before dispatch, check collision/ownership fresh once and repeat the chosen test-only request, not this full grid.

## Runtime sizing and exact proposed deadline policy

Historical original-source2949214 A100 job23194944 completed 4224 responses/4999 forwards in1109 allocation seconds, with794.536 forward seconds (~.159 seconds/forward),17.05GiB peak. The earlier calibration recorded81.378 seconds before model load,13.292 seconds load and1.138 seconds decode+.145 seconds publication for one short intact B8 batch. These are archived measurements, not fresh predictions. The new unprefilled responses can be longer.

Preliminary CPU geometry reports max prefix125, so unchanged B8/L224/cap64 is eligible. Final source/manifest must verify this; a changed shape/kernel/device requires renewed runtime assessment. The rough expected allocation remains4–8 minutes including setup, with15 minutes requested as a reasonable buffer. The full-cap main ceiling is80×67=5360 forwards (~853 compute seconds at the old mean), before setup/IO; it does not prove completion within15 minutes. Durable resume handles a long tail instead of inflating walltime.

Proposed exact policy for final implementation review:

- Bind allocation StartTime/EndTime from actual numeric Slurm values or reviewed `scontrol` parsing. Fail closed when they cannot be established. Effective model/batch deadline is **EndTime minus90 seconds**, reserving60 seconds for shutdown/terminal writes and30 seconds for final audit.
- Complete exactly four natural excluded preflight B8 batches with source/manifest/model checks and exact first-step numerical identity controls. Save all32 rows separately; no outcome-based fixture or prompt selection.
- Before any main batch, require `1.5 × 80 × max(preflight complete-batch decode+publication seconds) +90 <= current allocation seconds remaining`. Setup/hashing/load already elapsed must not be added again. If this fails, retain preflight artifacts and stop without main; root reviews a measured resumable follow-up separately.
- Before each batch require time for the **67-forward cap guard**: `1.5 × (67 × slowest measured per-forward seconds +2 × max measured batch publication seconds)` must fit before EndTime−90. The67 is64 emitted steps+two first-step kernel control forwards+one independent preflight forward. Exact instrumented forward accounting must be reviewed against the final kernel, including any additional forward.
- Incorporate slower accepted-main observations into subsequent timing guards. Check deadline/stop requests before each forward. No guarantee is made that four natural preflight batches reveal every latency tail; the per-forward deadline and unaccepted partial record are the final protection.
- Stop for numerical, source, model, manifest or identity failures. Preserve partial/failure records with pending IDs; no automatic retry, prompt change or job submission. Guarded deadline exit is partial completion, not a capability/semantic result.

These proposed constants/formulas must be reconciled with the final reviewed CLI/runtime before release. They do not certify the current in-progress implementation. The root accepted the15-minute resource proposal and measured admission/resume approach; source/review/freeze/wrapper gates remain open.

## Immutable batch and resume contract

Freeze ordered batches and row IDs before outcomes. Publish each accepted terminal once atomically, bound to manifest/source/run identity and exact full row membership, controls, generated IDs/text, finish/status and timings. Accepted terminal files are never replaced. On explicit later resume, validate every accepted terminal's hash, membership, source/manifest binding and completeness; skip only valid accepted batches. Failed/partial batches remain unaccepted. Numerical/provenance failure requires diagnosis, not automatic resume.

Assembly requires exactly640 unique planned main IDs and separately32 preflight IDs, with all cap/refusal/error/missing states retained. No cap/error/missing row certifies capability. A later invocation requires root release and a new reservation entry; it is not implicit in this proposal.

## Prospective commands and remaining gates

The wrapper was still provisional (45 bytes) when inspected. No CPU dry-run was attempted against incomplete source. Root owns final git freeze and supplies the full committed revision; do not bind the new code to the older base commit as if identical.

After final review/freeze, operator must run `bash -n` and the **actual absolute new wrapper's CPU dry-run** from the approved cwd with model loading disabled, explicit mgnp interpreter, temporary operator dry-run output and final frozen arguments. Verify both direct invocation and Slurm-like deadline variables/parsing, without a model load, GPU call or real run-directory write. Save exact argv/stdout/stderr/result and the final wrapper/source hashes. Final CLI flags are pending; do not invent a ready-to-run launch command today.

The exact proposed Slurm resource envelope is below. `FINAL_REVIEWED_RUN_ARGUMENTS` is an intentionally unresolved marker; this is documentation and must not be executed as written.

```bash
sbatch --account=beto-delta-gpu --qos=beto-delta-gpu \
  --partition=gpuA100x4-interactive --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=64G --gres=gpu:1 --time=00:15:00 \
  --chdir=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot \
  --job-name=sdr-clause-choice-baseline \
  --output=/projects/beto/swong2/Alignment/.scratch/sdr-clause-choice/operator/slurm-%j.out \
  --error=/projects/beto/swong2/Alignment/.scratch/sdr-clause-choice/operator/slurm-%j.err \
  --wrap='exec bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/scripts/jobs/run_sdr_clause_choice.sh FINAL_REVIEWED_RUN_ARGUMENTS'
```

`--wrap exec bash ABSOLUTE_WRAPPER` ensures BASH_SOURCE points at the reviewed original wrapper rather than Slurm's spool script. Use explicit --chdir/--time and absolute logs; no credential-bearing environment dumps or shell tracing. Root must approve the concrete final invocation/reservation after the remaining gates. No job is submitted by this preparation.


## Final committed CPU closure — 2026-10-26T15:41Z

The provisional-wrapper discussion above is superseded by `readiness-final-4f02784.json`. Actual committed absolute-wrapper CPU dry-run PASS in51.4303s with the frozen manifest, no model and no output mutation; three local CPU deadline parsing/rejection probes PASS. Final exact per-batch formula is `1.5 *67 *max_forward +2 *max_publication` against EndTime−90 (the earlier proposed formula placed IO inside the multiplier). Actual main forecasting is rechecked for all remaining batches using the slowest observed preflight/main batch; it is not only an initial check. The prospective full invocation and bindings are stored in the readiness JSON. Source/input independent review, final dispatch collision/test-only and root release are still required; no reservation or submission occurred. The runner currently requires an exact900s interval, so a declined main does not authorize another identical job or an unreviewed different walltime.
