# Hand-back 78: A3 native adapter independent review

Agent: Codex independent reviewer. Ticket: approved plan-a3.md Task 4a native adapter subset. Status: handed-back.

## What changed

Scoped acceptance of the native HF forward/gradient adapter. The original nonblocking test gap is closed by the follow-up below. No implementation or test source was changed. The author report 76 was not read. No git command was run.

Commit from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report78-a3-native-review-handback.md`. Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report78-a3-native-review-handback.md`.

Inspected `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_native.py` and its owning test file, plus the relevant existing hooks and path-patching conventions and approved Task 4 semantics. Source SHA256: adapter `b87683892df31ec87fdfab21d005d955338082699020e86846268694a690362c`; tests `1bcbe0768579941b2f78efb7612ca2a58de2de41f686bf23d77082401ce4ce4a`.

No high or medium severity findings in this scope. The adapter reconstructs selected Q/K/V projection slices from true incoming residual leaves through RMSNorm and projection. K/V receiver identity is the KV group, independently selected branches can use different fixed residual values, unselected slices stay live, and caller patch tensors are detached into independent leaves. MLP input leaves also precede their norm. Readout uses differentiable FP32 final normalization/unembedding matching the inference convention. Frozen/eval admission prevents parameter gradients and model-state mutation; exception cleanup removes this call's hooks while preserving preexisting hooks. Padding and explicit readout positions are handled at the adapter boundary.

**Low, test coverage:** in `tests/test_a3_native.py:37`, the readout case perturbs row 0 position 2 while its scored readout is position 3. Both the analytic directional derivative and finite difference are zero, so that case cannot detect a broken readout Jacobian. Reproduction: use the existing parametrized readout case and inspect `(gradient * direction).sum()`. A useful strengthening is to perturb the actual readout position, require a nonzero derivative, and compare its finite difference. The independent active-position probe below supplies acceptance evidence for the current implementation, so this is not a Task 4a blocker.

**Caller contract for Task 4b:** with `grad=True`, every requested receiver becomes an independent leaf, as does every patched receiver. Returned `fp32_logits` and readout indices alone do not activate the READOUT leaf. Thus `capture_sites=[('q', L, H)]` safely gives a local branch VJP with downstream paths live. Adding `('readout',0,0)` to that request explicitly clamps the downstream readout and blocks upstream gradients; an observed zero upstream VJP then describes the joint clamped computation. Run local incoming-residual attribution for one active receiver branch at a time; do not request all receivers merely to observe their values. Use a separate intact capture for caches. Joint fixed-cache clamping is appropriate for the exact intervention estimand. This distinction is explicit in the adapter's activation rule and no ambiguity makes the single-receiver call unsafe.



Follow-up closure: the revised owning test now sets the readout perturbation position from `out["readout"][0]` and asserts that the absolute directional derivative exceeds `1e-4` before comparing finite differences. This closes the inactive-position case above. Only the requested receiver is active in each test call, so Q/K/V and MLP-input cases still retain live downstream readout paths; the readout case intentionally activates only its own readout leaf. The adapter SHA256 remains `b87683892df31ec87fdfab21d005d955338082699020e86846268694a690362c`; revised tests SHA256 is `eee521191f1b4504d39965bd1ae4fe66d929353a87e0b5ea21d6854dfc6aaee5`. No source was edited by this reviewer. No findings remain open in this narrow closure.

## How verified

All commands below ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder` on CPU, with no large model loading or network access. Shell sandbox startup failed before execution; the same read/test operations ran through the permitted escalation path.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_native.py -p no:cacheprovider -q
```

Observed: 18 passed in 13.21 seconds. The actual pinned NNsight 0.7 parity test executed.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_native.py -p no:cacheprovider -q
```

Observed: 17 passed, 1 skipped in 15.88 seconds. The skip is the explicit pinned-NNsight-version gate, not a native-model test skip. Three environment deprecation/dependency warnings were emitted.

Independent reviewer script `/tmp/a3_review_probe.py` uses a separate random tiny two-layer Llama with SDPA, a left-padded row, and an explicit earlier unpadded readout for that row. Its finite-difference intervention uses HF's actual norm module and manual projection-slice replacement on an ordinary HF forward, without calling the adapter reconstruction. Each tested direction has a nonzero effect. The same script checks FP32/BF16 intact versus gradient-enabled replay, grad-mode restoration, absent parameter gradients, and a jointly selected downstream readout leaf blocking an upstream Q VJP.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/a3_review_probe.py
```

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 /tmp/a3_review_probe.py
```

Observed in both environments, all assertions passed. Values agree across environments:

| Receiver | Token position | Analytic derivative | Independent central difference |
| --- | ---: | ---: | ---: |
| Q, layer 0, head 2 | 3 | -0.000235369 | -0.000240281 |
| K, layer 0, group 1 | 1 | -0.000679675 | -0.000677072 |
| V, layer 0, group 1 | 1 | 0.0817546 | 0.0817487 |
| MLP input, layer 0 | 3 | 0.0862113 | 0.0861641 |
| Readout | 3 | 1.69848 | 1.69831 |

Finite-difference step was 0.002 in each direction; tolerance was absolute 0.00002 plus 1 percent of derivative magnitude. Both dtypes had exactly zero maximum FP32-logit replay error. Parameters retained `grad=None`. A downstream readout leaf gave zero upstream gradient as intended. The first version of this reviewer script asserted the gradient must be `None`; padding's preserved live path instead produces an all-zero tensor. That reviewer assertion was corrected, and both corrected runs exited successfully. This was not an adapter failure.

Additional actual NNsight parity on tiny BF16 SDPA Llama:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/a3_review_nnsight_bf16.py
```

