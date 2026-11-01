# 189 — One-shot CPU finisher after exact recovery completion

Prepared only new `transfer-v5/final-eval5-audit/watch-final-audit.py` and `test_watch_final_audit.py`, plus this report. **Not activated; no actual child, Slurm query/submission, API/model/GPU work, reservation, cache/ledger/input mutation or bound-source edit.** Root finalizes config and activates after188 auditor review and this code review.

The finisher watches the exact recovery state for manifest `33ba99c1d08b3aa5aa9c886c820828ba40ce7b1b8bdebf8dcdef35fd5a018d63`. Root config binds recovery launch/manifest, PID, exact argv, `/proc` start ticks, state path, exact five remaining datasets, reviewed final auditor/index and their transitive immutable input/source hashes, finisher/test, and config bytes. Process identity uses read-only `/proc`, never a scheduler query. Polling is quiet60seconds with a maximum24h root-configured expiry. A dead/reused/zombie process with unresolved state stops; one immediate final-state reread handles the process exiting just after appending complete.

Only one final `complete` event at the end, after exactly five unique submitted jobs, their matching COMPLETED/0:0 terminal rows and matching validated rows in proper submission→terminal→validation order, allows the audit. Any stopped event, torn/malformed/rewritten/truncated state, mismatch, expired config, missing process without complete evidence, changed bound file or existing output prevents execution. There are no scientific thresholds or acquisition claims in this watcher.

On completion it requires two fresh distinct output paths under `final-eval5-audit/`, consumes exclusive permanent `final-audit-watch-001.used` with fsync, then invokes exactly one literal CPU command:

```bash
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/final-eval5-audit/audit-final-eval5.py --index /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/final-eval5-audit/frozen-input-index.json --output /ABSOLUTE/FRESH.json --markdown-output /ABSOLUTE/FRESH.md
```

There is no retry, GPU allocation, API access, Slurm operation, resume or service installation. Auditor186 itself opens outputs exclusively; pre-existing artifacts cannot be overwritten even by an intervening race. The child receives only PATH/HOME/USER/LOGNAME/LANG/LC_ALL/TMPDIR from the inherited environment, then offline flags, BLAS/OMP1 and `PYTHONDONTWRITEBYTECODE=1`. All API credentials/custom tokens are excluded. Output is captured without echoing environment or child text. The watcher prints only child exit status and output paths, and returns that exit status; a failed/incomplete audit is never described as acquisition success. CPU child timeout3600seconds consumes the once guard and stops without retry.

Root config fields (JSON; no template/config was finalized by this worker):

- `schema:1`, `reviewed:true`, nonempty `root_decision`.
- `created_unix`, `expires_unix` with current creation time and expiry no more than24h later.
- `recovery_pid:188657`, `recovery_start_ticks` as the exact string from field22 of `/proc/188657/stat`, `recovery_argv` exactly the command array in `fixed-paid-recovery-root-launch.json`.
- `state_path` exactly the activation record's recovery state; `expected_datasets` exactly the five manifest entries in order.
- `file_bindings`: SHA256 map containing finisher, its test, final186 helper/index, recovery manifest/root launch record and every `immutable_bindings` member of the index. Root binds only immutable artifacts; live state/cache/budget remain semantically audited. Config bytes are additionally bound by `--config-sha256` and rechecked on each poll.
- `output`, `markdown_output`: new absolute distinct files directly under `final-eval5-audit/`.
- `once_guard`: `/projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/final-eval5-audit/final-audit-watch-001.used`.
- `audit_argv`: exact literal command array shown above, with those chosen output paths.

Root verification command:

```bash
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/final-eval5-audit/watch-final-audit.py --config /ABSOLUTE/ROOT-CONFIG.json --config-sha256 EXACT_SHA --dry-run
```

Dry run validates bindings/config only; no waiting, process/scheduler/child calls or guard/output writes. Root alone may launch the same command without `--dry-run`, using its existing persistent session or absolute `/usr/bin/nohup` redirected to a new log. Root must not reset the guard after interruption. A stopped/expired watcher needs root reconciliation, with no automatic rerun.

Verification: test-first missing-finisher tests failed before implementation; event-order and process-exit/append-race regressions were also observed failing before fixes. **13 focused mock tests pass in both mgnp and base Python3.9.** Cases cover completion exactly once, stopped/malformed/incomplete ordering, helper/index changes, no-clobber outputs, stripped API credentials/offline/BLAS1, unresolved dead process, expiry, actual wait→complete, and the atomic final-state/process-exit race. Every subprocess transport is mocked; no auditor was executed by the worker. Source/runtime/helper/index remain unchanged.
