# Hand-back 86: Independent A3 edge-core review

Agent: Codex reviewer. Ticket: approved A3 Task 4b edge-core scope. Status: handed-back.

## What changed

Review only; no production or owning-test edits. The reviewed contract is Task 4 and the global semantic-position policies in the approved plan, with root's explicit ruling that primary bin attribution sums token contractions. The author handback was not read.

- Orchestrator-owned worktree report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report86-a3-edge-review-handback.md`.
- Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report86-a3-edge-review-handback.md`.
- Independent temporary probe: `/tmp/a3_edge_review_probe.py`.

**Disposition: accept the scoped edge core, with one low-severity numerical robustness finding.** No blocker was found in fixed-cache joint clamps, branch-local gradients, source signs, token summation, GQA handling, or cohort normalization. This acceptance does not admit a model-fitting or assessment run.

**Low: finite-score overflow in stability normalization.** At `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_edges.py:535`, the sum of absolute finite scores can overflow to infinity. Reproduce with twenty distinct valid edge records, eight-node scores all `8e306`, sixteen-node scores all `1e307`. The function reports `normalized_l1=0.0` and `stable=True`, although scaled arithmetic gives `0.20`, above the frozen threshold. Each input passes `math.isfinite`; the denominator sum is infinite and the numerator finite. Rescale both vectors by their maximum absolute score before summing, or refuse a nonfinite aggregate. Add a regression test. Severity is low because ordinary finite FP32 native contractions cannot produce scores this large; this is a public-helper robustness boundary, not evidence of incorrect native attribution.

Standards axis: no documented-standard violation found within scope. Spec axis: no blocking scoped requirement missing; the numerical helper issue above is nonblocking.

## How verified

All commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`. Only CPU random tiny models were instantiated.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_edges.py tests/test_a3_native.py -p no:cacheprovider -q
```

Observed: `42 passed, 1 warning in 14.54s`, exit zero.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_edges.py tests/test_a3_native.py -p no:cacheprovider -q
```

Observed: `41 passed, 1 skipped, 3 warnings in 19.36s`, exit zero. The sole skip is the separate native NNsight-version inference parity test. Native Q/K/V, MLP-input and readout gradient/finite-difference tests actually ran. The edge test comparing a single readout receiver against existing two-pass path patching passed in both environments.

```bash
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python /tmp/a3_edge_review_probe.py
```

```bash
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 /tmp/a3_edge_review_probe.py
```

Both initial probes exited zero. They instrument actual native forwards: all sixteen integration forwards had exactly one receiver leaf, each previous leaf was unreachable before the next forward, and no final leaf survived attribution return. Three invalid canonical-label cases were rejected: float labels, an out-of-range label, and identical opposite/honest labels. Independent single-row scoring reproduced the caller weights `0.25/0.75`; scores in both environments were `[-0.0011615126259130193, 1.005716751478758e-05]`. Identical nonzero `1e-30` scores yielded finite zero relative L1 and stable overlap. Initial overflow probes used `9e306`; the final mgnp probe sharpened that reproduction to `8e306` so the mathematically correct relative L1 is strictly outside the acceptance threshold. The first invocation omitted `PYTHONPATH=.` and failed import before executing any probe; the commands above corrected it.

Code and test inspection also covered:

- Native receiver isolation: only `capture_sites=[r]` is gradient-active, with downstream readout and branches live; the pre-norm leaf differentiates the full selected norm/projection Jacobian. Base model parameters stay frozen.
- Fixed-cache clamps: intact and donor captures are separate, detached and retained on CPU; every selected sender delta uses those captures. Receiver deltas are grouped and deterministically ordered. Branch slices are merged once by the native adapter, and unselected slices remain live.
- Joint behavior: two senders into one receiver, selected chains, downstream readout blocking, disjoint Q/K/V selections, identity replay, edge permutation invariance, and actual effective receiver values are covered by passing tiny-native tests.
- Geometry and maps: forward order, same-token residual endpoints, deduplicated GQA receivers, supported nonempty positions, padding, duplicate edges/maps, changed geometry, cross-bin physical aliases and forbidden D/I splices are checked. Explicit IOI clean-recipient/corrupt-donor ids and streams pass, while a changed donor id fails. Maps are caller-supplied supported builder records; this core checks identity/index consistency rather than regenerating builder semantics or binding prompt bytes itself.
- Attribution: condition-minus-neutral source deltas contract with canonical opposite-minus-honest VJPs. Tokens sum within a frozen cell, while rows use cohort weights. Explicit weights sum to one over the iterable; ragged token counts are exposed. The complete linear toy has causal score `10.0`, dead score `0.0`, and full donor endpoint recovery. This endpoint guarantee is not asserted for incomplete production graphs.
- Stability: unchanged scores, exact L1 threshold, a failure just beyond it, sign reversal, empty candidates, zero scores, nonfinite inputs and changed geometry are covered. Tiny-native eight-versus-sixteen comparison passes. Weak nonzero equality is only numerical agreement, not evidence of meaningful attribution power.

Reviewed SHA256 fingerprints:

```text
cfb95f2fc24ed4e3dff1d7c90abb5ce9a7c44537acd3c761fb2fdac8d0d49e8a  component_analysis/a3_edges.py
b87683892df31ec87fdfab21d005d955338082699020e86846268694a690362c  component_analysis/a3_native.py
315db064b5341358391416fa7f4f13c93189c5a67fb2721fa2f5813dcd8b3225  tests/test_a3_edges.py
eee521191f1b4504d39965bd1ae4fe66d929353a87e0b5ea21d6854dfc6aaee5  tests/test_a3_native.py
```

## Execution evidence

Local CPU review only; no scientific dataset run is claimed.

- Job id and cluster: none; local commands above.
- Exit codes: both scoped pytest commands and both initial independent probes returned zero. The final mgnp overflow stress probe also returned zero and reproduced the incorrect stable result reported above.
- Row counts: scoped suite collected forty-two cases; mgnp ran all forty-two, base ran forty-one and skipped the separate NNsight parity case. Independent native probes used two random toy rows, two receiver kinds and eight integration nodes each.
- Baseline reproduces: the two independent probe environments returned the same two weighted scores displayed above. Existing empty-edge and identity-donor replay tests compare patched against intact logits and passed in both environments.
- Provenance file: no scientific `run_manifest.json` was created; source fingerprints above identify the reviewed bytes. Scientific efficacy and deployment-scale parity remain not yet verified.
- Live Codex usage checkpoint: used 23 percent, remaining 77 percent, pause false; reset `2026-11-06T16:07:41+00:00`.

## What is NOT done

No production edits, git commands, subagents, GPU/Slurm/API work, large pretrained weights, notebook execution or broad test suite. No full-shape gradient timing/memory pilot. No train/validation orchestration, bootstrap fit ranking, exact validation budget selection, matched-null family, frozen transfer panel or assessment admission. Those are deferred work, not core defects. No scientific specificity result is inferred from these toy checks. No production donor endpoint guarantee is asserted.

## Open questions

- Default: accept Task 4b core and retain the overflow fix as a low-severity helper follow-up, with a scaled-arithmetic test before wider reuse.
- Root ruling: source authentication belongs to the later frozen-design/builder adapter. Before model execution that adapter must bind actual input tokens, masks, readouts and maps to frozen source bytes and check utility-bin applicability. The low-level core enforces its documented row identities, token bounds, canonical labels, position metadata and supplied mapping structure; these are not full source authentication. No permission to synthesize utility clause maps follows from this API.

The report-number checker output was manually reconciled: case counts, scores, node counts and durations come from the displayed tests and probe; threshold constants come from the approved plan; line references and fingerprints are source identifiers; the overflow magnitudes are synthetic review inputs, not observed scientific effects.

Checker reconciliation: its four unresolved entries are report identifier 86, approved plan Task 4, and live usage percentages 23 spent and 77 remaining from the account-limit JSON. All are accounted for; none is an efficacy estimate.


**Scoped closure: stability aggregate arithmetic.** Status remains handed-back. The low-severity overflow finding above is closed; the earlier finding and follow-up recommendation describe the pre-fix source. The revised helper rejects nonfinite denominator, absolute-difference sum, or ratio with `ValueError`, even when every individual input score is finite. Rejecting those unsupported inputs resolves the false-stability issue without changing the frozen ordinary thresholds. No other accepted edge semantics were reopened, and the frozen-design adapter provenance obligation still applies.

Closure commands, each run from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_edges.py -p no:cacheprovider -q
```

