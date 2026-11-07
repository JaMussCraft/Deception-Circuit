# Hand-back

## What changed

No operational artifacts were changed. Read-only inspection found the successor binding replacements and immutable GPU pins summarized below.

## How verified

Read the listed artifacts directly after using the scoped read-only sandbox fallback. No dynamic or scheduler verification was performed.

## Execution evidence

The initial default shell attempt failed during sandbox startup with `bwrap: Can't mkdir parents for /tmp/usertmp/swong2/codex-daemon-78031: Read-only file system`; the authorized read-only fallback then succeeded.

The existing `helper-bindings.json` pins GPU config path/SHA, packet, GPU execution and release paths, SSH/DTN, session and cache reference. `placement.r2.json` pins GPU job `50189932`, reservation `r-041`, account/cluster/partition/resources, source/groups/snapshot/launch packet hashes and output directory. Preserve these anchors and bytes.

For a successor support/helper, root must bind the actual new CPU job/config path and SHA in the successor bindings' `standing_config.path` and `standing_config.sha256`, retain the unchanged accepted CPU packet at `standing_packet`, point `state_directory` to the successor helper's own `r5/executions`, and compute fresh `helper_manifest_sha256` after the binding bytes settle. The actual CPU ID/config and READY evidence belong in fresh phase evidence and an append-only continuation attestation; `placement.r2.json`'s `standing_CPU_job_id` and `standing_config_sha256` are historical and stay unchanged. Keep GPU config path/SHA and reservation/job anchors untouched.

The current watcher hard-codes `root-model-phase-release-helper/r4/helper.py` and a SHA-256 of `helper-bindings.json`. For r5, update that helper path in the watcher to `root-model-phase-release-helper/r5/helper.py`, and bind/check the finalized successor bindings digest at both hash checks and the helper `--bindings-sha256` argument. It waits for actual `WAITING-bank.json`, invokes phase `bank`, then waits for `WAITING-prefix4.json` and invokes `prefix4`; no retarget or retry. Invocation shape: `python root-watch-phases.py` from the job directory. It dispatches `/u/swong2/.conda/envs/mgnp/bin/python <r5/helper.py> run-phase --phase <bank|prefix4> --bindings <successor helper-bindings.json> --bindings-sha256 <successor bindings SHA-256> --execute`.

## What is NOT done

- No artifacts were edited other than this required hand-back.
- No new CPU job, successor helper, binding, or continuation attestation was created or accepted.
- No commands changing state, git, SSH, scheduler, or tests were run.

## Open questions

The available artifacts do not establish the actual new CPU job/config values; root must populate them from its new allocation before review. HOLD remains in force until exact successor bindings and continuation evidence are reviewed.
