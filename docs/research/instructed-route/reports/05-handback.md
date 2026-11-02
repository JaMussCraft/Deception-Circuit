# Hand-back 05: sender position masks in path patching (B1 ticket 2)

Agent: implementer, Opus. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B1-plan.md` section 5, ticket 2. Status: resolved.

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/component_analysis/path_patching.py`, `receiver_inputs` gains the keyword `sender_positions=None` plus two private helpers, `_sender_mask` and `_masked_sender`.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_path_patching_sender_positions.py`, a new file with 15 tiny-Llama tests.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/05-handback.md`, this hand-back.

The interface is one boolean mask, `[batch, seq]` or `[seq]`, applied to every key in `senders`. Sections 1.5 and 2.3 write one joint sender at one mask per call, so a per-sender mapping was not needed. Inside the mask the senders carry the corrupt capture. Outside it they carry their clean capture, not their live value, so a sender downstream of another masked sender stays exactly clean there. The merge happens before the forward, and the value is written at every position. This makes an all-True mask bit-identical to `None` and an all-False mask bit-identical to `senders=[]`. A non-bool mask raises TypeError and a mask of the wrong shape raises ValueError. Both errors name `sender_positions`.

## How verified

Baseline before the change, on the four existing path-patching test files:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_path_patching.py tests/test_path_patching_cli.py tests/test_path_patching_neutral_twin.py tests/test_path_patching_passes.py
```

Observed: 89 passed.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_path_patching.py tests/test_path_patching_cli.py tests/test_path_patching_neutral_twin.py tests/test_path_patching_passes.py
```

Observed: 55 passed, 5 skipped.

Red run of the new file before the implementation:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_path_patching_sender_positions.py
```

Observed: 12 failed, 2 passed. The failures were the unknown keyword. The 2 that passed were the mask-construction check and the index-mask refusal, which matched the unknown-keyword TypeError by name. After the implementation the same command gave 14 passed. A 15th test, for the `[seq]` mask form, was added afterwards and passed on its first run.

After the change, the new file plus the four existing files:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_path_patching_sender_positions.py tests/test_path_patching.py tests/test_path_patching_cli.py tests/test_path_patching_neutral_twin.py tests/test_path_patching_passes.py
```

Observed: 104 passed, 0 failed. That is 89 existing plus 15 new.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider -rs tests/test_path_patching_sender_positions.py tests/test_path_patching.py tests/test_path_patching_cli.py tests/test_path_patching_neutral_twin.py tests/test_path_patching_passes.py
```

Observed: 55 passed, 6 skipped, 0 failed. The new skip is the new file, which is skipped as designed because base 3.9 has nnsight 0.5.12 rather than the pinned 0.7.0. There are no regressions and no pre-existing failures in these files.

The new tests cover the following:

- An all-True mask gives `torch.equal` receiver inputs and logits to `None`, for one head, one MLP and three joint senders.
- An all-False mask is `torch.equal` to the `senders=[]` patch, and it is within 1e-4 of the clean Readout.
- For the last-layer MLP into the Readout, the Readout-only mask and its complement each match a plain clean forward. That forward replaces the MLP through `hooks.Replacement` at the same positions, within 1e-5.
- For a layer-0 head into the Readout, the Readout-only mask and its complement each match a frozen `capture_forward` with a `Replacement` at the same positions, within 1e-5. The complement equals clean, because a direct path into the Readout reads only the Readout row.
- For a layer-0 head into `k.1.0`, both masks match the frozen `Replacement` forward, and both differ from clean. This is the case where the complement carries signal.
- A `[seq]` mask is `torch.equal` to its `[batch, seq]` expansion.
- Wrong-shape and non-bool masks are refused by name.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- `patched_readout` and `positioned_effects` do not pass `sender_positions` through. The ticket owns only `receiver_inputs`. The tests compose pass 1 and pass 2 themselves.
- No CLI flag exposes sender masks in `path_patching.run()`. The plan routes masked runs through the new `route_closure.py`, which is another ticket.

## Open questions

- Should `patched_readout` and `positioned_effects` forward `sender_positions`, so that `route_closure.py` can call one function? Default: add a pass-through keyword in the route-closure ticket if its implementer needs it.
- Is one mask shared across all senders enough for section 1.5? It writes the quartet heads at the Readout, and the plan's K and V at post-clause positions are receiver-side masks. Default: yes. A per-sender mapping can be added later without breaking callers.