Observed: `27 passed, 1 warning in 14.60s`, exit zero.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_edges.py -p no:cacheprovider -q
```

Observed: `27 passed, 3 warnings in 18.75s`, exit zero. Both runs executed every edge case, with no skips. These runs include the three newly added aggregate-overflow regression cases and the unchanged exact `0.10` boundary test. The author's reported pre-fix red executions were not independently rerun.

```bash
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python /tmp/a3_stability_closure_probe.py
```

```bash
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 /tmp/a3_stability_closure_probe.py
```

Both model-free independent probes exited zero. The original large finite-score reproduction, twenty `8e306` versus `1e307` scores, now rejects with `nonfinite stability aggregate denominator`. Single-edge `1e308` versus `-1e308` rejects the difference sum, and `1e308` versus `1e-308` rejects the ratio. Ordinary identical scores remain stable with relative L1 zero; twenty `9.0` versus `10.0` scores retain exact relative L1 `0.1` and pass; `8.99` versus `10.0` remains outside the threshold and fails; weak equal `1e-30` scores remain stable with relative L1 zero. Empty and all-zero sets retain their previous explicit statuses. The last decimal of the outside-threshold relative L1 differs across environments, without changing the decision.

Closure execution evidence: local commands only, all exit zero; twenty-seven edge tests expected and observed in each environment. Both model-free probes reproduce the same ordinary pass/fail baseline decisions stated above. No scientific rows, pretrained model, GPU/job/API work, production edits, or new scientific provenance manifest. Revised source SHA256:

```text
fbda1700cd646807de52533764cc470ad47f10aeb511db39b628fcc571b2ad66  component_analysis/a3_edges.py
048f123bd701c38c48a4f89339ca9050f065eee1890e45e4cf839c7e55f35be0  tests/test_a3_edges.py
```

Closure numeric-source reconciliation: suite counts and elapsed times are terminal observations; all overflow magnitudes and ordinary score pairs are synthetic probe inputs; thresholds are unchanged approved settings. No finding remains open within this scoped review.