Observed: exact equality at seven captured sites (head, MLP, Q, K, V, MLP input, readout), native logits, and FP32 readout logits. The assertion requires installed NNsight 0.7.0. This complements the owning suite's FP32 eager parity.

The owning tests additionally exercise independent joint Q/K/V patches, preserved neighboring slices and padding, caller constants detached from autograd, projected head sums and down-projection hidden values, valid GQA group ranges, exception hook cleanup, invalid patch cleanup, and readout-clamp blocking of an upstream patch. Code inspection shows no changed-sender recursion: patch values are supplied whole residual constants and copied at entry to each selected branch. Summing edge deltas and constructing those constants remains the caller's later responsibility.

The report-number checker ran on this report. Its unresolved entries were manually read against the displayed pytest outputs, the independent scripts and their captured outputs, and the live usage JSON: report/task labels are identifiers; suite counts and durations are terminal observations; receiver indices, token positions, finite-difference settings and derivative values come from the reviewer script; baseline zeros come from its exact-equality assertions; usage values come from the live account check. No number is an efficacy estimate. The primary mirror was compared byte-for-byte with this worktree report.



Follow-up closure commands (same worktree, local CPU):

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_native.py -k receiver_vjp_matches -p no:cacheprovider -q
```

Observed: 5 passed, 13 deselected in 12.65 seconds.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_native.py -k receiver_vjp_matches -p no:cacheprovider -q
```

Observed: 5 passed, 13 deselected in 13.37 seconds, with the same three base environment warnings. All five receiver types executed in each environment; no skip occurred in this focused run. Full-suite author counts are not independently rerun or claimed in this closure. These closure counts/times come directly from the observed terminal outputs; the derivative threshold is read directly from the revised test.

## Execution evidence

- Job and cluster: local CPU pytest commands and the two reviewer scripts above; no Slurm job.
- Exit status: both pytest commands and all final reviewer script invocations exited 0. The initial reviewer probe's overstrict `None` assertion exited 1, then was corrected as described above.
- Counts: mgnp 18 of 18 owning tests passed; base 17 passed and 1 expected skip of 18 collected. Independent probes exercised all 5 receiver kinds in both environments and both dtypes for replay. Additional pinned NNsight probe compared all 7 requested sites.
- Baseline reproduction: intact versus reconstructed FP32 logits had maximum absolute error 0.0 against required 0.0 for FP32 and BF16 in both environments. Pinned NNsight BF16 SDPA captures/logits also had exact equality.
- Follow-up closure evidence: both focused pytest commands exited 0; each executed 5 of 5 selected receiver cases with 13 deselected, no skipped case. The source adapter was unchanged; the revised test fingerprint is recorded above. No scientific model result or new baseline measurement is claimed by this closure.
- Provenance: no scientific `run_manifest.json` or committed execution identity is claimed for these local random-model checks. Reviewed source fingerprints are above; no commit was supplied for the uncommitted adapter, and git was prohibited. These are bounded software acceptance checks, not a scientific run or real-model pilot.
- Usage checkpoint: live Codex weekly usage was 21 percent used, 79 percent remaining, reset 2026-11-06T16:07:41Z; `should_pause=false` at the 80-percent threshold.

## What is NOT done

No Task 4b integration, EAP-IG ranking, exact selected-edge set construction, edge deduplication/permutation testing, integration-node stability check, finite linear-circuit attribution test, or edge-budget selection is claimed. These remain required in the later edge orchestrator. The adapter only consumes caller-constructed fixed residual clamps.

No full-model pilot, GPU/Slurm/API work, benchmark assessment, utility scoring, scientific efficacy result, or complete edge implementation is claimed. Native dtype leaves retain the native BF16 quantization convention; BF16 finite-difference precision and full-model kernel/backend parity still belong to the admitted pilot. No broad repository suite, notebook, git operation, source edit, or subagent was used.

## Open questions

No blocking question for Task 4a scoped acceptance. Default: accept the native seam, preserve the local-VJP versus joint-clamp caller contract in Task 4b, and retain the strengthened active-position readout regression test. The requested test-gap closure is complete.
