# Hand-back: Native differentiable receiver adapter

Agent: Codex worker. Ticket: approved `plan-a3.md`, Task 4a. Status: handed-back.

## What changed

The orchestrator owns commits. These worktree files are the complete implementation scope:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_native.py`: scoped native Hugging Face Llama forward, independent receiver residual leaves, differentiable final readout, projected head senders, whole MLP and down-projection input captures.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_native.py`: random CPU tiny-Llama contract tests.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report76-a3-native-adapter-handback.md`: this hand-back; mirrored to `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report76-a3-native-adapter-handback.md`.

`native_forward(model,batch,*,capture_sites,patches=None,grad=False)` requires every model module in eval mode and every base parameter frozen. The caller supplies the separately loaded pinned native model. It returns `logits` (native diagnostic), `fp32_logits` (differentiable metric), `outputs`, `incoming`, `additive`, `leaves`, and `readout`. Batch is a dictionary or object containing `input_ids`, `attention_mask`, and optional per-row `readout`. Readout positions must be valid unmasked tokens; defaults also support left padding.

Tuple site keys follow existing inference hooks. Heads are native pre-output-projection values; additive head captures multiply the matching output-projection columns into residual width. Receiver `incoming` caches are pre-layernorm residuals; receiver `outputs` are native projected or normalized hook values. K and V use unique KV-group indices. `neuron_hidden` is capture capability only.

`ResidualPatch(value,positions=None)` supplies a fixed full incoming residual, with an optional boolean token mask. Padding always stays live. In gradient mode, requested receiver sites and patched receiver sites receive independent detached interpolation leaves; callers differentiate `leaves`, not their original patch tensors. Each selected Q/K/V slice uses its own full norm/projection Jacobian. Other slices retain their live forward values. Reconstructed norms use a pure computation, avoiding reentry into installed capture hooks. Detached captures retain no additional graphs; consume and release each batch graph before the next forward.

The adapter supports frozen intact-delta branch clamps supplied by a caller. It never derives clamp values from changed senders. A fixed readout clamp intentionally blocks upstream changes. Causal residual-addition geometry requires equal source/receiver token positions and upstream module order; attention transport from K/V positions is a separate downstream effect.

Review addendum: the low test-coverage finding in `report78-a3-native-review-handback.md` is addressed in the owning test only. The readout finite-difference case now perturbs the actual validated `out["readout"][0]` position and requires the analytic directional derivative magnitude to exceed `1e-4`. The other receiver cases retain their original perturbation position. Production adapter code is unchanged; its SHA256 remains `b87683892df31ec87fdfab21d005d955338082699020e86846268694a690362c`.

## How verified

All commands below ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_native.py -p no:cacheprovider -q
```

Observed final result: `18 passed in 13.01s`, exit `0`. The actual pinned NNsight inference parity test ran without a skip. It compares native logits and head/MLP/Q/K/V/MLP-input/readout values against existing `capture_forward`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_native.py -p no:cacheprovider -q
```

Observed final result: `17 passed, 1 skipped, 3 warnings in 16.31s`, exit `0`. Base uses the older NNsight dependency, so its actual NNsight parity check explicitly skips; the native gradient tests run.

The initial test invocation failed at collection with `ModuleNotFoundError` for the absent implementation. A subsequent targeted regression failed when projection reconstruction reentered layernorm hooks and replaced intact caches. The pure native norm fixed that regression. Tests cover residual-coordinate central finite differences for every receiver kind; distinct semantic-position gradients; independently patched Q/K/V slices; padding exclusion and zero padding gradients; projected-head additivity; hidden captures; fixed readout blocking; strict frozen/eval contracts; invalid site/readout rejection; and hook cleanup after model and patch failures. The FP32 readout matches the existing inference convention exactly on the BF16 tiny model. No model parameter or caller patch constant receives a gradient.

Hand-back checks:

```bash
/u/swong2/.local/bin/research-session lint docs/research/specificity-ladder/reports/report76-a3-native-adapter-handback.md
/sw/external/python/anaconda3/bin/python3.9 scripts/check_report_numbers.py docs/research/specificity-ladder/reports/report76-a3-native-adapter-handback.md --strict
```

Observed: both exit `0`; the number checker reports no unresolved numbers.

Review-addendum checks used the same scoped commands above. Before moving the readout perturbation, adding the nonzero assertion caused the expected readout failure: `1 failed, 4 passed, 13 deselected`; the derivative was exactly zero. The command was:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_native.py -k receiver_vjp -p no:cacheprovider -q
```

After moving the readout perturbation, the full scoped commands above returned `18 passed in 7.51s` in mgnp and `17 passed, 1 skipped, 3 warnings in 15.74s` in base, both exit `0`. The analytic readout derivative is nonzero and agrees with the central finite difference under the existing tolerance. The skip and dependency warnings are unchanged. No production change was needed.

## Execution evidence

Local CPU unit tests only; no production research run occurred. Both test commands and observed summaries are above. No Slurm job, research output rows, or scientific baseline is claimed. No `run_manifest.json` was created, so this hand-back supplies implementation test evidence rather than a provenance-complete empirical result.

## What is NOT done

No edge integrated-gradient ranking, edge grid orchestration, exact edge-set construction, selection, pipeline, production parity pilot, or production memory/timing admission is implemented. Those remain Task 4b. The known-edge linear toy and full donor recovery checks belong to that later edge estimator. No neuron assessment is authorized or performed. No model weights were downloaded, and no GPU, API, notebook, git command, or full repository suite ran. Generic inference hooks remain unchanged.

The base environment's old NNsight skips actual inference-hook parity there; pinned mgnp runs that parity gate. Base emits existing dependency warnings about the cache environment variable, TensorFlow float type, and pandas bottleneck version. The adapter validates model mode and freezing, while revision/dtype/backend matching remains the caller's pinned-load responsibility. This is prospective adapter functionality, not evidence for specificity or attribution accuracy.

## Open questions

None requiring a user decision. Independent review accepted the adapter; its readout test-coverage gap is addressed by the addendum above. Default next step: orchestrator commit, then Task 4b integration against this explicit schema. Task 4b must sum and deduplicate frozen receiver deltas before constructing patches; duplicate edge rejection and permutation invariance belong there.
