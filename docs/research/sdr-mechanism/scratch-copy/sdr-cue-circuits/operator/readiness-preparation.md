# Operator readiness preparation — no release

2026-10-24. Current lead compactions: **6**. Operator owns only this directory and the phase ledger. Historical `resource-proposal-initial.json` remains unchanged (historical lead count 5). No GPU/account/queue query, reservation, submission, inference or source/git mutation performed. Source parent is `5f74d0c3653a63c411997e0f666a79171076a8d8`; source under development is not a released freeze.

## Inputs required before actual CPU readiness execution

- Root identifies exact committed new source, frozen protocol path and protocol/provenance/science hashes, confirms independent source/schema/byte-ceiling reviews PASS, and supplies the actual operator release decision separately.
- Implementation confirms final wrapper interface and operations schema. Current observed interface is provisional until confirmed: `bash scripts/jobs/run_sdr_cue_circuits.sh calibration --protocol PROTOCOL --operations OPERATIONS --output FRESH_OUTPUT --dry-run`; same for `main`, with `--calibration CAL_DIR` for eventual actual main. Both run from the exact approved worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot`.
- Current wrapper accepts `SDR_CC_PYTHON` to use an explicit interpreter; otherwise it initializes mgnp. It sets offline HuggingFace/Transformers and BLAS thread limits. Actual job mode derives allocation times from numeric Slurm variables or `scontrol show job` and exports `SDR_CC_ALLOCATION_START`, `SDR_CC_ALLOCATION_END`, `SDR_CC_WRAPPER_ENTRY`.
- Current required operations keys: `hardware_class`, `reserved_seconds`, `deadline_utc`, `startup_buffer_seconds`, `premodel_headroom_seconds`, `shutdown_buffer_seconds`, `safety_margin_seconds`. Optional actual allocation timestamps: `allocation_start_utc`, `allocation_end_utc`. Extra keys are rejected. These observations do not approve tentative buffers or release a reservation.

## CPU checks after committed freeze

1. Record wrapper/source hashes and exact interpreter path without dumping environment or process command lines. Use fresh operator-owned output paths only.
2. Run `bash -n` on the actual committed wrapper. Run its calibration and main CPU dry-runs using the final frozen protocol and explicit future operations deadline. Capture return codes and concise output. Do not simulate a Slurm allocation or exercise model mode on login.
3. Verify both output receipts explicitly say `cpu_dry_run`, `numerical_pass=false`, `physical_forwards=0`, `completed_batches=0`. Confirm operations/protocol/forecast metadata were produced and operations hashes match exact input. CPU dry-run is not numerical/calibration success and does not establish fit.
4. Compare frozen counts against 112 calibration slots/14 B8 batches/64 forced steps/5460 forwards; 384 baselines+8960 patches=9344 main completions/1168 batches/147648 full-cap forwards. Verify six strict record classes and audited integer byte ceilings/construction hashes; record calibration 48 benchmark writes plus48 healthy journal writes and one emergency reserve; main3510 healthy writes plusone emergency reserve.
5. Explicitly test occupied-output rejection using an existing CPU-only artifact directory, preserving its bytes. Verify actual main without a matched calibration fails closed before model construction only if the engineer supplies a safe CPU test seam; do not enter actual main mode on login.
6. Reconfirm unchanged prior artifacts/ledgers via root's source audit. Operator never edits source, scientific manifests, old ledgers or git.

## Release and accounting gates

Only after root explicit committed-freeze/review calibration release: query live eligibility/QOS and projections for all four accounts (`beto`, `bimc`, `bgrb`, `bjhz`) and suitable GPU partitions; pessimistic test-only dates are observations, not guarantees or a hard block. No unrelated job mutations. Before submission, append the full time×GPU reservation and exact command/resource/operations/source bindings to the ledger. Retain every reservation, including failed/cancelled attempts. The initial H2001800s/4CPU/64G proposal is unverified and is neither a release nor cap.

Main requires a separate root release after fresh successful calibration, matching exact source/payload/cache/software/GPU identity and independently recomputable full-cap forecast: cold-once/warm-max by signature; exact IO class counts, packing/transfer/final audit; 25% on compute+IO subtotal; separately stated premodel/model-load/headroom/shutdown buffers with shutdown charged once. No mean-length, old IO48 scaling, automatic sharding/retry/panel reduction. Preserve attempted-incomplete rows and all emergency/failure artifacts. No paid APIs, notebooks, login-node model, v2 evaluation, training, merge or push.


## Locked wrapper confirmation and revised proposal

Read the implementation task report under the worktree `.superpowers/sdd/plan-sdr-cue-circuits/task-1-report.md`. Locked script SHA256 `efd5b28c772fbc0a1c2131902d800578ac6b8e2bb0e591c615daa8ed3e81c1e8`; wrapper `b7eeb26a5f1a6416754aeaf2e39796b105c775f47ad8598f226d760e0b654ac4`; direct read-only hash checks match. Reported provisional actualwrapper freeze/cal/main CPU PASS is worker evidence, not a final committed operator readiness result. Provisional freeze remains UNCOMMITTED and independent taskreview is pending.

Exact CPU commands after root supplies final committed `FREEZE`, accepted `OPERATIONS` and fresh output paths (cwd exact approvedworktree):

```bash
bash -n scripts/jobs/run_sdr_cue_circuits.sh
env SDR_CC_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python bash scripts/jobs/run_sdr_cue_circuits.sh verify --protocol "$FREEZE/protocol.json"
env SDR_CC_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python bash scripts/jobs/run_sdr_cue_circuits.sh calibration --protocol "$FREEZE/protocol.json" --operations "$OPERATIONS" --output "$FRESH_CAL_CPU" --dry-run
env SDR_CC_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python bash scripts/jobs/run_sdr_cue_circuits.sh main --protocol "$FREEZE/protocol.json" --operations "$OPERATIONS" --output "$FRESH_MAIN_CPU" --dry-run
```

All names above are task-local placeholders; commands are documented, not executed by this preparation. Realmain additionally requires `--calibration MATCHED_CAL_DIR`. Required numeric operations fields are finite nonnegative ≤1e9, reservation positive; hardware_class≤64UTF8 and future timezone-aware deadline≤40UTF8. Only allocation timestamp fields are optional extras.

Revised resource proposal is `resource-proposal-revised-3600.json`: root-selected oneH200/3600s/4CPU64G, not a usercap/reservation/release. Operator suggests startup120s, premodelheadroom1200s, shutdown90s, safety120s pending root acceptance. Current worker CPUfixture uses120/300/60/60; it does not measure realIO fit. The1200s premodel guard explicitly accommodates44,507,362,016bytes from48benchmarkwrites plus verification/environment overhead; no throughput claim is made. Streaming model-free construction10.902s/~90.7MiB is separate from actualwrite timing. All48stressfiles retained; root's dated381GiBfree observation supports capacity only. Final committedsource and rootrelease still required; allphase accounting stayszero.


## Root accepted final operations, committed source pending freeze checks

Root identifies reviewed commit `ca41bfdb2fd4e4c4c784eabd321ea75e41a45299`, script SHA256 `a7fb9dae0036c0664fe3b56b2866f215973b6dd0622518a933a6a1645961396e`, and accepts H2003600s/4CPU64G buffers120/1200/90/120. Operator wrote `operations-calibration-3600-ca41bfd.json` with a future proposal deadline for CPUchecks. Actual runtime local binding replaces proposal deadline/reservation with exact Slurm bounds while retaining bounded proposal provenance fields; no manual actual timestamps inserted. This artifact is not a reservation or submission. Committed freeze notification and final independent provenance audit remain pending.

R1/R2 corrected I/O ceiling is progress32531bytes; corrected fixed48benchmark total **44,507,365,288bytes**, superseding the earlier proposal's historical44,507,362,016bytes. Other six-class ceilings unchanged. Freshcal additionally measures virtual fullcap main audit CPU and16reads of existing8attempt/8terminal benchmarkfiles, and forecast charges1168attempt/2336terminalreads. No additional journalwrites ormodelforwards. Old provisional science/source notes above are historical only; final protocol hashes must be read from the committedfreeze.
