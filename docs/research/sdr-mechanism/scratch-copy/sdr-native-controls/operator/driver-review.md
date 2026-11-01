# Fixed-shard operator driver review

**Final verdict: PASS after the fixes documented below.** Static review only; no driver execution, jobs, source/git/ledger changes or repeated source/tests. Reviewed inert `run-fixed-shards.py`, actual q34/12 frozen plan, policy/release proposal and authoritative current ledger40800reserved/223actual.

1. Request untruncated accounting state (`State%32` or wider). Default sacct field width can truncate `OUT_OF_MEMORY`/other terminal names, leaving the loop polling instead of stopping. Explicitly disable scheduler requeue (`--no-requeue`) and reject nonzero restart/requeue counts so automatic scheduler restarts cannot bypass the no-retry policy.
2. Make reservation/inventory persistence fail closed before sbatch. Current unchecked `str.replace` can silently leave the authoritative ledger total or reservation row unchanged if its baseline/marker drifts; current ledger matches, but execute may occur later. Assert exact expected current totals and unique replacement markers, then use atomic write + file/directory fsync for ledger, inventory, state/submission records before submission. Event persistence should likewise flush/fsync. Preserve reservation on every subsequent error.
3. Pin this fixed driver to reviewed exact plan hash `1e72decf396e70c532ad676c9f726e94aff045add07bc78871d8104578a71f5a` and code commit `1eb79892b0c4a428774cf340350d2297d9ec58f7`, with native science52f386...; q34/12 alone is insufficient to establish this driver still executes precisely the reviewed fixed proposal.

Checks that align: default is inert; activated canonical release and fresh registry are required; STATE O_EXCL prevents concurrent/restarted drivers; all12 original ranges execute in ascending order via unchanged approved wrapper; each3600reservation is written before sbatch; failures retain it and stop without retry. Next submission waits for scheduler COMPLETED0:0 and the shared full predecessor artifact/ownership/numerical validator. Registry counts/operator inventory are checked, root activation remains external, and no unrelated-job mutation exists. Commands use argument arrays and constrained account choices; no shell interpolation or secret/environment dump is present. Full main release is not implied by this review.


## Final narrow delta review

All three initial findings are resolved. Driver pins exact plan/source/science, requests State%32 and supported Restarts accounting, submits with --no-requeue, and stops on restart or any non-COMPLETED0:0 terminal result. Reservation totals and unique ledger markers are checked before submission; ledger/inventory/state/submission/event writes now flush/fsync, with atomic replacement and directory fsync where applicable. Each3600 reservation remains durably recorded before sbatch, with no refunds or retries.

Directly inspected `test-driver-cpu.py` and `driver-cpu-tests.log`: four mocked CPU checks PASS, covering12 sequential submissions with pre-submission reservations and predecessor validation, full OUT_OF_MEMORY terminal stop, scheduler-restart stop, drift/pin guards and durable write behavior. No scheduler/driver execution or duplicate test reruns by this reviewer.

**No remaining must-fix findings.** Ready for root activation of this exact fixed execution driver and approved plan; this PASS itself submits no job or changes the ledger/registry/release. Existing source/science/calibration reviews remain separately authoritative.
